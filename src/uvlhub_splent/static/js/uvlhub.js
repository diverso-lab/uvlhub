/* uvlhub's shell script, loaded right after AdminKit's app.js, at the end of
 * the page (so what it reads is already parsed).
 *
 * - The chrome's icons. The features' slot markup in the sidebar and the
 *   header names feather icons; the chrome draws those it has a duotone
 *   icon for with it, from the table the page carries (#uvl-chrome-icons,
 *   built by _uvl_icons.html). It runs before feather replaces the
 *   placeholders on DOMContentLoaded, so feather only draws what is left.
 * - The sidebar. On a desktop it folds to a rail and unfolds over the page
 *   while the pointer is on it; the choice is kept for the next page in
 *   localStorage (a browser that refuses it just forgets). On a phone it is
 *   a drawer over the page, closed by its overlay, Escape or a link.
 * - The header's menus open right under it, and the account menu and the
 *   menus features put among the header's buttons open on hover from a
 *   desktop, as uvlhub.io's do; a click still works.
 * - Bootstrap starts no tooltip or popover by itself, and AdminKit does not
 *   either. Every element that asks for one with data-bs-toggle gets it
 *   once the page is parsed. Content a feature draws later starts its own.
 * - The Copy buttons of the citation dialog (cites.html) copy the box their
 *   data-citation-copy names, and say so for a moment.
 */
(function () {
    'use strict';

    const SVG = 'http://www.w3.org/2000/svg';
    const DESKTOP = window.matchMedia('(min-width: 992px)');
    const MINIMIZED = 'uvl-sidebar-minimized';
    const DRAWER_OPEN = 'uvl-drawer-open';
    const STORE_KEY = 'uvl-sidebar-minimized';

    // ── The chrome's icons ──────────────────────────────────────────────

    function chromeIcons() {
        const data = document.getElementById('uvl-chrome-icons');
        if (!data) return;
        let table;
        try {
            table = JSON.parse(data.textContent);
        } catch (error) {
            return;
        }
        const swap = (placeholder, inHeader) => {
            const name = placeholder.dataset.feather;
            const icon = (inHeader && table.header[name]) || table.icons[name];
            if (!icon) return;
            const svg = document.createElementNS(SVG, 'svg');
            svg.setAttribute('class', 'uvl-icon');
            svg.setAttribute('aria-hidden', 'true');
            svg.setAttribute('focusable', 'false');
            const use = document.createElementNS(SVG, 'use');
            use.setAttribute('href', `${table.sprite}#ph-${icon}`);
            svg.appendChild(use);
            placeholder.replaceWith(svg);
        };
        document.querySelectorAll('#sidebar .sidebar-link i[data-feather]').forEach((el) => swap(el, false));
        // The header's buttons, not what their menus list.
        document.querySelectorAll('.uvl-header i[data-feather]').forEach((el) => {
            if (!el.closest('.dropdown-menu')) swap(el, true);
        });
    }

    // ── The sidebar ─────────────────────────────────────────────────────

    function remember(minimized) {
        try {
            window.localStorage.setItem(STORE_KEY, minimized ? '1' : '0');
        } catch (error) {
            // Private mode or storage blocked: the fold lasts for this page.
        }
    }

    function sidebar() {
        const body = document.body;
        const aside = document.getElementById('sidebar');
        const toggle = document.querySelector('[data-uvl-sidebar-toggle]');
        const burger = document.querySelector('[data-uvl-drawer-toggle]');
        const overlay = document.querySelector('[data-uvl-drawer-close]');
        if (!aside) return;

        const pressed = () => toggle && toggle.setAttribute('aria-pressed', String(body.classList.contains(MINIMIZED)));
        pressed();

        if (toggle) {
            toggle.addEventListener('click', () => {
                const minimized = body.classList.toggle(MINIMIZED);
                // The pointer is on the sidebar right after a click: it stays
                // folded until the pointer leaves and comes back.
                if (minimized && aside.matches(':hover')) aside.classList.add('uvl-sidebar-resting');
                remember(minimized);
                pressed();
            });
            aside.addEventListener('mouseleave', () => aside.classList.remove('uvl-sidebar-resting'));
        }

        const setDrawer = (open) => {
            body.classList.toggle(DRAWER_OPEN, open);
            if (overlay) overlay.hidden = !open;
            if (burger) burger.setAttribute('aria-expanded', String(open));
            if (open) {
                const first = aside.querySelector('.sidebar-link');
                if (first) first.focus({ preventScroll: true });
            } else if (burger && aside.contains(document.activeElement)) {
                burger.focus({ preventScroll: true });
            }
        };

        if (burger) burger.addEventListener('click', () => setDrawer(!body.classList.contains(DRAWER_OPEN)));
        if (overlay) overlay.addEventListener('click', () => setDrawer(false));
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && body.classList.contains(DRAWER_OPEN)) setDrawer(false);
        });
        aside.addEventListener('click', (event) => {
            if (event.target.closest('a[href]') && body.classList.contains(DRAWER_OPEN)) setDrawer(false);
        });
        // A phone turned into a wide screen has no drawer to keep open.
        DESKTOP.addEventListener('change', (event) => {
            if (event.matches) setDrawer(false);
        });
    }

    // ── Dropdowns that open on hover from a desktop ─────────────────────

    function hoverDropdowns() {
        if (!window.bootstrap || !window.matchMedia('(hover: hover)').matches) return;
        // The account menu, and the menus features put among the header's
        // buttons (Download all), as uvlhub.io opens them.
        const toggles = new Set(document.querySelectorAll(
            '[data-uvl-hover-dropdown], .uvl-header-actions .uvl-header-slot [data-bs-toggle="dropdown"]'));
        toggles.forEach((toggle) => {
            const holder = toggle.closest('.dropdown') || toggle.parentElement;
            let timer = null;
            const dropdown = () => bootstrap.Dropdown.getOrCreateInstance(toggle);
            holder.addEventListener('mouseenter', () => {
                if (!DESKTOP.matches) return;
                clearTimeout(timer);
                dropdown().show();
            });
            holder.addEventListener('mouseleave', () => {
                if (!DESKTOP.matches) return;
                clearTimeout(timer);
                timer = setTimeout(() => dropdown().hide(), 200);
            });
        });
    }

    // ── The header's menus open under the header ──────────────────────

    function headerMenus() {
        const header = document.querySelector('.uvl-header');
        if (!header) return;
        header.querySelectorAll('[data-bs-toggle="dropdown"]').forEach((toggle) => {
            if (toggle.dataset.bsOffset) return;
            const gap = header.getBoundingClientRect().bottom - toggle.getBoundingClientRect().bottom;
            // Read by Bootstrap when the menu is first opened.
            toggle.dataset.bsOffset = `0,${Math.max(2, Math.round(gap))}`;
        });
    }

    chromeIcons();
    sidebar();
    headerMenus();

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.bootstrap) return;
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
            bootstrap.Tooltip.getOrCreateInstance(element);
        });
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach((element) => {
            bootstrap.Popover.getOrCreateInstance(element);
        });
        hoverDropdowns();
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
