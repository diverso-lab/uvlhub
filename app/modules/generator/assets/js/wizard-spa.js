// wizard-spa.js — in-place navigation for the generator wizard so that the
// Pyodide runtime (expensive to load) is initialised ONCE per tab and survives
// every step transition.
//
// Strategy: intercept the form submit, POST via fetch, swap only the stepper
// subtree (#stepper_generator) with the one coming from the server response.
// The runtime bundle lives in {% block scripts %}, outside that subtree, so it
// keeps executing and window.__generatorRuntime is preserved.

(function () {
    "use strict";

    const ROOT_SELECTOR = "#stepper_generator";

    function reinit(root) {
        // Re-run any inline <script> that just got injected into the DOM.
        root.querySelectorAll("script").forEach((old) => {
            const replacement = document.createElement("script");
            for (const attr of old.attributes) {
                replacement.setAttribute(attr.name, attr.value);
            }
            replacement.text = old.textContent;
            old.replaceWith(replacement);
        });

        // Re-init Metronic tooltips / menus inside the new content.
        if (window.KTApp && typeof window.KTApp.init === "function") {
            try { window.KTApp.init(); } catch (e) { /* noop */ }
        }

        // Re-init wizard helpers (clamp, probability groups).
        if (typeof window.wizardInit === "function") {
            window.wizardInit();
        }

        window.scrollTo({ top: 0, behavior: "instant" });
    }

    async function handleSubmit(event) {
        const form = event.target;
        if (!form || form.tagName !== "FORM") return;
        const root = document.querySelector(ROOT_SELECTOR);
        if (!root || !root.contains(form)) return;

        event.preventDefault();

        // Let any form-local pre-submit hooks (e.g. the relation-distribution
        // normaliser) rewrite hidden inputs BEFORE we snapshot the form data.
        form.dispatchEvent(new CustomEvent("wizard:pre-submit"));

        const submitter = event.submitter;
        const formData = new FormData(form);
        if (submitter && submitter.name) {
            formData.set(submitter.name, submitter.value);
        }

        // UI feedback
        const buttons = form.querySelectorAll("button[type=submit]");
        buttons.forEach((b) => { b.disabled = true; });

        let response;
        try {
            response = await fetch(form.action, {
                method: (form.method || "POST").toUpperCase(),
                body: formData,
                headers: { "X-Requested-With": "fetch" },
                credentials: "same-origin",
            });
        } catch (err) {
            console.error("Wizard SPA fetch failed, falling back to full reload:", err);
            form.removeEventListener("submit", handleSubmit);
            form.submit();
            return;
        } finally {
            buttons.forEach((b) => { b.disabled = false; });
        }

        if (!response.ok && response.status >= 500) {
            console.error("Wizard server error", response.status);
            window.location.href = response.url || form.action;
            return;
        }

        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        const incoming = doc.querySelector(ROOT_SELECTOR);
        if (!incoming) {
            window.location.href = response.url || form.action;
            return;
        }

        root.replaceWith(incoming);
        if (response.url && response.url !== window.location.href) {
            history.pushState({}, "", response.url);
        }

        reinit(incoming);
        window.dispatchEvent(new CustomEvent("wizard:swapped", { detail: { root: incoming } }));
    }

    function bind() {
        document.addEventListener("submit", handleSubmit, { capture: true });
        window.addEventListener("popstate", () => {
            // Pop means user clicked browser back — just reload that URL in place.
            fetch(window.location.href, {
                headers: { "X-Requested-With": "fetch" },
                credentials: "same-origin",
            })
                .then((r) => r.text())
                .then((html) => {
                    const doc = new DOMParser().parseFromString(html, "text/html");
                    const incoming = doc.querySelector(ROOT_SELECTOR);
                    const root = document.querySelector(ROOT_SELECTOR);
                    if (incoming && root) {
                        root.replaceWith(incoming);
                        reinit(incoming);
                    } else {
                        window.location.reload();
                    }
                });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bind);
    } else {
        bind();
    }
})();
