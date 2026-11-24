import sys, re, html, importlib.util
C0 = ''.join(chr(i) for i in range(0x21))
def browser_scheme(href_attr):
    url = html.unescape(href_attr).strip(C0)
    url = re.sub(r'[\t\n\r]', '', url)
    m = re.match(r'^([A-Za-z][A-Za-z0-9+.-]*):', url)
    return m.group(1).lower() if m else ''
payloads = ['javascript:alert(1)','JaVaScRiPt:alert(1)',' javascript:alert(1)','\x01javascript:alert(1)',
 '\x00javascript:alert(1)','java\tscript:alert(1)','java\nscript:alert(1)','\x1fjavascript:alert(1)',
 'javascript&#58;alert(1)','&#106;avascript:alert(1)','data:text/html,<script>alert(1)</script>',
 'vbscript:msgbox(1)','\x08data:text/html,x','x" onmouseover="alert(1)','"><script>alert(1)</script>',
 'javascript\x00:alert(1)']
names = ['"><img src=x onerror=alert(1)>', "' onclick='x"]
for path in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location('c', path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    bad = []
    for p in payloads:
        try: out = m.render_profile_link('n', p)
        except Exception: continue
        href = re.match(r'<a href="([^"]*)">', out)
        if not href or browser_scheme(href.group(1)) in ('javascript','data','vbscript') or out.count('<') != 2 or ' on' in out.split('>')[0][9+len(href.group(1)):]:
            bad.append((p, out))
    for n in names:
        out = m.render_profile_link(n, 'https://e.com')
        if out.count('<') != 2 or out.count('"') != 2: bad.append((n, out))
    print(path.split('/')[-2], 'BYPASS' if bad else 'ok', bad[:3])
