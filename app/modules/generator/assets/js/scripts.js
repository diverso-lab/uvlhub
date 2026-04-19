import JSZip from "jszip";
import { saveAs } from "file-saver";
import noUiSlider from "nouislider";

// Generator runtime: Pyodide + required wheels + fmgen_wrapper.
// Loaded ONCE per tab (cached on window.__generatorRuntime) and reused for every
// generation. Started on import, so by the time the user reaches step 5 it is
// usually ready. A modal gives the user visible feedback about what's happening.

const WHEELS = [
    "afmparser-1.0.3-py3-none-any.whl",
    "antlr4_python3_runtime-4.13.1-py3-none-any.whl",
    "astutils-0.0.6-py3-none-any.whl",
    "blinker-1.9.0-py3-none-any.whl",
    "dd-0.5.7-py3-none-any.whl",
    "flamapy_bdd-2.5.0-py3-none-any.whl",
    "flamapy_configurator-2.0.1-py3-none-any.whl",
    "flamapy_fm-2.5.0-py3-none-any.whl",
    "flamapy_fw-2.5.0-py3-none-any.whl",
    "flamapy_sat-2.5.0-py3-none-any.whl",
    "flamapy-2.5.0-py3-none-any.whl",
    "flask-3.1.0-py3-none-any.whl",
    "fm_generator-0.0.1-py3-none-any.whl",
    "graphviz-0.20-py3-none-any.whl",
    "itsdangerous-2.2.0-py3-none-any.whl",
    "networkx-3.4.2-py3-none-any.whl",
    "ply-3.11-py2.py3-none-any.whl",
    "pydot-4.0.0-py3-none-any.whl",
    "setuptools-80.9.0-py3-none-any.whl",
    "six-1.17.0-py2.py3-none-any.whl",
    "uvlparser-2.0.1-py3-none-any.whl",
    "werkzeug-3.1.3-py3-none-any.whl",
];

// ─── Status modal ──────────────────────────────────────────────────────────

let modalEl = null;
let modalInstance = null;

function ensureModal() {
    if (modalEl) return modalEl;
    modalEl = document.createElement("div");
    modalEl.className = "modal fade";
    modalEl.id = "generatorRuntimeModal";
    modalEl.setAttribute("tabindex", "-1");
    modalEl.setAttribute("aria-hidden", "true");
    modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body text-center py-12 px-10">
                    <div id="genRuntimeIcon" class="mb-6">
                        <div class="spinner-border text-primary" role="status" style="width: 3.5rem; height: 3.5rem;">
                            <span class="visually-hidden">Loading…</span>
                        </div>
                    </div>
                    <h3 id="genRuntimeTitle" class="fw-bold text-gray-900 mb-2">Preparing generator</h3>
                    <div id="genRuntimeMsg" class="text-gray-600 fw-semibold fs-6 mb-6">Warming up the Python runtime…</div>
                    <div class="progress h-8px rounded-pill">
                        <div id="genRuntimeBar" class="progress-bar bg-primary rounded-pill" role="progressbar" style="width: 0%;"></div>
                    </div>
                    <div id="genRuntimeSubtle" class="text-gray-500 fs-7 fw-semibold mt-4">&nbsp;</div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modalEl);
    modalInstance = new window.bootstrap.Modal(modalEl, { backdrop: "static", keyboard: false });
    return modalEl;
}

