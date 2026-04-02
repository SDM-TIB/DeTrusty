/**
 * detrusty-admin.js
 *
 * Federation Admin UI logic.
 *
 * Panels:
 *   Federations – lists all named graphs (federations)
 *   Endpoints   – per-federation endpoint management
 *   Prefixes    – per-federation prefix management with prefix.cc lookup
 *   SPARQL      – full Yasgui instance wired to /federation/sparql (admin-authed)
 *                 with autocompleters driven by /classes, /predicates, /namespaces
 */
'use strict';

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Constants & state
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const SESSION_KEY = 'detrusty_admin_token';

// Module-level state
let _yasgui          = null;
let _yasguiInited    = false;
let _federations     = [];    // cached list of federation URIs

// prefix.cc bulk lookup — fetched once, inverted to Map<uri, prefix>
let _prefixccMap     = null;  // null = not yet fetched
let _prefixccLoading = null;  // in-flight Promise (prevents duplicate fetches)

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Token helpers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const getToken = () => sessionStorage.getItem(SESSION_KEY) || '';

function storeToken(t) {
  if (t) sessionStorage.setItem(SESSION_KEY, t);
  else   sessionStorage.removeItem(SESSION_KEY);
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Login wall
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $loginWall  = document.getElementById('login-wall');
const $adminApp   = document.getElementById('admin-app');
const $wallToken  = document.getElementById('wall-token');
const $wallLogin  = document.getElementById('btn-wall-login');
const $wallError  = document.getElementById('wall-error');

/** Test a token against the admin API; returns true if accepted. */
async function testToken(token) {
  try {
    const r = await fetch('/federation/sparql?' + new URLSearchParams({ query: 'ASK {}' }), {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + token }
    });
    // 401/403 = bad token; anything else (incl. 400 "bad query") = token accepted
    return r.status !== 401 && r.status !== 403;
  } catch {
    return false;
  }
}

function showWallError(msg) {
  $wallError.textContent = msg;
  $wallToken.style.borderColor = '#c0392b';
}

function revealApp() {
  $loginWall.style.display = 'none';
  $adminApp.style.display  = 'block';
  $adminApp.removeAttribute('aria-hidden');
}

$wallLogin.addEventListener('click', async () => {
  const token = $wallToken.value.trim();
  if (!token) { showWallError('Please enter a token.'); return; }

  $wallLogin.disabled    = true;
  $wallLogin.textContent = 'Checking…';
  $wallError.textContent = '';
  $wallToken.style.borderColor = '';

  const ok = await testToken(token);
  $wallLogin.disabled    = false;
  $wallLogin.textContent = 'Sign in →';

  if (ok) {
    storeToken(token);
    revealApp();
    boot();
  } else {
    showWallError('Invalid token or server error. Please try again.');
  }
});

$wallToken.addEventListener('keydown', e => { if (e.key === 'Enter') $wallLogin.click(); });

document.getElementById('btn-logout').addEventListener('click', () => {
  storeToken('');
  if (_yasgui) { _yasgui.destroy(); _yasgui = null; _yasguiInited = false; }
  $adminApp.style.display = 'none';
  $adminApp.setAttribute('aria-hidden', 'true');
  $wallToken.value = '';
  $wallError.textContent = '';
  $wallToken.style.borderColor = '';
  $loginWall.style.display = 'flex';
});

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Banner notifications
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $banner = document.getElementById('admin-banner');
let   _bannerTimer = null;

