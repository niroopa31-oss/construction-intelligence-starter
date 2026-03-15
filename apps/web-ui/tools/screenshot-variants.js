const puppeteer = require('puppeteer');

const url = process.env.SERVE_URL || 'http://localhost:4201';
const outDir = './src/assets';

const variants = [
  { name: 'base', vars: {} },
  {
    name: 'strong',
    vars: {
      '--bg-glow-1': 'rgba(0,210,255,0.30)',
      '--bg-glow-2': 'rgba(124,58,237,0.22)',
      '--neon-glow': 'rgba(0,210,255,0.32)'
    }
  },
  {
    name: 'weak',
    vars: {
      '--bg-glow-1': 'rgba(0,210,255,0.08)',
      '--bg-glow-2': 'rgba(124,58,237,0.06)',
      '--neon-glow': 'rgba(0,210,255,0.08)'
    }
  }
];

(async () => {
  console.log('Launching headless browser...');
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  page.setViewport({ width: 1280, height: 900 });

  console.log(`Opening ${url} ...`);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

  // give SPA a moment to render
  await page.waitForTimeout(1200);

  for (const v of variants) {
    console.log('Applying variant:', v.name);
    await page.evaluate((vars) => {
      for (const k in vars) document.documentElement.style.setProperty(k, vars[k]);
    }, v.vars);

    // small wait to let CSS settle
    await page.waitForTimeout(400);

    const out = `${outDir}/project-overview-bg-${v.name}.png`;
    console.log('Saving screenshot to', out);
    await page.screenshot({ path: out, fullPage: true });
  }

  await browser.close();
  console.log('Screenshots complete');
})();
