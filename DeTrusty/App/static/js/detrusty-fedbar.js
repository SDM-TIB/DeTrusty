document.addEventListener('DOMContentLoaded', function () {
    const bar = document.getElementById('federation-bar');
    if (!bar) return;

    const select = document.getElementById('federation-select'),
          selectLabel = document.getElementById('federation-select-label'),
          nameEl = document.getElementById('federation-name');

    function shortName(uri) {
        return uri.split(/[#\/]/).filter(Boolean).pop() || uri;
    }

    fetch(bar.dataset.federationsEndpoint)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            const federations = data.federations || [];
            if (federations.length === 0) return;

            if (federations.length === 1) {
                // Nothing to choose, but users should still see what they query.
                nameEl.textContent = 'Federation: ' + shortName(federations[0]);
                nameEl.title = federations[0];
                nameEl.hidden = false;
            } else {
                federations.forEach(function (uri) {
                    const opt = document.createElement('option');
                    opt.value = uri;
                    opt.textContent = shortName(uri);
                    opt.title = uri;
                    select.appendChild(opt);
                });
                selectLabel.hidden = false;
                select.hidden = false;
            }
            bar.classList.add('is-visible');
        })
        .catch(function (err) {
            console.warn('Could not load federation list:', err);
        });
});
