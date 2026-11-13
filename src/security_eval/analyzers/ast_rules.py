"""Custom AST rules (Member 2). Source is parsed as data; it is never imported or executed.

All rules use the same intraprocedural approximation of "untrusted input": a value is
*input-derived* if it is a parameter of the enclosing function, a call to ``input()``, or a
local variable assigned (directly or transitively) from an expression that contains one.
To add a rule, write ``check(tree, ctx) -> list[finding]`` and append a ``Rule`` to RULES.
"""
import ast
from dataclasses import dataclass
from typing import Callable

RULESET_VERSION = "0.2.0"
SQL_METHODS = {"execute", "executemany", "executescript"}
SHELL_SINKS = {"os.system", "os.popen", "subprocess.getoutput", "subprocess.getstatusoutput"}
PROCESS_SINKS = {"subprocess.run", "subprocess.call", "subprocess.check_call",
                 "subprocess.check_output", "subprocess.Popen"}
FILE_OPEN_FUNCTIONS = {"open", "io.open", "os.open", "codecs.open"}
FILE_READ_METHODS = {"open", "read_bytes", "read_text"}
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
LOOPS = (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


class Context:
    """Per-file helpers: source text, parent links, import aliases and per-scope taint."""

    def __init__(self, tree: ast.Module, source: str):
        self.source = source
        self.parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        self.aliases = {}  # local name -> qualified name, e.g. "sp" -> "subprocess"
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.aliases[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom) and node.module:
                for a in node.names:
                    self.aliases[a.asname or a.name] = f"{node.module}.{a.name}"
        self._taint = {}

    def qualified_name(self, func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            return self.aliases.get(func.id, func.id)
        if isinstance(func, ast.Attribute):
            base = self.qualified_name(func.value)
            return f"{base}.{func.attr}" if base else None
        return None

    def scope(self, node: ast.AST) -> ast.AST:
        while node in self.parent and not isinstance(node, FUNCTIONS):
            node = self.parent[node]
        return node

    def tainted(self, scope: ast.AST) -> set[str]:
        if scope not in self._taint:
            names = set()
            if isinstance(scope, FUNCTIONS):
                args = scope.args
                names = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
                names |= {a.arg for a in (args.vararg, args.kwarg) if a}
            self._taint[scope] = names
            assignments = [n for n in ast.walk(scope)
                           if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign,
                                             ast.NamedExpr, ast.For, ast.comprehension))]
            changed = True
            while changed:  # flow-insensitive fixpoint: loops and reassignments are approximated
                changed = False
                for node in assignments:
                    value = getattr(node, "value", None) or getattr(node, "iter", None)
                    if value is None or not self.derived(value, scope):
                        continue
                    targets = getattr(node, "targets", None) or [node.target]
                    for target in targets:
                        for name in ast.walk(target):
                            if isinstance(name, ast.Name) and name.id not in names:
                                names.add(name.id)
                                changed = True
        return self._taint[scope]

    def derived(self, expr: ast.AST, scope: ast.AST) -> bool:
        names = self._taint.get(scope) if scope in self._taint else self.tainted(scope)
        for node in ast.walk(expr):
            if isinstance(node, ast.Name) and node.id in names:
                return True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                return True
        return False

    def inside_loop(self, node: ast.AST, scope: ast.AST) -> bool:
        while node is not scope and node in self.parent:
            node = self.parent[node]
            if isinstance(node, LOOPS):
                return True
        return False

    def finding(self, rule: "Rule", node: ast.AST, severity: str, message: str) -> dict:
        segment = ast.get_source_segment(self.source, node) or ast.unparse(node)
        return {"rule_id": rule.rule_id, "cwe": rule.cwe, "severity": severity,
                "confidence": "medium", "message": message, "line": node.lineno,
                "evidence": " ".join(segment.split())[:300]}


def _first_arg(call: ast.Call, keyword: str) -> ast.expr | None:
    if call.args:
        return call.args[0]
    return next((k.value for k in call.keywords if k.arg == keyword), None)


