// Static component artwork is intentionally independent of executable models.
(async () => {
  for (let i = 0; i < 100 && !document.getElementById('upstream-lab'); i++) await new Promise(r => setTimeout(r, 50));
  const dialog = document.getElementById('upstream-lab');
  if (!dialog) return;
  const el = (tag, text, attrs = {}) => Object.assign(document.createElement(tag), {textContent: text, ...attrs});
  const section = el('section', '', {className: 'component-library', id: 'component-library'});
  const heading = el('h3', 'Community component library');
  const summary = el('p', 'Loading offline component library…', {id: 'component-library-summary'});
  summary.setAttribute('role', 'status');
  section.append(heading, summary);
  dialog.insertBefore(section, dialog.querySelector('#upstream-elements'));
  try {
    const response = await fetch('/vendor/components/catalog.json');
    if (!response.ok) throw Error('Component catalogue unavailable. Reload to retry.');
    const data = await response.json(), parts = data.parts;
    const search = el('input', '', {type: 'search', placeholder: 'Search names, connectors or properties', id: 'community-search'});
    search.setAttribute('aria-label', 'Search community components');
    const source = el('select', '', {id: 'community-source'}), category = el('select', '', {id: 'community-category'});
    source.setAttribute('aria-label', 'Component source'); category.setAttribute('aria-label', 'Component category');
    function options(select, label, values) {
      select.append(el('option', label, {value: ''}));
      for (const value of [...new Set(values)].sort()) select.append(el('option', value, {value}));
    }
    options(source, 'All repositories', parts.map(p => p.repository));
    options(category, 'All categories', parts.map(p => p.category));
    const controls = el('div', '', {className: 'community-controls'}); controls.append(search, source, category);
    const grid = el('div', '', {className: 'parts-grid', id: 'community-parts'});
    const previous = el('button', 'Previous page'), next = el('button', 'Next page'), position = el('span', '', {id: 'community-page'});
    const pages = el('div', '', {className: 'community-pages'}); pages.append(previous, position, next);
    const detail = el('section', '', {id: 'community-detail'}); detail.hidden = true;
    const tray = el('section', '', {id: 'community-tray'});
    const trayTitle = el('h4', 'Visual project parts list'), trayNote = el('p', 'Reference artwork and connector labels only. These selections do not create a simulated circuit.');
    const selectedList = el('ul'), exportButton = el('button', 'Export parts list JSON');
    const storageKey = 'mina-community-parts-v1';
    let saved = [];
    try { saved = JSON.parse(localStorage.getItem(storageKey) || '[]'); } catch {}
    const selected = new Set(Array.isArray(saved) ? saved.filter(id => parts.some(p => p.id === id)) : []);
    let page = 0;
    function renderTray() {
      selectedList.replaceChildren();
      for (const id of selected) {
        const part = parts.find(p => p.id === id), row = el('li', part.name + ' '), remove = el('button', 'Remove');
        remove.setAttribute('aria-label', 'Remove ' + part.name);
        remove.onclick = () => { selected.delete(id); renderTray(); render(); };
        row.append(remove); selectedList.append(row);
      }
      exportButton.disabled = !selected.size;
      trayTitle.textContent = `Visual project parts list (${selected.size})`;
      try { localStorage.setItem(storageKey, JSON.stringify([...selected])); } catch {}
    }
    exportButton.onclick = () => {
      const blob = new Blob([JSON.stringify({schemaVersion: 1, purpose: 'visual-reference-only', parts: parts.filter(p => selected.has(p.id))}, null, 2)], {type: 'application/json'});
      const url = URL.createObjectURL(blob), link = el('a', '', {href: url, download: 'mina-visual-parts.json'}); link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    function showDetail(part) {
      detail.replaceChildren(el('h4', part.name), el('p', 'Visual only · no electrical simulation adapter'));
      const image = el('img', '', {src: part.svgUrl, alt: part.name});
      const info = el('p', `${part.repository} · ${part.author} · ${part.license}`);
      const links = el('p');
      for (const [label, href] of [['Original source', part.sourceUrl], ['Artwork license', part.licenseUrl], ['Full attribution', part.noticeUrl]]) {
        links.append(el('a', label, {href, target: '_blank', rel: 'noopener noreferrer'}), document.createTextNode(' · '));
      }
      const connectors = el('p', 'Connectors: ' + (part.connectors.map(c => c.name || c.id).join(', ') || 'None specified upstream'));
      const properties = el('pre', JSON.stringify(part.properties, null, 2));
      detail.append(image, info, links, connectors, el('p', part.changes), properties); detail.hidden = false;
    }
    function render() {
      const query = search.value.trim().toLowerCase();
      const matches = parts.filter(p => (!source.value || p.repository === source.value) && (!category.value || p.category === category.value) && (!query || JSON.stringify([p.name, p.connectors, p.properties]).toLowerCase().includes(query)));
      const totalPages = Math.max(1, Math.ceil(matches.length / 24)); page = Math.min(page, totalPages - 1);
      grid.replaceChildren();
      summary.textContent = `${parts.length} imported component records · ${data.sources.length} repositories · ${matches.length} matching · artwork only; simulation support unchanged`;
      if (!matches.length) grid.append(el('p', 'No components match these filters.'));
      for (const part of matches.slice(page * 24, page * 24 + 24)) {
        const card = el('article', '', {className: 'part-card'}); card.dataset.part = part.id;
        const image = el('img', '', {src: part.svgUrl, alt: part.name, loading: 'lazy', decoding: 'async'});
        const inspect = el('button', 'View connectors & source'); inspect.onclick = () => showDetail(part);
        const add = el('button', selected.has(part.id) ? 'Added to parts list' : 'Add to visual parts list'); add.disabled = selected.has(part.id);
        add.onclick = () => { selected.add(part.id); renderTray(); render(); };
        card.append(image, el('b', part.name), el('small', 'Visual only · no simulation model'), el('span', `${part.repository} · ${part.category} · ${part.connectors.length} connectors · ${part.license}`), inspect, add); grid.append(card);
      }
      previous.disabled = page === 0; next.disabled = page >= totalPages - 1;
      position.textContent = `Page ${page + 1} / ${totalPages}`;
    }
    for (const control of [search, source, category]) control.addEventListener(control === search ? 'input' : 'change', () => {page = 0; render();});
    previous.onclick = () => {page--; render();}; next.onclick = () => {page++; render();};
    tray.append(trayTitle, trayNote, selectedList, exportButton);
    section.append(controls, grid, pages, detail, tray);
    renderTray(); render();
  } catch (error) { summary.textContent = error.message; }
})();
