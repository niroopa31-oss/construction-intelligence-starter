/*
  Simple SVG -> PNG/ICO conversion script using sharp and png-to-ico.
  Usage: node tools/svg-to-favicons.js
  Inputs: src/assets/logo-construction-intelligence-square.svg
  Outputs: src/assets/favicon-16x16.png, favicon-32x32.png, favicon-48x48.png, apple-touch-icon.png, favicon.ico
*/

const path = require('path');
const fs = require('fs');

async function run() {
  const sharp = require('sharp');
  const pngToIcoModule = require('png-to-ico');
  const pngToIco = pngToIcoModule.default || pngToIcoModule;

  const root = path.resolve(__dirname, '..', 'src', 'assets');
  const inputSvg = path.join(root, 'logo-construction-intelligence-square.svg');
  if (!fs.existsSync(inputSvg)) {
    console.error('Input SVG not found:', inputSvg);
    process.exit(1);
  }

  // include larger sizes for PWA / store assets (512, 1024) and additional store sizes
  const sizes = [16, 32, 48, 180, 192, 256, 384, 512, 1024];
  const outFiles = [];
  for (const s of sizes) {
    const out = path.join(root, `favicon-${s}x${s}.png`);
    await sharp(inputSvg)
      .resize(s, s)
      .png({compressionLevel:9})
      .toFile(out);
    console.log('Wrote', out);
    outFiles.push(out);
  }

  // also create specific named files
  fs.copyFileSync(path.join(root, 'favicon-180x180.png'), path.join(root, 'apple-touch-icon.png'));
  fs.copyFileSync(path.join(root, 'favicon-48x48.png'), path.join(root, 'favicon-48x48.png'));
  // copy larger assets to standard names for PWA / stores
  fs.copyFileSync(path.join(root, 'favicon-512x512.png'), path.join(root, 'icon-512x512.png'));
  fs.copyFileSync(path.join(root, 'favicon-1024x1024.png'), path.join(root, 'icon-1024x1024.png'));
  fs.copyFileSync(path.join(root, 'favicon-192x192.png'), path.join(root, 'icon-192x192.png'));
  fs.copyFileSync(path.join(root, 'favicon-256x256.png'), path.join(root, 'icon-256x256.png'));
  fs.copyFileSync(path.join(root, 'favicon-384x384.png'), path.join(root, 'icon-384x384.png'));

  // create .ico from 16,32,48
  const icoOut = path.join(root, 'favicon.ico');
  const pngsForIco = [
    path.join(root, 'favicon-16x16.png'),
    path.join(root, 'favicon-32x32.png'),
    path.join(root, 'favicon-48x48.png')
  ];
  const buf = await pngToIco(pngsForIco);
  fs.writeFileSync(icoOut, buf);
  console.log('Wrote', icoOut);
}

run().catch(err => { console.error(err); process.exit(2); });