function setModal({ title, msg, subtle, percent, state }) {
    ensureModal();
    if (title !== undefined) modalEl.querySelector("#genRuntimeTitle").innerText = title;
    if (msg   !== undefined) modalEl.querySelector("#genRuntimeMsg").innerText   = msg;
    if (subtle !== undefined) modalEl.querySelector("#genRuntimeSubtle").innerText = subtle;
    if (percent !== undefined) {
        const bar = modalEl.querySelector("#genRuntimeBar");
        bar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }
    if (state) {
        const icon = modalEl.querySelector("#genRuntimeIcon");
        const bar  = modalEl.querySelector("#genRuntimeBar");
        bar.classList.remove("bg-primary", "bg-success", "bg-danger");
        if (state === "success") {
            bar.classList.add("bg-success");
            icon.innerHTML = `
                <div class="symbol symbol-70px">
                    <span class="symbol-label bg-light-success">
                        <i class="ki-duotone ki-check-circle fs-3x text-success"><span class="path1"></span><span class="path2"></span></i>
                    </span>
                </div>`;
        } else if (state === "error") {
            bar.classList.add("bg-danger");
            icon.innerHTML = `
                <div class="symbol symbol-70px">
                    <span class="symbol-label bg-light-danger">
                        <i class="ki-duotone ki-cross-circle fs-3x text-danger"><span class="path1"></span><span class="path2"></span></i>
                    </span>
                </div>`;
        } else {
            bar.classList.add("bg-primary");
            icon.innerHTML = `
                <div class="spinner-border text-primary" role="status" style="width: 3.5rem; height: 3.5rem;">
                    <span class="visually-hidden">Loading…</span>
                </div>`;
        }
    }
}

function showModal() {
    ensureModal();
    if (!modalEl.classList.contains("show")) modalInstance.show();
}

function hideModal(delay = 900) {
    ensureModal();
    setTimeout(() => modalInstance.hide(), delay);
}

// ─── Runtime boot ──────────────────────────────────────────────────────────

async function bootRuntime() {
    if (typeof window.loadPyodide !== "function") {
        throw new Error("loadPyodide is not available. Make sure pyodide.js is loaded before scripts.js.");
    }

    showModal();
    setModal({ title: "Preparing generator", msg: "Loading Python runtime…", subtle: "Pyodide 0.27", percent: 5 });
    const pyodide = await window.loadPyodide({ indexURL: "/generator/js/pyodide" });

    setModal({ msg: "Preparing package manager…", percent: 10 });
    await pyodide.loadPackage("micropip");
    await pyodide.loadPackage("packaging");

    setModal({ msg: "Installing Python packages…", percent: 15 });
    for (let i = 0; i < WHEELS.length; i++) {
        const wheel = WHEELS[i];
        pyodide.globals.set("wheel_url", `/generator/js/${wheel}`);
        let lastErr = null;
        // One retry — most wheel install failures are transient (flaky network,
        // CDN hiccup). A second attempt recovers without user intervention.
        for (let attempt = 0; attempt < 2; attempt++) {
            try {
                await pyodide.runPythonAsync(`
                    import micropip
                    await micropip.install(wheel_url, deps=False)
                `);
                lastErr = null;
                break;
            } catch (e) {
                lastErr = e;
                console.warn(`Wheel install failed (attempt ${attempt + 1}/2): ${wheel}`, e);
            }
        }
        if (lastErr) {
            throw new Error(`Could not install ${wheel} — ${lastErr.message || lastErr}`);
        }
        const done = i + 1;
        setModal({
            subtle: `${done} / ${WHEELS.length} · ${wheel.replace(/-py3-none-any\.whl$/, "")}`,
            percent: 15 + (done / WHEELS.length) * 70,
        });
    }

    setModal({ msg: "Loading generator wrapper…", subtle: "fmgen_wrapper.py", percent: 90 });
    const wrapperSource = await (await fetch("/generator/js/fmgen_wrapper.py")).text();
    await pyodide.runPythonAsync(wrapperSource);

    setModal({
        title: "Generator ready",
        msg: "You can configure and download your models.",
        subtle: " ",
        percent: 100,
        state: "success",
    });
    hideModal(900);
    return pyodide;
}

// Idempotent global bootstrap. Start as soon as the module is imported in any step.
// A watchdog caps the total bootstrap time so the "Preparing generator" modal
// can't hang indefinitely if a wheel request stalls.
const BOOT_TIMEOUT_MS = 120_000; // 2 minutes
function withBootTimeout(promise) {
    return new Promise((resolve, reject) => {
        const t = setTimeout(
            () => reject(new Error(`Runtime boot timed out after ${BOOT_TIMEOUT_MS / 1000}s`)),
            BOOT_TIMEOUT_MS,
        );
        promise.then(
            (v) => { clearTimeout(t); resolve(v); },
            (e) => { clearTimeout(t); reject(e); },
        );
    });
}

