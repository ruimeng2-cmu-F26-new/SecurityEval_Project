"""Custom AST rules (Member 2). Source is parsed as data; it is never imported or executed.

All rules use the same intraprocedural approximation of "untrusted input": a value is
*input-derived* if it is a parameter of the enclosing function, a call to ``input()``, or a
local variable assigned (directly or transitively) from an expression that contains one.
To add a rule, write ``check(tree, ctx) -> list[finding]`` and append a ``Rule`` to RULES.
"""
import ast
import re
import stat
from dataclasses import dataclass
from typing import Callable

RULESET_VERSION = "0.4.0"
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


# --- Rules added in rule set 0.3.0 for the 15-task experiment --------------------------------

SAFE_TAR_FILTERS = {"data", "tar", "tarfile.data_filter", "tarfile.tar_filter"}
EVAL_VALIDATORS = {"re.fullmatch", "re.match", "ast.parse", "ast.walk", ".fullmatch", ".match", "all"}
CLOCK_SOURCES = {"time.time", "time.time_ns", "time.monotonic", "time.perf_counter", "os.getpid",
                 "datetime.now", "datetime.utcnow", "datetime.datetime.now", "datetime.datetime.utcnow"}
DIGESTS = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_224", "sha3_256", "sha3_384",
           "sha3_512", "blake2b", "blake2s", "new"}
KDFS = {"hashlib.pbkdf2_hmac": 2, "hashlib.scrypt": None}  # position of the salt argument, if positional
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
LOG_SANITIZERS = {".replace", ".translate", ".splitlines", ".isprintable", "repr", "ascii", "re.sub", "json.dumps"}
HTML_ESCAPERS = {"escape", "quoteattr", "clean", "conditional_escape", "escape_html"}
REGEX_FUNCTIONS = {"re.sub", "re.subn", "re.compile", "re.search", "re.findall", "re.finditer", "re.split",
                   "re.match", "re.fullmatch"}
HTML_TEXT = re.compile(r"<[A-Za-z/!]")
DOMAIN = re.compile(r"[A-Za-z0-9-]+\.[A-Za-z]{2,}")
UNESCAPED_DOT = re.compile(r"[A-Za-z0-9]\.[A-Za-z]{2,}")
URL_NAME = re.compile(r"url|next|redirect|target|location|return_to|dest|goto", re.I)


