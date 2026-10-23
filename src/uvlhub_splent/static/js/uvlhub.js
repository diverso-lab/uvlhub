/* uvlhub's shell script, loaded right after AdminKit's app.js, at the end of
 * the page (so what it reads is already parsed).
 *
 * - The chrome's icons. The features' slot markup in the sidebar and the
 *   header names feather icons; the chrome draws those it has a duotone
 *   icon for with it, from the table the page carries (#uvl-chrome-icons,
 *   built by _uvl_icons.html). It runs before feather replaces the
 *   placeholders on DOMContentLoaded, so feather only draws what is left.
 * - feather stops at the first name it does not know and leaves every
 *   icon after it undrawn, the page's and the footer's. A name it lacks is
 *   drawn as its circle instead, and the console says which it was.
 * - The sidebar. On a desktop it folds to a rail and unfolds over the page
 *   while the pointer is on it; the choice is kept for the next page in
 *   localStorage (a browser that refuses it just forgets). On a phone it is
 *   a drawer over the page, closed by its overlay, Escape or a link, and so
 *   is the header's menu (the search), from the right. While a drawer is
 *   open the rest of the page is inert, so the keyboard stays in it.
 * - The mode. The Mode menu of the header sets Light, Dark or System;
 *   data-bs-theme on <html> carries the one drawn (System follows the
 *   device, also when it changes), and localStorage keeps the choice for
 *   the next page, read by the script at the top of the page.
 * - Which hand moves the focus. A browser marks every focused text field
 *   :focus-visible, mouse or keyboard; <html data-uvl-input> says which, so
 *   the skin rings a field only when the keyboard reached it.
 * - The header's menus open right under it, and the account menu and the
 *   menus features put among the header's buttons open on hover from a
 *   desktop, as uvlhub.io's do; a click on an open one leaves it open.
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
    const HEADER_DRAWER_OPEN = 'uvl-header-drawer-open';
    const STORE_KEY = 'uvl-sidebar-minimized';
    const THEME_KEY = 'uvl-theme';
    const PREFERS_DARK = window.matchMedia('(prefers-color-scheme: dark)');

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

    function unknownFeatherIcons() {
        if (!window.feather || !window.feather.icons) return;
        document.querySelectorAll('[data-feather]').forEach((placeholder) => {
            const name = placeholder.dataset.feather;
            if (window.feather.icons[name]) return;
            console.warn(`feather has no icon "${name}"; drawn as a circle.`);
            placeholder.dataset.feather = 'circle';
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
    }

    // ── The drawers of a phone: the sidebar, and the header's menu ──────

    function drawers() {
        const body = document.body;
        const overlay = document.querySelector('[data-uvl-drawer-close]');
        const all = [
            {
                panel: document.getElementById('sidebar'),
                button: document.querySelector('[data-uvl-drawer-toggle]'),
                open: DRAWER_OPEN,
            },
            {
                panel: document.getElementById('uvl-header-menu'),
                button: document.querySelector('[data-uvl-header-drawer-toggle]'),
                open: HEADER_DRAWER_OPEN,
            },
        ].filter((drawer) => drawer.panel && drawer.button);
        if (!all.length) return;

        // What a drawer covers: the frame's parts that neither hold it nor
        // are inside it.
        const covered = (panel) => [...document.querySelectorAll(
            '.uvl-skip-link, .uvl-sidebar, .uvl-header > *, .uvl-toolbar, .uvl-content, .uvl-footer')]
            .filter((part) => !part.contains(panel) && !panel.contains(part));

        const setDrawer = (drawer, open) => {
            if (open) all.filter((other) => other !== drawer).forEach((other) => setDrawer(other, false));
            const wasOpen = body.classList.contains(drawer.open);
            body.classList.toggle(drawer.open, open);
            drawer.button.setAttribute('aria-expanded', String(open));
            covered(drawer.panel).forEach((part) => { part.inert = open; });
            if (overlay) overlay.hidden = !all.some((one) => body.classList.contains(one.open));
            if (open) {
                // The drawer itself takes the focus, so the keyboard starts
                // in it without a ring on its first entry.
                drawer.panel.setAttribute('tabindex', '-1');
                drawer.panel.focus({ preventScroll: true });
            } else if (wasOpen && drawer.panel.contains(document.activeElement)) {
                drawer.button.focus({ preventScroll: true });
            }
        };
        const openOne = () => all.find((drawer) => body.classList.contains(drawer.open));

        all.forEach((drawer) => {
            drawer.button.addEventListener('click', () => setDrawer(drawer, !body.classList.contains(drawer.open)));
            drawer.panel.addEventListener('click', (event) => {
                if (event.target.closest('a[href]') && body.classList.contains(drawer.open)) setDrawer(drawer, false);
            });
        });
        if (overlay) overlay.addEventListener('click', () => all.forEach((drawer) => setDrawer(drawer, false)));
        document.addEventListener('keydown', (event) => {
            const drawer = openOne();
            // A menu open inside the drawer takes its own Escape first.
            if (event.key === 'Escape' && drawer && !drawer.panel.querySelector('.dropdown-menu.show')) setDrawer(drawer, false);
        });
        // A phone turned into a wide screen has no drawer to keep open.
        DESKTOP.addEventListener('change', (event) => {
            if (event.matches) all.forEach((drawer) => setDrawer(drawer, false));
        });
    }

    // ── The mode ────────────────────────────────────────────────────────

    function themeMode() {
        const items = document.querySelectorAll('[data-uvl-theme]');
        let chosen = 'light';
        try {
            chosen = window.localStorage.getItem(THEME_KEY) || 'light';
        } catch (error) {
            // Storage blocked: light, as the page was drawn.
        }
        const apply = () => {
            const dark = chosen === 'dark' || (chosen === 'system' && PREFERS_DARK.matches);
            document.documentElement.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
            items.forEach((item) => {
                const on = item.dataset.uvlTheme === chosen;
                item.classList.toggle('active', on);
                item.setAttribute('aria-pressed', String(on));
            });
        };
        items.forEach((item) => item.addEventListener('click', () => {
            chosen = item.dataset.uvlTheme;
            try {
                window.localStorage.setItem(THEME_KEY, chosen);
            } catch (error) {
                // The choice lasts for this page.
            }
            apply();
        }));
        PREFERS_DARK.addEventListener('change', () => {
            if (chosen === 'system') apply();
        });
        apply();
    }

    // ── Which hand moves the focus ──────────────────────────────────────

    function inputModality() {
        const root = document.documentElement;
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab' || event.key.startsWith('Arrow')) root.dataset.uvlInput = 'keyboard';
        }, true);
        document.addEventListener('pointerdown', () => {
            root.dataset.uvlInput = 'pointer';
        }, true);
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
                const focused = document.activeElement === toggle;
                dropdown().show();
                // Bootstrap focuses the toggle as it opens the menu, and the
                // browser rings it as if the keyboard had: not for a pointer.
                if (!focused) toggle.blur();
            });
            holder.addEventListener('mouseleave', () => {
                if (!DESKTOP.matches) return;
                clearTimeout(timer);
                timer = setTimeout(() => dropdown().hide(), 200);
            });
        });
        // The pointer opened the menu on its way to the button, so a click
        // there finds it open: Bootstrap would toggle it shut, and nothing
        // reopens it while the pointer stays. On uvlhub.io the click leaves
        // it open. Bootstrap listens on the document while the click goes
        // down, so this listens on the window, before it. A click from the
        // keyboard (Enter or Space, detail 0) still toggles the menu.
        window.addEventListener('click', (event) => {
            if (!DESKTOP.matches || event.detail === 0 || !(event.target instanceof Element)) return;
            const toggle = event.target.closest('[data-bs-toggle="dropdown"]');
            if (!toggle || !toggles.has(toggle) || !toggle.classList.contains('show')) return;
            event.preventDefault();
            event.stopPropagation();
        }, true);
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
    unknownFeatherIcons();
    sidebar();
    drawers();
    themeMode();
    inputModality();
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