if (!window.__generatorRuntime) {
    window.__generatorRuntime = withBootTimeout(bootRuntime()).catch((err) => {
        console.error("Generator runtime failed:", err);
        setModal({
            title: "Failed to load generator",
            msg: String(err && err.message ? err.message : err),
            subtle: "Reload the page to retry, or check the browser console.",
            state: "error",
            percent: 100,
        });
        throw err;
    });
}

// ─── Public API ────────────────────────────────────────────────────────────

export function getRuntime() {
    return window.__generatorRuntime;
}

export async function generateAndDownload() {
    showModal();
    setModal({ title: "Generating models", msg: "Running the generator…", subtle: " ", percent: 40, state: "loading" });
    const pyodide = await getRuntime();

    const resp = await fetch("/generator/random/params-json");
    if (!resp.ok) throw new Error("Failed to fetch params-json: " + resp.status);
    const paramsObj = await resp.json();

    pyodide.globals.set("params_json", JSON.stringify(paramsObj));
    const uvlsJson = await pyodide.runPythonAsync("generate_models(params_json)");
    const uvls = JSON.parse(uvlsJson);

    setModal({ msg: "Packaging ZIP…", percent: 85 });
    const zip = new JSZip();
    const prefix = paramsObj.NAME_PREFIX || "fm";
    uvls.forEach((u, i) => zip.file(`${prefix}_${i}.uvl`, u));
    const blob = await zip.generateAsync({ type: "blob" });
    saveAs(blob, "feature_models.zip");

    setModal({
        title: `${uvls.length} model${uvls.length === 1 ? "" : "s"} ready`,
        msg: "Your download has started.",
        subtle: " ",
        state: "success",
        percent: 100,
    });
    hideModal(1200);
    return uvls.length;
}

window.generatorRuntime = { ready: getRuntime, generate: generateAndDownload };

// ─── Parent–child distribution slider ──────────────────────────────────────
// Renders a 3-handle noUiSlider that splits [0, 1 - groupCardinality] into 4
// coloured segments and keeps the hidden inputs in sync with its positions.
// When `group_cardinality` is on, the slider range shrinks so all five values
// still sum to 1.

const REL_BASE = [
    { id: "dist_optional",    label: "Optional",    color: "#5e6278" },
    { id: "dist_mandatory",   label: "Mandatory",   color: "#3f4254" },
    { id: "dist_alternative", label: "Alternative", color: "#2b2b40" },
    { id: "dist_or",          label: "Or",          color: "#181c32" },
];
const REL_GROUP = {
    id: "dist_group_cardinality",
    label: "Group cardinality",
    color: "repeating-linear-gradient(-45deg, #b5b5c3 0 8px, #a1a5b7 8px 16px)",
};

