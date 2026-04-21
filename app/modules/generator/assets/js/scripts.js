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
    "uvlparser-2.5.0-py3-none-any.whl",
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

// ─── Wheel diagnostics ────────────────────────────────────────────────────
//
// When micropip reports "File is not a zip file" we want to know why. This
// helper fetches the same URL directly and reports HTTP status, content
// type, content length, and the first bytes of the response (either the
// ZIP magic "PK\x03\x04" if it *is* a valid zip the server sent, or a
// snippet of whatever HTML/error was served instead). Logged to console in
// full; returns a short single-line summary for the user-facing error.
async function diagnoseWheelUrl(url) {
    try {
        const resp = await fetch(url, { credentials: "same-origin" });
        const ct = resp.headers.get("content-type") || "?";
        const ce = resp.headers.get("content-encoding") || "none";
        const cl = resp.headers.get("content-length") || "?";
        const status = `HTTP ${resp.status} ${resp.statusText || ""}`.trim();
        const buf = new Uint8Array(await resp.arrayBuffer());
        const isZip = buf.length >= 4 &&
            buf[0] === 0x50 && buf[1] === 0x4b &&
            buf[2] === 0x03 && buf[3] === 0x04;
        let bodySnippet = "";
        if (!isZip) {
            // Show the first 200 chars decoded as UTF-8 — makes HTML error
            // pages instantly recognisable.
            const text = new TextDecoder("utf-8", { fatal: false }).decode(buf.subarray(0, 200));
            bodySnippet = text.replace(/\s+/g, " ").trim();
        }
        console.error("Wheel diagnostic for", url, {
            status, contentType: ct, contentEncoding: ce, contentLength: cl,
            bytesReceived: buf.length, isZip, bodySnippet,
        });
        if (isZip) return `${status}, ${buf.length} bytes, valid zip magic (install-side issue)`;
        return `${status}, ct=${ct}, ce=${ce}, ${buf.length} bytes, body="${bodySnippet.slice(0, 80)}…"`;
    } catch (e) {
        console.error("Wheel diagnostic fetch failed for", url, e);
        return `fetch failed: ${e.message || e}`;
    }
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
        const wheelUrl = `/generator/js/${wheel}`;
        pyodide.globals.set("wheel_url", wheelUrl);
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
            // micropip's BadZipFile is almost always the server returning
            // something other than the wheel — an HTML 404/login page, a
            // gzipped body the browser failed to decompress, a CDN stub,
            // etc. Fetch the URL ourselves to surface *what* came back so
            // the failure is diagnosable from the UI without needing
            // server logs. The extra info goes into the thrown Error so
            // it also reaches the "Failed to load generator" modal.
            const diag = await diagnoseWheelUrl(wheelUrl);
            throw new Error(
                `Could not install ${wheel} — ${lastErr.message || lastErr}` +
                (diag ? ` | server returned: ${diag}` : "")
            );
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

// ─── Primitives — used by step6 to orchestrate a live UI ─────────────────

export async function fetchParams() {
    const resp = await fetch("/generator/random/params-json");
    if (!resp.ok) throw new Error("Failed to fetch params-json: " + resp.status);
    return resp.json();
}

export async function generateOne(pyodide, paramsObj, index) {
    // Each call re-sets params_json because paramsObj may have changed
    // between invocations (the user flipping checkboxes on step 6 before
    // clicking Generate). Kept cheap — Python parses it lazily.
    pyodide.globals.set("params_json", JSON.stringify(paramsObj));
    pyodide.globals.set("model_index", index);
    const resultJson = await pyodide.runPythonAsync(
        "generate_one_model(params_json, int(model_index))",
    );
    return JSON.parse(resultJson);
}

export async function packageZip(files) {
    const zip = new JSZip();
    files.forEach((f) => zip.file(f.filename, f.content));
    return zip.generateAsync({ type: "blob" });
}

export function triggerDownload(blob, filename = "feature_models.zip") {
    saveAs(blob, filename);
}

window.generatorRuntime = {
    ready: getRuntime,
    fetchParams,
    generateOne,
    packageZip,
    triggerDownload,
};

// ─── Generic distribution control ───────────────────────────────────────
// Renders an N-handle noUiSlider whose segments partition [0, 1], backed
// by one visible number input per segment. The slider and the inputs are
// two-way bound:
//
//   * Dragging a handle rewrites every input to the rounded segment share.
//   * Typing a value in an input (0..1) clamps, rebalances the siblings so
//     the total stays 1, and repositions the slider handles to match.
//
// Segments whose input element is missing from the DOM are skipped — this
// is how the templates gate off segments (e.g. "Integer" when Arithmetic
// level is off). If fewer than two segments survive the filter, the
// slider is hidden and a 100%-tag is displayed instead.
function initDistributionControl({ sliderId, allSegments, labelPrefix = "label_" }) {
    const slider = document.getElementById(sliderId);
    if (!slider || !window.noUiSlider) return;

    const segments = allSegments.filter((s) => document.getElementById(s.id));
    if (segments.length === 0) return;

    function inputs() {
        return segments.map((s) => document.getElementById(s.id));
    }
    function readValues() {
        return inputs().map((el) => parseFloat(el?.value || "0") || 0);
    }
    function normalise(vals) {
        const sum = vals.reduce((a, b) => a + b, 0);
        return sum > 0 ? vals.map((v) => v / sum) : vals.map(() => 1 / vals.length);
    }
    function roundAndFix(vals) {
        const rounded = vals.map((v) => Math.round(v * 10000) / 10000);
        const diff = 1 - rounded.reduce((a, b) => a + b, 0);
        rounded[rounded.length - 1] = Math.max(0, rounded[rounded.length - 1] + diff);
        return rounded;
    }
    function writeValues(vals) {
        inputs().forEach((el, i) => {
            if (!el) return;
            const next = vals[i].toFixed(4);
            if (el.value !== next) el.value = next;
        });
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
    function updateLegend(vals) {
        segments.forEach((s, i) => {
            const badge = document.getElementById(`${labelPrefix}${s.id}`);
            if (badge) badge.textContent = `${Math.round((vals[i] || 0) * 100)}%`;
        });
    }

    // Degenerate case: only one active segment. Hide the slider and pin
    // the value to 1.0 — there's nothing to distribute.
    if (segments.length === 1) {
        slider.style.display = "none";
        writeValues([1.0]);
        updateLegend([1.0]);
        return;
    }

    const startVals = roundAndFix(normalise(readValues()));
    writeValues(startVals);
    updateLegend(startVals);

    if (slider.noUiSlider) slider.noUiSlider.destroy();
    slider.innerHTML = "";
    slider.style.display = "";
    noUiSlider.create(slider, {
        start: cumulativeFromDist(startVals),
        connect: Array(segments.length).fill(true),
        range: { min: 0, max: 1 },
        step: 0.01,
        behaviour: "drag-tap",
        margin: 0,
    });
    slider.querySelectorAll(".noUi-connect").forEach((c, i) => {
        c.style.background = segments[i].color;
    });

    let suppressSliderUpdate = false;

    // Setting el.value programmatically does NOT fire `input`/`change`,
    // so the sidebar live-refresh (which listens for those) would stay
    // silent while the user drags handles. We emit a bubbling custom
    // event once per drag update; wizard-spa.js is wired to refresh the
    // summary on it.
    function notifyDraftChanged() {
        const form = slider.closest("form");
        if (form) {
            form.dispatchEvent(new CustomEvent("wizard:draft-changed", { bubbles: true }));
        }
    }

    slider.noUiSlider.on("update", (raw) => {
        if (suppressSliderUpdate) return;
        const cum = raw.map(Number);
        const vals = [];
        let prev = 0;
        for (let i = 0; i < cum.length; i++) {
            vals.push(Math.max(0, cum[i] - prev));
            prev = cum[i];
        }
        vals.push(Math.max(0, 1 - prev));
        const rounded = roundAndFix(vals);
        writeValues(rounded);
        updateLegend(rounded);
        notifyDraftChanged();
    });

    // Bind number-input changes: rebalance siblings, reposition slider.
    segments.forEach((s, idx) => {
        const el = document.getElementById(s.id);
        if (!el) return;
        if (el.__distHandler) {
            el.removeEventListener("input", el.__distHandler);
            el.removeEventListener("change", el.__distHandler);
        }
        const handler = () => {
            let v = parseFloat(el.value);
            if (!Number.isFinite(v)) v = 0;
            if (v < 0) v = 0;
            if (v > 1) v = 1;
            const vals = readValues();
            vals[idx] = v;
            const others = vals.map((_, i) => i).filter((i) => i !== idx);
            const remaining = 1 - v;
            const otherSum = others.reduce((s, i) => s + vals[i], 0);
            if (otherSum > 1e-6) {
                const factor = remaining / otherSum;
                others.forEach((i) => {
                    vals[i] = vals[i] * factor;
                });
            } else {
                const share = remaining / Math.max(1, others.length);
                others.forEach((i) => {
                    vals[i] = share;
                });
            }
            const rounded = roundAndFix(vals);
            writeValues(rounded);
            updateLegend(rounded);
            suppressSliderUpdate = true;
            try {
                slider.noUiSlider.set(cumulativeFromDist(rounded));
            } finally {
                suppressSliderUpdate = false;
            }
        };
        el.__distHandler = handler;
        el.addEventListener("input", handler);
        el.addEventListener("change", handler);
    });

    // Pre-submit safety net: normalise exactly to 1.0.
    const form = slider.closest("form");
    if (form && !form[`__${sliderId}Bound`]) {
        form[`__${sliderId}Bound`] = true;
        const onSubmit = () => {
            const rounded = roundAndFix(normalise(readValues()));
            writeValues(rounded);
            updateLegend(rounded);
        };
        form.addEventListener("wizard:pre-submit", onSubmit);
        form.addEventListener("submit", onSubmit, { capture: true });
    }
}

// ─── Segment definitions ───────────────────────────────────────────────
// Each set is passed to initDistributionControl; segments whose input is
// missing from the current page are skipped automatically.

const REL_SEGMENTS = [
    { id: "dist_optional",          label: "Optional",         color: "#5e6278" },
    { id: "dist_mandatory",         label: "Mandatory",        color: "#3f4254" },
    { id: "dist_alternative",       label: "Alternative",      color: "#2b2b40" },
    { id: "dist_or",                label: "Or",               color: "#181c32" },
    { id: "dist_group_cardinality", label: "Group cardinality",
      color: "repeating-linear-gradient(-45deg, #b5b5c3 0 8px, #a1a5b7 8px 16px)" },
];

const BOOL_OPS_SEGMENTS = [
    { id: "prob_and",     label: "AND",         color: "#5e6278" },
    { id: "prob_or",      label: "OR",          color: "#3f4254" },
    { id: "prob_implies", label: "IMPLIES",     color: "#2b2b40" },
    { id: "prob_equiv",   label: "EQUIVALENCE", color: "#181c32" },
];

const ARITH_OPS_SEGMENTS = [
    { id: "prob_plus",  label: "+",     color: "#5e6278" },
    { id: "prob_minus", label: "−",     color: "#3f4254" },
    { id: "prob_times", label: "×",     color: "#2b2b40" },
    { id: "prob_div",   label: "÷",     color: "#181c32" },
    { id: "prob_sum",   label: "sum()", color: "#009ef7" },
    { id: "prob_avg",   label: "avg()", color: "#0b76b7" },
];

const CMP_OPS_SEGMENTS = [
    { id: "prob_eq",  label: "=",  color: "#5e6278" },
    { id: "prob_lt",  label: "<",  color: "#3f4254" },
    { id: "prob_gt",  label: ">",  color: "#2b2b40" },
    { id: "prob_leq", label: "≤",  color: "#181c32" },
    { id: "prob_geq", label: "≥",  color: "#7e8299" },
];

const CTC_DIST_SEGMENTS = [
    { id: "ctc_dist_boolean", label: "Boolean", color: "#5e6278" },
    { id: "ctc_dist_integer", label: "Integer", color: "#3f4254" },
    { id: "ctc_dist_real",    label: "Real",    color: "#2b2b40" },
    { id: "ctc_dist_string",  label: "String",  color: "#181c32" },
];

const ATTR_DIST_SEGMENTS = [
    { id: "dist_boolean", label: "Boolean", color: "#5e6278" },
    { id: "dist_integer", label: "Integer", color: "#3f4254" },
    { id: "dist_real",    label: "Real",    color: "#2b2b40" },
    { id: "dist_string",  label: "String",  color: "#181c32" },
];

function initAllDistributionControls() {
    initDistributionControl({ sliderId: "rel_slider",        allSegments: REL_SEGMENTS });
    initDistributionControl({ sliderId: "boolop_slider",     allSegments: BOOL_OPS_SEGMENTS });
    initDistributionControl({ sliderId: "arith_slider",      allSegments: ARITH_OPS_SEGMENTS });
    initDistributionControl({ sliderId: "cmp_slider",        allSegments: CMP_OPS_SEGMENTS });
    initDistributionControl({ sliderId: "ctc_dist_slider",   allSegments: CTC_DIST_SEGMENTS });
    initDistributionControl({ sliderId: "attr_dist_slider",  allSegments: ATTR_DIST_SEGMENTS });
}

function initStepHelpers() {
    initAllDistributionControls();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initStepHelpers);
} else {
    initStepHelpers();
}
window.addEventListener("wizard:swapped", initStepHelpers);

window.generatorRuntime.initStepHelpers = initStepHelpers;
