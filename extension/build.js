/**
 * Simple build script for the Chrome extension
 * Copies files to dist/ folder ready for loading in Chrome
 */

const fs = require('fs');
const path = require('path');

const distDir = path.join(__dirname, 'dist');

// Clean dist
if (fs.existsSync(distDir)) {
  fs.rmSync(distDir, { recursive: true });
}
fs.mkdirSync(distDir);
fs.mkdirSync(path.join(distDir, 'icons'));

// Copy manifest
fs.copyFileSync(
  path.join(__dirname, 'manifest.json'),
  path.join(distDir, 'manifest.json')
);

// Copy content script
fs.copyFileSync(
  path.join(__dirname, 'src/content/content.js'),
  path.join(distDir, 'content.js')
);

fs.copyFileSync(
  path.join(__dirname, 'src/content/content.css'),
  path.join(distDir, 'content.css')
);

// Copy background script
fs.copyFileSync(
  path.join(__dirname, 'src/background/background.js'),
  path.join(distDir, 'background.js')
);

// Copy popup
fs.copyFileSync(
  path.join(__dirname, 'src/popup/popup.html'),
  path.join(distDir, 'popup.html')
);

fs.copyFileSync(
  path.join(__dirname, 'src/popup/popup.js'),
  path.join(distDir, 'popup.js')
);

// Copy icons if they exist
const iconSizes = [16, 32, 48, 128];
for (const size of iconSizes) {
  const iconPath = path.join(__dirname, `public/icons/icon${size}.png`);
  if (fs.existsSync(iconPath)) {
    fs.copyFileSync(iconPath, path.join(distDir, `icons/icon${size}.png`));
  }
}

console.log('Extension built successfully to dist/');
console.log('Load the dist/ folder as an unpacked extension in Chrome.');