def _calls(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _seen_calls(ctx: Context, scopes: list[ast.AST]) -> set[str]:
    """Qualified names of the calls in these scopes, plus '.method' for every attribute call."""
    seen = set()
    for call in (c for scope in scopes for c in _calls(scope)):
        name = ctx.qualified_name(call.func)
        if name:
            seen.add(name)
        if isinstance(call.func, ast.Attribute):
            seen.add("." + call.func.attr)
    return seen


def _strings(scopes: list[ast.AST]) -> list[str]:
    return [n.value for scope in scopes for n in ast.walk(scope)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _constant_text(tree: ast.Module, expr: ast.expr | None) -> str | None:
    """A string literal, or a name assigned exactly one string literal anywhere in the module."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == expr.id for t in n.targets)]
        if len(values) == 1:
            return _constant_text(tree, values[0]) if not isinstance(values[0], ast.Name) else None
    return None


def _random_source(name: str) -> bool:
    return (name in ("os.urandom", "os.getrandom", "uuid.uuid4", "random.SystemRandom")
            or name.startswith("secrets."))


def check_eval(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func)
        if name not in ("eval", "exec", "builtins.eval", "builtins.exec") or not call.args:
            continue
        scope = ctx.scope(call)
        if isinstance(call.args[0], ast.Constant) or not ctx.derived(call.args[0], scope):
            continue
        if _seen_calls(ctx, _linked_scopes(tree, scope)) & EVAL_VALIDATORS:
            findings.append(ctx.finding(EVAL_RULE, call, "low",
                f"{name}() runs input-derived text after a validation step; verify that the "
                "validation admits nothing but the intended syntax."))
        else:
            findings.append(ctx.finding(EVAL_RULE, call, "high",
                f"{name}() runs input-derived text as Python code and no validation was found; "
                "restricting builtins does not prevent code execution."))
    return findings


def check_tar(tree: ast.Module, ctx: Context) -> list[dict]:
    if not any(v.split(".")[0] == "tarfile" for v in ctx.aliases.values()):
        return []
    findings = []
    for call in _calls(tree):
        if not (isinstance(call.func, ast.Attribute) and call.func.attr in ("extractall", "extract")):
            continue
        scopes = _linked_scopes(tree, ctx.scope(call))
        chosen = next((k.value for k in call.keywords if k.arg == "filter"), None)
        if chosen is not None:
            label = chosen.value if isinstance(chosen, ast.Constant) else ctx.qualified_name(chosen)
            if label in SAFE_TAR_FILTERS:
                continue
            if label not in ("fully_trusted", "tarfile.fully_trusted_filter"):
                findings.append(ctx.finding(TAR_RULE, call, "low",
                    "Archive extraction uses a custom filter; verify that it rejects entries "
                    "that leave the destination."))
                continue
        elif any(isinstance(n, ast.Attribute) and n.attr == "extraction_filter" and isinstance(n.ctx, ast.Store)
                 for scope in scopes for n in ast.walk(scope)):
            continue
        guards = _path_guards(ctx, scopes)
        name_checks = ".isabs" in _seen_calls(ctx, scopes) or ".." in _strings(scopes)
        if guards["contained"] and guards["resolved"]:
            severity, problem = "low", "after a containment check on resolved paths; verify it also covers link entries"
        elif guards["contained"] or guards["prefix"] or name_checks:
            severity, problem = "medium", "after an incomplete entry-name check (symlink entries or prefix matches may escape)"
        else:
            severity, problem = "high", "without an extraction filter or any check of the entry paths"
        findings.append(ctx.finding(TAR_RULE, call, severity, f"Archive entries are extracted {problem}."))
    return findings


def check_random(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func) or ""
        if name == "uuid.uuid1":
            findings.append(ctx.finding(RANDOM_RULE, call, "high",
                "uuid.uuid1() is built from the clock and the host address and is predictable."))
        elif name.startswith("random.") and name != "random.SystemRandom":
            findings.append(ctx.finding(RANDOM_RULE, call, "high",
                f"{name}() uses the Mersenne Twister generator, whose output is predictable; "
                "use the secrets module for security-sensitive values."))
    for scope in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        seen = _seen_calls(ctx, _linked_scopes(tree, scope))
        hashes = [c for c in _calls(scope) if (ctx.qualified_name(c.func) or "").startswith("hashlib.")]
        if hashes and seen & CLOCK_SOURCES and not any(_random_source(n) for n in seen):
            findings.append(ctx.finding(RANDOM_RULE, hashes[0], "medium",
                "A value is derived by hashing the clock or process ID with no unpredictable input."))
    return findings


def check_password_hash(tree: ast.Module, ctx: Context) -> list[dict]:
    module_calls = _seen_calls(ctx, [tree])
    salted = any(_random_source(n) or n.startswith("random.") for n in module_calls)
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func) or ""
        scope = ctx.scope(call)
        if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if name in KDFS:
            position = KDFS[name]
            salt = next((k.value for k in call.keywords if k.arg == "salt"), None)
            if salt is None and position is not None and len(call.args) > position:
                salt = call.args[position]
            if isinstance(salt, ast.Constant) or not salted:
                findings.append(ctx.finding(HASH_RULE, call, "high",
                    f"{name}() is called with a salt that is constant or not randomly generated; "
                    "equal passwords produce equal stored values."))
            continue
        if not (name in ("hmac.new", "hmac.digest") or (name.startswith("hashlib.") and name[8:] in DIGESTS)):
            continue
        values = call.args + [k.value for k in call.keywords]
        updates = [a for c in _calls(scope) if isinstance(c.func, ast.Attribute) and c.func.attr == "update"
                   for a in c.args]
        if salted or not any(ctx.derived(v, scope) for v in values + updates):
            continue
        findings.append(ctx.finding(HASH_RULE, call, "high",
            f"{name}() digests input-derived data and the module generates no random salt; "
            "equal passwords produce equal stored values."))
    return findings


def _mode_bits(ctx: Context, expr: ast.expr) -> int:
    """Permission bits that are certainly set; unknown operands contribute nothing."""
    if isinstance(expr, ast.Constant) and type(expr.value) is int:
        return expr.value
    name = ctx.qualified_name(expr) if isinstance(expr, (ast.Name, ast.Attribute)) else None
    if name and name.startswith("stat.S_I"):
        return getattr(stat, name[5:], 0)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):
        return _mode_bits(ctx, expr.left) | _mode_bits(ctx, expr.right)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitAnd):
        return _mode_bits(ctx, expr.left) & _mode_bits(ctx, expr.right)
    return 0


def check_permissions(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func)
        keyword = next((k.value for k in call.keywords if k.arg == "mode"), None)
        if name in ("os.chmod", "os.fchmod", "os.lchmod"):
            mode = keyword or (call.args[1] if len(call.args) > 1 else None)
        elif name == "os.open":
            mode = keyword or (call.args[2] if len(call.args) > 2 else None)
        elif name == "os.umask" and call.args:
            if isinstance(call.args[0], ast.Constant) and not call.args[0].value & 0o022:
                findings.append(ctx.finding(PERMISSION_RULE, call, "medium",
                    "os.umask() no longer masks group/other write permission for files created afterwards."))
            continue
        elif isinstance(call.func, ast.Attribute) and call.func.attr == "chmod":
            mode = keyword or (call.args[0] if call.args else None)
        else:
            continue
        if mode is not None and _mode_bits(ctx, mode) & 0o022:
            findings.append(ctx.finding(PERMISSION_RULE, call, "high",
                f"File mode {_mode_bits(ctx, mode) & 0o7777:04o} grants write permission to group or other users."))
    return findings


def check_log(tree: ast.Module, ctx: Context) -> list[dict]:
    findings = []
    for call in _calls(tree):
        if not (isinstance(call.func, ast.Attribute) and call.func.attr in LOG_METHODS):
            continue
        receiver = (ctx.qualified_name(call.func.value) or "").lower()
        if "log" not in receiver:
            continue
        scope = ctx.scope(call)
        values = [v for v in call.args + [k.value for k in call.keywords] if ctx.derived(v, scope)]
        if not values:
            continue
        converted = any(isinstance(n, ast.FormattedValue) and n.conversion in (ord("r"), ord("a"))
                        for v in values for n in ast.walk(v))
        template = call.args[0].value if call.args and isinstance(call.args[0], ast.Constant) else ""
        if (converted or (isinstance(template, str) and "%r" in template and "%s" not in template)
                or _seen_calls(ctx, _linked_scopes(tree, scope)) & LOG_SANITIZERS):
            findings.append(ctx.finding(LOG_RULE, call, "low",
                "Input-derived data is logged after a conversion step; verify that carriage "
                "returns and line feeds cannot reach the log."))
        else:
            findings.append(ctx.finding(LOG_RULE, call, "high",
                "Input-derived data is written to the log unchanged; a line break in it forges "
                "a separate log entry."))
    return findings


def _html_values(node: ast.AST, parent: ast.AST | None) -> list[ast.expr] | None:
    """Expressions interpolated into a string that contains HTML markup, else None."""
    def markup(e):
        return isinstance(e, ast.Constant) and isinstance(e.value, str) and HTML_TEXT.search(e.value)

    def operands(e):
        return operands(e.left) + operands(e.right) if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add) else [e]

    if isinstance(node, ast.JoinedStr) and any(markup(v) for v in node.values):
        return [v.value for v in node.values if isinstance(v, ast.FormattedValue)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Add):
            return None  # reported once, at the outermost concatenation
        parts = operands(node)
        if any(markup(p) for p in parts) and not any(isinstance(p, ast.JoinedStr) for p in parts):
            return [p for p in parts if not isinstance(p, ast.Constant)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and markup(node.left):
        return list(node.right.elts) if isinstance(node.right, ast.Tuple) else [node.right]
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format"
            and markup(node.func.value)):
        return node.args + [k.value for k in node.keywords]
    return None


def check_html(tree: ast.Module, ctx: Context) -> list[dict]:
    def escaper(e):
        name = ctx.qualified_name(e.func) if isinstance(e, ast.Call) else None
        return bool(name) and name.split(".")[-1] in HTML_ESCAPERS

    def manual(e):
        return any(isinstance(n, ast.Constant) and n.value == "&lt;" for n in ast.walk(e))

    findings = []
    for node in ast.walk(tree):
        values = _html_values(node, ctx.parent.get(node))
        if not values:
            continue
        scope = ctx.scope(node)
        assigned = [n for n in ast.walk(scope) if isinstance(n, ast.Assign)]
        escaped = {t.id for n in assigned if any(escaper(c) for c in ast.walk(n.value))
                   for t in n.targets if isinstance(t, ast.Name)}
        replaced = {t.id for n in assigned if manual(n.value) for t in n.targets if isinstance(t, ast.Name)}
        levels = []
        for value in values:
            if not ctx.derived(value, scope) or escaper(value) or (isinstance(value, ast.Name) and value.id in escaped):
                continue
            levels.append("low" if manual(value) or (isinstance(value, ast.Name) and value.id in replaced) else "high")
        if "high" in levels:
            findings.append(ctx.finding(HTML_RULE, node, "high",
                "Input-derived data is placed in HTML markup without escaping."))
        elif levels:
            findings.append(ctx.finding(HTML_RULE, node, "low",
                "Input-derived data is placed in HTML markup after hand-written replacement; "
                "verify that <, >, & and quotes are all escaped."))
    return findings


def check_script_filter(tree: ast.Module, ctx: Context) -> list[dict]:
    repeated = any(isinstance(n, ast.While) for n in ast.walk(tree))
    severity = "medium" if repeated else "high"
    detail = ("repeated until stable, but tag syntax variants may still pass" if repeated
              else "applied in a single pass, so nested or malformed tags survive")
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func)
        if name in REGEX_FUNCTIONS:
            pattern = _constant_text(tree, _first_arg(call, "pattern"))
            kind = "A regular expression"
        elif isinstance(call.func, ast.Attribute) and call.func.attr == "replace" and call.args:
            pattern = _constant_text(tree, call.args[0])
            kind = "A fixed-string replacement"
            pattern = pattern if pattern and "<" in pattern else None
        else:
            continue
        if pattern and "script" in pattern.lower():
            findings.append(ctx.finding(FILTER_RULE, call, severity,
                f"{kind} is used to remove script tags; it is {detail}. Use an HTML parser."))
    return findings


def check_url(tree: ast.Module, ctx: Context) -> list[dict]:
    def domain(e):
        return isinstance(e, ast.Constant) and isinstance(e.value, str) and DOMAIN.search(e.value)

    findings = []
    for node in ast.walk(tree):
        scope = ctx.scope(node)
        if (isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn))
                and domain(node.left) and ctx.derived(node.comparators[0], scope)):
            findings.append(ctx.finding(URL_RULE, node, "high",
                "A host name is looked for anywhere in input-derived text; it also matches in "
                "the path, query, user info or a longer host name."))
        if not isinstance(node, ast.Call):
            continue
        name = ctx.qualified_name(node.func)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("startswith", "endswith") and node.args:
            if not ctx.derived(node.func.value, scope):
                continue
            first = node.args[0]
            for item in [e for e in (first.elts if isinstance(first, ast.Tuple) else [first]) if domain(e)]:
                if node.func.attr == "endswith" and not item.value.startswith("."):
                    findings.append(ctx.finding(URL_RULE, node, "high",
                        f"Suffix check {item.value!r} has no leading dot and accepts other "
                        "registered domains that end with the same text."))
                elif node.func.attr == "startswith" and "://" in item.value and not item.value.endswith("/"):
                    findings.append(ctx.finding(URL_RULE, node, "high",
                        f"Prefix check {item.value!r} does not end the host name and accepts "
                        "longer host names."))
        elif name in ("re.match", "re.search", "re.fullmatch", "re.compile"):
            pattern = _constant_text(tree, _first_arg(node, "pattern"))
            if not pattern or not DOMAIN.search(pattern.replace("\\", "")):
                continue
            if name != "re.compile" and not any(ctx.derived(a, scope) for a in node.args[1:]):
                continue
            anchored = name == "re.fullmatch" or pattern.rstrip().endswith(("$", "\\Z"))
            if UNESCAPED_DOT.search(pattern) or not anchored:
                problem = "an unescaped dot" if UNESCAPED_DOT.search(pattern) else "no end anchor"
                findings.append(ctx.finding(URL_RULE, node, "high",
                    f"A host name is validated by a regular expression with {problem}."))
            else:
                findings.append(ctx.finding(URL_RULE, node, "low",
                    "A host name is validated by a regular expression; verify that nothing "
                    "can precede the host name inside the same label."))
    return findings


def check_redirect(tree: ast.Module, ctx: Context) -> list[dict]:
    def passes_through(e, names):
        if isinstance(e, ast.Name):
            return e.id in names
        if isinstance(e, ast.BoolOp):
            return any(passes_through(v, names) for v in e.values)
        if isinstance(e, ast.IfExp):
            return passes_through(e.body, names) or passes_through(e.orelse, names)
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ("strip", "lstrip"):
            return passes_through(e.func.value, names)
        return False

    findings = []
    for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        parameters = [a.arg for a in function.args.posonlyargs + function.args.args + function.args.kwonlyargs]
        if not ("redirect" in function.name.lower() or any(URL_NAME.search(p) for p in parameters)):
            continue
        names = ctx.tainted(function)
        scopes = _linked_scopes(tree, function)
        seen, strings = _seen_calls(ctx, scopes), _strings(scopes)
        if seen & {"url_has_allowed_host_and_scheme", "is_safe_url"}:
            continue
        attributes = {n.attr for scope in scopes for n in ast.walk(scope) if isinstance(n, ast.Attribute)}
        parsed = any(n.split(".")[-1] in ("urlparse", "urlsplit") for n in seen)
        if parsed and attributes & {"netloc", "hostname", "scheme"}:
            severity, problem = "low", "after its parsed host or scheme was inspected; verify backslash and control-character forms"
        elif ".startswith" in seen and "/" in strings:
            if any("//" in s for s in strings) and any("\\" in s for s in strings):
                severity, problem = "low", "after local-path checks; verify they cover every browser-normalized form"
            else:
                severity, problem = "medium", "after a leading-slash check that still admits //host or /\\host"
        else:
            severity, problem = "high", "without checking that it stays on this site"
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None and ctx.scope(node) is function \
                    and passes_through(node.value, names):
                findings.append(ctx.finding(REDIRECT_RULE, node, severity,
                    f"An input-derived redirect target is returned {problem}."))
    return findings


# --- Rules added in rule set 0.4.0 ------------------------------------------------------------

XML_ENTRY_POINTS = {"fromstring", "XML", "parse", "parseString", "iterparse", "fromstringlist"}
DTD_HANDLERS = {"StartDoctypeDeclHandler", "EntityDeclHandler", "UnparsedEntityDeclHandler", "forbid_dtd",
                "forbid_entities"}


def check_error_disclosure(tree: ast.Module, ctx: Context) -> list[dict]:
    def trace_call(node):
        return isinstance(node, ast.Call) and (ctx.qualified_name(node.func) or "").startswith("traceback.format")

    def class_name_only(expr, names):
        """Every use of an exception name sits inside type(e).__name__ or e.__class__.__name__."""
        inner = {id(n) for a in ast.walk(expr) if isinstance(a, ast.Attribute) and a.attr == "__name__"
                 for n in ast.walk(a.value)}
        return all(id(n) in inner for n in ast.walk(expr) if isinstance(n, ast.Name) and n.id in names)

    findings = []
    for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for handler in [n for n in ast.walk(function) if isinstance(n, ast.ExceptHandler)]:
            caught = {handler.name} if handler.name else set()
            carried = set()  # names assigned, inside the handler, from the exception or a stack trace
            changed = True
            while changed:
                changed = False
                for node in [n for part in handler.body for n in ast.walk(part) if isinstance(n, ast.Assign)]:
                    uses = any(isinstance(n, ast.Name) and n.id in caught | carried for n in ast.walk(node.value))
                    if uses or any(trace_call(n) for n in ast.walk(node.value)):
                        for target in node.targets:
                            for name in ast.walk(target):
                                if isinstance(name, ast.Name) and name.id not in carried:
                                    carried.add(name.id)
                                    changed = True
            inside = {id(n) for part in handler.body for n in ast.walk(part)}
            for node in ast.walk(function):
                if not (isinstance(node, ast.Return) and node.value is not None and ctx.scope(node) is function):
                    continue
                names = carried | (caught if id(node) in inside else set())
                traced = any(trace_call(n) for n in ast.walk(node.value)) and id(node) in inside
                used = any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node.value))
                if traced:
                    findings.append(ctx.finding(ERROR_RULE, node, "high",
                        "A stack trace is returned to the caller from an exception handler."))
                elif used and class_name_only(node.value, names) and not carried & {
                        n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}:
                    findings.append(ctx.finding(ERROR_RULE, node, "low",
                        "The exception class name is returned to the caller."))
                elif used:
                    findings.append(ctx.finding(ERROR_RULE, node, "high",
                        "Text of the caught exception is returned to the caller; it may hold "
                        "credentials, paths or other internal detail."))
    return findings


def check_xml_entities(tree: ast.Module, ctx: Context) -> list[dict]:
    refuses_dtd = any("<!DOCTYPE" in t.upper() or "<!ENTITY" in t.upper() or t.upper() in ("DOCTYPE", "ENTITY")
                      for t in _strings([tree]))
    refuses_dtd = refuses_dtd or any(isinstance(n, (ast.Attribute, ast.keyword))
                                     and getattr(n, "attr", getattr(n, "arg", None)) in DTD_HANDLERS
                                     for n in ast.walk(tree))
    findings = []
    for call in _calls(tree):
        name = ctx.qualified_name(call.func) or ""
        if not (name.startswith("xml.") and name.split(".")[-1] in XML_ENTRY_POINTS):
            continue
        scope = ctx.scope(call)
        if not any(ctx.derived(v, scope) for v in call.args + [k.value for k in call.keywords]):
            continue
        if refuses_dtd:
            findings.append(ctx.finding(XML_RULE, call, "low",
                f"{name}() parses input-derived XML in a module that looks for a DTD or entity "
                "declarations; verify that such documents are refused before parsing."))
        else:
            findings.append(ctx.finding(XML_RULE, call, "high",
                f"{name}() parses input-derived XML with entity expansion enabled and no DTD "
                "check was found; nested entities can expand to a very large document."))
    return findings


def check_link(tree: ast.Module, ctx: Context) -> list[dict]:
    def escaper(e):
        name = ctx.qualified_name(e.func) if isinstance(e, ast.Call) else None
        return bool(name) and name.split(".")[-1] in HTML_ESCAPERS

    findings = []
    for node in ast.walk(tree):
        values = _html_values(node, ctx.parent.get(node))
        text = " ".join(n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str))
        if not values or "href" not in text.lower():
            continue
        scope = ctx.scope(node)
        scopes = _linked_scopes(tree, scope)
        escaped = {t.id for n in ast.walk(scope) if isinstance(n, ast.Assign)
                   and any(escaper(c) for c in ast.walk(n.value)) for t in n.targets if isinstance(t, ast.Name)}
        raw = [v for v in values if ctx.derived(v, scope) and not escaper(v)
               and not (isinstance(v, ast.Name) and v.id in escaped)]
        seen, strings = _seen_calls(ctx, scopes), _strings(scopes)
        attributes = {n.attr for s in scopes for n in ast.walk(s) if isinstance(n, ast.Attribute)}
        scheme_check = ("scheme" in attributes and any(n.split(".")[-1] in ("urlparse", "urlsplit") for n in seen)) \
            or (".startswith" in seen and any(t.lower().startswith("http") for t in strings))
        if raw:
            findings.append(ctx.finding(LINK_RULE, node, "high",
                "Input-derived data is placed in a link without escaping."))
        elif not scheme_check:
            findings.append(ctx.finding(LINK_RULE, node, "high",
                "An input-derived URL is used as a link target and no scheme check was found; "
                "escaping does not stop javascript: or data: URLs."))
        else:
            findings.append(ctx.finding(LINK_RULE, node, "low",
                "An input-derived URL is used as a link target after a scheme check; verify "
                "that only http and https pass."))
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
EVAL_RULE = Rule(
    "AST-EVAL-001", "CWE-095",
    "eval()/exec() whose code argument is input-derived (high: no validation found; low: a "
    "regular-expression, character or syntax-tree validation exists in the same or linked functions).",
    "Cannot tell whether the validation is sufficient or precedes the call; compile(), "
    "getattr-based access and dynamic imports are not covered.", check_eval)
TAR_RULE = Rule(
    "AST-TAR-001", "CWE-022",
    "tarfile extract()/extractall() without a restricting extraction filter (high: no entry "
    "check; medium: name-only or prefix check; low: containment check on resolved paths).",
    "Does not follow hand-written extraction through extractfile() and open(); cannot prove "
    "that a recognized check guards every entry, including link entries; any .extract() "
    "call in a module importing tarfile counts.", check_tar)
RANDOM_RULE = Rule(
    "AST-RAND-001", "CWE-330",
    "A call into the random module or uuid.uuid1() (high), or a hash over the clock or "
    "process ID with no unpredictable input in the function (medium).",
    "Does not know whether the value is security-sensitive; a random.SystemRandom instance "
    "and custom generators are not tracked; other predictable sources are not recognized.",
    check_random)
HASH_RULE = Rule(
    "AST-HASH-001", "CWE-759",
    "A hashlib/hmac digest of input-derived data in a module that generates no random salt, "
    "or a key-derivation call whose salt is a constant.",
    "The salt check is module-wide: it does not prove the generated salt reaches this call. "
    "A salted but fast digest is not reported (that is CWE-916); third-party hashing "
    "libraries are not covered; the input is not known to be a password.", check_password_hash)
PERMISSION_RULE = Rule(
    "AST-PERM-001", "CWE-732",
    "chmod()/os.open() with a mode whose known bits grant group or other write permission, "
    "or os.umask() with a mask that stops removing it.",
    "Only constant and stat.S_* operands are evaluated; modes computed from the existing "
    "file mode or from variables are not reported.", check_permissions)
LOG_RULE = Rule(
    "AST-LOG-001", "CWE-117",
    "A logging call with an input-derived argument (high: unchanged; low: a replacement, "
    "repr-style conversion or similar step exists in the same or linked functions).",
    "A logger is recognized by a receiver name containing 'log'; cannot tell whether the "
    "conversion removes CR and LF or applies to the logged value; the logger parameter "
    "itself counts as input.", check_log)
HTML_RULE = Rule(
    "AST-HTML-001", "CWE-080",
    "A string containing HTML markup that is formatted or concatenated with input-derived "
    "data not passed through an escaping function (low when only hand-written replacement is found).",
    "Flow-insensitive: a name escaped anywhere in the function counts as escaped everywhere; "
    "template engines, attribute and script contexts are not distinguished.", check_html)
FILTER_RULE = Rule(
    "AST-FILTER-001", "CWE-116",
    "Script-tag removal by regular expression or fixed-string replacement (high: single "
    "pass; medium: the module repeats it in a while loop).",
    "Reports the technique, not a proven bypass: a careful repeated regular expression is "
    "still reported at medium, and loops are detected module-wide.", check_script_filter)
URL_RULE = Rule(
    "AST-URL-001", "CWE-020",
    "Host validation by substring test, suffix test without a leading dot, prefix test "
    "that does not end the host name, or a regular expression with an unescaped dot or no "
    "end anchor (low for an escaped, anchored expression).",
    "Does not know whether the checked text is a whole URL or a parsed host name; cannot "
    "detect a pattern that lets other characters precede the host inside one label; "
    "equality and leading-dot suffix checks are assumed correct.", check_url)
REDIRECT_RULE = Rule(
    "AST-REDIR-001", "CWE-601",
    "A function with a URL-like parameter or 'redirect' in its name that returns the input "
    "value (high: no check; medium: leading-slash check only; low: parsed host/scheme or "
    "full local-path checks).",
    "Selected by naming convention; only returned values are sinks (framework redirect "
    "calls are not); cannot prove that a recognized check is correct or enforced.", check_redirect)
ERROR_RULE = Rule(
    "AST-ERR-001", "CWE-209",
    "A function that returns the text of a caught exception or a formatted stack trace "
    "(high), or only the exception class name (low).",
    "Only returned values are sinks; values that leave through attributes, containers "
    "filled elsewhere, or other functions are not followed; cannot tell whether the "
    "caller is remote.", check_error_disclosure)
XML_RULE = Rule(
    "AST-XML-001", "CWE-776",
    "A standard-library XML parser applied to input-derived text (high: no DTD or entity "
    "check anywhere in the module; low: the module looks for a DTD or entity declaration).",
    "The DTD check is recognized by string constants or expat handler names module-wide; "
    "cannot prove that it runs before parsing or rejects the document; parser objects fed "
    "through feed() and third-party parsers are not covered.", check_xml_entities)
LINK_RULE = Rule(
    "AST-LINK-001", "CWE-079",
    "Markup with an href that is built from input-derived data: unescaped, or escaped but "
    "with no URL scheme check (high); escaped with a scheme check (low).",
    "Does not know which interpolated value is the URL; a scheme check is recognized by "
    "urlparse/urlsplit with .scheme or a startswith test on an http prefix and is not "
    "proven correct; template engines are not covered.", check_link)
RULES = (SQL_RULE, COMMAND_RULE, PATH_RULE, EVAL_RULE, TAR_RULE, RANDOM_RULE, HASH_RULE,
         PERMISSION_RULE, LOG_RULE, HTML_RULE, FILTER_RULE, URL_RULE, REDIRECT_RULE,
         ERROR_RULE, XML_RULE, LINK_RULE)


def scan(code: bytes | str) -> list[dict]:
    """Return contract-shaped findings sorted by line. Raises SyntaxError for invalid code."""
    tree = ast.parse(code)
    source = code.decode("utf-8", errors="replace") if isinstance(code, bytes) else code
    ctx = Context(tree, source)
    findings = [f for rule in RULES for f in rule.check(tree, ctx)]
    return sorted(findings, key=lambda f: (f["line"], f["rule_id"]))
