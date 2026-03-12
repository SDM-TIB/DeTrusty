document.addEventListener('DOMContentLoaded', function () {
    const yasguiEl = document.getElementById('yasgui'),
          federationSelect = document.getElementById('federation-select'),
          BASE_ENDPOINT = yasguiEl.dataset.endpoint;

    // -------------------------------------------------------------------------
    // Network-level federation injection
    //
    // YASGUI builds and fires its XHR internally, bypassing any public API we
    // can wrap.  The only reliable injection point is XMLHttpRequest.prototype.open.
    // We intercept every request whose URL starts with our SPARQL endpoint and
    // append the current federation value as a query parameter if one is selected.
    // -------------------------------------------------------------------------
    (function () {
        let _open = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function (method, url) {
            if (typeof url === 'string' && url.indexOf(BASE_ENDPOINT) !== -1) {
                let federation = federationSelect ? federationSelect.value : '';
                if (federation) {
                    let sep = url.indexOf('?') === -1 ? '?' : '&';
                    url = url + sep + 'federation=' + encodeURIComponent(federation);
                }
            }
            return _open.apply(this, [method, url].concat(Array.prototype.slice.call(arguments, 2)));
        };
    })();

    // Populate the federation dropdown from the backend.
    fetch(yasguiEl.dataset.federationsEndpoint)
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
        .catch(function (err) {
            console.warn('Could not load federation list:', err);
        });

    const yasgui = new Yasgui(yasguiEl, {
        persistenceId: null,
        yasqe: {
            tabSize: 2,
            indentUnit: 2,
            value: "SELECT DISTINCT ?concept\nWHERE {\n\t?s a ?concept\n} LIMIT 10"
        },
        extraKeys: {
            Tab: function (cm) {
                var spaces = new Array(cm.getOption("indentUnit") + 1).join(" ");
                cm.replaceSelection(spaces);
            }
        },
        requestConfig: {
            endpoint: BASE_ENDPOINT,
            method: 'POST',
            args: [{name: 'yasqe', value: true}]
        }
    });

    function renderYasrError(tab, message) {
        let existing = tab.yasr.rootEl.querySelector('.yasr-error');
        if (existing) existing.remove();

        let alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger yasr-error';
        alertEl.textContent = message;

        tab.yasr.rootEl.appendChild(alertEl);
        tab.yasr.rootEl.classList.add('yasr-has-error');

        // Switch to response view
        let responseBtn = tab.yasr.rootEl.querySelector('.select_response');
        if (responseBtn) responseBtn.click();

        // Disable table and response buttons
        ['.select_table', '.select_response'].forEach(function (sel) {
            let btn = tab.yasr.rootEl.querySelector(sel);
            if (btn) {
                btn.disabled = true;
                btn.classList.add('disabled');
            }
        });
    }

    function clearYasrError(tab) {
        let existing = tab.yasr.rootEl.querySelector('.yasr-error');
        if (existing) existing.remove();
        tab.yasr.rootEl.classList.remove('yasr-has-error');

        // Re-enable table and response buttons
        ['.select_table', '.select_response'].forEach(function (sel) {
            let btn = tab.yasr.rootEl.querySelector(sel);
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('disabled');
            }
        });

        // Switch to table view
        let tableBtn = tab.yasr.rootEl.querySelector('.select_table');
        if (tableBtn) tableBtn.click();
    }

    function attachQueryResponseHook(tab) {
        tab.yasqe.on('queryResponse', function (yasqe, req, duration) {
            clearYasrError(tab);
            try {
                let body = JSON.parse(req.text);
                if (body.error) {
                    renderYasrError(tab, body.error);
                }
            } catch (e) {
                // Not JSON or not parseable — let YASGUI handle it normally
            }
        });
    }

    attachQueryResponseHook(yasgui.getTab());

    yasgui.on('tabAdd', function (yasgui, tabId) {
        setTimeout(function () {
            let newTab = yasgui.getTab(tabId);
            if (newTab) attachQueryResponseHook(newTab);
        }, 0);
    });

}); // end DOMContentLoaded
