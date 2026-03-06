document.addEventListener('DOMContentLoaded', function () {
    const yasgui = new Yasgui(document.getElementById("yasgui"), {
        persistenceId: null,
        yasqe: {
            // modify codemirror tab handling to solely use 2 spaces
            tabSize: 2,
            indentUnit: 2,
            // set default query
            value: "SELECT DISTINCT ?concept\nWHERE {\n\t?s a ?concept\n} LIMIT 10"
        },
        extraKeys: {
            Tab: function (cm) {
                var spaces = new Array(cm.getOption("indentUnit") + 1).join(" ");
                cm.replaceSelection(spaces);
            }
        },
        requestConfig: {
            // configuring the endpoint for DeTrusty
            endpoint: document.getElementById('yasgui').dataset.endpoint,
            method: 'POST',
            args: [{name: "yasqe", value: true}]
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

    let tab = yasgui.getTab();
    attachQueryResponseHook(tab);

    yasgui.on('tabAdd', function (yasgui, tabId) {
        setTimeout(function () {
            let newTab = yasgui.getTab(tabId);
            if (newTab) {
                attachQueryResponseHook(newTab);
            }
        }, 0);
    });
}); // end DOMContentLoaded