function showBanner(msg, type /* 'success'|'error' */, duration = 5000) {
  $banner.textContent  = msg;
  $banner.className    = 'admin-banner ' + type;
  $banner.style.display = 'block';
  clearTimeout(_bannerTimer);
  if (duration > 0) {
    _bannerTimer = setTimeout(() => { $banner.style.display = 'none'; }, duration);
  }
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Tab navigation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $tabs   = document.querySelectorAll('.admin-tab');
const $panels = document.querySelectorAll('.admin-panel');

function activatePanel(panelId) {
  $tabs.forEach(t   => t.classList.toggle('active', t.dataset.panel === panelId));
  $panels.forEach(p => p.classList.toggle('active', p.id === panelId));

  // Lazy-init YASGUI when SPARQL tab is first shown
  if (panelId === 'panel-sparql' && !_yasguiInited) {
    _yasguiInited = true;
    initYasgui();
  }
}

$tabs.forEach(tab => tab.addEventListener('click', () => activatePanel(tab.dataset.panel)));

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Refresh buttons
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

document.querySelectorAll('[data-refresh]').forEach(btn => {
  btn.addEventListener('click', () => {
    switch (btn.dataset.refresh) {
      case 'federations': return loadFederations();
      case 'endpoints':   return loadEndpoints();
      case 'prefixes':    return loadPrefixes();
    }
  });
});

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   API helpers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/** Admin request (requires Bearer token). */
async function adminFetch(method, path, body = null) {
  const token = getToken();
  if (!token) {
    showBanner('No admin token. Please sign in again.', 'error');
    return { ok: false, status: 401, data: null };
  }
  const init = { method, headers: { 'Authorization': 'Bearer ' + token } };
  if (body) init.body = body;
  try {
    const resp = await fetch(path, init);
    const ct   = resp.headers.get('Content-Type') || '';
    const data = ct.includes('application/json') ? await resp.json() : await resp.text();
    return { ok: resp.ok, status: resp.status, data };
  } catch (err) {
    showBanner('Network error: ' + err.message, 'error');
    return { ok: false, status: 0, data: null };
  }
}

/** Public (unauthenticated) GET. */
async function pubGet(path, params = {}) {
  const url = new URL(path, location.href);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  try {
    const r = await fetch(url.toString());
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

/** Normalise the various JSON shapes the metadata service may return for a list. */
function extractList(data, ...keys) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  for (const k of keys) {
    if (Array.isArray(data[k])) return data[k];
  }
  // SPARQL-JSON
  if (data.results?.bindings) {
    return data.results.bindings.map(b => {
      const firstVal = Object.values(b)[0];
      return firstVal?.value ?? null;
    }).filter(Boolean);
  }
  return [];
}

/** Friendly label for a URI: last path/fragment segment, or the full URI. */
function uriLabel(uri) {
  try {
    const u = new URL(uri);
    const last = (u.pathname + u.hash).split(/[/#]/).filter(Boolean).pop();
    return last || uri;
  } catch { return uri; }
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Colour palette (for dots / endpoint tags)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const PALETTE = [
  '#4a90d9','#e67e22','#8e44ad','#27ae60','#c0392b',
  '#16a085','#f39c12','#2980b9','#d35400','#7f8c8d',
];
const dotColour = idx => PALETTE[idx % PALETTE.length];

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Federation selectors (shared state)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $epFedFilter  = document.getElementById('ep-fed-filter');
const $epFedExSel   = document.getElementById('ep-fed-existing-select');
const $pfxFedSelect = document.getElementById('pfx-fed-select');

function populateFedSelectors(feds) {
  const selectors = [$epFedFilter, $epFedExSel, $pfxFedSelect];
  selectors.forEach(sel => {
    const preserved = sel.value;
    // Keep the first "All" placeholder if present
    while (sel.options.length > 1) sel.remove(1);
    feds.forEach((uri, i) => {
      const opt = document.createElement('option');
      opt.value       = uri;
      opt.textContent = uriLabel(uri);
      opt.title       = uri;
      sel.appendChild(opt);
    });
    // Restore selection if still valid
    if ([...sel.options].some(o => o.value === preserved)) sel.value = preserved;
  });
  // Re-sync the add form in case the filter already has a value
  if (typeof syncAddFormToFilter === 'function') syncAddFormToFilter();
}

// When the filter changes, pre-fill the existing-federation select to match.
function syncAddFormToFilter() {
  const fed = $epFedFilter.value;
  if (fed) $epFedExSel.value = fed;
}

// Federation filter changes trigger endpoint reload + add-form sync
$epFedFilter.addEventListener('change', () => {
  syncAddFormToFilter();
  loadEndpoints();
});
$pfxFedSelect.addEventListener('change', loadPrefixes);

// Add-endpoint radio toggle
document.querySelectorAll('input[name="ep-fed-mode"]').forEach(radio => {
  radio.addEventListener('change', () => {
    const isNew = radio.value === 'new' && radio.checked;
    document.getElementById('ep-fed-existing-row').style.display = isNew ? 'none'  : 'flex';
    document.getElementById('ep-fed-new-row').style.display      = isNew ? 'flex'  : 'none';
  });
});

/**
 * Switch to the Endpoints tab with the add-form pre-set for a brand-new
 * federation URI.  The user lands directly on the endpoint URL input so
 * they can add the first endpoint in one motion.
 */
function startNewFederation(uri) {
  // Pre-fill the new-federation URI input and switch to "new" mode
  document.querySelector('input[name="ep-fed-mode"][value="new"]').checked = true;
  document.getElementById('ep-fed-existing-row').style.display = 'none';
  document.getElementById('ep-fed-new-row').style.display      = 'flex';
  document.getElementById('ep-fed-new-uri').value              = uri;
  $epFedFilter.value = '';

  activatePanel('panel-endpoints');
  document.getElementById('ep-url').focus();
}

document.getElementById('btn-new-federation').addEventListener('click', () => {
  const uri = document.getElementById('new-fed-uri').value.trim();
  if (!uri) {
    document.getElementById('new-fed-uri').focus();
    return;
  }
  startNewFederation(uri);
});

document.getElementById('new-fed-uri').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-new-federation').click();
});

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▌FEDERATIONS PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $fedList = document.getElementById('fed-list');

async function loadFederations() {
  $fedList.innerHTML = '<p class="list-empty">Loading…</p>';
  const data = await pubGet('/federations');
  const items = extractList(data, 'federations', 'graphs');

  _federations = items.map(i => (typeof i === 'string' ? i : i.uri || i.url || ''));
  populateFedSelectors(_federations);

  if (_federations.length === 0) {
    $fedList.innerHTML = '<p class="list-empty">No federations found.</p>';
    return;
  }

  $fedList.innerHTML = '';
  _federations.forEach((uri, idx) => {
    const row = document.createElement('div');
    row.className = 'fed-row';

    const dot = document.createElement('span');
    dot.className = 'fed-dot';
    dot.style.background = dotColour(idx);

    const label = document.createElement('span');
    label.className = 'fed-label';
    label.title = uri;
    label.textContent = uri;

    const actions = document.createElement('span');
    actions.className = 'item-actions';

    // Copy URI
    const btnCopy = document.createElement('button');
    btnCopy.className = 'btn btn-ghost btn-sm';
    btnCopy.textContent = 'Copy URI';
    btnCopy.addEventListener('click', () => {
      navigator.clipboard.writeText(uri).then(() => showBanner('URI copied to clipboard.', 'success', 2000));
    });

    // Navigate to endpoints for this federation
    const btnEp = document.createElement('button');
    btnEp.className = 'btn btn-ghost btn-sm';
    btnEp.textContent = 'View endpoints →';
    btnEp.addEventListener('click', () => {
      $epFedFilter.value = uri;
      activatePanel('panel-endpoints');
      loadEndpoints();
    });

    actions.append(btnCopy, btnEp);
    row.append(dot, label, actions);
    $fedList.appendChild(row);
  });
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▌ENDPOINTS PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $endpointList = document.getElementById('endpoint-list');
const $epCount      = document.getElementById('ep-count');
const $epUrl        = document.getElementById('ep-url');
const $btnAddEp     = document.getElementById('btn-add-endpoint');

/**
 * Fetch endpoints for the selected federation via a SPARQL query
 * to the metadata service.  We try both sd:endpoint and void:sparqlEndpoint
 * patterns, plus a broader subject-object sweep as fallback.
 */
/**
 * Fetch endpoints for a federation (or all federations) from the metadata store.
 *
 * We try three progressively broader SPARQL strategies because the exact
 * predicate used by the metadata service is not guaranteed:
 *   1. Known endpoint predicates (sd:endpoint, void:sparqlEndpoint, sd:url)
 *   2. Any predicate whose namespace suggests service-description / void
 *   3. Any URI object in the named graph (last-resort; filtered to look like
 *      SPARQL endpoints by requiring "sparql" or "/query" in the URL)
 *
 * For "all federations" we query across all named graphs in one shot.
 */
/** Fetch endpoints via the dedicated metadata route. */
async function queryEndpoints(federationUri) {
  const params = federationUri ? `?federation=${encodeURIComponent(federationUri)}` : '';
  const { ok, status, data } = await adminFetch('GET', `/federation/endpoints${params}`);
  if (!ok) return null;
  // Response: { endpoints: [{url, federation}, ...] }
  return data?.endpoints ?? [];
}


async function loadEndpoints() {
  const fed = $epFedFilter.value;
  $endpointList.innerHTML = '<p class="list-empty">Loading…</p>';
  $epCount.textContent = '';

  const bindings = await queryEndpoints(fed);

  if (bindings === null) {
    $endpointList.innerHTML =
      '<p class="list-empty">Could not retrieve endpoints — check your token.</p>';
    return;
  }

  if (bindings.length === 0) {
    $endpointList.innerHTML = fed
      ? '<p class="list-empty">No endpoints registered for this federation.</p>'
      : '<p class="list-empty">No endpoints found across all federations.</p>';
    return;
  }

  $endpointList.innerHTML = '';
  $epCount.textContent = bindings.length;

  bindings.forEach((b, idx) => {
    const url   = b.url        || '';
    const graph = b.federation || fed || '';
    if (!url) return;

    const row = document.createElement('div');
    row.className = 'ep-row';

    const dot = document.createElement('span');
    dot.className = 'ep-dot';
    dot.style.background = dotColour(idx);

    const urlEl = document.createElement('span');
    urlEl.className = 'ep-url';
    urlEl.title = url;
    urlEl.textContent = url;

    const actions = document.createElement('span');
    actions.className = 'item-actions';

    if (graph) {
      const tag = document.createElement('span');
      tag.className = 'ep-fed-tag';
      tag.title = graph;
      tag.textContent = uriLabel(graph);
      actions.appendChild(tag);
    }

    const btnDel = document.createElement('button');
    btnDel.className = 'btn btn-danger btn-sm';
    btnDel.textContent = 'Remove';
    btnDel.addEventListener('click', () => deleteEndpoint(url, graph, row));
    actions.appendChild(btnDel);

    row.append(dot, urlEl, actions);
    $endpointList.appendChild(row);
  });
}

async function addEndpoint() {
  const url = $epUrl.value.trim();
  if (!url) { showBanner('Please enter an endpoint URL.', 'error'); return; }

  const mode = document.querySelector('input[name="ep-fed-mode"]:checked').value;
  const graph = mode === 'new'
    ? document.getElementById('ep-fed-new-uri').value.trim()
    : $epFedExSel.value;

  if (!graph) {
    showBanner(mode === 'new' ? 'Please enter a URI for the new federation.' : 'Please select a federation.', 'error');
    return;
  }

  const form = new FormData();
  form.append('endpoint',    url);
  form.append('federation',  graph);

  $btnAddEp.disabled = true;
  const { ok, status, data } = await adminFetch('POST', '/federation/endpoint', form);
  $btnAddEp.disabled = false;

  if (!ok) {
    showBanner(
      (data?.error) || (status === 401 ? 'Unauthorized – check your token.' : 'Failed to add endpoint.'),
      'error'
    );
    return;
  }

  showBanner('Endpoint added.', 'success');
  $epUrl.value = '';
  document.getElementById('ep-fed-new-uri').value = '';
  // Refresh federations in case a new one was created, then reload endpoints
  await loadFederations();
  $epFedFilter.value = graph;
  loadEndpoints();
}

async function deleteEndpoint(url, graph, rowEl) {
  if (!confirm(`Remove endpoint:\n${url}${graph ? '\nfrom federation: ' + graph : ''}?`)) return;

  const form = new FormData();
  form.append('endpoint', url);
  if (graph) form.append('federation', graph);

  const { ok, status, data } = await adminFetch('DELETE', '/federation/endpoint', form);
  if (!ok) {
    showBanner(
      (data?.error) || (status === 401 ? 'Unauthorized.' : 'Failed to remove endpoint.'),
      'error'
    );
    return;
  }

  showBanner('Endpoint removed.', 'success');
  rowEl.remove();
  const remaining = $endpointList.querySelectorAll('.ep-row').length;
  $epCount.textContent = remaining || '';
  if (!remaining) $endpointList.innerHTML = '<p class="list-empty">No endpoints registered.</p>';
}

$btnAddEp.addEventListener('click', addEndpoint);
$epUrl.addEventListener('keydown', e => { if (e.key === 'Enter') addEndpoint(); });

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▌PREFIXES PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

const $prefixList    = document.getElementById('prefix-list');
const $unnamedList   = document.getElementById('unnamed-list');
const $pfxCount      = document.getElementById('pfx-count');
const $unnamedCount  = document.getElementById('unnamed-count');
const $pfxUnnamedCard = document.getElementById('pfx-unnamed-card');
const $pfxName       = document.getElementById('pfx-name');
const $pfxUri        = document.getElementById('pfx-uri');
const $btnAddPrefix  = document.getElementById('btn-add-prefix');

/**
 * Ensure the prefix.cc dataset is loaded.
 *
 * Uses the same URL as detrusty-autocompleters.js so the browser can reuse
 * its cached response:
 *   //prefix.cc/popular/all.file.json -> { "rdf": "http://...", ... }
 *
 * We invert the { prefix->uri } object into a Map<uri, prefix> for fast
 * reverse lookups. The result is cached for the lifetime of the page.
 */
async function getPrefixccMap() {
  if (_prefixccMap !== null) return _prefixccMap;
  if (_prefixccLoading)      return _prefixccLoading;

  // Protocol-relative URL -- mirrors detrusty-autocompleters.js exactly.
  const url = (location.protocol.startsWith('http') ? '//' : 'http://')
    + 'prefix.cc/popular/all.file.json';

  _prefixccLoading = fetch(url, { signal: AbortSignal.timeout(8000) })
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(data => {
      // Response shape: { "rdf": "http://...", "owl": "http://...", ... }
      // Invert to Map<uri, prefix> for O(1) reverse lookups.
      const map = new Map();
      for (const [prefix, uri] of Object.entries(data)) {
        // Keep first occurrence — all.file.json is ordered so the canonical
        // prefix (e.g. "dbp") appears before aliases (e.g. "dbpprop").
        if (typeof uri === 'string' && !map.has(uri)) map.set(uri, prefix);
      }
      _prefixccMap     = map;
      _prefixccLoading = null;
      return map;
    })
    .catch(() => {
      _prefixccMap     = new Map(); // empty -- every URI treated as unknown
      _prefixccLoading = null;
      return _prefixccMap;
    });

  return _prefixccLoading;
}

/**
 * Look up whether a URI is a well-known namespace according to prefix.cc.
 * Returns the canonical prefix string, or null if not found.
 * All lookups are local after the first bulk fetch.
 */
async function lookupPrefixcc(uri) {
  const map = await getPrefixccMap();
  return map.get(uri) ?? null;
}

async function loadPrefixes() {
  const fed = $pfxFedSelect.value;
  $prefixList.innerHTML = '<p class="list-empty">Loading…</p>';
  $pfxUnnamedCard.style.display = 'none';
  $pfxCount.textContent = '';

  const params = {};
  if (fed) params.federation = fed;
  const data = await pubGet('/namespaces', params);

  // /namespaces returns:
  //   { namespaces: ["http://...", ...],          ← derived namespace URIs (no prefix)
  //     prefixes:   { "k4covid": "http://...", … } ← user-declared PrefixDeclarations }
  const nsUris    = Array.isArray(data?.namespaces) ? data.namespaces : [];
  const pfxObject = (data?.prefixes && typeof data.prefixes === 'object') ? data.prefixes : {};

  // Named = user-declared prefix declarations
  const named = Object.entries(pfxObject).map(([prefix, uri]) => ({ prefix, uri }));

  // Unnamed = namespace URIs derived from the data that have no user-declared prefix
  const declaredUris = new Set(Object.values(pfxObject));
  const unnamed = nsUris
    .filter(uri => !declaredUris.has(uri))
    .map(uri => ({ prefix: '', uri }));

  // ── Named prefixes
  $pfxCount.textContent = named.length || '';
  if (named.length === 0) {
    $prefixList.innerHTML = '<p class="list-empty">No named prefixes for this selection.</p>';
  } else {
    $prefixList.innerHTML = '';
    named.forEach(item => $prefixList.appendChild(buildPfxRow(item, fed)));
  }

  // ── Unnamed prefixes
  if (unnamed.length === 0) return;
  $pfxUnnamedCard.style.display = 'block';
  $unnamedList.innerHTML = '<p class="list-empty">Looking up prefix.cc…</p>';
  $unnamedCount.textContent = unnamed.length;

  // Resolve prefix.cc for all unnamed in parallel
  const suggestions = await Promise.all(unnamed.map(i => lookupPrefixcc(i.uri)));

  $unnamedList.innerHTML = '';
  unnamed.forEach((item, idx) => {
    $unnamedList.appendChild(buildUnnamedRow(item, suggestions[idx], fed));
  });

  // Update cleanup button: only enable if at least one is known to prefix.cc
  const knownCount = suggestions.filter(Boolean).length;
  const $cleanup = document.getElementById('btn-cleanup-unnamed');
  $cleanup.disabled = knownCount === 0;
  $cleanup.title = knownCount > 0
    ? `Remove ${knownCount} namespace(s) already covered by prefix.cc`
    : 'No redundant namespaces found';
}

/** Build a row for a named prefix, showing "name: URI". */
function buildPfxRow({ prefix, uri }, federation) {
  const row = document.createElement('div');
  row.className = 'pfx-row';

  const nameEl = document.createElement('span');
  nameEl.className = 'pfx-name';
  nameEl.title = prefix;
  nameEl.textContent = prefix;

  const colon = document.createElement('span');
  colon.className = 'pfx-colon';
  colon.textContent = ':';

  const uriEl = document.createElement('span');
  uriEl.className = 'pfx-uri';
  uriEl.title = uri;
  uriEl.textContent = uri;

  const actions = document.createElement('span');
  actions.className = 'item-actions';

  const btnDel = document.createElement('button');
  btnDel.className = 'btn btn-danger btn-sm';
  btnDel.textContent = 'Remove';
  btnDel.addEventListener('click', () => deletePrefix(prefix, uri, federation, row));
  actions.appendChild(btnDel);

  row.append(nameEl, colon, uriEl, actions);
  return row;
}

/**
 * Build a row for a prefix without a shorthand.
 * @param {{prefix:string, uri:string}} item
 * @param {string|null} suggestedPrefix  – result from prefix.cc, or null
 * @param {string} federation
 */
function buildUnnamedRow({ uri }, suggestedPrefix, federation) {
  const row = document.createElement('div');
  row.className = 'unnamed-row';
  row.dataset.uri = uri;

  const uriEl = document.createElement('div');
  uriEl.className = 'unnamed-uri';
  uriEl.textContent = uri;

  const actions = document.createElement('div');
  actions.className = 'unnamed-actions';

  if (suggestedPrefix) {
    // ── Known to prefix.cc: show suggestion + set/remove options
    const suggestion = document.createElement('span');
    suggestion.className = 'prefixcc-suggestion';
    suggestion.innerHTML =
      `<span class="prefixcc-label">prefix.cc suggests:</span>`
      + `<span class="prefixcc-name">${suggestedPrefix}:</span>`;

    const btnUse = document.createElement('button');
    btnUse.className = 'btn btn-ghost btn-sm';
    btnUse.textContent = `Use "${suggestedPrefix}"`;
    btnUse.addEventListener('click', async () => {
      await savePrefix(suggestedPrefix, uri, federation);
      loadPrefixes();
    });

    const btnRm = document.createElement('button');
    btnRm.className = 'btn btn-danger btn-sm';
    btnRm.textContent = 'Remove (redundant)';
    btnRm.title = 'This namespace is already well-known; remove it from the federation registry.';
    btnRm.addEventListener('click', async () => {
      await deletePrefix('', uri, federation, row);
      loadPrefixes();
    });

    actions.append(suggestion, btnUse, btnRm);
  } else {
    // ── Not known to prefix.cc: let the user assign a name
    const nameInput = document.createElement('input');
    nameInput.type        = 'text';
    nameInput.placeholder = 'shorthand';
    nameInput.className   = 'admin-input unnamed-name-input';
    nameInput.spellcheck  = false;
    // Pre-fill with the prefix.cc suggestion when one exists (passed as
    // suggestedPrefix even in this branch when it was trimmed to avoid
    // double-listing — not currently the case, but keeps the path open).
    if (suggestedPrefix) nameInput.value = suggestedPrefix;

    const btnSet = document.createElement('button');
    btnSet.className = 'btn btn-primary btn-sm';
    btnSet.textContent = 'Set name';
    btnSet.addEventListener('click', async () => {
      const name = nameInput.value.trim().replace(/:$/, '');
      if (!name) { nameInput.focus(); return; }
      await savePrefix(name, uri, federation);
      loadPrefixes();
    });

    nameInput.addEventListener('keydown', e => { if (e.key === 'Enter') btnSet.click(); });

    const btnRm = document.createElement('button');
    btnRm.className = 'btn btn-danger btn-sm';
    btnRm.textContent = 'Remove';
    btnRm.addEventListener('click', async () => {
      await deletePrefix('', uri, federation, row);
      loadPrefixes();
    });

    actions.append(nameInput, btnSet, btnRm);
  }

  row.append(uriEl, actions);
  return row;
}

async function savePrefix(name, uri, federation) {
  const form = new FormData();
  form.append('name',        name);
  form.append('uri',         uri);
  if (federation) form.append('federation', federation);

  const { ok, status, data } = await adminFetch('POST', '/federation/prefix', form);
  if (!ok) {
    showBanner(
      data?.error || (status === 401 ? 'Unauthorized.' : 'Failed to save prefix.'),
      'error'
    );
    return false;
  }
  showBanner(`Prefix "${name}:" saved.`, 'success');
  return true;
}

async function deletePrefix(name, uri, federation, rowEl) {
  if (rowEl && !confirm(`Remove prefix${name ? ' "' + name + ':"' : ''}?\n${uri}`)) return false;

  const form = new FormData();
  if (name) form.append('name', name);
  if (federation) form.append('federation', federation);

  const { ok, status, data } = await adminFetch('DELETE', '/federation/prefix', form);
  if (!ok) {
    showBanner(
      data?.error || (status === 401 ? 'Unauthorized.' : 'Failed to remove prefix.'),
      'error'
    );
    return false;
  }
  showBanner('Prefix removed.', 'success');
  if (rowEl) rowEl.remove();
  return true;
}

async function addPrefix() {
  const name = $pfxName.value.trim().replace(/:$/, '');
  const uri  = $pfxUri.value.trim();
  if (!name || !uri) {
    showBanner('Please enter both a prefix name and a URI.', 'error');
    return;
  }
  $btnAddPrefix.disabled = true;
  const ok = await savePrefix(name, uri, $pfxFedSelect.value);
  $btnAddPrefix.disabled = false;
  if (ok) {
    $pfxName.value = '';
    $pfxUri.value  = '';
    loadPrefixes();
  }
}

// "Clean up" button: remove all unnamed that prefix.cc knows
document.getElementById('btn-cleanup-unnamed').addEventListener('click', async () => {
  const rows = [...document.querySelectorAll('#unnamed-list .unnamed-row')];
  if (!rows.length) return;

  const toRemove = rows.filter(r => r.querySelector('.prefixcc-name'));
  if (!toRemove.length) { showBanner('No redundant namespaces to remove.', 'success'); return; }

  if (!confirm(`Remove ${toRemove.length} namespace(s) already covered by prefix.cc?`)) return;

  let removed = 0;
  for (const r of toRemove) {
    const uri = r.dataset.uri;
    const ok  = await deletePrefix('', uri, $pfxFedSelect.value, null);
    if (ok) { r.remove(); removed++; }
  }
  showBanner(`Removed ${removed} redundant namespace(s).`, 'success');
  loadPrefixes();
});

$btnAddPrefix.addEventListener('click', addPrefix);
$pfxName.addEventListener('keydown', e => { if (e.key === 'Enter') $pfxUri.focus(); });
$pfxUri.addEventListener('keydown',  e => { if (e.key === 'Enter') addPrefix(); });

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ▌YASGUI – SPARQL console
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function initYasgui() {
  if (typeof Yasgui === 'undefined') {
    document.getElementById('panel-sparql').innerHTML =
      '<p style="color:#a94442;padding:16px">Yasgui library not loaded. Ensure yasgui.min.js is present.</p>';
    return;
  }

  const el        = document.getElementById('admin-yasgui');
  const endpoint  = el.dataset.endpoint;
  const classesEp = el.dataset.classesEndpoint;
  const predsEp   = el.dataset.predicatesEndpoint;
  const nsEp      = el.dataset.namespacesEndpoint;

  // ── Register semsd ontology autocompleters ───────────────────────
  // These mirror the pattern expected by detrusty-autocompleters.js,
  // but are self-contained so the admin page has no extra JS dependency.

  function makeCompleter(name, fetchItems, isValidFn) {
    return {
      isValidCompletionPosition: isValidFn,
      bulk: true,
      preOrPost: 'pre',
      get: (yasqe, token) => {
        return fetch(fetchItems)
          .then(r => r.json())
          .then(data => {
            // Accept arrays, {values:[...]}, SPARQL-JSON, or {classes/predicates:[...]}
            const list = Array.isArray(data) ? data
              : data.results?.bindings?.map(b => Object.values(b)[0]?.value).filter(Boolean)
              || data.values || data.classes || data.predicates || data.namespaces || [];
            return list.map(v => (typeof v === 'string' ? v : v.uri || v.value || ''));
          })
          .catch(() => []);
      },
      cache: { expiresAfterMs: 5 * 60 * 1000 } // 5 min
    };
  }

  // Register only if Yasqe exposes the API (not all YASGUI builds do)
  const Yasqe = Yasgui.Yasqe || window.Yasqe;
  if (Yasqe?.registerAutocompleter) {
    Yasqe.registerAutocompleter('semsd-classes', makeCompleter(
      'semsd-classes', classesEp,
      yasqe => Yasqe.isClass ? Yasqe.isClass(yasqe) : true
    ));
    Yasqe.registerAutocompleter('semsd-predicates', makeCompleter(
      'semsd-predicates', predsEp,
      yasqe => Yasqe.isProperty ? Yasqe.isProperty(yasqe) : true
    ));
  }

  // ── Initialise Yasgui ─────────────────────────────────────────────
  _yasgui = new Yasgui(el, {
    requestConfig: {
      endpoint,
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + getToken() }
    },
    copyEndpointOnNewTab: false,
  });

  // Populate namespace prefixes from /namespaces for the editor
  fetch(nsEp)
    .then(r => r.json())
    .then(data => {
      const items = extractList(data, 'namespaces', 'prefixes');
      const prefixMap = {};
      items.forEach(item => {
        const p = item.prefix || item.name  || '';
        const u = item.uri    || item.value || '';
        if (p && u) prefixMap[p] = u;
      });
      if (Object.keys(prefixMap).length) {
        try {
          const yasqe = _yasgui.getTab()?.yasqe;
          if (yasqe) yasqe.options.prefixCcApi = null; // use local only
          Yasgui.Yasqe.defaults.autocompleters = (Yasgui.Yasqe.defaults.autocompleters || [])
            .filter(a => a !== 'prefixes');
        } catch { /* best-effort */ }
      }
    })
    .catch(() => {});
}

/** Update YASGUI auth header when the token changes (e.g. after re-login). */
function syncYasguiToken() {
  if (!_yasgui) return;
  try {
    const yasqe = _yasgui.getTab()?.yasqe;
    if (yasqe) {
      yasqe.options.requestConfig = {
        ...yasqe.options.requestConfig,
        headers: { 'Authorization': 'Bearer ' + getToken() }
      };
    }
  } catch { /* best-effort */ }
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Boot (called after successful auth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

async function boot() {
  await loadFederations();
  await loadPrefixes();
  await loadEndpoints();
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Init
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

(function init() {
  const saved = getToken();
  if (saved) {
    // Session has a token: validate silently, reveal app if still good
    testToken(saved).then(ok => {
      if (ok) { revealApp(); boot(); }
      // else: leave login wall up; token expired
    });
  }
  // else: login wall is already visible (HTML default)
})();
