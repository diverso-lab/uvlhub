// llm-page.js — Page controller for /generator/llm.
//
// This script glues three runtimes together to generate UVL feature
// models in the browser:
//
//   1. UVLHub   — provides the SEED in seed mode. Uses the public
//                 /api/v1/search endpoint and /doi/<doi>/files/raw/<filename>
//                 to pull real UVL files from the hub. No API key needed;
//                 these endpoints are public.
//
//   2. WebLLM   — lives in llm-worker.js. A Web Worker loads a small coder
//                 model (Qwen 2.5 Coder 0.5B / 1.5B / 3B / 7B) from esm.run,
//                 keeps weights in IndexedDB for next visits, and runs
//                 inference through WebGPU. The user's machine does all
//                 the compute; uvlhub.io serves zero tokens.
//
//   3. Pyodide  — reuses the runtime already booted by scripts.js and exposed
//                 on window.generatorRuntime (flamapy wheels are already
//                 installed). Every generated candidate is parsed with
//                 UVLReader to separate syntactically valid variants from
//                 broken ones.
//
// The script does not use ES modules or npm imports on its own so we can
// avoid touching the webpack config — it loads as a classic <script> from
// the llm.html template.

(function () {
    "use strict";

    // ─── Preset seeds (shown when UVLRepo returns nothing / user offline) ───
    //
    // Two tiny UVL models taken from the UVL reference paper and the thesis
    // running example. They act as a safety net so the page is usable even
    // without a working search backend.
    const PRESET_SEEDS = [
        {
            doi: null,
            filename: "sandwich.uvl",
            title: "Sandwich (UVL reference example)",
            content: [
                "features",
                "    Sandwich",
                "        mandatory",
                "            Bread",
                "        optional",
                "            Sauce",
                "                alternative",
                "                    Ketchup",
                "                    Mustard",
                "            Cheese",
                "",
                "constraints",
                "    Ketchup => Cheese",
                ""
            ].join("\n"),
        },
        {
            doi: null,
            filename: "smartwatch.uvl",
            title: "Smartwatch (thesis running example)",
            content: [
                "features",
                "    Smartwatch",
                "        mandatory",
                "            Screen",
                "                alternative",
                "                    Touch",
                "                    Standard",
                "            EnergyManagement",
                "                alternative",
                "                    Basic",
                "                    AdvancedSolar",
                "        optional",
                "            Payment",
                "            GPS",
                "            SportsTracking",
                "                or",
                "                    Running",
                "                    Skiing",
                "                    Hiking",
                "",
                "constraints",
                "    SportsTracking => GPS",
                "    Payment => !Standard",
                ""
            ].join("\n"),
        },
    ];

    // ─── WebLLM model catalog (code-specialized, q4f16_1 int4 quant) ─────
    //
    // Concept-mode asks the LLM to emit a structured JSON tree. Generalist
    // chat models of this size (Llama 3.2 3B, Phi 3.5 mini, Qwen 2.5 3B)
    // start the JSON well but lose nesting coherence partway through deeper
    // trees — they produce invented tokens like "Computerisem" when
    // backtracking on structure they can't hold in context. Coder models
    // pretrain on billions of tokens of JSON/YAML/source code, so balanced
    // braces and nested objects are effectively native. Seed-mode infill
    // also benefits (UVL is indented keyword DSL, which reads like code).
    //
    // Qwen2.5-Coder is currently the only code-specialized family in
    // WebLLM's prebuilt catalog. Order matters — first entry is the
    // default suggestion.
    const MODELS = [
        {
            id: "Qwen2.5-Coder-3B-Instruct-q4f16_1-MLC",
            name: "Qwen 2.5 Coder 3B",
            size: "2.5 GB",
            note: "recommended default",
        },
        {
            id: "Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC",
            name: "Qwen 2.5 Coder 7B",
            size: "5.1 GB",
            note: "best quality — needs RAM/GPU",
        },
        {
            id: "Qwen2.5-Coder-1.5B-Instruct-q4f16_1-MLC",
            name: "Qwen 2.5 Coder 1.5B",
            size: "1.6 GB",
            note: "fast, good for iteration",
        },
        {
            id: "Qwen2.5-Coder-0.5B-Instruct-q4f16_1-MLC",
            name: "Qwen 2.5 Coder 0.5B",
            size: "950 MB",
            note: "fastest, often incoherent",
        },
    ];

    // ─── Model state (shared by the model table and generate paths) ─────────
    //
    // currentLoadedModel  the model currently held by the engine in VRAM/RAM.
    //                     This is what generate() uses. Null until a Load
    //                     button succeeds.
    // cacheStatus         map modelId → bool, populated from the worker's
    //                     WebLLM hasModelInCache() probe on init and after
    //                     each load/delete.
    // busyModel           modelId currently downloading or deleting. While
    //                     non-null other model buttons are disabled so the
    //                     user can't start a parallel load and race the
    //                     progress bar.
    let currentLoadedModel = null;
    let cacheStatus = {};
    let busyModel = null;
    // null = not probed yet, true = probe succeeded, false = probe failed.
    // Consulted by updateRow() to keep Load/Delete buttons disabled after
    // each re-render when WebGPU is unavailable. The generate button has
    // its own lifecycle (enabled only after a successful model load).
    let webGpuReady = null;

    // ─── DOM helpers ─────────────────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);
    function log(msg, kind) {
        const el = $("llm_log");
        if (!el) return;
        const line = document.createElement("div");
        line.className = "llm-log-line " + (kind ? "llm-log-" + kind : "");
        line.textContent = msg;
        el.appendChild(line);
        el.scrollTop = el.scrollHeight;
    }

    // Two progress bars live on the page: one in the Models card footer
    // (used for model downloads during load), and a mirrored one in the
    // Generate card (so users see progress right above the streaming
    // results, same position as the random generator's step 6). We always
    // update both — the "wrong" one just sits at the value it had before.
    function setProgress(percent, text) {
        const pct = Math.max(0, Math.min(100, percent)) + "%";
        const bar = $("llm_progress_bar");
        if (bar) bar.style.width = pct;
        const label = $("llm_progress_text");
        if (label && text !== undefined) label.textContent = text;
        const genBar = $("llm_gen_progress_bar");
        if (genBar) genBar.style.width = pct;
        const genLabel = $("llm_gen_progress_text");
        if (genLabel && text !== undefined) genLabel.textContent = text;
    }

    // ─── UVLRepo seed picker ─────────────────────────────────────────────────
    //
    // Hits the public /api/v1/search endpoint. That index mixes dataset-level
    // and hubfile-level documents; only hubfile hits carry a `filename`, and
    // those are the ones we can feed directly into /doi/<doi>/files/raw.

    let searchTimer = null;
    async function runSearch(q) {
        const results = $("llm_search_results");
        if (!results) return;
        results.innerHTML = "";
        if (!q || q.length < 2) return;
        try {
            const resp = await fetch("/api/v1/search?q=" + encodeURIComponent(q) + "&size=20");
            if (!resp.ok) throw new Error("Search HTTP " + resp.status);
            const data = await resp.json();
            // The Elasticsearch index mixes file types (UVL, SPLOT xml,
            // DIMACS, Glencoe JSON, PDFs of papers…). Filter to "plausibly
            // a UVL file": either the filename ends in .uvl, OR it has no
            // extension at all (some hubfiles are stored as bare names). We
            // only reject filenames that explicitly end in a different,
            // clearly non-UVL extension.
            // Hubfile docs in the ES index carry `dataset_doi` (never `doi`),
            // and their `type` is "hubfile"; dataset-level docs don't have a
            // filename so they drop out naturally. Accept either field name
            // to stay compatible if the index schema ever gets renamed.
            const allHits = (data.results || [])
                .map((h) => Object.assign({}, h, { doi: h.doi || h.dataset_doi }))
                .filter((h) => h.filename && h.doi);
            const NON_UVL_EXT = /\.(xml|pdf|json|dimacs|cnf|splx|jpg|jpeg|png|gif|zip|tar|gz|txt|md|doc|docx)$/i;
            const hits = allHits.filter((h) => {
                if (/\.uvl$/i.test(h.filename)) return true;
                if (NON_UVL_EXT.test(h.filename)) return false;
                // No recognized extension → include; might be a bare-name UVL.
                return true;
            });
            if (hits.length === 0) {
                // Diagnostic: if Elasticsearch returned anything at all, tell
                // the user the filter is what dropped them. Saves 10 minutes
                // of "why isn't my file showing up" confusion.
                if (allHits.length > 0) {
                    const first = allHits[0];
                    console.log("[llm-search] all %d hits filtered out as non-UVL. First hit:", allHits.length, first);
                    results.innerHTML =
                        '<div class="text-muted fs-7 p-3">' +
                        allHits.length + " hit(s) returned, but none look like UVL files. " +
                        "Open DevTools console for a sample hit." +
                        "</div>";
                } else {
                    results.innerHTML = '<div class="text-muted fs-7 p-3">No UVL files matched in the hub. Use a preset below or paste your own.</div>';
                }
                return;
            }
            hits.forEach((h) => {
                const row = document.createElement("button");
                row.type = "button";
                row.className = "list-group-item list-group-item-action d-flex flex-column";

                // Best-effort snippet from Elasticsearch highlights. The
                // /api/v1/search response may or may not include it depending
                // on how the query is shaped server-side; if absent we just
                // skip the snippet line.
                const snippet = extractSearchSnippet(h);

                // The DOI field in ES is already a full uvlhub URL
                // (http://host/doi/<doi>), not a bare DOI. Keep only the
                // canonical "10.xxxx/..." portion for display so the pill
                // stays compact; loadSeedFromHub uses the hubfile id,
                // not the DOI, so we don't need it in the click handler.
                const doiDisplay = (h.doi.match(/\/doi\/(.+?)\/?$/) || [null, h.doi])[1];

                let inner =
                    '<span class="fw-semibold">' + escapeHtml(h.filename) + "</span>" +
                    '<span class="text-muted fs-7">' +
                        escapeHtml(h.dataset_title || h.title || "") +
                        ' · <span class="font-monospace">' + escapeHtml(doiDisplay) + "</span></span>";
                if (snippet) {
                    inner += '<span class="text-gray-700 fs-8 mt-1 font-monospace text-truncate">' +
                             snippet +  // already HTML-safe (sanitized in helper)
                             "</span>";
                }
                row.innerHTML = inner;
                row.addEventListener("click", () => loadSeedFromHub(h.id, h.filename, h.dataset_title || h.filename));
                results.appendChild(row);
            });
        } catch (err) {
            results.innerHTML = '<div class="text-danger fs-7 p-3">Search failed: ' + escapeHtml(err.message || String(err)) + "</div>";
        }
    }

    // Pull a short snippet from whichever highlight field the search API
    // exposes. Elasticsearch typically returns `highlight.<field>` as an
    // array of pre-marked HTML fragments with <em>…</em> around hits; some
    // backends flatten it into a top-level `snippet` or `content_snippet`
    // string. Try both shapes and fall back to a raw content slice.
    function extractSearchSnippet(hit) {
        const MAX = 140;
        let raw = null;
        if (hit.highlight) {
            if (typeof hit.highlight === "string") raw = hit.highlight;
            else if (Array.isArray(hit.highlight)) raw = hit.highlight.join(" … ");
            else if (typeof hit.highlight === "object") {
                for (const k of ["content", "filename", "title"]) {
                    if (hit.highlight[k]) {
                        raw = Array.isArray(hit.highlight[k]) ? hit.highlight[k].join(" … ") : hit.highlight[k];
                        break;
                    }
                }
            }
        }
        if (!raw && hit.snippet) raw = hit.snippet;
        if (!raw && hit.content_snippet) raw = hit.content_snippet;
        if (!raw && typeof hit.content === "string") raw = hit.content.slice(0, MAX);
        if (!raw) return null;

        // Preserve <em> / </em> from ES highlights; escape everything else.
        // Simple two-step: escape the whole thing, then re-enable <em> tags.
        let safe = escapeHtml(raw).slice(0, MAX * 2);
        safe = safe.replace(/&lt;em&gt;/g, "<em>").replace(/&lt;\/em&gt;/g, "</em>");
        if (safe.length >= MAX * 2) safe += "…";
        return safe.replace(/\s+/g, " ").trim();
    }

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    async function loadSeedFromHub(hubfileId, filename, title) {
        const results = $("llm_search_results");
        // Collapse the dropdown into a single "loading" row so the user can
        // see the click registered. Keeping it in the same container means
        // the visual jump on success/error is contained.
        if (results) {
            results.innerHTML =
                '<div class="list-group-item d-flex align-items-center gap-2 fs-7">' +
                '  <span class="spinner-border spinner-border-sm text-primary" role="status"></span>' +
                '  <span>Loading <span class="font-monospace">' + escapeHtml(filename) + '</span>…</span>' +
                '</div>';
        }
        try {
            // /hubfiles/raw/<id>/<filename> streams the UVL as text/plain
            // and is public when the parent dataset has a DOI — the only
            // case the search UI surfaces anyway.
            const resp = await fetch(
                "/hubfiles/raw/" + encodeURIComponent(hubfileId) + "/" + encodeURIComponent(filename)
            );
            if (!resp.ok) throw new Error("Fetch HTTP " + resp.status);
            const text = await resp.text();
            $("llm_seed").value = text;
            $("llm_seed_name").value = filename;
            renderSeedOrganicBadge();
            log("Seed loaded from hub: " + title + " (" + filename + ")", "info");

            // Replace the dropdown with a persistent "selected" banner the
            // user can't miss. Clicking "Change" re-opens the search (empty
            // state — the input still has their query, so it re-runs).
            if (results) {
                results.innerHTML =
                    '<div class="list-group-item d-flex align-items-center gap-3 bg-light-success">' +
                    '  <i class="ki-duotone ki-check-circle fs-2 text-success"><span class="path1"></span><span class="path2"></span></i>' +
                    '  <div class="flex-grow-1 min-w-0">' +
                    '    <div class="fw-semibold text-gray-900">Seed loaded into the editor below</div>' +
                    '    <div class="text-muted fs-7 text-truncate">' +
                         '<span class="font-monospace">' + escapeHtml(filename) + '</span>' +
                         ' · ' + escapeHtml(title) +
                    '    </div>' +
                    '  </div>' +
                    '  <button type="button" class="btn btn-sm btn-light-primary flex-shrink-0" id="llm_search_change">Change</button>' +
                    '</div>';
                const changeBtn = document.getElementById("llm_search_change");
                if (changeBtn) {
                    changeBtn.addEventListener("click", () => {
                        const input = $("llm_search");
                        results.innerHTML = "";
                        if (input) {
                            input.focus();
                            if (input.value) runSearch(input.value.trim());
                        }
                    });
                }
            }

            // Also flash the seed textarea so the user's eye catches that
            // *something* changed below. Class toggle; fade handled in CSS
            // injected once on first call.
            flashSeedTextarea();
        } catch (err) {
            log("Could not load seed: " + (err.message || err), "error");
            if (results) {
                results.innerHTML =
                    '<div class="list-group-item text-danger fs-7">' +
                    '  <i class="ki-duotone ki-cross-circle fs-4 me-2"><span class="path1"></span><span class="path2"></span></i>' +
                    '  Could not load ' + escapeHtml(filename) + ': ' + escapeHtml(err.message || String(err)) +
                    '</div>';
            }
        }
    }

    // Short green border flash on the seed textarea after a successful load
    // from the hub, so the user's attention lands on the freshly-populated
    // editor even if they were looking at the search results.
    function flashSeedTextarea() {
        const seed = $("llm_seed");
        if (!seed) return;
        if (!document.getElementById("llm_seed_flash_style")) {
            const st = document.createElement("style");
            st.id = "llm_seed_flash_style";
            st.textContent =
                "@keyframes llmSeedFlash {" +
                "  0%   { box-shadow: 0 0 0 0 rgba(80,205,137,0.6); border-color: #50cd89; }" +
                "  60%  { box-shadow: 0 0 0 6px rgba(80,205,137,0); border-color: #50cd89; }" +
                "  100% { box-shadow: 0 0 0 0 rgba(80,205,137,0); }" +
                "}" +
                ".llm-seed-flash { animation: llmSeedFlash 900ms ease-out; }";
            document.head.appendChild(st);
        }
        seed.classList.remove("llm-seed-flash");
        // Re-add on next frame so the animation restarts on consecutive loads.
        requestAnimationFrame(() => seed.classList.add("llm-seed-flash"));
        // Bring the editor into view on small screens where the dropdown
        // pushes it off the fold.
        seed.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // ─── Organic-feature check (port of the 2026 notebook heuristic) ─────────
    //
    // A feature model is "organic" when its feature names look like real
    // domain concepts rather than placeholders (f1, x2, var3, …). Feeding the
    // LLM a non-organic seed is garbage-in-garbage-out: whatever it infers
    // inherits the obfuscated vocabulary. We check it up-front to warn the
    // user, and also after generation to verify the infill is consistent.
    //
    // Mirrors the Python used in llm_splc'26v2.py:
    //   GENERIC_PATTERN = ^(f\d+|x\d+|var\d+|feature\d+|[a-z]{1,3}\d*(_[a-z]{1,3}\d*)*)$
    //   informative  := len(name) >= 5  AND  not GENERIC  AND  /[A-Za-z]{3,}/
    //   organic      := features >= 10  AND  informative_ratio >= 0.6
    const ORGANIC_MIN_FEATURES = 10;
    const ORGANIC_MIN_RATIO = 0.6;
    const GENERIC_PATTERN = /^(f\d+|x\d+|var\d+|feature\d+|[a-z]{1,3}\d*(_[a-z]{1,3}\d*)*)$/i;

    function isInformativeFeatureName(name) {
        const s = String(name).trim();
        if (s.length < 5) return false;
        if (GENERIC_PATTERN.test(s)) return false;
        if (!/[A-Za-z]{3,}/.test(s)) return false;
        return true;
    }

    // Extract feature names from raw UVL text via regex — cheap approximation
    // that runs without Pyodide, good enough to flag obviously obfuscated
    // seeds. The authoritative check runs in Python after parsing.
    function organicCheckFromText(uvlText) {
        const lines = uvlText.split("\n");
        const featuresIdx = lines.findIndex((l) => l.trim() === "features");
        const constraintsIdx = lines.findIndex((l) => l.trim() === "constraints");
        const end = constraintsIdx > featuresIdx ? constraintsIdx : lines.length;
        const keywords = new Set(["mandatory", "optional", "alternative", "or", "features", "constraints"]);
        const names = [];
        const start = featuresIdx >= 0 ? featuresIdx + 1 : 0;
        for (let i = start; i < end; i++) {
            const raw = lines[i];
            if (!raw || !raw.trim()) continue;
            const m = raw.match(/^\s*(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_\- ]*[A-Za-z0-9_]))\s*(\{.*)?$/);
            if (!m) continue;
            const name = (m[1] || m[2] || "").trim();
            if (!name || keywords.has(name)) continue;
            if (/[=|&!()<>]/.test(name)) continue;
            names.push(name);
        }
        const total = names.length;
        if (total === 0) {
            return { organic: false, total: 0, informative: 0, ratio: 0, reason: "no features detected" };
        }
        const informative = names.filter(isInformativeFeatureName).length;
        const ratio = informative / total;
        let organic = true, reason = "";
        if (total < ORGANIC_MIN_FEATURES) {
            organic = false;
            reason = "only " + total + " features (< " + ORGANIC_MIN_FEATURES + ")";
        } else if (ratio < ORGANIC_MIN_RATIO) {
            organic = false;
            reason = Math.round(ratio * 100) + "% informative names (< " + Math.round(ORGANIC_MIN_RATIO * 100) + "%)";
        }
        return { organic, total, informative, ratio, reason };
    }

    function renderSeedOrganicBadge() {
        const host = $("llm_seed_organic");
        if (!host) return;
        const text = $("llm_seed").value;
        if (!text.trim()) {
            host.innerHTML = "";
            return;
        }
        const r = organicCheckFromText(text);
        const cls = r.organic ? "badge-light-success" : "badge-light-warning";
        const label = r.organic ? "organic" : "non-organic";
        const detail = r.organic
            ? r.informative + "/" + r.total + " informative names"
            : (r.reason || "low informative ratio");
        host.innerHTML =
            '<span class="badge ' + cls + ' me-2">' + label + "</span>" +
            '<span class="text-muted fs-7">' + escapeHtml(detail) + "</span>";
    }

    // ─── Structural UVL infill (legacy; kept for line-level indentation helpers)
    //
    // Earlier seed mode produced variants by inserting LLM-generated feature
    // lines into a random block of the seed UVL. Seed mode now uses
    // plan-diff (parseUvlToPlan → variant prompt → renderPlanToUvl) so the
    // functions below are no longer called from the generation loop. They
    // remain because `indentLen`, `findFeaturesLine`,
    // `findConstraintsLineOptional` and `splitKeepEnds` are still used by
    // `parseUvlToPlan` and `appendConstraints`.

    const BLOCK_KEYWORDS = new Set(["optional", "mandatory", "alternative", "or"]);
    const UVL_HEADERS = new Set(["features", "constraints"]);

    function indentLen(line) {
        let n = 0;
        while (n < line.length && (line[n] === " " || line[n] === "\t")) n++;
        return n;
    }

    // Mirrors Python's str.splitlines(keepends=True): each element includes
    // its trailing "\n" (except possibly the last line). Needed because the
    // v2 algorithm joins slices with "".join and relies on per-line newlines.
    function splitKeepEnds(text) {
        const out = [];
        let i = 0;
        while (i < text.length) {
            let j = i;
            while (j < text.length && text[j] !== "\n") j++;
            if (j < text.length) { out.push(text.slice(i, j + 1)); i = j + 1; }
            else { out.push(text.slice(i)); i = text.length; }
        }
        return out;
    }

    function findTopLevelIndices(lines, needle) {
        const out = [];
        for (let i = 0; i < lines.length; i++) {
            if (indentLen(lines[i]) === 0 && lines[i].trim() === needle) out.push(i);
        }
        return out;
    }

    function findFeaturesLine(lines) {
        const idxs = findTopLevelIndices(lines, "features");
        if (idxs.length !== 1) {
            throw new Error("Expected exactly 1 top-level 'features' line, found " + idxs.length);
        }
        return idxs[0];
    }

    function findConstraintsLineOptional(lines) {
        const idxs = findTopLevelIndices(lines, "constraints");
        if (idxs.length > 1) {
            throw new Error("Expected at most 1 top-level 'constraints' line, found " + idxs.length);
        }
        return idxs.length === 0 ? null : idxs[0];
    }

    function collectBlockCandidates(lines, start, end) {
        const out = [];
        for (let i = start; i < end; i++) {
            const s = lines[i].trim();
            if (BLOCK_KEYWORDS.has(s)) out.push({ idx: i, indent: indentLen(lines[i]) });
        }
        return out;
    }

    function blockEndIndex(lines, blockIdx, endLimit) {
        // Return the index right after the last child line of the block.
        // Any trailing blank lines between the last child and the next
        // sibling/section must stay attached to what follows them, so we
        // rewind past trailing empties before returning — otherwise the
        // infill lands after the blank line and looks detached.
        const baseIndent = indentLen(lines[blockIdx]);
        let i = blockIdx + 1;
        let firstTrailingEmpty = -1;
        while (i < endLimit) {
            const line = lines[i];
            if (line.trim() === "") {
                if (firstTrailingEmpty < 0) firstTrailingEmpty = i;
                i++; continue;
            }
            if (indentLen(line) <= baseIndent) {
                return firstTrailingEmpty >= 0 ? firstTrailingEmpty : i;
            }
            firstTrailingEmpty = -1;
            i++;
        }
        return firstTrailingEmpty >= 0 ? firstTrailingEmpty : endLimit;
    }

    function chooseInsertionPoint(lines) {
        const featuresIdx = findFeaturesLine(lines);
        const constraintsIdx = findConstraintsLineOptional(lines);
        const endLimit = constraintsIdx !== null ? constraintsIdx : lines.length;
        const candidates = collectBlockCandidates(lines, featuresIdx + 1, endLimit);

        if (candidates.length === 0) {
            // Fallback: insert at the end of the features region.
            let lastNonempty = -1;
            for (let i = featuresIdx + 1; i < endLimit; i++) {
                if (lines[i].trim()) lastNonempty = i;
            }
            const childIndent = lastNonempty >= 0 ? indentLen(lines[lastNonempty]) : 4;
            return { insertAt: endLimit, childIndent, strategy: "fallback_before_end_or_constraints" };
        }

        const chosen = candidates[Math.floor(Math.random() * candidates.length)];
        const endIdx = blockEndIndex(lines, chosen.idx, endLimit);

        // Look for an existing child to copy its indentation exactly.
        let childIndent = null;
        for (let j = chosen.idx + 1; j < Math.min(endIdx, endLimit); j++) {
            if (lines[j].trim()) {
                const ind = indentLen(lines[j]);
                if (ind > chosen.indent) { childIndent = ind; break; }
            }
        }
        if (childIndent === null) childIndent = chosen.indent + 4;

        return {
            insertAt: endIdx,
            childIndent,
            strategy: "end_of_block:" + lines[chosen.idx].trim() + "@" + chosen.idx,
        };
    }

    function splitUvlByInsertion(lines, insertAt) {
        return {
            prefix: lines.slice(0, insertAt).join(""),
            suffix: lines.slice(insertAt).join(""),
        };
    }

    // ─── Hard sanitizers (port of v2 hard_sanitize_*) ────────────────────────
    //
    // Small LLMs hallucinate in specific, predictable ways: bullet-list
    // markers, Markdown fences, "features"/"constraints" headers they were
    // told to skip, tokens like '->'/';' that never appear in UVL, unbalanced
    // quotes. These filters remove all of those before flamapy sees the
    // candidate — dramatically fewer retries are needed.

    function balancedQuotes(s) {
        let c = 0;
        for (let i = 0; i < s.length; i++) if (s[i] === '"') c++;
        return c % 2 === 0;
    }

    // Catch the two common degeneration patterns small LLMs fall into when
    // sampling structured output: immediate substring repetition inside a
    // single token ("MustMust", "unchangedunchanged") and the same word
    // repeated 3+ times in a row ("foo foo foo"). Both produce lines that
    // flamapy accepts tokenwise but that are obviously garbage.
    const REPEAT_IN_TOKEN = /([A-Za-z]{4,})\1/;
    const REPEAT_WORD = /\b([A-Za-z]{3,})\b(?:\s+\1\b){2,}/;
    function looksDegenerate(line) {
        if (REPEAT_IN_TOKEN.test(line)) return true;
        if (REPEAT_WORD.test(line)) return true;
        return false;
    }

    function baseSanitize(text) {
        let t = text.replace(/```[a-zA-Z0-9_-]*\n?/g, "").replace(/```/g, "");
        t = t.replace(/\t/g, "    ");
        // Strip leading "- " bullet markers (common in markdown-tuned LLMs).
        t = t.replace(/^\s*-\s+/gm, "");
        t = t.split("\n").map((l) => l.replace(/\s+$/, "")).join("\n");
        if (t.length > 0 && !t.endsWith("\n")) t += "\n";
        return t;
    }

    // Tokens that are legal in the constraints section but never in the
    // features tree. Small LLMs sometimes "help" by emitting an implication
    // or logical combination during seed-mode infill; flamapy then rejects
    // the model with "mismatched input '=>'" at the child feature's column.
    // Drop any candidate line that contains one of these.
    const FEATURE_FORBIDDEN_SUBSTRINGS = ["->", "=>", "<=>", ";", "==", "!=", ">=", "<="];
    const FEATURE_FORBIDDEN_CHARS = /[&|!()<>=]/;

    function hardSanitizeFeaturesInfill(text) {
        const base = baseSanitize(text);
        const kept = [];
        for (const raw of base.split("\n")) {
            const s = raw.trim();
            if (!s) { kept.push(""); continue; }
            if (UVL_HEADERS.has(s)) continue;
            if (FEATURE_FORBIDDEN_SUBSTRINGS.some((t) => s.includes(t))) continue;
            if (FEATURE_FORBIDDEN_CHARS.test(s)) continue;
            if (!balancedQuotes(s)) continue;
            if (BLOCK_KEYWORDS.has(s)) continue;
            if (looksDegenerate(s)) continue;
            kept.push(raw);
        }
        let out = kept.join("\n").replace(/\n+$/, "");
        if (out) out += "\n";
        return out;
    }

    function hardSanitizeConstraintsInfill(text) {
        const base = baseSanitize(text);
        const kept = [];
        for (const raw of base.split("\n")) {
            const s = raw.trim();
            if (!s) continue;
            if (s.includes("->") || s.includes(";")) continue;
            if (!balancedQuotes(s)) continue;
            kept.push(raw);
        }
        let out = kept.join("\n").replace(/\n+$/, "");
        if (kept.length) out += "\n";
        return out;
    }

    // Feature-name extractor used to seed the constraints prompt with real
    // identifiers the model just emitted (so constraints reference them).
    const FEATURE_NAME_RE = /^\s*(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_\- ]*[A-Za-z0-9_]))\s*$/;
    const NON_FEATURE_TOKENS = ["=>", "<=>", "&", "|", "!", "(", ")"];

    function extractFeatureNamesFromInfill(infill) {
        const seen = new Set();
        const out = [];
        for (const line of infill.split("\n")) {
            const s = line.trim();
            if (!s) continue;
            if (BLOCK_KEYWORDS.has(s) || UVL_HEADERS.has(s)) continue;
            if (s.includes("{") || s.includes("}")) continue;
            const m = FEATURE_NAME_RE.exec(line);
            if (!m) continue;
            const name = ((m[1] || m[2]) || "").trim();
            if (!name) continue;
            if (NON_FEATURE_TOKENS.some((t) => name.includes(t))) continue;
            const key = name.toLowerCase();
            if (!seen.has(key)) { seen.add(key); out.push(name); }
        }
        return out;
    }

    function mergeVariantFeatures(prefix, featuresInfill, suffix) {
        let inf = featuresInfill;
        if (inf && suffix && !inf.endsWith("\n") && !suffix.startsWith("\n")) {
            inf += "\n";
        }
        return prefix + inf + suffix;
    }

    function appendConstraints(lines, constraintsInfill) {
        const stripped = constraintsInfill.replace(/^\n+|\n+$/g, "");
        if (!stripped.trim()) return lines;

        const constraintsIdx = findConstraintsLineOptional(lines);

        // 4-space indent under the constraints section (UVL convention).
        const extra = stripped.split("\n").map((l) =>
            l.trim() ? "    " + l.replace(/\s+$/, "") + "\n" : "\n"
        );

        if (constraintsIdx === null) {
            const out = lines.slice();
            if (out.length > 0 && !out[out.length - 1].endsWith("\n")) {
                out[out.length - 1] += "\n";
            }
            if (out.length > 0 && out[out.length - 1].trim() !== "") {
                out.push("\n");
            }
            out.push("constraints\n");
            return out.concat(extra);
        }

        const head = lines.slice(0, constraintsIdx + 1);
        const tail = lines.slice(constraintsIdx + 1);
        if (tail.length > 0 && !tail[tail.length - 1].endsWith("\n")) {
            tail[tail.length - 1] += "\n";
        }
        return head.concat(tail).concat(extra);
    }

    // ─── Concept-mode: plan (JSON) → UVL deterministic renderer ─────────────
    //
    // Small LLMs fail at whole-model UVL generation because they have to
    // handle tree structure AND UVL syntax AND domain semantics in one pass.
    // We split the problem: the LLM only produces a JSON tree (semantics +
    // structure); a deterministic JS renderer turns that JSON into valid UVL.
    // Flamapy still validates the final UVL as a safety net, but by
    // construction the tree is always well-formed.

    const VALID_GROUP_TYPES = new Set(["mandatory", "optional", "alternative", "or"]);

    // Plans are "find the outermost braces" because small LLMs often wrap
    // JSON in prose or Markdown fences despite being told not to. On top of
    // that, they frequently emit near-JSON: // line comments, /* block */
    // comments, and trailing commas. We try strict parse first, then apply a
    // tolerance pass, then a brace-balancing scan to salvage partial output
    // (e.g. when max_tokens truncates the last closing brace).
    function extractJsonObject(text) {
        if (!text) return null;
        let t = String(text).replace(/```(?:json)?\s*/gi, "").replace(/```/g, "").trim();
        const i = t.indexOf("{");
        const j = t.lastIndexOf("}");
        if (i < 0 || j <= i) return null;

        const outer = t.slice(i, j + 1);

        // 1) Strict parse.
        try { return JSON.parse(outer); } catch (e) { /* fall through */ }

        // 2) Tolerant parse: strip JS-style comments and trailing commas.
        const repaired = outer
            .replace(/\/\*[\s\S]*?\*\//g, "")
            .replace(/(^|[^:])\/\/[^\n]*/g, "$1")
            .replace(/,(\s*[}\]])/g, "$1");
        try { return JSON.parse(repaired); } catch (e) { /* fall through */ }

        // 3) Brace-balancing scan from the first '{'. If the LLM truncated
        // partway through, this recovers the largest balanced prefix.
        const scanned = scanBalancedJson(t.slice(i));
        if (scanned) {
            const scRep = scanned
                .replace(/\/\*[\s\S]*?\*\//g, "")
                .replace(/(^|[^:])\/\/[^\n]*/g, "$1")
                .replace(/,(\s*[}\]])/g, "$1");
            try { return JSON.parse(scRep); } catch (e) { /* give up */ }
        }

        return null;
    }

    function scanBalancedJson(s) {
        let depth = 0;
        let inStr = false;
        let esc = false;
        let end = -1;
        for (let k = 0; k < s.length; k++) {
            const c = s[k];
            if (inStr) {
                if (esc) esc = false;
                else if (c === "\\") esc = true;
                else if (c === '"') inStr = false;
                continue;
            }
            if (c === '"') { inStr = true; continue; }
            if (c === "{") depth++;
            else if (c === "}") {
                depth--;
                if (depth === 0) { end = k; break; }
            }
        }
        return end > 0 ? s.slice(0, end + 1) : null;
    }

    // UVL identifiers allow quoted names with spaces, but quoted names
    // complicate downstream constraint references. Coercing to strict
    // [A-Za-z0-9_] keeps the generated models analyzable without quoting.
    function sanitizeFeatureName(raw) {
        if (raw == null) return null;
        let s = String(raw).trim();
        if (!s) return null;
        s = s.replace(/[\s'\-./]+/g, "_");
        s = s.replace(/[^A-Za-z0-9_]/g, "");
        s = s.replace(/_+/g, "_").replace(/^_|_$/g, "");
        if (!s) return null;
        if (!/^[A-Za-z_]/.test(s)) s = "F_" + s;
        return s;
    }

    function slugifyConcept(concept) {
        const s = String(concept || "").trim().toLowerCase()
            .replace(/[^a-z0-9_]+/g, "_")
            .replace(/_+/g, "_")
            .replace(/^_|_$/g, "")
            .slice(0, 30);
        return s || "concept";
    }

    function finalizeName(raw, usedNames) {
        let name = sanitizeFeatureName(raw);
        if (!name) return null;
        let key = name.toLowerCase();
        if (usedNames.has(key)) {
            let suffix = 2;
            while (usedNames.has((name + "_" + suffix).toLowerCase())) suffix++;
            name = name + "_" + suffix;
            key = name.toLowerCase();
        }
        usedNames.add(key);
        return name;
    }

    function renderPlanToUvl(plan) {
        if (!plan || typeof plan !== "object") {
            throw new Error("plan is not an object");
        }
        const root = sanitizeFeatureName(plan.root);
        if (!root) throw new Error("plan has no valid root feature");
        const usedNames = new Set([root.toLowerCase()]);
        const nameList = [root];
        const lines = ["features", "    " + root];
        renderNodeChildren(plan, 4, lines, usedNames, nameList);
        return { text: lines.join("\n") + "\n", names: nameList };
    }

    // UVL lets a parent hold multiple groups (a mandatory group AND an
    // optional group under the same feature). The JSON schema we ask for
    // carries one `type` per child (relationship to parent), so at render
    // time we bucket siblings by their type and emit one group per bucket,
    // preserving first-occurrence order so the UVL reads in the same
    // conceptual order the LLM laid out.
    function renderNodeChildren(node, parentIndent, lines, usedNames, nameList) {
        const children = Array.isArray(node.children) ? node.children : [];
        if (children.length === 0) return;

        const groups = new Map();
        const orderedTypes = [];
        for (const ch of children) {
            let t = (ch && typeof ch.type === "string") ? ch.type.toLowerCase() : "optional";
            if (!VALID_GROUP_TYPES.has(t)) t = "optional";
            if (!groups.has(t)) {
                groups.set(t, []);
                orderedTypes.push(t);
            }
            groups.get(t).push(ch);
        }

        const groupIndent = parentIndent + 4;
        const childIndent = parentIndent + 8;
        for (const type of orderedTypes) {
            lines.push(" ".repeat(groupIndent) + type);
            for (const kid of groups.get(type)) {
                const name = finalizeName(kid && kid.name, usedNames);
                if (!name) continue;
                lines.push(" ".repeat(childIndent) + name);
                if (nameList) nameList.push(name);
                renderNodeChildren(kid, childIndent, lines, usedNames, nameList);
            }
        }
    }

    // ─── UVL → plan parser (inverse of renderPlanToUvl) ────────────────────
    //
    // Seed mode feeds an existing UVL file through the LLM asking for a
    // semantic variant. Instead of giving the raw text (which wastes
    // prompt space, breaks on attributes/cardinalities, and invites the
    // model to repeat it verbatim), we parse the UVL into the same plan
    // schema concept mode emits — then the LLM receives a compact,
    // unambiguous JSON tree and returns another one of the same shape.
    //
    // The parser is indentation-based: walk feature-section lines, keep a
    // stack of (currentFeature, indent, pendingGroupType). Block keyword
    // lines (mandatory/optional/alternative/or/[n..m]) don't create
    // features; they set the group type applied to the NEXT feature lines
    // more deeply indented under the same parent.

    function countPlanFeatures(plan) {
        let n = plan && plan.root ? 1 : 0;
        (function walk(node) {
            const kids = (node && Array.isArray(node.children)) ? node.children : [];
            for (const k of kids) { n++; walk(k); }
        })(plan);
        return n;
    }

    function parseUvlToPlan(uvlText) {
        if (!uvlText || !uvlText.trim()) throw new Error("empty UVL");
        const rawLines = uvlText.replace(/\t/g, "    ").split("\n");
        const featuresIdx = rawLines.findIndex((l) => l.trim() === "features");
        if (featuresIdx < 0) throw new Error("no 'features' section");
        let endIdx = rawLines.length;
        for (let i = featuresIdx + 1; i < rawLines.length; i++) {
            const s = rawLines[i].trim();
            if (s === "constraints") { endIdx = i; break; }
        }

        // Tokenize: each non-empty line becomes either a feature or a group.
        const items = [];
        for (let i = featuresIdx + 1; i < endIdx; i++) {
            const line = rawLines[i];
            const s = line.trim();
            if (!s) continue;
            const indent = indentLen(line);

            // Group keyword line (optional/mandatory/alternative/or) or
            // bare group cardinality like "[2..5]" which acts like or/and.
            if (BLOCK_KEYWORDS.has(s) || /^\[\s*\d+\s*\.\.\s*\d+\s*\]$/.test(s)) {
                const kw = BLOCK_KEYWORDS.has(s) ? s : "or"; // cardinality → approximate as "or"
                items.push({ kind: "group", indent, keyword: kw });
                continue;
            }

            // Feature line. Strip attribute block and cardinality suffix,
            // unwrap quotes, then validate the remaining identifier.
            let body = s.replace(/\{[^}]*\}/g, "").replace(/\s+cardinality\s+\[[^\]]*\]/i, "").trim();
            const m = body.match(/^"([^"]+)"$|^([A-Za-z_][A-Za-z0-9_\- ]*[A-Za-z0-9_])$/);
            if (!m) continue;
            const name = sanitizeFeatureName(m[1] || m[2]);
            if (!name) continue;
            items.push({ kind: "feature", indent, name });
        }

        if (items.length === 0 || items[0].kind !== "feature") {
            throw new Error("no features under 'features' section");
        }

        const rootItem = items[0];
        const plan = { root: rootItem.name, children: [] };
        const stack = [{ node: plan, indent: rootItem.indent, pendingGroupType: null }];

        for (let i = 1; i < items.length; i++) {
            const it = items[i];
            while (stack.length > 1 && stack[stack.length - 1].indent >= it.indent) {
                stack.pop();
            }
            const top = stack[stack.length - 1];
            if (it.kind === "group") {
                top.pendingGroupType = it.keyword;
            } else {
                const type = top.pendingGroupType || "optional";
                const feature = { name: it.name, type, children: [] };
                if (!Array.isArray(top.node.children)) top.node.children = [];
                top.node.children.push(feature);
                stack.push({ node: feature, indent: it.indent, pendingGroupType: null });
            }
        }

        return plan;
    }

    // ─── Constraints addition for a rendered concept tree ──────────────────
    //
    // Second LLM call after the tree is valid. We ask the model for 1–3 UVL
    // constraint lines referencing the features we emitted, then validate
    // each candidate individually by appending it to the tree and
    // reparsing. Valid ones stick, broken ones get dropped — the tree is
    // never sacrificed for a bad constraint. This keeps concept-mode's
    // "tree always parses" guarantee intact when the toggle is on.
    async function addConstraintsToTree(treeText, featureNames, temperature, maxTokens, seed) {
        let raw;
        try {
            const res = await callWorker("generate", {
                phase: "constraints",
                modelText: treeText,
                newFeatures: featureNames,
                temperature,
                maxTokens: Math.min(Math.max(maxTokens || 0, 220), 400),
                seed,
            });
            raw = res.infill || "";
        } catch (err) {
            return { text: treeText, kept: 0, dropped: 0, error: err.message || String(err) };
        }

        const sanitized = hardSanitizeConstraintsInfill(raw);
        if (!sanitized.trim()) {
            return { text: treeText, kept: 0, dropped: 0 };
        }

        const candidates = sanitized.split("\n").map((l) => l.trim()).filter(Boolean);
        const kept = [];
        const dropped = [];

        for (const c of candidates) {
            const trialLines = appendConstraints(splitKeepEnds(treeText), [...kept, c].join("\n"));
            const trialText = trialLines.join("");
            let verdict;
            try { verdict = await validateCandidate(trialText); }
            catch (e) { verdict = { ok: false, error: String(e.message || e) }; }
            if (verdict.ok) kept.push(c);
            else dropped.push(c);
        }

        if (kept.length === 0) {
            return { text: treeText, kept: 0, dropped: dropped.length };
        }

        const finalLines = appendConstraints(splitKeepEnds(treeText), kept.join("\n"));
        return { text: finalLines.join(""), kept: kept.length, dropped: dropped.length };
    }

    // ─── Pyodide validation (flamapy) ────────────────────────────────────────
    //
    // scripts.js already boots Pyodide and installs the flamapy wheels; we
    // just append a small helper function and call it per candidate. We keep
    // the full error as a string so the UI can show a human-readable reason
    // for every invalid model.

    // Mirrors the JS organic heuristic so we can compute it over parsed
    // feature names instead of regex-extracting from raw text. Thresholds are
    // the exact ones from llm_splc'26v2.py.
    // Avoid DiscoverMetamodels: it imports every flamapy plugin, including
    // pysat_metamodel which needs python-sat (not loaded in Pyodide). Using
    // UVLReader directly transforms a .uvl file into a FeatureModel without
    // touching the SAT-based plugins.
    const VALIDATION_PY = [
        "import tempfile, os, json, re",
        "from flamapy.metamodels.fm_metamodel.transformations.uvl_reader import UVLReader as _UVLReader",
        "",
        "_ORGANIC_MIN_FEATURES = 10",
        "_ORGANIC_MIN_RATIO = 0.6",
        "_GENERIC_PATTERN = re.compile(r'^(f\\d+|x\\d+|var\\d+|feature\\d+|[a-z]{1,3}\\d*(_[a-z]{1,3}\\d*)*)$', re.IGNORECASE)",
        "",
        "def _llm_informative(name: str) -> bool:",
        "    s = str(name).strip()",
        "    if len(s) < 5: return False",
        "    if _GENERIC_PATTERN.match(s): return False",
        "    if not re.search(r'[A-Za-z]{3,}', s): return False",
        "    return True",
        "",
        "def _llm_feature_to_name(f) -> str:",
        "    for attr in ('name', 'id', 'identifier'):",
        "        if hasattr(f, attr):",
        "            v = getattr(f, attr)",
        "            try: v = v() if callable(v) else v",
        "            except Exception: pass",
        "            if isinstance(v, str) and v.strip():",
        "                return v.strip()",
        "    for meth in ('get_name', 'get_id', 'get_identifier'):",
        "        if hasattr(f, meth) and callable(getattr(f, meth)):",
        "            try:",
        "                v = getattr(f, meth)()",
        "                if isinstance(v, str) and v.strip(): return v.strip()",
        "            except Exception: pass",
        "    return str(f).strip()",
        "",
        "def _llm_organic(fm):",
        "    try: names = [_llm_feature_to_name(f) for f in fm.get_features()]",
        "    except Exception: return {'organic': False, 'total': 0, 'informative': 0, 'ratio': 0.0, 'reason': 'cannot enumerate features'}",
        "    names = [n for n in names if n]",
        "    total = len(names)",
        "    if total == 0: return {'organic': False, 'total': 0, 'informative': 0, 'ratio': 0.0, 'reason': 'no features'}",
        "    informative = sum(1 for n in names if _llm_informative(n))",
        "    ratio = informative / total",
        "    if total < _ORGANIC_MIN_FEATURES:",
        "        return {'organic': False, 'total': total, 'informative': informative, 'ratio': ratio, 'reason': f'only {total} features'}",
        "    if ratio < _ORGANIC_MIN_RATIO:",
        "        return {'organic': False, 'total': total, 'informative': informative, 'ratio': ratio, 'reason': f'{int(ratio*100)}% informative names'}",
        "    return {'organic': True, 'total': total, 'informative': informative, 'ratio': ratio, 'reason': ''}",
        "",
        "def _llm_validate(text):",
        "    with tempfile.NamedTemporaryFile(mode='w', suffix='.uvl', delete=False, encoding='utf-8') as f:",
        "        f.write(text); path = f.name",
        "    try:",
        "        try:",
        "            fm = _UVLReader(path).transform()",
        "            feats = 0",
        "            try: feats = len(list(fm.get_features()))",
        "            except Exception: feats = 0",
        "            ctcs = 0",
        "            try: ctcs = len(fm.ctcs)",
        "            except Exception: ctcs = 0",
        "            org = _llm_organic(fm)",
        "            return json.dumps({'ok': True, 'features': feats, 'constraints': ctcs, 'organic': org})",
        "        except Exception as e:",
        "            return json.dumps({'ok': False, 'error': str(e)})",
        "    finally:",
        "        try: os.unlink(path)",
        "        except Exception: pass",
        "",
    ].join("\n");

    let validatorReady = null;
    async function ensureValidator() {
        if (validatorReady) return validatorReady;
        if (!window.generatorRuntime) {
            throw new Error("Generator runtime not available. Reload the page.");
        }
        validatorReady = (async () => {
            const pyodide = await window.generatorRuntime.ready();
            await pyodide.runPythonAsync(VALIDATION_PY);
            return pyodide;
        })();
        return validatorReady;
    }

    async function validateCandidate(text) {
        const pyodide = await ensureValidator();
        pyodide.globals.set("_llm_candidate", text);
        const raw = await pyodide.runPythonAsync("_llm_validate(_llm_candidate)");
        return JSON.parse(raw);
    }

    // ─── Model table ────────────────────────────────────────────────────────
    //
    // Renders MODELS as a table with per-row status and actions. Replaces
    // the old single-select dropdown so users can see at a glance which
    // weights are already in IndexedDB (no re-download) vs. which would
    // need a fresh download, and can delete cached models to reclaim disk
    // when they're done experimenting.

    function renderModelTable() {
        const tbody = $("llm_model_rows");
        if (!tbody) return;
        tbody.innerHTML = "";
        for (const m of MODELS) {
            const tr = document.createElement("tr");
            tr.dataset.modelId = m.id;

            const tdName = document.createElement("td");
            tdName.className = "ps-5";
            tdName.innerHTML =
                '<div class="fw-semibold text-gray-900">' + escapeHtml(m.name) + "</div>" +
                '<div class="text-muted fs-8">' + escapeHtml(m.note || "") + "</div>";
            tr.appendChild(tdName);

            const tdSize = document.createElement("td");
            tdSize.textContent = m.size || "—";
            tr.appendChild(tdSize);

            const tdStatus = document.createElement("td");
            tdStatus.className = "llm-model-status";
            tr.appendChild(tdStatus);

            const tdActions = document.createElement("td");
            tdActions.className = "text-end pe-5 llm-model-actions";
            tr.appendChild(tdActions);

            tbody.appendChild(tr);
        }
        updateAllRows();
    }

    function updateAllRows() {
        const tbody = $("llm_model_rows");
        if (!tbody) return;
        tbody.querySelectorAll("tr").forEach(updateRow);
    }

    function updateRow(tr) {
        const id = tr.dataset.modelId;
        const cached = !!cacheStatus[id];
        const active = currentLoadedModel === id;
        const thisBusy = busyModel === id;
        const anyBusy = !!busyModel;

        const statusEl = tr.querySelector(".llm-model-status");
        if (statusEl) {
            let badge;
            if (active) {
                badge = '<span class="badge badge-light-success">Active</span>';
            } else if (thisBusy) {
                badge = '<span class="badge badge-light-primary">Working…</span>';
            } else if (cached) {
                badge = '<span class="badge badge-light-info">Cached</span>';
            } else {
                badge = '<span class="badge badge-light-secondary">Not cached</span>';
            }
            statusEl.innerHTML = badge;
        }

        const actionsEl = tr.querySelector(".llm-model-actions");
        if (!actionsEl) return;
        actionsEl.innerHTML = "";

        if (thisBusy) {
            actionsEl.innerHTML = '<span class="text-muted fs-7">busy…</span>';
            return;
        }

        // Actions column is narrow — icon-only compact buttons keep each
        // row to a single line instead of wrapping "Download + load" to two.
        // Full labels live in title/aria-label so hover and screen readers
        // still spell them out.
        if (!active) {
            const load = document.createElement("button");
            load.type = "button";
            load.className = "btn btn-sm btn-icon " + (cached ? "btn-light-primary" : "btn-primary");
            const loadLabel = cached ? "Load" : "Download + load";
            load.title = loadLabel;
            load.setAttribute("aria-label", loadLabel);
            load.innerHTML = cached
                ? '<i class="ki-duotone ki-check fs-3"><span class="path1"></span><span class="path2"></span></i>'
                : '<i class="ki-duotone ki-cloud-download fs-3"><span class="path1"></span><span class="path2"></span></i>';
            load.disabled = anyBusy || webGpuReady === false;
            load.addEventListener("click", () => loadModel(id));
            actionsEl.appendChild(load);
        }

        if (cached || active) {
            const del = document.createElement("button");
            del.type = "button";
            del.className = "btn btn-sm btn-icon btn-light-danger ms-2";
            del.title = "Delete cached weights";
            del.setAttribute("aria-label", "Delete cached weights");
            del.innerHTML = '<i class="ki-duotone ki-trash fs-3"><span class="path1"></span><span class="path2"></span><span class="path3"></span><span class="path4"></span><span class="path5"></span></i>';
            del.disabled = anyBusy;
            del.addEventListener("click", () => deleteModel(id));
            actionsEl.appendChild(del);
        }
    }

    async function refreshCacheStatus() {
        try {
            const ids = MODELS.map((m) => m.id);
            const status = await callWorker("checkCache", { modelIds: ids });
            cacheStatus = status || {};
        } catch (err) {
            log("Cache status check failed: " + (err.message || err), "warn");
        }
        updateAllRows();
    }

    async function loadModel(modelId) {
        if (busyModel) return;
        busyModel = modelId;
        updateAllRows();
        setProgress(0, "Preparing model…");

        const gpuOk = await reportWebGpuAdapter();
        if (!gpuOk) {
            busyModel = null;
            updateAllRows();
            setProgress(0, "WebGPU required");
            return;
        }

        log("Loading model " + modelId + (cacheStatus[modelId] ? " from cache…" : " — first time downloads the weights."), "info");
        try {
            await callWorker("init", { model: modelId });
            currentLoadedModel = modelId;
            cacheStatus[modelId] = true;
            $("llm_generate_btn").disabled = false;
            log("Model ready: " + modelId, "success");
            if (/-0\.5B-/i.test(modelId)) {
                log("Note: 0.5B is very small. Expect lower JSON success rate and more retries on complex domains.", "warn");
            }
        } catch (err) {
            log("Failed to load: " + (err.message || err), "error");
        } finally {
            busyModel = null;
            updateAllRows();
        }
    }

    async function deleteModel(modelId) {
        if (busyModel) return;
        // Using confirm() here is deliberate: the hub uses SweetAlert2
        // elsewhere but importing it into this page for one dialog is
        // disproportionate, and browser confirm is clearer for a destructive
        // IndexedDB wipe than a custom modal.
        if (!confirm("Delete cached weights for " + modelId + "?\n\nYou'll need to re-download next time. The current tab's inference session will be closed.")) {
            return;
        }
        busyModel = modelId;
        updateAllRows();
        log("Deleting cached weights for " + modelId + "…", "info");
        try {
            const res = await callWorker("deleteCache", { modelId });
            cacheStatus[modelId] = false;
            if (currentLoadedModel === modelId) {
                currentLoadedModel = null;
                $("llm_generate_btn").disabled = true;
            }
            if (res && res.deleted) {
                log("Cache deleted for " + modelId, "success");
            } else {
                log("Cache delete reported: " + (res && res.reason || "no-op"), "warn");
            }
        } catch (err) {
            log("Delete failed: " + (err.message || err), "error");
        } finally {
            busyModel = null;
            updateAllRows();
        }
    }

    // ─── Browser detection (best-effort, for WebGPU guidance only) ────────────
    //
    // We sniff the UA only to tailor the *instructions* shown in the WebGPU
    // banner — the real support check is still navigator.gpu + requestAdapter.
    // If the UA is spoofed or unrecognised we just fall back to generic advice.
    function detectBrowser() {
        const ua = (typeof navigator !== "undefined" && navigator.userAgent) || "";
        const uaData = (typeof navigator !== "undefined" && navigator.userAgentData) || null;
        const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(ua) ||
            (uaData && uaData.mobile === true);

        // userAgentData is the clean path when available (Chromium on desktop).
        if (uaData && Array.isArray(uaData.brands)) {
            const brands = uaData.brands.filter(
                (b) => b && b.brand && !/not.?a.?brand/i.test(b.brand)
            );
            const edge = brands.find((b) => /edge/i.test(b.brand));
            if (edge) {
                return { name: "Edge", version: parseInt(edge.version, 10) || null, isMobile, raw: ua };
            }
            const opera = brands.find((b) => /opera|opr/i.test(b.brand));
            if (opera) {
                return { name: "Opera", version: parseInt(opera.version, 10) || null, isMobile, raw: ua };
            }
            const brave = brands.find((b) => /brave/i.test(b.brand));
            if (brave) {
                return { name: "Brave", version: parseInt(brave.version, 10) || null, isMobile, raw: ua };
            }
            const chrome = brands.find((b) => /chrome/i.test(b.brand));
            if (chrome) {
                return { name: "Chrome", version: parseInt(chrome.version, 10) || null, isMobile, raw: ua };
            }
        }

        // UA-string fallbacks. Order matters: Edge/Opera/Brave inherit
        // "Chrome/xx" in their UA, so match them before plain Chrome.
        let m;
        if ((m = ua.match(/Edg\/(\d+)/))) return { name: "Edge", version: parseInt(m[1], 10), isMobile, raw: ua };
        if ((m = ua.match(/OPR\/(\d+)/))) return { name: "Opera", version: parseInt(m[1], 10), isMobile, raw: ua };
        if (/Firefox\//.test(ua)) {
            m = ua.match(/Firefox\/(\d+)/);
            const isNightly = /Nightly/i.test(ua);
            return { name: isNightly ? "Firefox Nightly" : "Firefox", version: m ? parseInt(m[1], 10) : null, isMobile, raw: ua };
        }
        if (/CriOS\//.test(ua)) { // Chrome on iOS — same WebKit engine as Safari
            m = ua.match(/CriOS\/(\d+)/);
            return { name: "Chrome on iOS", version: m ? parseInt(m[1], 10) : null, isMobile: true, raw: ua };
        }
        if (/Chrome\//.test(ua)) {
            m = ua.match(/Chrome\/(\d+)/);
            return { name: "Chrome", version: m ? parseInt(m[1], 10) : null, isMobile, raw: ua };
        }
        if (/Safari\//.test(ua) && /Version\//.test(ua)) {
            m = ua.match(/Version\/(\d+)/);
            return { name: "Safari", version: m ? parseInt(m[1], 10) : null, isMobile, raw: ua };
        }
        return { name: "your browser", version: null, isMobile, raw: ua };
    }

    // Produces { summary, steps[] } explaining *why* WebGPU is unavailable and
    // how the user can fix it, tailored to their browser. reason is either
    // "missing" (navigator.gpu absent) or "no-adapter" (API exists but
    // requestAdapter() returned null — usually a disabled GPU flag or
    // blocklisted driver).
    function webGpuGuidance(reason) {
        const b = detectBrowser();
        const label = b.version ? `${b.name} ${b.version}` : b.name;
        const steps = [];
        let summary = "";

        const tooOldChromium = (b.name === "Chrome" || b.name === "Edge" || b.name === "Opera" || b.name === "Brave")
            && typeof b.version === "number" && b.version < 113;

        if (b.name === "Chrome on iOS") {
            summary = `You're on ${label}. On iOS, every browser uses WebKit, and WebGPU only ships on Safari 18+ (iOS 18+).`;
            steps.push("Open this page in Safari on iOS 18 or newer.");
            steps.push("Older iPhones/iPads may not be supported even with iOS 18 — small LLMs need several hundred MB of GPU memory.");
        } else if (b.name === "Safari") {
            if (typeof b.version === "number" && b.version >= 18) {
                summary = `You're on ${label}, which ships WebGPU — but no GPU adapter could be acquired.`;
                steps.push("Check that your macOS/iOS version is fully up to date.");
                steps.push("Try closing other tabs that may be using the GPU and reload this page.");
                steps.push("If the problem persists, test in Chrome or Edge 113+ to rule out a Safari-specific driver issue.");
            } else if (typeof b.version === "number" && b.version === 17) {
                summary = `You're on ${label}. WebGPU is available but behind a feature flag in Safari 17.`;
                steps.push("Open Develop → Feature Flags → enable WebGPU (requires the Develop menu: Safari → Settings → Advanced → “Show features for web developers”).");
                steps.push("Reload this page after enabling the flag.");
                steps.push("Alternatively, upgrade to Safari 18 (macOS 15 / iOS 18) where WebGPU is enabled by default.");
            } else {
                summary = `You're on ${label}. WebGPU ships enabled by default from Safari 18 (macOS 15 / iOS 18).`;
                steps.push("Upgrade to Safari 18 or newer.");
                steps.push("Or use Chrome / Edge 113+ on the same machine.");
            }
        } else if (b.name === "Firefox Nightly") {
            summary = `You're on ${label}. Firefox Nightly supports WebGPU but it is gated by a preference.`;
            steps.push("Open about:config and set dom.webgpu.enabled to true.");
            steps.push("Restart Firefox Nightly and reload this page.");
        } else if (b.name === "Firefox") {
            summary = `You're on ${label}. Stable Firefox doesn't enable WebGPU yet.`;
            steps.push("Install Firefox Nightly and enable dom.webgpu.enabled in about:config.");
            steps.push("Or use Chrome / Edge 113+ as a quick alternative.");
        } else if (tooOldChromium) {
            summary = `You're on ${label}. WebGPU requires ${b.name} 113 or newer.`;
            steps.push(`Update ${b.name} to the latest version and reload this page.`);
        } else if (b.name === "Chrome" || b.name === "Edge" || b.name === "Opera" || b.name === "Brave") {
            if (reason === "missing") {
                summary = `You're on ${label}. WebGPU should be available but navigator.gpu is not exposed — this usually means an enterprise policy or an extension is disabling it.`;
                steps.push("Open a private/incognito window with extensions disabled and reload this page.");
                steps.push("On managed devices, check with IT — policies like HardwareAccelerationModeEnabled can turn WebGPU off.");
            } else {
                summary = `You're on ${label}. The WebGPU API is present but no GPU adapter could be acquired — hardware acceleration is probably off, or your GPU/driver is blocklisted.`;
                const flagsUrl = b.name === "Edge" ? "edge://flags/#enable-unsafe-webgpu"
                    : b.name === "Opera" ? "opera://flags/#enable-unsafe-webgpu"
                    : b.name === "Brave" ? "brave://flags/#enable-unsafe-webgpu"
                    : "chrome://flags/#enable-unsafe-webgpu";
                const settingsUrl = b.name === "Edge" ? "edge://settings/system"
                    : b.name === "Opera" ? "opera://settings/system"
                    : b.name === "Brave" ? "brave://settings/system"
                    : "chrome://settings/system";
                steps.push(`Enable “Use graphics acceleration when available” at ${settingsUrl} and restart the browser.`);
                steps.push(`If still failing, set ${flagsUrl} to Enabled and restart — this overrides the driver blocklist.`);
                steps.push("Make sure the OS-level GPU driver is up to date.");
            }
        } else if (b.isMobile) {
            summary = `You're on a mobile browser (${label}). WebGPU support on mobile is limited and most phones don't have enough GPU memory for these models.`;
            steps.push("Open this page on a desktop browser: Chrome / Edge 113+ or Safari 18+.");
        } else {
            summary = `WebGPU is not available in ${label}.`;
            steps.push("Use a recent Chrome or Edge (113+), or Safari 18+ on macOS 15 / iOS 18.");
            steps.push("Firefox users: try Firefox Nightly with dom.webgpu.enabled = true in about:config.");
        }

        return { summary, steps, browser: b };
    }

    // Visibility is toggled via d-none/d-flex class swap (both ship with
    // !important in Bootstrap, but only one is applied at a time). Using
    // inline `style.display` would lose to .d-flex's !important and leave
    // the banner permanently visible.
    function showWebGpuBanner(reason) {
        const banner = $("llm_webgpu_banner");
        if (!banner) return;
        const { summary, steps } = webGpuGuidance(reason);
        const sumEl = $("llm_webgpu_banner_summary");
        const stepsEl = $("llm_webgpu_banner_steps");
        if (sumEl) sumEl.textContent = summary;
        if (stepsEl) {
            stepsEl.innerHTML = "";
            if (steps.length) {
                const ol = document.createElement("ol");
                ol.className = "mb-0 ps-4";
                steps.forEach((s) => {
                    const li = document.createElement("li");
                    li.className = "mb-1";
                    li.textContent = s;
                    ol.appendChild(li);
                });
                stepsEl.appendChild(ol);
            }
        }
        banner.classList.remove("d-none");
        banner.classList.add("d-flex");
    }

    function hideWebGpuBanner() {
        const banner = $("llm_webgpu_banner");
        if (!banner) return;
        banner.classList.remove("d-flex");
        banner.classList.add("d-none");
    }

    // Gates UI elements that are meaningless without WebGPU (model table
    // rows' Load/Download buttons, Generate button). We leave the table
    // visible so the user still sees what's on offer once they fix it.
    // The flag is also honored by updateRow() so subsequent re-renders
    // (cache refresh, etc.) don't re-enable the Load buttons.
    function setUiWebGpuEnabled(enabled) {
        webGpuReady = enabled;
        if (!enabled) {
            const genBtn = $("llm_generate_btn");
            if (genBtn) genBtn.disabled = true;
        }
        updateAllRows();
    }

    // ─── WebGPU probe ────────────────────────────────────────────────────────
    //
    // Returns true if WebGPU is available and a GPU adapter can be acquired.
    // Also logs the adapter's reported name so the user can tell whether
    // they are running on an integrated GPU (slow), a discrete GPU (fast),
    // or some fallback path. On Chrome/Edge this usually returns a real
    // vendor name; on Safari 18+ the name is anonymised ("Apple GPU").
    //
    // Side-effect: shows/hides the diagnostic banner based on the outcome,
    // so the same function works for the on-load probe and the per-click
    // guard in loadModel().
    //
    // Two safeties layered on top of the raw probe:
    //
    //  - Coalesce concurrent calls. init() fires a probe and the first
    //    loadModel() click fires another; without this they race and the
    //    last-to-finish wins the UI state, which has caused false
    //    "WebGPU required" banners to appear even after the model had
    //    already loaded successfully.
    //  - Cache the success outcome. Once WebGPU is confirmed working we
    //    trust it for the rest of the session — a transient adapter
    //    failure (driver briefly busy, another tab hogging the GPU)
    //    must not rip the UI out from under a user who already has
    //    models loaded. The Re-check button bypasses the cache.
    let webGpuProbePromise = null;

    async function reportWebGpuAdapter(options) {
        const force = !!(options && options.force);
        if (!force && webGpuReady === true) return true;
        if (webGpuProbePromise) return webGpuProbePromise;
        webGpuProbePromise = (async () => {
            try {
                return await runWebGpuProbe();
            } finally {
                webGpuProbePromise = null;
            }
        })();
        return webGpuProbePromise;
    }

    async function runWebGpuProbe() {
        if (typeof navigator === "undefined" || !navigator.gpu) {
            log("WebGPU not available in this browser. WebLLM requires WebGPU — " +
                "use a recent Chrome, Edge, or Safari 18+.", "error");
            showWebGpuBanner("missing");
            setUiWebGpuEnabled(false);
            return false;
        }
        try {
            const adapter = await navigator.gpu.requestAdapter();
            if (!adapter) {
                log("WebGPU is enabled but no GPU adapter could be acquired. " +
                    "Check the browser's GPU acceleration settings.", "error");
                showWebGpuBanner("no-adapter");
                setUiWebGpuEnabled(false);
                return false;
            }
            let name = "unknown";
            try {
                if (typeof adapter.requestAdapterInfo === "function") {
                    const info = await adapter.requestAdapterInfo();
                    name = [info.vendor, info.architecture, info.description]
                        .filter(Boolean).join(" ").trim() || "anonymous WebGPU adapter";
                } else if (adapter.info) {
                    // Newer browsers expose `adapter.info` synchronously.
                    const info = adapter.info;
                    name = [info.vendor, info.architecture, info.description]
                        .filter(Boolean).join(" ").trim() || "anonymous WebGPU adapter";
                }
            } catch (_) { /* non-fatal */ }
            log("WebGPU adapter: " + name, "success");
            hideWebGpuBanner();
            setUiWebGpuEnabled(true);
            return true;
        } catch (err) {
            log("WebGPU probe failed: " + (err.message || err), "error");
            showWebGpuBanner("no-adapter");
            setUiWebGpuEnabled(false);
            return false;
        }
    }

    // ─── WebLLM worker wrapper ───────────────────────────────────────────────

    let worker = null;
    let nextMsgId = 1;
    const pending = new Map();

    function ensureWorker() {
        if (worker) return worker;
        // Module worker: enables `import` inside the worker file itself so
        // it can pull WebLLM from esm.run on demand.
        worker = new Worker(
            "/generator/js/llm-worker.js",
            { type: "module" }
        );
        worker.onmessage = (ev) => {
            const data = ev.data || {};
            if (data.type === "progress") {
                const pct = Math.round((data.report.progress || 0) * 100);
                setProgress(pct, data.report.text || ("Downloading model… " + pct + "%"));
                return;
            }
            if (data.type === "ready") {
                setProgress(100, "Model ready: " + data.model);
                return;
            }
            if (data.id && pending.has(data.id)) {
                const { resolve, reject } = pending.get(data.id);
                pending.delete(data.id);
                if (data.ok) resolve(data.result);
                else reject(new Error(data.error || "worker error"));
            }
        };
        worker.onerror = (err) => {
            log("Worker error: " + (err.message || err), "error");
        };
        return worker;
    }

    function callWorker(action, payload) {
        const w = ensureWorker();
        const id = nextMsgId++;
        return new Promise((resolve, reject) => {
            pending.set(id, { resolve, reject });
            w.postMessage({ id, action, payload });
        });
    }

    // ─── Generate a batch of variants ────────────────────────────────────────
    //
    // Mirrors the random generator's step 6: one "live log" row per variant,
    // valid/invalid badge, feature/constraint counts, one "View" button to
    // open the full UVL in a modal.

    let generatedVariants = [];

    // Stop button state. The single #llm_generate_btn plays double duty:
    // while idle it starts a generation run, while busy it requests a stop.
    // `cancelRequested` is polled at safe points in the generation loops
    // (between variants, between retries, before the constraints phase)
    // and an extra `interrupt` worker call cuts the current LLM completion
    // short so the user doesn't have to wait for in-flight tokens.
    let isGenerating = false;
    let cancelRequested = false;

    function setGenButtonMode(mode) {
        const btn = $("llm_generate_btn");
        if (!btn) return;
        btn.classList.remove("btn-primary", "btn-light-danger");
        btn.disabled = false;
        if (mode === "generating") {
            btn.classList.add("btn-light-danger");
            btn.innerHTML =
                '<i class="ki-duotone ki-cross-square fs-2 me-2"><span class="path1"></span><span class="path2"></span></i>' +
                "Stop generation";
        } else if (mode === "stopping") {
            btn.classList.add("btn-light-danger");
            btn.disabled = true;
            btn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-2"></span>Stopping…';
        } else {
            btn.classList.add("btn-primary");
            btn.innerHTML =
                '<i class="ki-duotone ki-rocket fs-2 me-2"><span class="path1"></span><span class="path2"></span></i>' +
                "Generate variants";
        }
    }

    async function requestStop() {
        if (!isGenerating || cancelRequested) return;
        cancelRequested = true;
        setGenButtonMode("stopping");
        log("Stop requested — cutting current LLM call and halting further variants.", "warn");
        try { await callWorker("interrupt", {}); }
        catch (_) { /* best-effort; the loop-level cancelRequested check still fires */ }
    }

    // MVP generation loop: features-only.
    //
    // The v2 notebook (llm_splc'26v2.py) runs a two-phase pipeline (features
    // then constraints) but it does so against GPT-4o/5, Gemini 2.5 Pro, etc.
    // Small in-browser LLMs (Llama 1B/3B, Phi 3.5) collapse into token loops
    // far too often for the constraints phase to be worth the extra latency.
    // We keep the structural insertion and validation-with-retry, but skip
    // constraints entirely. A valid feature-only variant is a usable result.
    const MAX_RETRIES_FEATURES = 2;
    const MAX_RETRIES_PLAN = 2;

    function getMode() {
        const r = document.querySelector('input[name="llm_mode"]:checked');
        return r ? r.value : "seed";
    }

    async function generate() {
        // Single-entry guard so double-clicks don't kick off a second run.
        if (isGenerating) { await requestStop(); return; }
        isGenerating = true;
        cancelRequested = false;
        setGenButtonMode("generating");
        try {
            if (getMode() === "concept") await generateFromConcept();
            else                         await generateFromSeed();
        } finally {
            isGenerating = false;
            cancelRequested = false;
            setGenButtonMode("idle");
        }
    }

    // Seed mode (plan-diff): parse the seed UVL into a plan JSON, then ask
    // the LLM for a semantic VARIANT of that plan. The variant is still a
    // JSON tree, which we render deterministically to valid UVL — same
    // pipeline as concept mode, so the tree is always syntactically valid.
    //
    // This replaces the old "structural infill" approach where we spliced
    // a few LLM-generated feature lines into a random block of the seed.
    // That approach never saw the whole seed, so insertions read as
    // tacked-on; here the LLM gets the full structure in one shot.
    async function generateFromSeed() {
        const seedText = $("llm_seed").value;
        if (!seedText.trim()) {
            log("Paste a seed UVL or pick one from the hub first.", "error");
            return;
        }
        const seedName = $("llm_seed_name").value || "seed.uvl";
        const n = Math.max(1, Math.min(20, parseInt($("llm_n_variants").value, 10) || 5));
        const temperature = Math.max(0, Math.min(2, parseFloat($("llm_temperature").value) || 0.2));
        const maxTokens = Math.max(32, Math.min(2048, parseInt($("llm_max_tokens").value, 10) || 600));
        const withConstraints = !!($("llm_include_constraints") && $("llm_include_constraints").checked);

        if (!currentLoadedModel) {
            log("Load a model first (see the Models table).", "error");
            return;
        }

        try {
            await ensureValidator();
            const modelId = currentLoadedModel;
            log("Using model: " + modelId, "info");

            // Parse the seed UVL into a plan tree so the LLM never has to
            // look at raw UVL syntax.
            let seedPlan;
            try {
                seedPlan = parseUvlToPlan(seedText);
            } catch (err) {
                log("Cannot parse seed UVL: " + (err.message || err), "error");
                return;
            }
            const seedSize = countPlanFeatures(seedPlan);
            log("Seed parsed: root='" + seedPlan.root + "' · " + seedSize + " features", "info");
            if (seedSize > 30) {
                log("Seed has " + seedSize + " features — prompt is large. Consider trimming the seed or using a 7B model.", "warn");
            }

            const baseName = seedName.replace(/\.uvl$/i, "");
            generatedVariants = [];
            $("llm_results").innerHTML = "";
            $("llm_download_btn").disabled = true;

            for (let i = 1; i <= n; i++) {
                if (cancelRequested) { log("Stopped before variant " + i + ".", "warn"); break; }
                const seedBase = Date.now() + i;
                setProgress((i - 1) / n * 100, "Generating " + i + " / " + n + "…");
                log("▶ Variant " + i + "/" + n, "info");

                let plan = null;
                let variantText = "";
                let featureNames = [];
                let verdict = null;
                for (let attempt = 0; attempt <= MAX_RETRIES_PLAN; attempt++) {
                    if (cancelRequested) break;
                    log("  → variant LLM call (attempt " + (attempt + 1) + ")…", "info");
                    const t0 = performance.now();
                    let raw;
                    try {
                        const res = await callWorker("generate", {
                            phase: "variant",
                            plan: seedPlan,
                            targetFeatures: Math.max(5, Math.min(20, seedSize)),
                            temperature, maxTokens,
                            seed: seedBase * 1000 + attempt,
                        });
                        raw = res.infill || "";
                    } catch (err) {
                        log("  ✗ LLM error: " + (err.message || err), "error");
                        break;
                    }
                    const dt = Math.round(performance.now() - t0);
                    log("  ← response in " + dt + " ms, " + raw.length + " chars raw", "info");

                    if (cancelRequested) break;

                    plan = extractJsonObject(raw);
                    if (!plan) {
                        if (raw.trim().length < 20) {
                            log("  ↻ empty response, retrying", "warn");
                        } else {
                            const preview = raw.replace(/\s+/g, " ").slice(0, 220);
                            log("  ↻ JSON parse failed. Raw: " + preview + (raw.length > 220 ? "…" : ""), "warn");
                        }
                        continue;
                    }
                    let rendered;
                    try {
                        rendered = renderPlanToUvl(plan);
                    } catch (err) {
                        log("  ↻ plan malformed (" + (err.message || err) + "), retrying", "warn");
                        plan = null;
                        continue;
                    }
                    variantText = rendered.text;
                    featureNames = rendered.names;
                    try { verdict = await validateCandidate(variantText); }
                    catch (e) { verdict = { ok: false, error: String(e.message || e) }; }
                    if (verdict.ok) break;
                    log("  ↻ UVL invalid: " + (verdict.error || "").split("\n")[0].slice(0, 80) + ", retrying", "warn");
                }

                if (cancelRequested) break;

                if (!plan || !verdict || !verdict.ok) {
                    log("  ✗ variant " + i + ": no valid plan after " + (MAX_RETRIES_PLAN + 1) + " tries", "error");
                    continue;
                }

                if (withConstraints && featureNames.length > 0 && !cancelRequested) {
                    log("  → constraints LLM call…", "info");
                    const tc0 = performance.now();
                    const ctc = await addConstraintsToTree(
                        variantText, featureNames, temperature, maxTokens, seedBase * 2000
                    );
                    const tcDt = Math.round(performance.now() - tc0);
                    if (ctc.error) {
                        log("  ⚠ constraints step failed in " + tcDt + " ms: " + ctc.error + " (tree only)", "warn");
                    } else if (ctc.kept > 0) {
                        variantText = ctc.text;
                        try { verdict = await validateCandidate(variantText); } catch (_) { /* tree was valid */ }
                        log("  ← constraints done in " + tcDt + " ms: +" + ctc.kept + " kept / " + ctc.dropped + " dropped", "success");
                    } else {
                        log("  ← constraints done in " + tcDt + " ms: none kept (" + ctc.dropped + " dropped)", "warn");
                    }
                }

                const filename = i + "_" + baseName + ".uvl";
                generatedVariants.push({ filename, content: variantText, verdict });
                renderVariantRow(filename, variantText, verdict);
                log("  ✓ " + filename + " valid · " + verdict.features + "f / " + verdict.constraints + "c", "success");
            }
            setProgress(100, "Done");
            const validCount = generatedVariants.filter((v) => v.verdict && v.verdict.ok).length;
            log("Generated " + generatedVariants.length + " variants, " + validCount + " valid.", "info");
            if (validCount === 0) {
                log("Tip: seed mode works best with 3B or 7B coders. If the seed is very large, try trimming it or switch to the 7B model.", "info");
            }
            if (generatedVariants.length > 0) $("llm_download_btn").disabled = false;
        } catch (err) {
            log("Generation error: " + (err && err.message || err), "error");
        }
    }

    // Concept-mode loop: one LLM plan call per variant, parse JSON, render
    // to UVL, validate with flamapy. Retries the plan step on JSON or render
    // failure, but the render is deterministic so a valid plan always yields
    // valid UVL — retries mostly catch LLM outputs that are not JSON at all.
    async function generateFromConcept() {
        const concept = $("llm_concept").value.trim();
        if (!concept) {
            log("Enter a concept or domain name first.", "error");
            return;
        }
        const targetFeatures = Math.max(5, Math.min(60, parseInt($("llm_concept_target_features").value, 10) || 15));
        const maxDepth = Math.max(2, Math.min(5, parseInt($("llm_concept_max_depth").value, 10) || 3));
        const n = Math.max(1, Math.min(20, parseInt($("llm_n_variants").value, 10) || 5));
        const temperature = Math.max(0, Math.min(2, parseFloat($("llm_temperature").value) || 0.3));
        const maxTokens = Math.max(32, Math.min(2048, parseInt($("llm_max_tokens").value, 10) || 800));
        const withConstraints = !!($("llm_include_constraints") && $("llm_include_constraints").checked);

        if (maxTokens < 400) {
            log("Concept mode usually needs 600+ max tokens for a usable plan; current: " + maxTokens, "warn");
        }

        if (!currentLoadedModel) {
            log("Load a model first (see the Models table).", "error");
            return;
        }

        // Button state (idle/generating/stopping) is owned by generate().
        try {
            await ensureValidator();
            const modelId = currentLoadedModel;
            log("Using model: " + modelId + " · concept: " + concept, "info");

            const slug = slugifyConcept(concept);
            generatedVariants = [];
            $("llm_results").innerHTML = "";
            $("llm_download_btn").disabled = true;

            for (let i = 1; i <= n; i++) {
                if (cancelRequested) { log("Stopped before variant " + i + ".", "warn"); break; }
                const seedBase = Date.now() + i;
                setProgress((i - 1) / n * 100, "Generating " + i + " / " + n + "…");
                log("▶ Concept variant " + i + "/" + n, "info");

                let plan = null;
                let variantText = "";
                let featureNames = [];
                let verdict = null;
                for (let attempt = 0; attempt <= MAX_RETRIES_PLAN; attempt++) {
                    if (cancelRequested) break;
                    log("  → plan LLM call (attempt " + (attempt + 1) + ")…", "info");
                    const t0 = performance.now();
                    let raw;
                    try {
                        const res = await callWorker("generate", {
                            phase: "plan",
                            concept, targetFeatures, maxDepth,
                            temperature, maxTokens,
                            seed: seedBase * 1000 + attempt,
                        });
                        raw = res.infill || "";
                    } catch (err) {
                        log("  ✗ LLM error: " + (err.message || err), "error");
                        break;
                    }
                    const dt = Math.round(performance.now() - t0);
                    log("  ← response in " + dt + " ms, " + raw.length + " chars raw", "info");

                    plan = extractJsonObject(raw);
                    if (!plan) {
                        // Two distinct failure modes worth telling apart:
                        // - near-empty response: the model emitted a stop
                        //   sequence on the first token (e.g. opening
                        //   Markdown fence) — retry usually succeeds.
                        // - substantive response that does not parse: real
                        //   JSON issue; the preview helps diagnose it.
                        if (raw.trim().length < 20) {
                            log("  ↻ empty response (likely stop-sequence tripped early), retrying", "warn");
                        } else {
                            const preview = raw.replace(/\s+/g, " ").slice(0, 220);
                            log("  ↻ JSON parse failed. Raw: " + preview + (raw.length > 220 ? "…" : ""), "warn");
                        }
                        continue;
                    }
                    let rendered;
                    try {
                        rendered = renderPlanToUvl(plan);
                    } catch (err) {
                        log("  ↻ plan malformed (" + (err.message || err) + "), retrying", "warn");
                        plan = null;
                        continue;
                    }
                    variantText = rendered.text;
                    featureNames = rendered.names;
                    try { verdict = await validateCandidate(variantText); }
                    catch (e) { verdict = { ok: false, error: String(e.message || e) }; }
                    if (verdict.ok) break;
                    log("  ↻ UVL invalid: " + (verdict.error || "").split("\n")[0].slice(0, 80) + ", retrying", "warn");
                }

                if (cancelRequested) break;

                if (!plan || !verdict || !verdict.ok) {
                    log("  ✗ variant " + i + ": no valid plan after " + (MAX_RETRIES_PLAN + 1) + " tries", "error");
                    log("    Complex domain? Try: lower target features, reduce temperature to 0.1, or switch to Qwen 2.5 Coder 7B.", "info");
                    continue;
                }

                // Second pass (optional): ask the LLM for cross-tree
                // constraints against the already-valid tree. Drop any that
                // fail individual re-validation.
                if (withConstraints && featureNames.length > 0 && !cancelRequested) {
                    log("  → constraints LLM call…", "info");
                    const tc0 = performance.now();
                    const ctc = await addConstraintsToTree(
                        variantText, featureNames, temperature, maxTokens, seedBase * 2000
                    );
                    const tcDt = Math.round(performance.now() - tc0);
                    if (ctc.error) {
                        log("  ⚠ constraints step failed in " + tcDt + " ms: " + ctc.error + " (tree only)", "warn");
                    } else if (ctc.kept > 0) {
                        variantText = ctc.text;
                        try { verdict = await validateCandidate(variantText); }
                        catch (e) { /* tree was valid, we already kept only valid additions */ }
                        log("  ← constraints done in " + tcDt + " ms: +" + ctc.kept + " kept / " + ctc.dropped + " dropped", "success");
                    } else {
                        log("  ← constraints done in " + tcDt + " ms: none kept (" + ctc.dropped + " dropped)", "warn");
                    }
                }

                const filename = i + "_" + slug + ".uvl";
                generatedVariants.push({ filename, content: variantText, verdict });
                renderVariantRow(filename, variantText, verdict);
                log("  ✓ " + filename + " valid · " + verdict.features + "f / " + verdict.constraints + "c", "success");
            }
            setProgress(100, "Done");
            const validCount = generatedVariants.filter((v) => v.verdict && v.verdict.ok).length;
            log("Generated " + generatedVariants.length + " variants, " + validCount + " valid.", "info");
            if (validCount === 0) {
                log("Tip: concept mode works best with 3B or 7B coders. Try a different concept, reduce target features, or switch to Qwen 2.5 Coder 7B.", "info");
            }
            if (generatedVariants.length > 0) $("llm_download_btn").disabled = false;
        } catch (err) {
            log("Generation error: " + (err && err.message || err), "error");
        }
    }

    // Builds a flamapy IDE URL that carries the UVL content inline instead
    // of pointing to an http(s) file. The IDE's ?import=<url> param is
    // fetched client-side, and browsers' fetch() implementations accept
    // data: URLs (same-origin is not enforced for data: schemes), so the
    // UVL never has to leave the user's machine to reach the IDE.
    //
    // The resulting href encodes the UVL twice: once for the data: URL
    // payload (encodeURIComponent of the UVL) and once for the outer
    // query string (encodeURIComponent of the whole data: URL). Without
    // the outer pass the IDE parser would see the inner '#' or '&' as
    // boundaries and truncate the content. Very large models end up with
    // very long URLs — Chrome/Edge handle well over 1 MB, but we warn
    // above ~200 KB encoded just in case the IDE rejects the request.
    const FLAMAPY_IDE_BASE = "https://ide.flamapy.org/";
    function flamapyIdeUrlForContent(content) {
        const dataUrl = "data:text/plain;charset=utf-8," + encodeURIComponent(content);
        return FLAMAPY_IDE_BASE + "?import=" + encodeURIComponent(dataUrl);
    }

    function renderVariantRow(filename, content, verdict) {
        const host = $("llm_results");
        const row = document.createElement("div");
        row.className = "d-flex align-items-center justify-content-between py-2 border-bottom";
        const left = document.createElement("div");
        left.className = "d-flex align-items-center flex-grow-1 min-w-0";
        const badge = document.createElement("span");
        badge.className = "badge " + (verdict.ok ? "badge-light-success" : "badge-light-danger") + " me-3";
        badge.textContent = verdict.ok ? "valid" : "invalid";
        const name = document.createElement("span");
        name.className = "fw-semibold text-truncate me-3";
        name.textContent = filename;
        const meta = document.createElement("span");
        meta.className = "text-muted fs-7 me-3";
        meta.textContent = verdict.ok
            ? verdict.features + "f / " + verdict.constraints + "c"
            : (verdict.error || "").split("\n")[0].slice(0, 80);
        left.appendChild(badge);
        left.appendChild(name);
        left.appendChild(meta);

        // Organic badge — only meaningful when parsing succeeded.
        if (verdict.ok && verdict.organic) {
            const org = verdict.organic;
            const orgBadge = document.createElement("span");
            orgBadge.className = "badge " + (org.organic ? "badge-light-primary" : "badge-light-warning");
            orgBadge.title = org.organic
                ? org.informative + "/" + org.total + " informative names"
                : (org.reason || "non-organic vocabulary");
            orgBadge.textContent = org.organic ? "organic" : "synthetic";
            left.appendChild(orgBadge);
        }
        const actions = document.createElement("div");
        actions.className = "d-flex align-items-center gap-2 flex-shrink-0";

        // Icon-only compact buttons so the row stays on one line even when
        // the filename is long or the viewport narrow. Full labels live in
        // title + aria-label for hover and screen readers.
        const viewBtn = document.createElement("button");
        viewBtn.type = "button";
        viewBtn.className = "btn btn-sm btn-icon btn-light-primary";
        viewBtn.title = "View UVL";
        viewBtn.setAttribute("aria-label", "View UVL");
        viewBtn.innerHTML = '<i class="ki-duotone ki-eye fs-3"><span class="path1"></span><span class="path2"></span><span class="path3"></span></i>';
        viewBtn.addEventListener("click", () => showUvlModal(filename, content));
        actions.appendChild(viewBtn);

        // Flamapy IDE button — only offered for syntactically valid variants
        // (a broken UVL isn't worth the round trip). The IDE takes an
        // ?import=<url> query param and fetches it client-side, so we can
        // hand it a data: URL instead of uploading the UVL anywhere. Keeps
        // the page's "nothing leaves your machine" promise intact.
        if (verdict.ok) {
            const ideBtn = document.createElement("a");
            ideBtn.className = "btn btn-sm btn-icon btn-light-info";
            ideBtn.target = "_blank";
            ideBtn.rel = "noopener";
            ideBtn.href = flamapyIdeUrlForContent(content);
            ideBtn.title = "Open in flamapy IDE (ide.flamapy.org)";
            ideBtn.setAttribute("aria-label", "Open in flamapy IDE");
            ideBtn.innerHTML = '<i class="ki-duotone ki-rocket fs-3"><span class="path1"></span><span class="path2"></span></i>';
            actions.appendChild(ideBtn);
        }

        const dlBtn = document.createElement("button");
        dlBtn.type = "button";
        dlBtn.className = "btn btn-sm btn-icon btn-light-success";
        dlBtn.title = "Download UVL";
        dlBtn.setAttribute("aria-label", "Download UVL");
        dlBtn.innerHTML = '<i class="ki-duotone ki-download fs-3"><span class="path1"></span><span class="path2"></span></i>';
        dlBtn.addEventListener("click", () => downloadSingleVariant(filename, content));
        actions.appendChild(dlBtn);

        row.appendChild(left);
        row.appendChild(actions);
        host.appendChild(row);
    }

    // Per-row download: a plain text blob save-as dialog, no dependencies
    // on the generator runtime's ZIP helpers. Mirrors the standard browser
    // file download idiom used across uvlhub.
    function downloadSingleVariant(filename, content) {
        const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    // Cached CodeMirror instance so re-opening the modal is just setValue.
    let uvlPreviewEditor = null;
    function showUvlModal(filename, content) {
        let modal = document.getElementById("llm_uvl_modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.id = "llm_uvl_modal";
            modal.className = "modal fade";
            modal.setAttribute("tabindex", "-1");
            modal.innerHTML =
                '<div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">' +
                '  <div class="modal-content">' +
                '    <div class="modal-header">' +
                '      <h5 class="modal-title font-monospace me-auto" id="llm_uvl_modal_title">UVL</h5>' +
                '      <button type="button" class="btn btn-sm btn-light-primary me-2" id="llm_uvl_modal_copy">' +
                '        <i class="ki-duotone ki-copy fs-5 me-1"><span class="path1"></span><span class="path2"></span></i>Copy' +
                '      </button>' +
                '      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
                "    </div>" +
                '    <div class="modal-body p-3">' +
                '      <div id="llm_uvl_modal_host" class="uvl-preview"></div>' +
                "    </div>" +
                "  </div>" +
                "</div>";
            document.body.appendChild(modal);
            // CodeMirror measures wrong while the modal is display:none.
            // Refresh once Bootstrap paints the visible modal.
            modal.addEventListener("shown.bs.modal", () => {
                if (uvlPreviewEditor) uvlPreviewEditor.refresh();
            });
            // Copy the currently-shown UVL. The content lives on the
            // modal element as a dataset attribute so we don't capture a
            // stale closure the first time the modal is built.
            modal.querySelector("#llm_uvl_modal_copy").addEventListener("click", (ev) => {
                const text = modal.dataset.uvlContent || "";
                if (typeof window.copyUvlToClipboard === "function") {
                    window.copyUvlToClipboard(ev.currentTarget, text);
                }
            });
        }
        modal.dataset.uvlContent = content;
        document.getElementById("llm_uvl_modal_title").textContent = filename;
        const host = document.getElementById("llm_uvl_modal_host");
        if (typeof window.createUvlPreviewEditor === "function") {
            uvlPreviewEditor = window.createUvlPreviewEditor(host, content, uvlPreviewEditor);
        } else {
            // CodeMirror failed to load (offline, CDN blocked) — fall back
            // to a plain <pre> so View still works.
            host.innerHTML = "";
            const pre = document.createElement("pre");
            pre.className = "fs-7 bg-light-secondary rounded p-4 m-0";
            pre.style.cssText = "max-height: 60vh; overflow: auto; tab-size: 2; -moz-tab-size: 2; white-space: pre;";
            pre.textContent = content;
            host.appendChild(pre);
        }
        const instance = window.bootstrap.Modal.getOrCreateInstance(modal);
        instance.show();
    }

    // ─── ZIP download (reuses window.generatorRuntime.packageZip) ─────────
    async function downloadZip() {
        if (generatedVariants.length === 0) return;
        const files = generatedVariants.map((v) => ({ filename: v.filename, content: v.content }));
        const blob = await window.generatorRuntime.packageZip(files);
        window.generatorRuntime.triggerDownload(blob, "llm_variants.zip");
    }

    // ─── Bootstrap ───────────────────────────────────────────────────────
    function init() {
        // Model table (replaces the old dropdown + single download button)
        renderModelTable();
        refreshCacheStatus();

        // Run the WebGPU probe up front so users with unsupported setups see
        // a targeted banner immediately instead of getting a generic error
        // only after they click Load. Fire-and-forget: the probe handles its
        // own UI gating and the rest of init() is unaffected.
        reportWebGpuAdapter();

        const recheckBtn = $("llm_webgpu_recheck_btn");
        if (recheckBtn) {
            recheckBtn.addEventListener("click", () => {
                log("Re-checking WebGPU support…", "info");
                reportWebGpuAdapter({ force: true });
            });
        }

        const refreshBtn = $("llm_refresh_cache_btn");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", () => {
                log("Re-checking cached models…", "info");
                refreshCacheStatus();
            });
        }

        // Preset dropdown
        const presets = $("llm_presets");
        if (presets) {
            presets.addEventListener("change", () => {
                const v = presets.value;
                if (!v) return;
                const p = PRESET_SEEDS.find((x) => x.filename === v);
                if (!p) return;
                $("llm_seed").value = p.content;
                $("llm_seed_name").value = p.filename;
                renderSeedOrganicBadge();
                log("Seed loaded from preset: " + p.title, "info");
            });
            PRESET_SEEDS.forEach((p) => {
                const opt = document.createElement("option");
                opt.value = p.filename;
                opt.textContent = p.title;
                presets.appendChild(opt);
            });
        }

        // Search
        const searchInput = $("llm_search");
        if (searchInput) {
            searchInput.addEventListener("input", (ev) => {
                clearTimeout(searchTimer);
                const q = ev.target.value.trim();
                searchTimer = setTimeout(() => runSearch(q), 250);
            });
        }

        const genBtn = $("llm_generate_btn");
        if (genBtn) genBtn.addEventListener("click", generate);

        const dlBtn = $("llm_download_btn");
        if (dlBtn) dlBtn.addEventListener("click", downloadZip);

        // Refresh the organic badge whenever the seed textarea changes —
        // either the user pastes directly, types, or we set .value
        // programmatically (we trigger a manual refresh in those paths, but
        // this covers the free-form cases as a safety net).
        const seedTa = $("llm_seed");
        if (seedTa) {
            seedTa.addEventListener("input", renderSeedOrganicBadge);
            seedTa.addEventListener("blur", renderSeedOrganicBadge);
        }

        // Mode toggle (seed vs concept). The two panels live in the same
        // card, we just swap display. Auto-bump max_tokens the first time
        // the user enters concept mode if they left it at the seed-mode
        // default (which is far too small for a plan).
        document.querySelectorAll('input[name="llm_mode"]').forEach((r) => {
            r.addEventListener("change", (ev) => applyMode(ev.target.value));
        });
        applyMode(getMode());

        log("Tip: pick a mode (seed or concept), load the model, then Generate.", "info");
    }

    function applyMode(mode) {
        const seedPanel = $("llm_mode_seed_panel");
        const conceptPanel = $("llm_mode_concept_panel");
        if (mode === "concept") {
            if (seedPanel) seedPanel.style.display = "none";
            if (conceptPanel) conceptPanel.style.display = "";
            // A plan for ~15 features fits in ~500 tokens. Allowing more
            // just lets small coders ramble past their coherence limit
            // (missing keys, unclosed braces) and pay latency for output
            // we then have to throw away.
            const mt = $("llm_max_tokens");
            if (mt && parseInt(mt.value, 10) === 100) mt.value = "600";
        } else {
            if (seedPanel) seedPanel.style.display = "";
            if (conceptPanel) conceptPanel.style.display = "none";
            renderSeedOrganicBadge();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
