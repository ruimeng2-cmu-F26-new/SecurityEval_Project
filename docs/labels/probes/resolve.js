const data = JSON.parse(require('fs').readFileSync(0,'utf8'));
for (const [cand, r] of Object.entries(data)) {
  const bad = [];
  for (const [p, o] of Object.entries(r)) {
    if (o === null) continue;
    let u; try { u = new URL(o, 'https://shop.example/login'); } catch { continue; }
    if (u.host !== 'shop.example' || !['http:','https:'].includes(u.protocol)) bad.push([p, o, u.href]);
  }
  console.log(cand.replace('redirect_next_url__anthropic__claude-',''), bad.length ? 'BYPASS '+JSON.stringify(bad.slice(0,3)) : 'ok', bad.length);
}
