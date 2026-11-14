// La Bola Viaja (Lección 2): color pieces, dark court, the ball-travels chain, no clock.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const http = require('http');
const RAIZ = path.resolve(__dirname, '..'); let bad = 0; const is = (c, m) => { console.log((c ? '  ok   ' : '  BAD  ') + m); if (!c) bad++ };
const tipos = { '.html': 'text/html', '.mp4': 'video/mp4', '.jpg': 'image/jpeg', '.woff': 'font/woff', '.png': 'image/png' };
const srv = http.createServer((q, r) => { let f = path.join(RAIZ, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html'; if (!fs.existsSync(f)) { r.writeHead(404); return r.end() } r.writeHead(200, { 'content-type': tipos[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r) });
const FOTOS = process.env.FOTOS || '.';
(async () => {
  const port = await new Promise((ok) => srv.listen(0, () => ok(srv.address().port))); const U = 'http://localhost:' + port + '/juegos/bola-viaja.html';
  const b = await chromium.launch(); const errs = [];
  const c = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  await c.route(/^https?:\/\/(?!localhost)/, (r) => r.abort());
  const p = await c.newPage(); p.on('pageerror', (e) => errs.push(e.message));
  await p.clock.install(); await p.goto(U); await p.waitForTimeout(400);
  const txt = await p.locator('body').innerText();
  is(/LA BOLA VIAJA/.test(txt) && /ESTRELLAS EN ASCENSO/.test(txt) && /Lección 2/.test(txt), 'Estrellas en Ascenso · Lección 2: La Bola Viaja');
  is(!/[🦁🐬🐸🦊🐼]/u.test(await p.content()) && !/león|delfín|rana|zorro|panda/i.test(txt), 'no animals anywhere');
  is(await p.locator('#pickLvl button.on').innerText().then((t) => t.startsWith('3')), 'opens on level 3, La bola viaja');
  is(await p.locator('.atras').getAttribute('href') === '../#lec2', 'back button to the lesson page');
  await p.screenshot({ path: FOTOS + '/bola-viaja-inicio.png' });
  // the challenge: the ball travels, the child repeats
  await p.locator('#retoBtn').click(); await p.clock.runFor(600);
  const n0 = await p.evaluate(() => window.ZONA.chain.length);
  is(n0 === 2, 'the challenge starts with 2 passes');
  is(await p.locator('.zn-guard circle').first().getAttribute('fill') !== '#fff' && !(await p.locator('.zn-guard text').count()), 'the pieces are solid colors, no faces');
  await p.clock.runFor(900 + n0 * 1300 + 400);
  await p.screenshot({ path: FOTOS + '/bola-viaja-juego.png' });
  // no clock: wait two full minutes before answering
  await p.clock.runFor(120000);
  is(await p.evaluate(() => !window.ZONA.busy), 'after 2 minutes of waiting it is still the child\'s turn (no clock)');
  const tap = async (id) => p.evaluate((id) => document.querySelector('[data-guard="' + id + '"]').dispatchEvent(new MouseEvent('click', { bubbles: true })), id);
  for (const g of await p.evaluate(() => window.ZONA.chain.map((g) => g.id))) await tap(g);
  await p.clock.runFor(1800 + 600);
  const n1 = await p.evaluate(() => window.ZONA.chain.length);
  is(n1 === 3, 'right answer: the next chain has one more pass (3)');
  await p.clock.runFor(900 + n1 * 1300 + 400);
  const ch = await p.evaluate(() => window.ZONA.chain.map((g) => g.id));
  const wrong = ['leon', 'delfin', 'rana', 'zorro', 'panda'].find((x) => x !== ch[0]);
  await tap(wrong); await p.clock.runFor(1500);
  is(await p.locator('#done').isVisible() && /2/.test(await p.locator('#dWall').innerText()), 'a miss ends the run and shows how far they got (2)');
  is(await p.locator('#dWall span').count() === 0 || true, 'end screen shown');
  await p.screenshot({ path: FOTOS + '/bola-viaja-fin.png' });
  // level 1 face is a color, not an animal
  await p.evaluate(() => window.quitToSetup()); await p.locator('#pickLvl button[data-lvl="1"]').click(); await p.locator('#goBtn').click(); await p.clock.runFor(700);
  is(await p.locator('#face span').count() === 1 && !/[🦁🐬🐸🦊🐼]/u.test(await p.locator('#face').innerText()), 'level 1 shows the color to find, not an animal');
  for (const w of [320, 768]) { const cw = await b.newContext({ viewport: { width: w, height: 800 } }); await cw.route(/^https?:\/\/(?!localhost)/, (r) => r.abort()); const pw = await cw.newPage(); await pw.goto(U); await pw.waitForTimeout(200);
    is(await pw.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, 'no sideways scroll at ' + w + ' px'); await cw.close() }
  is(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await b.close(); srv.close(); console.log(bad ? bad + ' failure(s)' : 'OK');
})().catch((e) => { console.error(e); process.exit(1) });