function initParentChildSlider() {
    const slider = document.getElementById("rel_slider");
    if (!slider) return;

    function groupIsOn() {
        const gc = document.getElementById("group_cardinality");
        return !!(gc && gc.checked);
    }

    function currentSegments() {
        return groupIsOn() ? [...REL_BASE, REL_GROUP] : REL_BASE;
    }

    function readValues(segments) {
        return segments.map((s) => parseFloat(document.getElementById(s.id)?.value || "0"));
    }

    function normalised(values) {
        const sum = values.reduce((a, b) => a + b, 0) || 1;
        return values.map((v) => v / sum);
    }

    function cumulativeFromDist(dist) {
        const cum = [];
        let acc = 0;
        for (let i = 0; i < dist.length - 1; i++) {
            acc += dist[i];
            cum.push(acc);
        }
        return cum;
    }

    function updateLegend(segments, dist) {
        REL_BASE.forEach((s, i) => {
            const pct = Math.round((dist[i] || 0) * 100);
            const badge = document.getElementById(`label_${s.id}`);
            if (badge) badge.textContent = `${pct}%`;
        });
        const gcLbl = document.getElementById("label_group_card");
        if (gcLbl) {
            const gcDist = segments.length === 5 ? (dist[4] || 0) : 0;
            gcLbl.textContent = `${Math.round(gcDist * 100)}%`;
            const el = document.getElementById("dist_group_cardinality");
            if (el) el.value = gcDist.toFixed(4);
        }
    }

    function buildSlider(segments) {
        if (slider.noUiSlider) slider.noUiSlider.destroy();
        slider.innerHTML = "";
        slider.style.background = "";

        // When group_cardinality is freshly enabled, give it a sensible default
        // share (10%) so it is immediately visible on the bar.
        const gcEl = document.getElementById("dist_group_cardinality");
        const gcIdx = segments.findIndex((s) => s.id === "dist_group_cardinality");
        if (gcIdx >= 0 && gcEl) {
            const v = parseFloat(gcEl.value || "0");
            if (!(v > 0)) gcEl.value = "0.1";
        } else if (gcEl) {
            gcEl.value = "0.0";
        }

        const dist = normalised(readValues(segments));
        const startCum = cumulativeFromDist(dist);

        noUiSlider.create(slider, {
            start: startCum,
            connect: Array(segments.length).fill(true),
            range: { min: 0, max: 1 },
            step: 0.01,
            behaviour: "drag-tap",
            margin: 0,
        });

        const connects = slider.querySelectorAll(".noUi-connect");
        connects.forEach((c, i) => {
            c.style.background = segments[i].color;
        });

        slider.noUiSlider.on("update", (raw) => {
            const cum = raw.map(Number);
            const nextDist = [];
            let prev = 0;
            for (let i = 0; i < cum.length; i++) {
                nextDist.push(Math.max(0, cum[i] - prev));
                prev = cum[i];
            }
            nextDist.push(Math.max(0, 1 - prev));
            // Round to 4 decimals but absorb the rounding error on the last
            // segment so the sum is EXACTLY 1.0 (Params.__post_init__ asserts
            // abs(sum - 1) < 1e-6 and would otherwise fail).
            const rounded = nextDist.map((v) => Math.round(v * 10000) / 10000);
            const diff = 1 - rounded.reduce((a, b) => a + b, 0);
            rounded[rounded.length - 1] = Math.max(0, rounded[rounded.length - 1] + diff);
            segments.forEach((s, i) => {
                const el = document.getElementById(s.id);
                if (el) el.value = rounded[i].toFixed(4);
            });
            updateLegend(segments, rounded);
        });

        updateLegend(segments, dist);
    }

    function rebuild() { buildSlider(currentSegments()); }
    document.getElementById("group_cardinality")?.addEventListener("change", rebuild);
    rebuild();

    // Safety net: right before submitting the wizard form, make sure the 4
    // (or 5) probability inputs sum to EXACTLY 1.0, fixing any float residue.
    const form = slider.closest("form");
    if (form && !form.__relNormaliserBound) {
        form.__relNormaliserBound = true;
        const normalise = () => {
            const segs = currentSegments();
            const vals = segs.map((s) => parseFloat(document.getElementById(s.id)?.value || "0"));
            const total = vals.reduce((a, b) => a + b, 0) || 1;
            const norm = vals.map((v) => v / total);
            const rounded = norm.map((v) => Math.round(v * 10000) / 10000);
            const diff = 1 - rounded.reduce((a, b) => a + b, 0);
            rounded[rounded.length - 1] = Math.max(0, rounded[rounded.length - 1] + diff);
            segs.forEach((s, i) => {
                const el = document.getElementById(s.id);
                if (el) el.value = rounded[i].toFixed(4);
            });
        };
        // wizard-spa.js dispatches this synchronously before snapshotting the
        // form data, so the normalised values make it into the POST body.
        form.addEventListener("wizard:pre-submit", normalise);
        // Fallback for any non-SPA submit path (full-reload navigation).
        form.addEventListener("submit", normalise, { capture: true });
    }
}

