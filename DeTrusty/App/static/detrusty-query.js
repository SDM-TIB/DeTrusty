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
            endpoint: window.location.href,
            method: 'POST',
            args: [{name: "yasqe", value: true}]
        }
    });
}); // end DOMContentLoaded
