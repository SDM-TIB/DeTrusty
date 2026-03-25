// detrusty-autocompleters.js
//
// Registers federation-aware class, property, and prefix autocompleters for YASGUI/YASQE.
// Must be loaded *before* any page-specific script that instantiates Yasgui or Yasqe.
//
// The active federation is read lazily inside each callback (at the moment the
// user triggers autocomplete) so this module works on both the query editor page,
// which stores the value in a <select id="federation-select">, and any other page
// that follows the same convention.

(function () {
    // Returns the currently selected federation URI, or an empty string when none
    // is selected or the selector element is absent.
    function currentFederation() {
        let sel = document.getElementById('federation-select');
        return (sel && sel.value) ? sel.value : '';
    }

    // Builds a URL for the given metadata path, appending ?federation=... only
    // when a federation is actually selected.
    function metadataUrl(path) {
        let fed = currentFederation();
        let params = new URLSearchParams();
        if (fed) params.set('federation', fed);
        let qs = params.toString();
        return window.location.origin + path + (qs ? '?' + qs : '');
    }

    // Populated by get() and read by postprocessHints().
    // Kept in the module closure so both callbacks share state without globals.
    let _unknownNamespaceUris = []; // federation URIs not in prefix.cc

    Yasqe.forkAutocompleter('prefixes', {
        name: 'prefixes',
        persistenceId: null,
        get: function (yasqe) {
            let prefixCcUrl = (window.location.protocol.indexOf('http') === 0 ? '//' : 'http://')
                + 'prefix.cc/popular/all.file.json';

            let prefixCcPromise = fetch(prefixCcUrl)
                .then(function (r) { return r.json(); });

            let federationPromise = fetch(metadataUrl('/namespaces'))
                .then(function (r) { return r.json(); })
                .catch(function () { return []; });

            return Promise.all([prefixCcPromise, federationPromise])
                .then(function (results) {
                    let prefixCcData     = results[0]; // { prefix: uri, … }
                    let federationUris   = Array.isArray(results[1]) ? results[1] : [];
                    let federationUriSet = new Set(federationUris);

                    // prefix.cc entries limited to those whose URI appears in the federation.
                    let known = [];
                    let prefixCcUriSet = new Set();
                    for (let prefix in prefixCcData) {
                        let uri = prefixCcData[prefix];
                        prefixCcUriSet.add(uri);
                        if (federationUriSet.has(uri)) {
                            known.push(prefix + ': <' + uri + '>');
                        }
                    }
                    known.sort();

                    // Federation URIs not covered by prefix.cc — stored for postprocessHints.
                    _unknownNamespaceUris = federationUris.filter(function (uri) {
                        return !prefixCcUriSet.has(uri);
                    });

                    // Unnamed suggestions appended after the known ones.
                    let unknown = _unknownNamespaceUris.map(function (uri) {
                        return ': <' + uri + '>';
                    });

                    return known.concat(unknown);
                });
        },

        // The trie uses prefix-based lookup, so ": <uri>" entries only survive when
        // the user has typed nothing or ":".  postprocessHints re-injects them using
        // substring search on the URI itself so they appear for any partial URI match.
        postprocessHints: function (yasqe, hints) {
            hints.sort(function (a, b) {
                return a.text.split(':')[0].localeCompare(b.text.split(':')[0]);
            });

            if (!_unknownNamespaceUris.length) return hints;

            let token = yasqe.getCompleteToken();
            let typed = (token.autocompletionString || token.string || '').toLowerCase().trim();

            // Nothing typed or just ":" — the trie already included all ": <uri>" entries.
            if (!typed || typed === ':') return hints;

            let cursor = yasqe.getDoc().getCursor();
            let from   = { line: cursor.line, ch: token.start };
            let to     = { line: cursor.line, ch: token.end };

            _unknownNamespaceUris.forEach(function (uri) {
                if (uri.toLowerCase().includes(typed)) {
                    hints.push({
                        text:        ': <' + uri + '>',
                        displayText: ': <' + uri + '>',
                        from: from,
                        to:   to,
                    });
                }
            });

            return hints;
        },
    });

    Yasqe.forkAutocompleter('class', {
        name: 'customClassCompleter',
        bulk: true,
        autoShow: true,
        persistenceId: function () { return 'detrustyClasses_' + currentFederation(); },
        get: function () {
            return fetch(metadataUrl('/classes'))
                .then(function (r) { return r.json(); })
                .then(function (data) { return data.classes || []; });
        }
    });

    Yasqe.forkAutocompleter('property', {
        name: 'customPropertyCompleter',
        bulk: true,
        autoShow: true,
        persistenceId: function () { return 'detrustyProperties_' + currentFederation(); },
        get: function () {
            return fetch(metadataUrl('/predicates'))
                .then(function (r) { return r.json(); })
                .then(function (data) { return data.predicates || []; });
        }
    });
}());
