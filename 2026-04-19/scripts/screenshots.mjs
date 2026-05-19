import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

async function main() {
  const today = new Date().toISOString().slice(0, 10);
  const outDir = path.resolve('logs/screenshots', today);
  await mkdir(outDir, { recursive: true });

  const demoUrl = pathToFileURL(path.resolve('demo/index.html')).href;
  const browser = await chromium.launch();

  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.goto(demoUrl);
    await page.click('#draw');
    await page.locator('#output .ball').first().waitFor();

    const count = await page.locator('#output .ball').count();
    const EXPECTED = 18; // #count 기본값 3 × 6개/게임
    if (count !== EXPECTED) {
      throw new Error(`expected ${EXPECTED} balls, got ${count}`);
    }

    await page.screenshot({ path: path.join(outDir, 'demo.png'), fullPage: true });
    console.log(`ok  (${count} balls)  →  logs/screenshots/${today}/demo.png`);
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  const msg = String(err?.message || err);
  if (msg.includes("Cannot find package 'playwright'")) {
    console.error('❌ playwright 미설치 → npm i 후 npm run screenshots:install');
  } else if (/Executable doesn't exist|browserType\.launch/.test(msg)) {
    console.error('❌ Chromium 미설치 → npm run screenshots:install');
  } else {
    console.error(`❌ ${msg}`);
  }
  process.exit(1);
});