def check_sql(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr in SQL_METHODS):
            continue
        query = _first_arg(call, "sql")
        if query is None or isinstance(query, ast.Constant):
            continue
        if ctx.derived(query, ctx.scope(call)):
            findings.append(ctx.finding(SQL_RULE, call, "high",
                f"SQL text passed to .{call.func.attr}() is built from input-derived data; "
                "use a constant query with bound parameters (e.g. '?' placeholders)."))
    return findings


def _has_allowlist_check(ctx: Context, scope: ast.AST) -> bool:
    """True if the program position of the input is compared with non-input values.

    Length checks, substring tests, empty-string tests and per-character loops do not count.
    """
    for node in ast.walk(scope):
        if not (isinstance(node, ast.Compare) and len(node.ops) == 1
                and isinstance(node.ops[0], (ast.Eq, ast.NotEq, ast.In, ast.NotIn))):
            continue
        left, allowed = node.left, node.comparators[0]
        first_item = (isinstance(left, ast.Subscript) and isinstance(left.slice, ast.Constant)
                      and left.slice.value == 0)
        if not (isinstance(left, ast.Name) or first_item):
            continue
        if not ctx.derived(left, scope) or ctx.derived(allowed, scope) or ctx.inside_loop(node, scope):
            continue
        if isinstance(allowed, ast.Constant) and (not allowed.value or isinstance(node.ops[0], (ast.In, ast.NotIn))):
            continue
        return True
    return False


def check_command(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        name = ctx.qualified_name(call.func)
        if name not in SHELL_SINKS and name not in PROCESS_SINKS:
            continue
        command = _first_arg(call, "args" if name in PROCESS_SINKS else "cmd")
        if command is None or not ctx.derived(command, ctx.scope(call)):
            continue
        shell = name in SHELL_SINKS or any(
            k.arg == "shell" and not (isinstance(k.value, ast.Constant) and not k.value.value)
            for k in call.keywords)
        if shell:
            findings.append(ctx.finding(COMMAND_RULE, call, "high",
                f"{name}() passes an input-derived command to a shell; shell metacharacters "
                "in the input may run additional commands."))
        elif not (isinstance(command, (ast.List, ast.Tuple)) and command.elts
                  and isinstance(command.elts[0], ast.Constant)):
            if _has_allowlist_check(ctx, ctx.scope(call)):
                findings.append(ctx.finding(COMMAND_RULE, call, "low",
                    f"{name}() executes an input-derived program after an allowlist-style "
                    "comparison; verify that the check covers every path to this call."))
            else:
                findings.append(ctx.finding(COMMAND_RULE, call, "medium",
                    f"{name}() executes a program whose name is input-derived, and no "
                    "allowlist-style comparison was found."))
    return findings


def _linked_scopes(tree: ast.Module, scope: ast.AST) -> list[ast.AST]:
    """The scope plus same-module functions connected to it by calls, in either direction."""
    functions = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    links = {}
    for caller in [tree, *functions.values()]:
        for call in ast.walk(caller):
            if isinstance(call, ast.Call):
                callee = functions.get(getattr(call.func, "id", getattr(call.func, "attr", None)))
                if callee is not None and caller is not tree:
                    links.setdefault(caller, set()).add(callee)
                    links.setdefault(callee, set()).add(caller)
    linked = [scope]
    for current in linked:  # the list grows while iterating (breadth-first search)
        linked += [n for n in links.get(current, ()) if n not in linked]
    return linked


def _mentions_separator(expr: ast.expr, nodes: list[ast.AST]) -> bool:
    names = {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}
    values = [expr] + [n.value for n in nodes if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in names for t in n.targets)]
    for value in values:
        for node in ast.walk(value):
            if isinstance(node, ast.Attribute) and node.attr == "sep":
                return True
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and (
                    node.value == "" or "/" in node.value):  # "" covers os.path.join(base, "")
                return True
    return False


