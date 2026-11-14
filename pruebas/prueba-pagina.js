// Lección 1 page: loads, video plays, steps earn stars, stars stay, game link, fits a phone.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const http = require('http');
const RAIZ = path.resolve(__dirname, '..'); let bad = 0; const is = (c, m) => { console.log((c ? '  ok   ' : '  BAD  ') + m); if (!c) bad++ };
const tipos = { '.html': 'text/html', '.mp4': 'video/mp4', '.jpg': 'image/jpeg', '.woff': 'font/woff' };
const srv = http.createServer((q, r) => { let f = path.join(RAIZ, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html'; if (!fs.existsSync(f)) { r.writeHead(404); return r.end() } r.writeHead(200, { 'content-type': tipos[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r) });
(async () => {
  const port = await new Promise((ok) => srv.listen(0, () => ok(srv.address().port))); const U = 'http://localhost:' + port + '/';
  const b = await chromium.launch(); const errs = [];
  const c = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  await c.route(/^https?:\/\/(?!localhost)/, (r) => r.abort());
  const p = await c.newPage(); p.on('pageerror', (e) => errs.push(e.message));
  await p.goto(U); await p.waitForTimeout(500);
  is(/ESTRELLAS EN ASCENSO/.test(await p.locator('.sello').innerText()) && /LA ZONA 2-1-2/.test(await p.locator('#lec1 h1').innerText()), 'Estrellas en Ascenso, Lección 1: La Zona 2-1-2');
  is(await p.locator('.cielo i').count() === 18, 'rising stars in the header');
  const v = await p.evaluate(async () => { const v = document.getElementById('vid'); await new Promise((r) => { if (v.readyState >= 1) r(); else v.onloadedmetadata = r }); return { d: v.duration, w: v.videoWidth, h: v.videoHeight } });
  is(v.d > 55 && v.w === 1080 && v.h === 1920, 'the lesson video loads (' + v.d.toFixed(1) + ' s, ' + v.w + 'x' + v.h + ')');
  is(await p.locator('video').getAttribute('poster') === 'videos/leccion1-portada.jpg' && await p.evaluate(() => fetch('videos/leccion1-portada.jpg').then((r) => r.ok)), 'cover image is there');
  is(await p.locator('#jugar').getAttribute('href') === 'juegos/bola-viaja.html?lec=1' && !(await p.locator('#jugar').getAttribute('target')), 'Lección 1 Juega opens the new color-piece game (not the animal one)');
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 0 && !(await p.locator('#premio1').isVisible()), 'starts with 0 stars');
  await p.evaluate(() => document.getElementById('vid').dispatchEvent(new Event('ended')));
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 1 && /★ ¡Lo vi!/.test(await p.locator('[data-p=mira]').innerText()), 'finishing the video earns star 1 by itself');
  await p.evaluate(() => { const a = document.getElementById('jugar'); a.addEventListener('click', (e) => e.preventDefault(), { once: true }); a.click() });
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 2, 'opening the game earns star 2');
  await p.locator('#lec1 [data-p=casa]').tap();
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 3 && await p.locator('#premio1').isVisible() && /3 estrellas/.test(await p.locator('#mis').innerText()), 'practising at home: 3 stars and ¡Estrella en Ascenso!');
  await p.reload(); await p.waitForTimeout(300);
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 3, 'the stars stay after a reload (this device only)');
  await p.locator('#lec1 [data-p=casa]').tap();
  is(await p.locator('#lec1 .estrellas-lec i.si').count() === 2 && !(await p.locator('#premio1').isVisible()), 'a step can be un-ticked');
  await p.locator('#lec1 [data-p=casa]').tap();
  await p.screenshot({ path: path.join(process.env.FOTOS || '.', 'leccion1-pagina.png'), fullPage: true });
  is(/PARA MAMÁ Y PAPÁ/.test(await p.locator('.padres').innerText()) && /Lección 3/.test(await p.locator('.prox').innerText()), 'parent note and the coming lessons');
  // Lección 2
  is(await p.locator('#lec1 a.sigue').getAttribute('href') === '#lec2' && /LA BOLA VIAJA/.test(await p.locator('#lec1 a.sigue').innerText()), 'Lección 1 ends with a card linking to Lección 2');
  is(/LA BOLA VIAJA/.test(await p.locator('#lec2 h1').innerText()) && await p.locator('#lec2 a.jugar').getAttribute('href') === 'juegos/bola-viaja.html', 'Lección 2: La Bola Viaja, playing the Estrellas game');
  await p.evaluate(() => { const a = document.querySelector('#lec2 a.jugar'); a.addEventListener('click', (e) => e.preventDefault(), { once: true }); a.click() });
  await p.locator('#lec2 [data-p=casa]').tap(); await p.locator('#lec2 [data-p=record]').tap();
  is(await p.locator('#lec2 .estrellas-lec i.si').count() === 3 && await p.locator('#premio2').isVisible() && await p.locator('#lec1 .estrellas-lec i.si').count() === 3, 'Lección 2 earns its own 3 stars; Lección 1 keeps its own');
  is(/6 estrellas ganadas/.test(await p.locator('#mis').innerText()), 'the header counts all stars (6)');
  for (const w of [320, 390, 768, 1280]) { const cw = await b.newContext({ viewport: { width: w, height: 800 } }); await cw.route(/^https?:\/\/(?!localhost)/, (r) => r.abort()); const pw = await cw.newPage(); await pw.goto(U); await pw.waitForTimeout(200);
    is(await pw.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 0, 'no sideways scroll at ' + w + ' px'); await cw.close() }
  const c2 = await b.newContext({ viewport: { width: 390, height: 844 } }); await c2.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked') } }) }); await c2.route(/^https?:\/\/(?!localhost)/, (r) => r.abort());
  const p2 = await c2.newPage(); const e2 = []; p2.on('pageerror', (e) => e2.push(e.message)); await p2.goto(U); await p2.waitForTimeout(300); await p2.locator('#lec1 [data-p=casa]').click();
  is(e2.length === 0 && await p2.locator('#lec1 .estrellas-lec i.si').count() === 1, 'still works where the browser blocks storage');
  is(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  await b.close(); srv.close(); console.log(bad ? bad + ' failure(s)' : 'OK');
})().catch((e) => { console.error(e); process.exit(1) });
