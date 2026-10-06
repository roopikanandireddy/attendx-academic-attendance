const fs = require('fs');
const path = require('path');

const distDir = path.join(__dirname, 'dist');
const assetsDir = path.join(distDir, 'assets');

console.log('='.repeat(70));
console.log('MODULE 6: FRONTEND ROUTE-LEVEL CODE SPLITTING & BUNDLE VERIFICATION');
console.log('='.repeat(70));

if (!fs.existsSync(assetsDir)) {
  console.error('[FAIL] dist/assets directory does not exist! Please run npm run build first.');
  process.exit(1);
}

const files = fs.readdirSync(assetsDir);
const jsFiles = files.filter(f => f.endsWith('.js'));
const cssFiles = files.filter(f => f.endsWith('.css'));

console.log(`\n[INVENTORY] Total JS chunks generated: ${jsFiles.length}`);
console.log(`[INVENTORY] Total CSS files generated: ${cssFiles.length}`);

// Locate critical chunks
const entryChunk = jsFiles.find(f => f.startsWith('index-'));
const vendorReactChunk = jsFiles.find(f => f.startsWith('vendor-react-'));
const vendorChartsChunk = jsFiles.find(f => f.startsWith('vendor-charts-'));
const roleSelectionChunk = jsFiles.find(f => f.startsWith('RoleSelectionPage-'));
const loginChunk = jsFiles.find(f => f.startsWith('LoginPage-'));
const studentDashChunk = jsFiles.find(f => f.startsWith('StudentDashboard-'));
const adminDashChunk = jsFiles.find(f => f.startsWith('AdminDashboardPage-'));
const lecturerDashChunk = jsFiles.find(f => f.startsWith('LecturerDashboardPage-'));
const adminStudentsChunk = jsFiles.find(f => f.startsWith('AdminStudentsPage-'));

function getFileSizeKb(filename) {
  const stat = fs.statSync(path.join(assetsDir, filename));
  return (stat.size / 1024).toFixed(2);
}

console.log('\n--- CRITICAL CHUNK SIZES ---');
console.log(`Entry App Chunk       : ${entryChunk} -> ${getFileSizeKb(entryChunk)} kB`);
console.log(`Vendor React Chunk    : ${vendorReactChunk} -> ${getFileSizeKb(vendorReactChunk)} kB`);
console.log(`Vendor Charts (Recharts): ${vendorChartsChunk} -> ${getFileSizeKb(vendorChartsChunk)} kB`);
console.log(`Role Selection Page   : ${roleSelectionChunk} -> ${getFileSizeKb(roleSelectionChunk)} kB`);
console.log(`Login Page            : ${loginChunk} -> ${getFileSizeKb(loginChunk)} kB`);
console.log(`Student Dashboard     : ${studentDashChunk} -> ${getFileSizeKb(studentDashChunk)} kB`);
console.log(`Admin Dashboard       : ${adminDashChunk} -> ${getFileSizeKb(adminDashChunk)} kB`);
console.log(`Lecturer Dashboard    : ${lecturerDashChunk} -> ${getFileSizeKb(lecturerDashChunk)} kB`);
console.log(`Admin Students Page   : ${adminStudentsChunk} -> ${getFileSizeKb(adminStudentsChunk)} kB`);

// Check HTML script references
const indexHtml = fs.readFileSync(path.join(distDir, 'index.html'), 'utf8');
console.log('\n--- HTML ENTRY POINT AUDIT ---');
const scriptsInHtml = [...indexHtml.matchAll(/src="\/assets\/([^"]+)"/g)].map(m => m[1]);
console.log('Scripts linked in index.html:', scriptsInHtml);

const containsChartsInHtml = scriptsInHtml.some(s => s.includes('charts'));
const containsAdminInHtml = scriptsInHtml.some(s => s.toLowerCase().includes('admin'));
const containsStudentInHtml = scriptsInHtml.some(s => s.toLowerCase().includes('student'));

let pass = true;

if (containsChartsInHtml) {
  console.error('[FAIL] Recharts vendor bundle is referenced in index.html!');
  pass = false;
} else {
  console.log('[PASS] Recharts is NOT bundled into initial HTML.');
}

if (containsAdminInHtml) {
  console.error('[FAIL] Admin pages are referenced in index.html!');
  pass = false;
} else {
  console.log('[PASS] Admin pages are NOT bundled into initial HTML.');
}

if (containsStudentInHtml) {
  console.error('[FAIL] Student dashboard is referenced in index.html!');
  pass = false;
} else {
  console.log('[PASS] Student dashboard is NOT bundled into initial HTML.');
}

// Compute total public payload
const entryAppSize = parseFloat(getFileSizeKb(entryChunk));
const vendorReactSize = parseFloat(getFileSizeKb(vendorReactChunk));
const roleSelectionSize = parseFloat(getFileSizeKb(roleSelectionChunk));
const loginSize = parseFloat(getFileSizeKb(loginChunk));

const baselineEntrySize = 1054.94; // kB
const initialPublicLandingSize = entryAppSize + vendorReactSize + roleSelectionSize;
const initialLoginSize = entryAppSize + vendorReactSize + loginSize;

console.log('\n--- BUNDLE REDUCTION METRICS ---');
console.log(`Baseline Entry Chunk           : ${baselineEntrySize.toFixed(2)} kB`);
console.log(`Optimized Entry Application    : ${entryAppSize.toFixed(2)} kB (Reduction: ${(((baselineEntrySize - entryAppSize)/baselineEntrySize)*100).toFixed(1)}%)`);
console.log(`Optimized Public Landing Total : ${initialPublicLandingSize.toFixed(2)} kB (Reduction: ${(((baselineEntrySize - initialPublicLandingSize)/baselineEntrySize)*100).toFixed(1)}%)`);
console.log(`Optimized Login Route Total    : ${initialLoginSize.toFixed(2)} kB (Reduction: ${(((baselineEntrySize - initialLoginSize)/baselineEntrySize)*100).toFixed(1)}%)`);

if (entryAppSize > 250) {
  console.error(`[FAIL] Entry app chunk (${entryAppSize} kB) exceeds 250 kB threshold!`);
  pass = false;
} else {
  console.log(`[PASS] Entry app chunk is strictly under 250 kB.`);
}

if (initialPublicLandingSize > 400) {
  console.error(`[FAIL] Public landing payload (${initialPublicLandingSize} kB) exceeds 400 kB threshold!`);
  pass = false;
} else {
  console.log(`[PASS] Public landing payload is strictly under 400 kB.`);
}

console.log('\n' + '='.repeat(70));
if (pass) {
  console.log('ALL MODULE 6 FRONTEND CODE SPLITTING CHECKS PASSED (100% SUCCESS)');
} else {
  console.log('VERIFICATION FAILED!');
  process.exit(1);
}
console.log('='.repeat(70));
