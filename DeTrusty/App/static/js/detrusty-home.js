document.addEventListener('DOMContentLoaded', function () {
    const status = document.getElementById('home-status'),
          exampleBtn = document.getElementById('btn-example');

    // Show how many federations this instance serves.
    if (status) {
        fetch(status.dataset.federationsEndpoint)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                const n = (data.federations || []).length;
                if (n === 0) return;
                status.textContent = n === 1
                    ? 'This instance serves 1 federation.'
                    : 'This instance serves ' + n + ' federations.';
                status.hidden = false;
            })
            .catch(function () { /* status is optional */ });
    }

    // Hand an example query to the editor (see detrusty-query.js).
    if (exampleBtn) {
        exampleBtn.addEventListener('click', function () {
            try {
                sessionStorage.setItem('detrusty.query',
                    'SELECT DISTINCT ?concept\nWHERE {\n  ?s a ?concept\n} LIMIT 10');
            } catch (e) { /* storage unavailable: the editor opens with its default query */ }
            window.location.href = exampleBtn.dataset.editorUrl;
        });
    }
});
