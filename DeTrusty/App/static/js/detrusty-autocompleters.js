// detrusty-autocompleters.js
//
// Registers federation-aware class and property autocompleters for YASGUI/YASQE.
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
