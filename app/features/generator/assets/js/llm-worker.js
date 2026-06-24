// llm-worker.js — Web Worker that runs WebLLM (LLM inference in WASM + WebGPU).
//
// Stays alive for the tab. Lazy-loads WebLLM from esm.run on first `init`,
// then answers any number of `generate` requests. Three generation phases are
// supported:
//   - features    (seed mode, infill): extend an existing UVL tree
//   - constraints (seed mode, infill): append UVL cross-tree constraints
//   - plan        (concept mode):      emit a JSON tree for a given domain
//
// Message protocol (main ⇄ worker):
//
//   main → worker:   { id, action: "init",        payload: { model } }
//                    { id, action: "generate",    payload: { ...see below } }
//                    { id, action: "checkCache",  payload: { modelIds: [] } }
//                    { id, action: "deleteCache", payload: { modelId } }
//   worker → main:   { id, ok: true,  result }
//                    { id, ok: false, error }
//                    { type: "progress", report }
//                    { type: "ready",    model }
//
// `generate` payload shape by phase:
//   features:    { phase, prefix, suffix, childIndent, temperature, seed, maxTokens }
//   constraints: { phase, modelText, newFeatures,       temperature, seed, maxTokens }
//   plan:        { phase, concept, targetFeatures, maxDepth, temperature, seed, maxTokens }
//
// Loaded as a module worker so we can use dynamic `import(...)`.

let webllm = null;
let engine = null;
let currentModel = null;

async function loadWebllm() {
    if (webllm) return webllm;
    webllm = await import("https://esm.run/@mlc-ai/web-llm");
    return webllm;
}

async function init(model) {
    const lib = await loadWebllm();

    if (engine && currentModel === model) {
        self.postMessage({ type: "ready", model });
        return { model, reused: true };
    }

    if (engine) {
        try { await engine.unload(); } catch (e) { /* best-effort */ }
        engine = null;
        currentModel = null;
    }

    engine = await lib.CreateMLCEngine(model, {
        initProgressCallback: (report) => {
            self.postMessage({ type: "progress", report });
        },
    });
    currentModel = model;
    self.postMessage({ type: "ready", model });
    return { model, reused: false };
}

// ─── Prompt builders (ported from SPLC'26 v2 notebook) ───────────────────
//
// Two separate phases, each with a narrow system prompt. The hard rules
// ("no ->", "no ;", exact indentation, one feature per line, …) shift most
// of the burden away from free-form generation — small LLMs follow simple
// grammar rules much better than "produce valid UVL".

function buildFeaturesMessages(prefix, suffix, childIndent) {
    const indentHint = " ".repeat(Math.max(0, childIndent));
    const user =
        "You are editing a UVL feature model.\n" +
        "Generate ONLY 1 to 3 NEW feature lines to insert between PREFIX and SUFFIX.\n" +
        "Hard rules (must follow):\n" +
        "- Output only feature lines. No explanations. No code fences.\n" +
        "- Do NOT output 'features' or 'constraints' headers.\n" +
        "- Do NOT output ANY constraint syntax. Forbidden tokens anywhere " +
            "on a feature line: '->', '=>', '<=>', '&', '|', '!', '(', ')', " +
            "'==', '!=', '>=', '<=', ';', ':'. These belong to the " +
            "constraints section, which you are NOT editing.\n" +
        "- Use only valid UVL feature identifiers (letters, digits, underscore).\n" +
        "- Prefer unquoted identifiers. If you think you need a quote or " +
            "an apostrophe, replace it with an underscore.\n" +
        "- Each new feature line MUST start with exactly this indentation: " +
            JSON.stringify(indentHint) + "\n" +
        "- Each line must contain exactly ONE feature name (and nothing else).\n\n" +
        "PREFIX:\n-----\n" + prefix + "-----\n\n" +
        "SUFFIX:\n-----\n" + suffix + "-----\n";
    return [
        { role: "system", content: "Output only UVL feature-tree lines. No constraints. No operators. No extra text." },
        { role: "user", content: user },
    ];
}

