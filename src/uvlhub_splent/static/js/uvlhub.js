/* uvlhub's shell script, loaded right after AdminKit's app.js.
 *
 * - Bootstrap starts no tooltip or popover by itself, and AdminKit does not
 *   either, while the previous shell's script did. Every element that asks
 *   for one with data-bs-toggle gets it once the page is parsed. Content a
 *   feature draws later starts its own.
 * - The Copy buttons of the citation dialog (cites.html) copy the box their
 *   data-citation-copy names, and say so for a moment. One listener on the
 *   document, so the buttons need no inline handler.
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.bootstrap) return;
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
            bootstrap.Tooltip.getOrCreateInstance(element);
        });
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach((element) => {
            bootstrap.Popover.getOrCreateInstance(element);
        });
    });

    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-citation-copy]');
        // A second click while it says "Copied!" would keep that as its label.
        if (!button || button.dataset.copied) return;
        const source = document.getElementById(button.dataset.citationCopy);
        if (!source || !navigator.clipboard) return;
        navigator.clipboard.writeText(source.textContent.trim()).then(() => {
            const label = button.textContent;
            button.dataset.copied = 'true';
            button.textContent = button.dataset.copiedLabel || 'Copied!';
            setTimeout(() => {
                button.textContent = label;
                delete button.dataset.copied;
            }, 1500);
        }).catch((error) => {
            console.error('The citation could not be copied:', error);
        });
    });
})();
