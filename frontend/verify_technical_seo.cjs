const fs = require('fs');
const path = require('path');

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`[PASS] ${message}`);
    passed++;
  } else {
    console.error(`[FAIL] ${message}`);
    failed++;
  }
}

console.log('='.repeat(70));
console.log('ATTENDX TECHNICAL SEO & GOOGLE INDEXING READINESS VERIFICATION');
console.log('='.repeat(70));

const frontendDir = path.resolve(__dirname);
const publicDir = path.join(frontendDir, 'public');
const distDir = path.join(frontendDir, 'dist');
const indexHtmlPath = path.join(frontendDir, 'index.html');
const distHtmlPath = path.join(distDir, 'index.html');
const rolePagePath = path.join(frontendDir, 'src', 'pages', 'RoleSelectionPage.tsx');

// --- 1. Metadata Verification in index.html and dist/index.html ---
console.log('\n--- 1. Document Title, Description & Canonical URL ---');
[indexHtmlPath, distHtmlPath].forEach((filePath, idx) => {
  const label = idx === 0 ? 'Source index.html' : 'Built dist/index.html';
  assert(fs.existsSync(filePath), `${label} exists`);
  const content = fs.readFileSync(filePath, 'utf8');

  assert(
    content.includes('<title>AttendX — Academic Attendance Management System</title>'),
    `${label} contains exact expected <title>`
  );

  assert(
    content.includes('content="AttendX is a secure academic attendance management system for students, lecturers, and administrators."'),
    `${label} contains exact expected <meta name="description">`
  );

  assert(
    content.includes('<link rel="canonical" href="https://attendx-web-721g.onrender.com/" />'),
    `${label} contains canonical link pointing to public homepage`
  );

  assert(
    content.includes('<meta name="viewport" content="width=device-width, initial-scale=1.0" />'),
    `${label} contains mobile viewport metadata`
  );

  assert(
    content.includes('<html lang="en">'),
    `${label} declares English language attribute`
  );

  assert(
    content.includes('<link rel="icon" type="image/svg+xml" href="/favicon.svg" />'),
    `${label} references branded /favicon.svg`
  );

  assert(
    content.includes('<meta name="google-site-verification" content="CMMlZMXW-tSu9TiDEvkiiwVpRpRHRQHkT5fVqQNt6lo" />'),
    `${label} contains Google Search Console verification meta tag`
  );

  const headEndIdx = content.indexOf('</head>');
  const tagIdx = content.indexOf('google-site-verification');
  assert(tagIdx > -1 && tagIdx < headEndIdx, `${label} verification meta tag is located inside <head>`);

  const tagMatches = (content.match(/google-site-verification/g) || []).length;
  assert(tagMatches === 1, `${label} contains verification meta tag exactly once`);
});

// --- 2. Open Graph & Twitter / X Metadata ---
console.log('\n--- 2. Social Meta Tags (Open Graph & Twitter) ---');
const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf8');

assert(
  indexHtmlContent.includes('<meta property="og:type" content="website" />'),
  'index.html includes og:type=website'
);
assert(
  indexHtmlContent.includes('<meta property="og:site_name" content="AttendX" />'),
  'index.html includes og:site_name=AttendX'
);
assert(
  indexHtmlContent.includes('<meta property="og:title" content="AttendX — Academic Attendance Management System" />'),
  'index.html includes og:title matching page title'
);
assert(
  indexHtmlContent.includes('property="og:description"') &&
  indexHtmlContent.includes('AttendX is a secure academic attendance management system for students, lecturers, and administrators.'),
  'index.html includes truthful og:description'
);
assert(
  indexHtmlContent.includes('<meta property="og:url" content="https://attendx-web-721g.onrender.com/" />'),
  'index.html includes og:url matching canonical production URL'
);

assert(
  indexHtmlContent.includes('<meta name="twitter:card" content="summary" />'),
  'index.html includes twitter:card=summary'
);
assert(
  indexHtmlContent.includes('<meta name="twitter:title" content="AttendX — Academic Attendance Management System" />'),
  'index.html includes twitter:title'
);
assert(
  indexHtmlContent.includes('name="twitter:description"') &&
  indexHtmlContent.includes('AttendX is a secure academic attendance management system for students, lecturers, and administrators.'),
  'index.html includes twitter:description'
);