// Plan phase: concept → structured JSON tree. The main thread then renders
// that JSON to UVL deterministically (no free-form UVL text leaves the LLM),
// which is why small in-browser LLMs succeed here where they routinely fail
// at whole-model UVL generation. A PascalCase-only identifier rule lets us
// skip quote handling entirely downstream.
// Smaller few-shot than Coffee to reduce prefill cost. We keep it minimal but
// complete: the example covers all four group types (mandatory, optional,
// alternative, or) and nested children, which is everything the renderer
// needs the model to have learned.
const PLAN_EXAMPLE = {
    root: "Drink",
    children: [
        { name: "Size", type: "mandatory", children: [
            { name: "Small", type: "alternative" },
            { name: "Large", type: "alternative" }
        ]},
        { name: "Toppings", type: "optional", children: [
            { name: "Whip", type: "or" },
            { name: "Cinnamon", type: "or" }
        ]}
    ]
};

function buildPlanMessages(concept, targetFeatures, maxDepth) {
    // Hard cap on targetFeatures. Small coder models (even Qwen2.5-Coder 3B)
    // start dropping "name" keys, stray tokens like "!" or "g", or drifting
    // into instruction-following text ("gotta have a root", "kevin:") once
    // the JSON runs past ~600-800 tokens. Capping at 15 keeps plans within
    // the coherence horizon. For complex domains (casino, compiler, OS) the
    // user should either lower the target or use the 7B model.
    const cap = Math.max(5, Math.min(15, targetFeatures));

    const user =
        "Task: design a MINIMAL, COHERENT feature model for the domain: " + concept + "\n\n" +
        "Output EXACTLY one JSON object matching this schema:\n" +
        "  {\n" +
        '    "root": "<RootName>",\n' +
        '    "children": [\n' +
        '      { "name": "<Name>",\n' +
        '        "type": "mandatory" | "optional" | "alternative" | "or",\n' +
        '        "children": [ ...same shape... ] }\n' +
        "    ]\n" +
        "  }\n\n" +
        "HARD RULES — failure to follow ANY of these makes the output " +
        "useless:\n" +
        "- Output ONLY the JSON object. No Markdown. No code fences. No " +
        "commentary before or after. Stop immediately after the final `}`.\n" +
        '- Every non-root object MUST have BOTH "name" (non-empty string) ' +
        'and "type" (one of the four allowed values). NEVER emit entries ' +
        'like {": "X"}, {"nameFoo"}, {! "name": …}, or stray tokens ' +
        '(!, g, bare identifiers).\n' +
        "- Feature names: PascalCase, letters and digits only. No spaces, " +
        "no apostrophes, no punctuation, no accents, no emoji.\n" +
        '- "type" is relative to the PARENT: mandatory (always present), ' +
        "optional (may be absent), alternative (XOR with siblings), or " +
        "(at least one of siblings).\n" +
        '- Root has no "type". Leaves omit "children".\n' +
        "- **At most " + cap + " features total. At most " + maxDepth +
        " levels deep.** Prefer a SMALL coherent tree over a detailed one. " +
        "Do NOT try to enumerate every aspect of the domain — pick 3–5 " +
        "top-level concepts and stop.\n" +
        "- Names must be real domain concepts in English.\n\n" +
        "EXAMPLE (well-formed, minimal):\n" +
        JSON.stringify(PLAN_EXAMPLE) + "\n\n" +
        "Now output the JSON object for domain: " + concept;

    return [
        { role: "system", content: "You output exactly one JSON object. No Markdown. No commentary. Stop after the final closing brace. Prefer minimal coherent trees." },
        { role: "user", content: user },
    ];
}

