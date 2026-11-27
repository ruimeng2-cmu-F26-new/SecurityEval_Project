import sys, json, importlib.util
payloads = ['/orders/42?tab=items','//evil.com','/\\evil.com','\\\\evil.com','\\/evil.com','/\t/evil.com',' //evil.com',
 '\x01//evil.com','https://evil.com','https://shop.example@evil.com','https://evil.com\\@shop.example','javascript:alert(1)',
 'JavaScript:alert(1)','\x01javascript:alert(1)','java\tscript:alert(1)','data:text/html,x','http:evil.com','https:evil.com',
 'https:/\\evil.com','https://evilshop.example','https://shop.example.evil.com','evil.com','///evil.com','/%2F/evil.com',
 'https://shop.example//evil.com','https://shop.example/\\evil.com','/x/../\\evil.com','\t//evil.com','/\n/evil.com','?x','#x',
 'https://shop.example:443/x','https://shop.example/x?y#\\z']
out = {}
for path in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location('c', path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    r = {}
    for p in payloads:
        try: r[p] = m.get_redirect_target(p)
        except Exception as e: r[p] = None
    out[path.split('/')[-2]] = r
json.dump(out, sys.stdout)
