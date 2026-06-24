// wizard.js — interactive helpers for the generator wizard.
//
// Two behaviours wired via data-attributes:
//
// 1. Auto-clamp of interdependent numeric fields.
//    <input data-clamp
//           data-clamp-min-from="other_field_id"   (optional)
//           data-clamp-max-from="other_field_id"   (optional)>
//    Plus any regular min/max HTML attributes, which are respected too.
//
// 2. Auto-normalise probability groups so their sum stays at 1.
//    <div data-prob-group="badge_element_id"
//         data-prob-fields="id1 id2 id3 id4">
//    When the user edits one of the fields, the rest are rescaled
//    proportionally so the total is 1. The badge is updated.

(function () {
    "use strict";

    function toNum(v, fallback) {
        const n = parseFloat(v);
        return Number.isFinite(n) ? n : (fallback !== undefined ? fallback : NaN);
    }

    function getEl(id) {
        return id ? document.getElementById(id) : null;
    }

    function getNum(id, fallback) {
        return toNum(getEl(id)?.value, fallback);
    }

    // ─── Clamping ─────────────────────────────────────────────────────────
    function applyClamp(el) {
        let v = toNum(el.value);
        if (!Number.isFinite(v)) return;
        const hardMin = toNum(el.getAttribute("min"), -Infinity);
        const hardMax = toNum(el.getAttribute("max"), Infinity);
        const minFromId = el.dataset.clampMinFrom;
        const maxFromId = el.dataset.clampMaxFrom;
        const minFrom = minFromId ? getNum(minFromId, -Infinity) : -Infinity;
        const maxFrom = maxFromId ? getNum(maxFromId, Infinity) : Infinity;
        const lo = Math.max(hardMin, minFrom);
        const hi = Math.min(hardMax, maxFrom);
        let clamped = v;
        if (v < lo) clamped = lo;
        else if (v > hi) clamped = hi;
        if (clamped !== v) {
            el.value = Number.isInteger(clamped) ? String(clamped) : clamped.toFixed(4);
        }
    }

    function bindClamps() {
        const fields = document.querySelectorAll("[data-clamp]");
        fields.forEach((el) => {
            el.addEventListener("input", () => applyClamp(el));
            el.addEventListener("change", () => applyClamp(el));
        });

        // When an anchor changes, re-clamp any field that depends on it.
        const anchors = new Set();
        fields.forEach((el) => {
            if (el.dataset.clampMinFrom) anchors.add(el.dataset.clampMinFrom);
            if (el.dataset.clampMaxFrom) anchors.add(el.dataset.clampMaxFrom);
        });
        anchors.forEach((id) => {
            const anchor = getEl(id);
            if (!anchor) return;
            const dependents = document.querySelectorAll(
                `[data-clamp-min-from="${id}"], [data-clamp-max-from="${id}"]`
            );
            anchor.addEventListener("input", () => dependents.forEach(applyClamp));
            anchor.addEventListener("change", () => dependents.forEach(applyClamp));
        });
    }

    // ─── Probability groups ───────────────────────────────────────────────
    function paintBadge(badge, sum) {
        if (!badge) return;
        badge.innerText = sum.toFixed(4);
        badge.classList.remove("badge-light-success", "badge-light-danger");
        badge.classList.add(
            Math.abs(sum - 1.0) < 0.001 ? "badge-light-success" : "badge-light-danger"
        );
    }

    function rescaleGroup(fieldIds, editedId) {
        const edited = getEl(editedId);
        if (!edited) return;
        let v = toNum(edited.value, 0);
        if (v < 0) v = 0;
        if (v > 1) v = 1;
        edited.value = v.toFixed(2);
        const others = fieldIds
            .filter((id) => id !== editedId)
            .map(getEl)
            .filter(Boolean);
        if (others.length === 0) return;
        const remaining = 1 - v;
        const currentSum = others.reduce((s, el) => s + toNum(el.value, 0), 0);
        if (currentSum <= 0.0001) {
            const share = remaining / others.length;
            others.forEach((el) => {
                el.value = share.toFixed(4);
            });
        } else {
            const factor = remaining / currentSum;
            others.forEach((el) => {
                el.value = (toNum(el.value, 0) * factor).toFixed(4);
            });
        }
    }

    function bindProbGroups() {
        document.querySelectorAll("[data-prob-group]").forEach((group) => {
            const badge = getEl(group.dataset.probGroup);
            const fieldIds = (group.dataset.probFields || "")
                .split(/\s+/)
                .filter(Boolean);

            function update(editedId) {
                if (editedId) rescaleGroup(fieldIds, editedId);
                const sum = fieldIds.reduce(
                    (s, id) => s + toNum(getEl(id)?.value, 0),
                    0
                );
                paintBadge(badge, sum);
            }

            fieldIds.forEach((id) => {
                const el = getEl(id);
                if (!el) return;
                el.addEventListener("input", () => update(id));
                el.addEventListener("change", () => update(id));
            });

            update(null);
        });
    }

    // ─── Slider value badges + dynamic bounds ─────────────────────────────
    function updateSliderBounds(el) {
        const hardMin = toNum(el.dataset.sliderHardMin, toNum(el.getAttribute("min"), -Infinity));
        const hardMax = toNum(el.dataset.sliderHardMax, toNum(el.getAttribute("max"), Infinity));
        const anchorMin = el.dataset.clampMinFrom ? getNum(el.dataset.clampMinFrom) : NaN;
        const anchorMax = el.dataset.clampMaxFrom ? getNum(el.dataset.clampMaxFrom) : NaN;
        const effMin = Math.max(hardMin, Number.isFinite(anchorMin) ? anchorMin : -Infinity);
        const effMax = Math.min(hardMax, Number.isFinite(anchorMax) ? anchorMax : Infinity);
        if (Number.isFinite(effMin)) el.setAttribute("min", String(effMin));
        if (Number.isFinite(effMax)) el.setAttribute("max", String(effMax));
        const minLbl = getEl(el.dataset.sliderMinLabel);
        const maxLbl = getEl(el.dataset.sliderMaxLabel);
        if (minLbl && Number.isFinite(effMin)) minLbl.textContent = effMin;
        if (maxLbl && Number.isFinite(effMax)) maxLbl.textContent = effMax;
    }

    function bindSliderDisplays() {
        const sliders = document.querySelectorAll("[data-slider-display]");
        sliders.forEach((el) => {
            const badge = getEl(el.dataset.sliderDisplay);
            const sync = () => {
                if (badge) badge.textContent = el.value;
            };
            el.addEventListener("input", sync);
            el.addEventListener("change", sync);
            updateSliderBounds(el);
            sync();
        });

        // When a source changes (e.g. num_features_max), refresh bounds of any
        // slider that depends on it.
        const anchors = new Set();
        sliders.forEach((el) => {
            if (el.dataset.clampMinFrom) anchors.add(el.dataset.clampMinFrom);
            if (el.dataset.clampMaxFrom) anchors.add(el.dataset.clampMaxFrom);
        });
        anchors.forEach((id) => {
            const anchor = getEl(id);
            if (!anchor) return;
            const refresh = () => {
                document.querySelectorAll(
                    `[data-slider-display][data-clamp-min-from="${id}"], [data-slider-display][data-clamp-max-from="${id}"]`
                ).forEach((slider) => {
                    updateSliderBounds(slider);
                    const badge = getEl(slider.dataset.sliderDisplay);
                    if (badge) badge.textContent = slider.value;
                });
            };
            anchor.addEventListener("input", refresh);
            anchor.addEventListener("change", refresh);
        });
    }

    function init() {
        bindClamps();
        bindProbGroups();
        bindSliderDisplays();
    }

    window.wizardInit = init;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
