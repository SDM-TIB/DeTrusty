document.addEventListener('DOMContentLoaded', function () {
    let bar = document.getElementById('federation-bar');
    if (!bar) return;

    function applyYasguiStyle() {
        // YASGUI's tab bar / control toolbar — try several selectors
        // in order of specificity so we match any YASGUI version.
        let source = document.querySelector('.yasgui .tabBar')
            || document.querySelector('.yasgui .tab')
            || document.querySelector('.yasqe')
            || document.querySelector('.yasgui');
        if (!source) return false;

        let s = window.getComputedStyle(source),
            bg = s.backgroundColor,
            color = s.color,
            border = s.borderBottomColor !== 'rgba(0, 0, 0, 0)'
                ? s.borderBottomColor
                : s.borderColor;

        bar.style.background = bg;
        bar.style.color = color;
        bar.style.borderBottom = '1px solid ' + border;

        let sel = bar.querySelector('select');
        if (sel) {
            sel.style.background = bg;
            sel.style.color = color;
            sel.style.border = '1px solid ' + border;
        }
        return true;
    }

    // Try immediately in case YASGUI rendered synchronously.
    if (!applyYasguiStyle()) {
        // Otherwise observe the DOM until YASGUI's toolbar appears.
        let observer = new MutationObserver(function () {
            if (applyYasguiStyle()) observer.disconnect();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
});