// ─── Generic fixed-segments probability slider ─────────────────────────────
// Drives a noUiSlider that partitions [0,1] into N segments backed by hidden
// inputs. Used for step3's Boolean-operator distribution (AND/OR/IMPLIES/
// EQUIVALENCE). Simpler than the parent–child slider because the segments
// never change at runtime.
function initFixedSegmentsSlider({ sliderId, segments, labelSuffix = "label_" }) {
    const slider = document.getElementById(sliderId);
    if (!slider || !window.noUiSlider) return;

    function readValues() {
        return segments.map((s) => parseFloat(document.getElementById(s.id)?.value || "0"));
    }

    function normalised(values) {
        const sum = values.reduce((a, b) => a + b, 0) || 1;
        return values.map((v) => v / sum);
    }

    function cumulativeFromDist(dist) {
        const cum = [];
        let acc = 0;
        for (let i = 0; i < dist.length - 1; i++) {
            acc += dist[i];
            cum.push(acc);
        }
        return cum;
    }

    function updateLegend(dist) {
        segments.forEach((s, i) => {
            const badge = document.getElementById(`${labelSuffix}${s.id}`);
            if (badge) badge.textContent = `${Math.round((dist[i] || 0) * 100)}%`;
        });
    }

    function writeHiddenInputs(rounded) {
        segments.forEach((s, i) => {
            const el = document.getElementById(s.id);
            if (el) el.value = rounded[i].toFixed(4);
        });
    }

    const dist = normalised(readValues());
    noUiSlider.create(slider, {
        start: cumulativeFromDist(dist),
        connect: Array(segments.length).fill(true),
        range: { min: 0, max: 1 },
        step: 0.01,
        behaviour: "drag-tap",
        margin: 0,
    });
    slider.querySelectorAll(".noUi-connect").forEach((c, i) => {
        c.style.background = segments[i].color;
    });

    slider.noUiSlider.on("update", (raw) => {
        const cum = raw.map(Number);
        const nextDist = [];
        let prev = 0;
        for (let i = 0; i < cum.length; i++) {
            nextDist.push(Math.max(0, cum[i] - prev));
            prev = cum[i];
        }
        nextDist.push(Math.max(0, 1 - prev));
        const rounded = nextDist.map((v) => Math.round(v * 10000) / 10000);
        const diff = 1 - rounded.reduce((a, b) => a + b, 0);
        rounded[rounded.length - 1] = Math.max(0, rounded[rounded.length - 1] + diff);
        writeHiddenInputs(rounded);
        updateLegend(rounded);
    });

    updateLegend(dist);

    // Pre-submit safety net (same pattern as parent-child slider).
    const form = slider.closest("form");
    if (form && !form[`__${sliderId}Bound`]) {
        form[`__${sliderId}Bound`] = true;
        const normalise = () => {
            const vals = readValues();
            const total = vals.reduce((a, b) => a + b, 0) || 1;
            const norm = vals.map((v) => v / total);
            const rounded = norm.map((v) => Math.round(v * 10000) / 10000);
            const diff = 1 - rounded.reduce((a, b) => a + b, 0);
            rounded[rounded.length - 1] = Math.max(0, rounded[rounded.length - 1] + diff);
            writeHiddenInputs(rounded);
        };
        form.addEventListener("wizard:pre-submit", normalise);
        form.addEventListener("submit", normalise, { capture: true });
    }
}

const BOOL_OPS_SEGMENTS = [
    { id: "prob_and",     label: "AND",         color: "#5e6278" },
    { id: "prob_or",      label: "OR",          color: "#3f4254" },
    { id: "prob_implies", label: "IMPLIES",     color: "#2b2b40" },
    { id: "prob_equiv",   label: "EQUIVALENCE", color: "#181c32" },
];

function initBooleanOpsSlider() {
    initFixedSegmentsSlider({
        sliderId: "boolop_slider",
        segments: BOOL_OPS_SEGMENTS,
        labelSuffix: "label_",
    });
}

function initStepHelpers() {
    initParentChildSlider();
    initBooleanOpsSlider();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initStepHelpers);
} else {
    initStepHelpers();
}
window.addEventListener("wizard:swapped", initStepHelpers);

window.generatorRuntime.initStepHelpers = initStepHelpers;