def _path_guards(ctx: Context, scopes: list[ast.AST]) -> dict:
    nodes = [n for scope in scopes for n in ast.walk(scope)]
    guards = {"resolved": False, "contained": False, "prefix": False}
    for node in nodes:
        if isinstance(node, ast.Compare) and any(
                isinstance(n, ast.Attribute) and n.attr == "parents" for c in node.comparators for n in ast.walk(c)):
            guards["contained"] = True
        if not isinstance(node, ast.Call):
            continue
        attr = getattr(node.func, "attr", None)
        name = ctx.qualified_name(node.func)
        if attr == "resolve" or name == "os.path.realpath":
            guards["resolved"] = True
        if attr in ("is_relative_to", "relative_to") or name == "os.path.commonpath":
            guards["contained"] = True
        if name == "os.path.commonprefix":
            guards["prefix"] = True
        if attr == "startswith" and node.args and not isinstance(node.args[0], (ast.Constant, ast.Tuple)):
            guards["contained" if _mentions_separator(node.args[0], nodes) else "prefix"] = True
    return guards


def check_path(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        scope = ctx.scope(call)
        name = ctx.qualified_name(call.func)
        if name in FILE_OPEN_FUNCTIONS:
            path = _first_arg(call, "file")
        elif isinstance(call.func, ast.Attribute) and call.func.attr in FILE_READ_METHODS:
            path = call.func.value
        else:
            continue
        if path is None or not ctx.derived(path, scope):
            continue
        guards = _path_guards(ctx, _linked_scopes(tree, scope))
        if guards["contained"] and guards["resolved"]:
            continue
        if guards["contained"]:
            severity, problem = "medium", "the containment check does not resolve symlinks"
        elif guards["prefix"]:
            severity, problem = "medium", "a plain string-prefix check also accepts sibling directories"
        else:
            severity, problem = "high", "no containment check on the resolved path was found"
        findings.append(ctx.finding(PATH_RULE, call, severity,
            f"File access uses an input-derived path and {problem}."))
    return findings


@dataclass(frozen=True)
class Rule:
    rule_id: str
    cwe: str
    description: str
    limitations: str
    check: Callable[[ast.Module, Context], list[dict]]


SQL_RULE = Rule(
    "AST-SQL-001", "CWE-089",
    "A DB-API .execute/.executemany/.executescript call whose SQL text (first argument) is "
    "derived from a function parameter or input() instead of being a constant.",
    "Intraprocedural and flow-insensitive: misses taint passed through other functions, "
    "attributes, containers or globals; cannot tell whether the input was sanitized or is "
    "trusted; any method named execute is treated as a SQL sink.", check_sql)
COMMAND_RULE = Rule(
    "AST-CMD-001", "CWE-078",
    "A subprocess/os command call whose command is input-derived and either runs through a "
    "shell (shell=True, os.system, os.popen, getoutput) or selects the program to run.",
    "An allowlist-style comparison lowers the severity to low, but the rule cannot prove the "
    "check is correct or precedes the call; lists with a constant program name are not "
    "reported (argument injection is out of scope); shell=<variable> is treated as "
    "shell=True; os.exec*/spawn* and dynamic imports are not covered.", check_command)
PATH_RULE = Rule(
    "AST-PATH-001", "CWE-022",
    "File access through an input-derived path without a recognized containment check on "
    "the symlink-resolved path (high: no check; medium: symlinks unresolved or prefix check).",
    "Recognizes resolve/realpath with is_relative_to, relative_to, commonpath, parents or a "
    "separator-aware startswith in the same or call-linked functions, but cannot prove the "
    "check guards this access or that its result is enforced; a trusted directory parameter "
    "also counts as input; concurrent symlink races are out of scope.", check_path)
RULES = (SQL_RULE, COMMAND_RULE, PATH_RULE)


def scan(code: bytes | str) -> list[dict]:
    """Return contract-shaped findings sorted by line. Raises SyntaxError for invalid code."""
    tree = ast.parse(code)
    source = code.decode("utf-8", errors="replace") if isinstance(code, bytes) else code
    ctx = Context(tree, source)
    findings = [f for rule in RULES for f in rule.check(tree, ctx)]
    return sorted(findings, key=lambda f: (f["line"], f["rule_id"]))