// --- 3. Structured Data (JSON-LD) Validation ---
console.log('\n--- 3. JSON-LD Structured Data Schema ---');
const jsonLdMatch = indexHtmlContent.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
assert(!!jsonLdMatch, 'index.html contains JSON-LD structured data script block');

if (jsonLdMatch) {
  let parsedJsonLd = null;
  try {
    parsedJsonLd = JSON.parse(jsonLdMatch[1].trim());
    assert(true, 'JSON-LD schema parses as valid JSON');
  } catch (err) {
    assert(false, `JSON-LD schema parse error: ${err.message}`);
  }

  if (parsedJsonLd) {
    assert(parsedJsonLd['@context'] === 'https://schema.org', 'Schema @context is https://schema.org');
    const graph = parsedJsonLd['@graph'];
    assert(Array.isArray(graph) && graph.length >= 2, '@graph contains Organization and WebSite definitions');

    const org = graph.find(item => item['@type'] === 'Organization');
    const website = graph.find(item => item['@type'] === 'WebSite');

    assert(!!org, 'Schema defines Organization entity');
    assert(org?.name === 'AttendX', 'Organization name is AttendX');
    assert(org?.url === 'https://attendx-web-721g.onrender.com/', 'Organization URL is production homepage');

    assert(!!website, 'Schema defines WebSite entity');
    assert(website?.name === 'AttendX', 'WebSite name is AttendX');
    assert(website?.url === 'https://attendx-web-721g.onrender.com/', 'WebSite URL is production homepage');

    // Verify absence of fabricated claims
    const jsonLdStr = JSON.stringify(parsedJsonLd);
    assert(!jsonLdStr.includes('aggregateRating'), 'Zero fabricated ratings in structured data');
    assert(!jsonLdStr.includes('review'), 'Zero fabricated reviews in structured data');
    assert(!jsonLdStr.includes('offers'), 'Zero fabricated pricing in structured data');
  }
}

// --- 4. Robots.txt Verification ---
console.log('\n--- 4. robots.txt Verification ---');
const robotsPublic = path.join(publicDir, 'robots.txt');
const robotsDist = path.join(distDir, 'robots.txt');

assert(fs.existsSync(robotsPublic), 'public/robots.txt exists');
assert(fs.existsSync(robotsDist), 'dist/robots.txt bundled to production publish directory');

const robotsContent = fs.readFileSync(robotsPublic, 'utf8');
assert(robotsContent.includes('User-agent: *'), 'robots.txt allows all user agents');
assert(robotsContent.includes('Allow: /'), 'robots.txt explicitly allows public root /');
assert(
  robotsContent.includes('Sitemap: https://attendx-web-721g.onrender.com/sitemap.xml'),
  'robots.txt references production sitemap.xml URL'
);

// --- 5. XML Sitemap Verification ---
console.log('\n--- 5. sitemap.xml Verification ---');
const sitemapPublic = path.join(publicDir, 'sitemap.xml');
const sitemapDist = path.join(distDir, 'sitemap.xml');

assert(fs.existsSync(sitemapPublic), 'public/sitemap.xml exists');
assert(fs.existsSync(sitemapDist), 'dist/sitemap.xml bundled to production publish directory');

const sitemapContent = fs.readFileSync(sitemapPublic, 'utf8');
assert(sitemapContent.startsWith('<?xml version="1.0" encoding="UTF-8"?>'), 'sitemap.xml has valid XML declaration');
assert(sitemapContent.includes('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'), 'sitemap.xml specifies standard sitemaps 0.9 namespace');
assert(sitemapContent.includes('<loc>https://attendx-web-721g.onrender.com/</loc>'), 'sitemap.xml includes canonical public homepage URL');

