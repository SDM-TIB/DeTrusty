document.addEventListener('DOMContentLoaded', function () {
    const COLORS = ['#9ACD32', '#A52A2A', '#5B9AA0', '#FFA500', '#622569',
            '#BC8F8F', '#808080', '#006400', '#191970', '#8B4513'],
          btn_query_plan = document.createElement('button'),
          yasqe = new Yasqe(document.getElementById('yasqe'), {
              persistenceId: null,
              tabSize: 2,
              indentUnit: 2,
              extraKeys: {
                  Tab: function(cm) {
                      cm.replaceSelection(new Array(cm.getOption('indentUnit') + 1).join(' '));
                  }
              },
              pluginButtons: function() { return btn_query_plan }
          }),
          errorEl = document.getElementById('plan-error'),
          endpoint = document.getElementById('yasqe').dataset.endpoint,
          federationsEndpoint = document.getElementById('yasqe').dataset.federationsEndpoint,
          nativeBtn = document.querySelector('.yasqe_queryButton:not(#btn_query_plan)');

    btn_query_plan.innerHTML = nativeBtn.innerHTML;
    nativeBtn.remove();

    btn_query_plan.id    = 'btn_query_plan';
    btn_query_plan.title = 'Create Plan';
    btn_query_plan.classList.add('yasqe_queryButton');

    // Populate the federation selector.
    const federationSelect = document.getElementById('federation-select');
    fetch(federationsEndpoint)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            let federations = data.federations || [];
            if (federations.length < 2) return;
            federations.forEach(function (uri) {
                let opt = document.createElement('option');
                opt.value = uri;
                opt.textContent = uri.split(/[#\/]/).filter(Boolean).pop() || uri;
                opt.title = uri;
                federationSelect.appendChild(opt);
            });
            document.getElementById('federation-bar').style.display = 'flex';
        })
        .catch(function (err) { console.warn('Could not load federation list:', err); });

    function renderError(message) {
        errorEl.innerHTML = '';
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger';
        alertEl.textContent = message;
        errorEl.appendChild(alertEl);
    }

    function clearError() {
        errorEl.innerHTML = '';
    }

    btn_query_plan.onclick = function () {
        const query = yasqe.getValue(),
              canvas = document.getElementById('canvas'),
              queryPlanDetails = document.getElementById('details');

        canvas.innerHTML = '';
        queryPlanDetails.innerHTML = '';
        clearError();
        btn_query_plan.classList.add('busy');
        btn_query_plan.disabled = true;

        const params = { query };
        if (federationSelect && federationSelect.value) {
            params.federation = federationSelect.value;
        }

        fetch(endpoint, {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: new URLSearchParams(params)
        })
            .then(function (response) {
                if (!response.ok) {
                    return response.text().then(function (text) {
                        throw { status: response.status, message: text };
                    });
                }
                return response.json();
            })
            .then(function (data) {
                canvas.innerHTML = '';
                queryPlanDetails.innerHTML = '';
                document.getElementById('plan-container').style.display = 'flex';
                create_tree(data['tree'], data['details']);
            })
            .catch(function (err) {
                canvas.innerHTML = '';
                document.getElementById('plan-container').style.display = 'none';
                document.getElementById('canvas-toolbar').style.display = 'none';
                renderError('The server returned status ' + err.status + '. Message: ' + err.message);
            })
            .finally(function () {
                btn_query_plan.classList.remove('busy');
                btn_query_plan.disabled = false;
            });
    };

    function create_tree(treeData, details) {
        const endpoints = new Set();
        for (const ssq in details) endpoints.add(details[ssq]['endpoint']);
        const endpoints_list = Array.from(endpoints).sort(),
              detailsPanel = document.getElementById('details');
        detailsPanel.appendChild(buildLegend(endpoints_list));

        const detailsHeading = document.createElement('h3');
        detailsHeading.textContent = 'Sub-query Details';
        detailsPanel.appendChild(detailsHeading);

        const ssq_list = document.createElement('ul');
        ssq_list.id = 'subqueries';
        for (const ssq in details) {
            const li  = document.createElement('li'),
                  dot = document.createElement('span');
            dot.className = 'endpoint-dot';
            dot.style.background = endpointColor(details[ssq]['endpoint'], endpoints_list);
            const label = document.createElement('span');
            label.innerHTML = '<b>' + ssq + '</b><br>'
                + '<span class="detail-label">Endpoint:</span> '
                + '<code>' + details[ssq]['endpoint'] + '</code><br>'
                + '<span class="detail-label">Triples:</span><br>'
                + '<pre>' + details[ssq]['triples'] + '</pre>';
            li.appendChild(dot);
            li.appendChild(label);
            ssq_list.appendChild(li);
        }
        detailsPanel.appendChild(ssq_list);

        /* ---- canvas dimensions ---- */
        const canvasEl = document.getElementById('canvas'),
              totalW = canvasEl.clientWidth  || 860,
              totalH = canvasEl.clientHeight || 640;

        /* ---- tooltip ---- */
        let tooltip = document.getElementById('plan-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'plan-tooltip';
            document.body.appendChild(tooltip);
        }

        /* ---- SVG ---- */
        const svgRoot = d3.select('#canvas').append('svg')
            .attr('id', 'plan-svg')
            .attr('width',  '100%')
            .attr('height', totalH);

        const g = svgRoot.append('g').attr('class', 'tree-group');

        /* ---- zoom behaviour ---- */
        const zoom = d3.zoom()
            .scaleExtent([0.05, 8])
            .on('zoom', function (event) {
                g.attr('transform', event.transform);
            });
        svgRoot.call(zoom);

        /* ---- toolbar ---- */
        buildToolbar(zoom, svgRoot, totalW, totalH);

        /* ---- hierarchy & initial layout ---- */
        const DEPTH_GAP = 120;
        let root = d3.hierarchy(treeData, d => d.children);

        /* use full canvas dimensions so initial spread fills space */
        const treemap = d3.tree().size([totalW - 40, totalH - 40]);

        root.x0 = totalW / 2;
        root.y0 = 0;

        update(root);
        fitTree(0); /* instant fit on first render */

        function update(source) {
            const layout = treemap(root),
                  nodes = layout.descendants(),
                  links = layout.links();

            /* fixed vertical depth spacing */
            nodes.forEach(d => { d.y = d.depth * DEPTH_GAP; });

            /* ---- NODES ---- */
            const node = g.selectAll('g.node')
                .data(nodes, d => d.id || (d.id = Math.random()));

            /* --- enter --- */
            const nodeEnter = node.enter().append('g')
                .attr('class', d => 'node' + (d.children || d._children ? ' node--internal' : ' node--leaf'))
                .attr('transform', () => 'translate(' + source.x0 + ',' + source.y0 + ')')
                .style('opacity', 0)
                .on('click', function (event, d) {
                    if (d.children) { d._children = d.children; d.children = null; }
                    else            { d.children  = d._children; d._children = null; }
                    update(d);
                })
                .on('mousemove', function (event, d) {
                    if (!d.data.name) return;
                    const ssqDetails = details[d.data.name];
                    if (!ssqDetails) return;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (event.pageX + 14) + 'px';
                    tooltip.style.top = (event.pageY - 28) + 'px';
                    tooltip.innerHTML = '<strong>' + d.data.name + '</strong><br>'
                        + '<span class="tt-label">Endpoint:</span> '
                        + ssqDetails['endpoint'] + '<br>'
                        + '<span class="tt-label">Triples:</span><br><pre>'
                        + ssqDetails['triples'] + '</pre>';
                })
                .on('mouseleave', function () {
                    tooltip.style.display = 'none';
                });

            /* node shapes */
            nodeEnter.each(function (d) {
                const sel = d3.select(this),
                      isJoin = !!(d.children || d._children || d.data.children),
                      color = d.data.endpoint
                          ? endpointColor(d.data.endpoint, endpoints_list)
                          : (isJoin ? '#ddd' : '#fff');

                if (isJoin) {
                    sel.append('rect')
                        .attr('class', 'node-shape node-join')
                        .attr('width', 18).attr('height', 18)
                        .attr('x', -9).attr('y', -9)
                        .attr('transform', 'rotate(45)')
                        .style('fill', color);
                } else {
                    sel.append('circle')
                        .attr('class', 'node-shape node-source')
                        .attr('r', 10)
                        .style('fill', color);
                }

                /* collapse indicator — always in DOM, shown/hidden via merge below */
                sel.append('text')
                    .attr('class', 'collapse-indicator')
                    .attr('dy', '0.35em')
                    .attr('text-anchor', 'middle')
                    .style('pointer-events', 'none')
                    .text('+');
            });

            /* label */
            nodeEnter.append('text')
                .attr('class', 'node-label')
                .attr('dy', '0.35em')
                .attr('x', d => (d.children || d._children) ? -16 : 16)
                .attr('y', d => (d.children || d._children) && d.depth !== 0 ? -16 : 0)
                .attr('text-anchor', d => (d.children || d._children) ? 'end' : 'start')
                .text(d => d.data.name || '');

            /* --- merge enter + existing: update collapse indicator visibility --- */
            const nodeAll = nodeEnter.merge(node);

            /* '+' visible only when node IS collapsed (_children set, children null) */
            nodeAll.select('.collapse-indicator')
                .style('display', d => d._children ? null : 'none');

            /* --- transitions --- */
            nodeEnter.transition().duration(400)
                .attr('transform', d => 'translate(' + d.x + ',' + d.y + ')')
                .style('opacity', 1);

            node.transition().duration(400)
                .attr('transform', d => 'translate(' + d.x + ',' + d.y + ')')
                .style('opacity', 1);

            node.exit().transition().duration(400)
                .attr('transform', () => 'translate(' + source.x + ',' + source.y + ')')
                .style('opacity', 0)
                .remove();

            /* ---- LINKS ---- */
            const link = g.selectAll('path.link')
                .data(links, d => d.target.id);

            link.enter().insert('path', 'g')
                .attr('class', 'link')
                .attr('d', () => {
                    const o = { x: source.x0, y: source.y0 };
                    return diagonal({ source: o, target: o });
                })
                .style('opacity', 0)
                .transition().duration(400)
                .attr('d', diagonal)
                .style('opacity', 1);

            link.transition().duration(400).attr('d', diagonal);

            link.exit().transition().duration(400)
                .attr('d', () => {
                    const o = { x: source.x, y: source.y };
                    return diagonal({ source: o, target: o });
                })
                .style('opacity', 0)
                .remove();

            nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
        }

        function diagonal(d) {
            return 'M '  + d.source.x + ' ' + d.source.y
                + ' C ' + d.source.x + ' ' + (d.source.y + d.target.y) / 2
                + ', '  + d.target.x + ' ' + (d.source.y + d.target.y) / 2
                + ', '  + d.target.x + ' ' + d.target.y;
        }

        function fitTree(duration) {
            const allNodes = root.descendants();
            if (!allNodes.length) return;

                  xs = allNodes.map(d => d.x),
                  ys = allNodes.map(d => d.y),
                  x0 = Math.min(...xs), x1 = Math.max(...xs),
                  y0 = Math.min(...ys), y1 = Math.max(...ys),
                  pad = 48,
                  treeW = (x1 - x0) || 1,
                  treeH = (y1 - y0) || 1,
                  scale = Math.min(
                (totalW - pad * 2) / treeW,
                (totalH - pad * 2) / treeH,
                2
            );

            const tx = (totalW - treeW * scale) / 2 - x0 * scale,
                  ty = pad - y0 * scale;

            svgRoot.transition().duration(duration === undefined ? 500 : duration)
                .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
        }

        function exportSVG() {
            const allNodes = root.descendants();
            if (!allNodes.length) return;

            /* compute bounding box of the laid-out tree */
            const xs = allNodes.map(d => d.x),
                  ys = allNodes.map(d => d.y),
                  pad = 48,
                  x0 = Math.min(...xs) - pad,
                  y0 = Math.min(...ys) - pad,
                  vw = Math.max(...xs) - Math.min(...xs) + pad * 2,
                  vh = Math.max(...ys) - Math.min(...ys) + pad * 2;

            /* clone the SVG */
            const original = document.getElementById('plan-svg'),
                  clone = original.cloneNode(true);

            /* set explicit size and viewBox; remove zoom transform from the group */
            clone.setAttribute('width',   vw);
            clone.setAttribute('height',  vh);
            clone.setAttribute('viewBox', x0 + ' ' + y0 + ' ' + vw + ' ' + vh);
            const grp = clone.querySelector('.tree-group');
            if (grp) grp.removeAttribute('transform');

            /* inline computed styles for every element that needs them */
            const INLINE_PROPS = [
                'fill', 'stroke', 'stroke-width', 'stroke-linecap',
                'font-size', 'font-family', 'font-weight', 'text-anchor',
                'display', 'opacity'
            ];

            const srcEls  = original.querySelectorAll('path, circle, rect, text, g'),
                  destEls = clone.querySelectorAll('path, circle, rect, text, g');

            srcEls.forEach(function (src, i) {
                const computed = window.getComputedStyle(src),
                      dest = destEls[i];
                if (!dest) return;
                INLINE_PROPS.forEach(function (prop) {
                    const val = computed.getPropertyValue(prop);
                    if (val && val !== '') dest.style[prop] = val;
                });
            });

            /* serialise and download */
            const blob = new Blob(
                ['<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone)],
                { type: 'image/svg+xml;charset=utf-8' }
            );
            const url = URL.createObjectURL(blob);
            const a   = Object.assign(document.createElement('a'),
                { href: url, download: 'query-plan.svg' });
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function buildToolbar(zoom, svgRoot, totalW, totalH) {
            const toolbar = document.getElementById('canvas-toolbar');
            toolbar.style.display = 'flex';
            toolbar.innerHTML = '';

            const buttons = [
                {
                    title: 'Zoom in',
                    svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/><line x1="16.5" y1="16.5" x2="21" y2="21"/></svg>',
                    action: () => svgRoot.transition().duration(300).call(zoom.scaleBy, 1.4)
                },
                {
                    title: 'Zoom out',
                    svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="8" y1="11" x2="14" y2="11"/><line x1="16.5" y1="16.5" x2="21" y2="21"/></svg>',
                    action: () => svgRoot.transition().duration(300).call(zoom.scaleBy, 1 / 1.4)
                },
                { separator: true },
                {
                    title: 'Fit to screen',
                    svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
                    action: () => fitTree(400)
                },
                {
                    title: '1:1 zoom, centred',
                    svg: '<svg viewBox="0 0 24 24" fill="none" stroke="none"><text x="12" y="16" font-size="9.5" font-family="monospace" font-weight="bold" fill="currentColor" text-anchor="middle">1:1</text></svg>',
                    action: () => {
                        const allNodes = root.descendants(),
                              xs = allNodes.map(d => d.x),
                              ys = allNodes.map(d => d.y),
                              cx = (Math.min(...xs) + Math.max(...xs)) / 2,
                              cy = (Math.min(...ys) + Math.max(...ys)) / 2,
                              tx = totalW / 2 - cx,
                              ty = totalH / 2 - cy;
                        svgRoot.transition().duration(400)
                            .call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(1));
                    }
                },
                { separator: true },
                {
                    title: 'Export SVG',
                    svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
                    action: exportSVG
                }
            ];

            buttons.forEach(function (b) {
                if (b.separator) {
                    const sep = document.createElement('div');
                    sep.className = 'toolbar-sep';
                    toolbar.appendChild(sep);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'toolbar-btn';
                btn.title     = b.title;
                btn.innerHTML = b.svg;
                btn.addEventListener('click', b.action);
                toolbar.appendChild(btn);
            });
        }
    }

    function buildLegend(endpoints_list) {
        const wrap    = document.createElement('div');
        wrap.id       = 'endpoint-legend';
        const heading = document.createElement('h3');
        heading.textContent = 'Endpoints';
        wrap.appendChild(heading);
        endpoints_list.forEach(function (ep, i) {
            const row    = document.createElement('div');
            row.className = 'legend-row';
            const swatch = document.createElement('span');
            swatch.className        = 'legend-swatch';
            swatch.style.background = COLORS[i % COLORS.length];
            const label  = document.createElement('code');
            label.textContent = ep;
            row.appendChild(swatch);
            row.appendChild(label);
            wrap.appendChild(row);
        });
        return wrap;
    }

    function endpointColor(ep, list) {
        const idx = list.indexOf(ep);
        return idx >= 0 ? COLORS[idx % COLORS.length] : '#ccc';
    }

}); // end DOMContentLoaded