// Seed mode (new): given a plan JSON parsed from the user's seed UVL, ask
// the LLM to produce a NEW VARIANT — same domain, different shape. The
// model receives the structured JSON rather than the raw UVL so it never
// has to parse UVL syntax itself, which is what made the old line-infill
// seed mode so fragile.
function buildVariantMessages(planJson, targetFeatures) {
    const cap = Math.max(5, Math.min(20, targetFeatures || 15));
    const user =
        "You are given an existing feature model for a software product line.\n\n" +
        "ORIGINAL MODEL (JSON):\n" +
        JSON.stringify(planJson) + "\n\n" +
        "Task: design a NEW VARIANT of this feature model.\n\n" +
        "HARD RULES — failure to follow ANY of these makes the output " +
        "useless:\n" +
        "- Output EXACTLY one JSON object in the SAME schema as the input:\n" +
        "  { \"root\": \"<Name>\", \"children\": [ { \"name\": ..., " +
            "\"type\": \"mandatory|optional|alternative|or\", \"children\": [ ... ] } ] }\n" +
        "- Output ONLY the JSON. No Markdown, no fences, no commentary. " +
        "Stop immediately after the final `}`.\n" +
        "- Keep the same domain — the variant must represent the same kind " +
        "of product line as the original.\n" +
        "- You MUST modify the model in some meaningful way: rename " +
        "features, add or remove subtrees, change group types, or " +
        "reorganize siblings. Do NOT just echo the original back.\n" +
        "- Every non-root object MUST have both \"name\" and \"type\".\n" +
        "- Feature names: PascalCase, letters and digits only. No spaces, " +
        "no apostrophes, no punctuation, no accents.\n" +
        "- Aim for about " + cap + " features total. Prefer a minimal " +
        "coherent tree over a large detailed one.\n\n" +
        "Now output the JSON for the variant:";

    return [
        { role: "system", content: "You output exactly one JSON object. No Markdown. No commentary. Stop after the final closing brace." },
        { role: "user", content: user },
    ];
}