// Strict privacy exclusion assertions in sitemap
assert(!sitemapContent.includes('/admin'), 'sitemap.xml strictly excludes /admin/* routes');
assert(!sitemapContent.includes('/student'), 'sitemap.xml strictly excludes /student/* routes');
assert(!sitemapContent.includes('/lecturer'), 'sitemap.xml strictly excludes /lecturer/* routes');
assert(!sitemapContent.includes('/dashboard'), 'sitemap.xml strictly excludes /dashboard routes');
assert(!sitemapContent.includes('token'), 'sitemap.xml strictly excludes token parameters');
assert(!sitemapContent.includes('activate'), 'sitemap.xml strictly excludes activation routes');
assert(!sitemapContent.includes('password'), 'sitemap.xml strictly excludes password reset routes');

// --- 6. Public Landing Semantic HTML & Content ---
console.log('\n--- 6. Public Landing Semantic HTML & Heading Hierarchy ---');
assert(fs.existsSync(rolePagePath), 'RoleSelectionPage.tsx exists');
const rolePageContent = fs.readFileSync(rolePagePath, 'utf8');

// Exactly one primary H1 assertion
const h1Matches = rolePageContent.match(/<h1[^>]*>([\s\S]*?)<\/h1>/g);
assert(h1Matches && h1Matches.length === 1, `RoleSelectionPage has exactly ONE <h1> tag (found: ${h1Matches ? h1Matches.length : 0})`);
assert(
  rolePageContent.includes('AttendX — Academic Attendance Management System'),
  'RoleSelectionPage <h1> explicitly includes "AttendX — Academic Attendance Management System"'
);

// Check semantic elements presence
assert(rolePageContent.includes('<header'), 'RoleSelectionPage contains semantic <header>');
assert(rolePageContent.includes('<nav'), 'RoleSelectionPage contains semantic <nav>');
assert(rolePageContent.includes('<main'), 'RoleSelectionPage contains semantic <main>');
assert(rolePageContent.includes('<section'), 'RoleSelectionPage contains semantic <section>');
assert(rolePageContent.includes('<article'), 'RoleSelectionPage contains semantic <article> cards');
assert(rolePageContent.includes('<footer'), 'RoleSelectionPage contains semantic <footer>');

// Verify truthful coverage of core roles and attendance capabilities
assert(rolePageContent.includes('Student'), 'RoleSelectionPage explains Student capabilities');
assert(rolePageContent.includes('Lecturer'), 'RoleSelectionPage explains Lecturer capabilities');
assert(rolePageContent.includes('Admin'), 'RoleSelectionPage explains Admin capabilities');
assert(rolePageContent.includes('75%'), 'RoleSelectionPage explains academic threshold monitoring');
assert(rolePageContent.includes('Secure Role-Based Access Control'), 'RoleSelectionPage explains RBAC security');

// --- 7. Static Asset & Favicon Branding ---
console.log('\n--- 7. Favicon & Branding ---');
const faviconPublic = path.join(publicDir, 'favicon.svg');
const faviconDist = path.join(distDir, 'favicon.svg');
assert(fs.existsSync(faviconPublic), 'public/favicon.svg exists');
assert(fs.existsSync(faviconDist), 'dist/favicon.svg exists in build output');

const faviconContent = fs.readFileSync(faviconPublic, 'utf8');
assert(faviconContent.includes('<svg') && faviconContent.includes('</svg>'), 'favicon.svg is valid SVG document');

// --- 8. Security & Secret Leakage Inspection ---
console.log('\n--- 8. Security & Privacy Audit on Public Artifacts ---');
const publicArtifacts = [indexHtmlContent, robotsContent, sitemapContent, rolePageContent];
const sensitiveTerms = ['password_hash', 'JWT_SECRET', 'DATABASE_URL', 'SUPABASE_KEY', 'EMAIL_PASSWORD', 'access_token'];

sensitiveTerms.forEach(term => {
  const leaked = publicArtifacts.some(artifact => artifact.includes(term));
  assert(!leaked, `Zero exposure of secret term '${term}' across public SEO assets`);
});

console.log('\n' + '='.repeat(70));
console.log(`TECHNICAL SEO VERIFICATION SUMMARY: ${passed} PASSED, ${failed} FAILED`);
console.log('='.repeat(70));

if (failed > 0) {
  process.exit(1);
}