function buildConstraintsMessages(modelText, newFeatures) {
    const nf = (newFeatures && newFeatures.length)
        ? newFeatures.map((x) => String(x).replace(/"/g, "")).join(", ")
        : "(none)";
    const user =
        "You are editing a UVL feature model.\n" +
        "Generate ONLY 1 to 3 NEW constraint lines to append under the 'constraints' section.\n" +
        "Hard rules (must follow):\n" +
        "- Output only constraint lines. No explanations. No code fences.\n" +
        "- Do NOT output any of these tokens: '->' ';' ':'\n" +
        "- Use only UVL boolean operators: ! & | => <=> and parentheses.\n" +
        "- One constraint per line.\n" +
        "- Avoid quoting feature names; use identifiers.\n" +
        "- If sensible, reference these new features: " + nf + "\n\n" +
        "FULL MODEL:\n-----\n" + modelText + "-----\n";
    return [
        { role: "system", content: "Output only UVL constraint lines. No extra text." },
        { role: "user", content: user },
    ];
}

async function generate(payload) {
    if (!engine) {
        throw new Error("Engine not initialised. Load a model first.");
    }
    const { phase, temperature, maxTokens, seed } = payload;
    let messages;
    if (phase === "constraints") {
        messages = buildConstraintsMessages(payload.modelText, payload.newFeatures);
    } else if (phase === "plan") {
        messages = buildPlanMessages(payload.concept, payload.targetFeatures, payload.maxDepth);
    } else if (phase === "variant") {
        messages = buildVariantMessages(payload.plan, payload.targetFeatures);
    } else {
        messages = buildFeaturesMessages(payload.prefix, payload.suffix, payload.childIndent);
    }

    // Stop sequences: give the model a clean way to end without padding.
    // In plan mode, chat-tuned coders routinely add explanatory prose after
    // the JSON — those tokens cost latency for output we throw away. We
    // stop on the prose patterns Qwen Coder typically emits ("Here's the
    // JSON…", Markdown headers).
    //
    // We intentionally do NOT stop on "```" even though the model often
    // wants to wrap JSON in a fenced block: Qwen sometimes emits the
    // opening ``` as its FIRST token, which would trip the stop sequence
    // before any JSON is generated (visible as "1 chars raw" in the log).
    // The parser already strips fences, so letting them through is safer.
    const isJsonPhase = phase === "plan" || phase === "variant";
    const stopSeqs = isJsonPhase ? ["\n\n#", "\n\nHere"] : undefined;
    // Chat-tuned 3B coders at t≥0.2 on hard domains drift into degenerate
    // modes: multilingual tokens, f-strings, renamed JSON keys, pure
    // gibberish. Clamp sampling for the plan phase — at most 0.2 — so the
    // structured output stays on the most likely paths.
    const effectiveTemp = isJsonPhase
        ? Math.min((typeof temperature === "number") ? temperature : 0.2, 0.2)
        : ((typeof temperature === "number") ? temperature : 0.2);

    const request = {
        messages,
        temperature: effectiveTemp,
        max_tokens: (typeof maxTokens === "number") ? maxTokens : 350,
        seed: (typeof seed === "number") ? seed : undefined,
        stop: stopSeqs,
        stream: false,
    };

    // Earlier versions of this worker used
    //     request.response_format = { type: "json_object" }
    // to get grammar-constrained JSON decoding. The WebLLM build pulled
    // from esm.run throws
    //     BindingError: Cannot pass non-string to std::string
    //     at GrammarCompiler.CompileJSONSchema
    // inside xgrammar whenever that option is set, and because the error
    // fires inside an unhandled Promise the worker appears to hang
    // indefinitely instead of failing cleanly. See browser DevTools when
    // debugging.
    //
    // Until WebLLM ships a fixed xgrammar we enforce JSON purely from the
    // prompt side (strict system message + tolerant parser in llm-page.js).
    // Accuracy is slightly lower on complex domains but generation is
    // reliable and doesn't hang.

    const response = await engine.chat.completions.create(request);
    const text = response?.choices?.[0]?.message?.content ?? "";
    return { infill: text };
}

// ─── Cache management ────────────────────────────────────────────────────
//
// WebLLM stores model weights in IndexedDB under a per-model namespace. The
// library exposes helpers to probe and drop that storage — using them lets
// us show an at-a-glance cache table in the UI instead of forcing the user
// to re-download to find out what's on disk. All helpers are best-effort:
// older WebLLM builds may not export them, in which case we fall back to
// "unknown" status (renders as not-cached; the Download button still works).

async function checkCache(modelIds) {
    const lib = await loadWebllm();
    const out = {};
    const fn = typeof lib.hasModelInCache === "function" ? lib.hasModelInCache : null;
    for (const id of (modelIds || [])) {
        if (!fn) { out[id] = false; continue; }
        try { out[id] = !!(await fn(id)); }
        catch (_) { out[id] = false; }
    }
    return out;
}

// WebLLM's engine.interruptGenerate() stops the currently running
// completion without waiting for EOS. The in-flight
// `chat.completions.create(…)` resolves early with whatever tokens were
// produced so far (which our parser will likely reject — fine, the
// main-thread loop checks cancelRequested next and exits cleanly).
async function interruptCurrent() {
    if (!engine) return { interrupted: false, reason: "no engine loaded" };
    if (typeof engine.interruptGenerate !== "function") {
        return { interrupted: false, reason: "interruptGenerate not available in this WebLLM build" };
    }
    try {
        const maybe = engine.interruptGenerate();
        if (maybe && typeof maybe.then === "function") await maybe;
        return { interrupted: true };
    } catch (err) {
        return { interrupted: false, reason: String(err && err.message || err) };
    }
}

async function deleteCache(modelId) {
    const lib = await loadWebllm();
    // If the currently loaded engine owns this model, unload it first —
    // otherwise the IndexedDB rows can be reopened by the runtime and
    // re-created after we delete them.
    if (engine && currentModel === modelId) {
        try { await engine.unload(); } catch (_) { /* best-effort */ }
        engine = null;
        currentModel = null;
    }
    if (typeof lib.deleteModelAllInfoInCache === "function") {
        await lib.deleteModelAllInfoInCache(modelId);
        return { deleted: true };
    }
    if (typeof lib.deleteModelInCache === "function") {
        await lib.deleteModelInCache(modelId);
        return { deleted: true, partial: true };
    }
    return { deleted: false, reason: "delete API not available in this WebLLM build" };
}

self.onmessage = async (ev) => {
    const { id, action, payload } = ev.data || {};
    try {
        let result;
        if (action === "init") {
            result = await init(payload.model);
        } else if (action === "generate") {
            result = await generate(payload);
        } else if (action === "checkCache") {
            result = await checkCache(payload.modelIds);
        } else if (action === "deleteCache") {
            result = await deleteCache(payload.modelId);
        } else if (action === "interrupt") {
            result = await interruptCurrent();
        } else {
            throw new Error("Unknown action: " + action);
        }
        self.postMessage({ id, ok: true, result });
    } catch (err) {
        const msg = (err && err.message) ? err.message : String(err);
        self.postMessage({ id, ok: false, error: msg });
    }
};
