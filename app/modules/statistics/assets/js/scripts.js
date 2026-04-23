// Dashboard chart bootstrap. The server renders the series as JSON inside
// `<script id="dashboard-data">` so this module has a single parse step and
// no template-interpolation inside JS (safer, easier to cache, no CSP hacks).

import Chart from "chart.js/auto";

// Shared palette so platform/corpus charts feel like one dashboard.
const COLORS = {
    primary: "rgba(54, 153, 255, 1)",
    primarySoft: "rgba(54, 153, 255, 0.2)",
    danger: "rgba(246, 78, 96, 1)",
    dangerSoft: "rgba(246, 78, 96, 0.2)",
    success: "rgba(80, 205, 137, 1)",
    successSoft: "rgba(80, 205, 137, 0.2)",
    warning: "rgba(255, 193, 7, 1)",
    warningSoft: "rgba(255, 193, 7, 0.25)",
    info: "rgba(0, 188, 212, 1)",
    infoSoft: "rgba(0, 188, 212, 0.25)",
    secondary: "rgba(108, 117, 125, 1)",
    secondarySoft: "rgba(108, 117, 125, 0.25)",
};

// Cycled per-slice palette for doughnuts/pies.
const SLICE_PALETTE = [
    COLORS.primary, COLORS.danger, COLORS.success, COLORS.warning,
    COLORS.info, COLORS.secondary,
];

function readData() {
    const el = document.getElementById("dashboard-data");
    if (!el) return null;
    try {
        return JSON.parse(el.textContent || "{}");
    } catch (e) {
        console.error("dashboard: bad JSON payload", e);
        return null;
    }
}

// ── Platform charts ────────────────────────────────────────────────────────

function renderUploads(data) {
    const canvas = document.getElementById("uploadsChart");
    if (!canvas || !data.months?.length) return;
    new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
            labels: data.months,
            datasets: [{
                label: "Datasets uploaded",
                data: data.uploads || [],
                backgroundColor: COLORS.primarySoft,
                borderColor: COLORS.primary,
                borderWidth: 2,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        },
    });
}

function renderActivity(data) {
    const canvas = document.getElementById("activityChart");
    if (!canvas || !data.months?.length) return;
    new Chart(canvas.getContext("2d"), {
        type: "line",
        data: {
            labels: data.months,
            datasets: [
                {
                    label: "Downloads",
                    data: data.downloads || [],
                    backgroundColor: COLORS.dangerSoft,
                    borderColor: COLORS.danger,
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                },
                {
                    label: "Views",
                    data: data.views || [],
                    backgroundColor: COLORS.successSoft,
                    borderColor: COLORS.success,
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true, position: "top" } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        },
    });
}

// ── Corpus charts ──────────────────────────────────────────────────────────

function renderHistogram(canvasId, buckets, color, softColor) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !buckets?.length) return;
    new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
            labels: buckets.map((b) => b.label),
            datasets: [{
                label: "Models",
                data: buckets.map((b) => b.count),
                backgroundColor: softColor,
                borderColor: color,
                borderWidth: 2,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });
}

function renderHorizontalBar(canvasId, labels, values, colors) {
    // Horizontal bars are more perceptually accurate than doughnuts for
    // magnitude comparison (Cleveland & McGill 1984) and give long category
    // labels room to breathe.
    const canvas = document.getElementById(canvasId);
    if (!canvas || !values?.length) return;
    if (values.every((v) => !v)) return;  // all-zero series: skip the chart

    // Sort descending so the eye lands on the biggest category first; keep
    // colors aligned to the reordered labels.
    const ordered = labels
        .map((label, i) => ({ label, value: values[i], color: colors[i] }))
        .sort((a, b) => b.value - a.value);

    new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
            labels: ordered.map((o) => o.label),
            datasets: [{
                label: "Count",
                data: ordered.map((o) => o.value),
                backgroundColor: ordered.map((o) => o.color),
                borderWidth: 0,
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw.toLocaleString()}` } },
            },
            scales: {
                x: { beginAtZero: true, ticks: { precision: 0 } },
                y: { ticks: { autoSkip: false } },
            },
        },
    });
}

function renderCategoryBar(canvasId, pairs) {
    // `pairs` is a list of [label, count]; tolerates Python-side tuple
    // serialisation that comes out as a 2-element array.
    if (!pairs?.length) return;
    const labels = pairs.map((p) => p[0]);
    const values = pairs.map((p) => p[1]);
    const colors = labels.map((_, i) => SLICE_PALETTE[i % SLICE_PALETTE.length]);
    renderHorizontalBar(canvasId, labels, values, colors);
}

function renderSatisfiability(data) {
    const sat = data.satisfiability || {};
    renderHorizontalBar(
        "satChart",
        ["Satisfiable", "Unsatisfiable", "Unknown"],
        [sat.yes || 0, sat.no || 0, sat.unknown || 0],
        [COLORS.success, COLORS.danger, COLORS.secondary],
    );
}

function init() {
    const data = readData();
    if (!data) return;

    // Platform usage
    renderUploads(data);
    renderActivity(data);

    // Corpus characterisation
    renderSatisfiability(data);
    renderCategoryBar("constraintTypesChart", data.constraintTypes);
    renderCategoryBar("groupTypesChart", data.groupTypes);
    renderHistogram("featuresHistChart", data.featuresHistogram, COLORS.primary, COLORS.primarySoft);
    renderHistogram("constraintsHistChart", data.constraintsHistogram, COLORS.danger, COLORS.dangerSoft);
    renderHistogram("depthHistChart", data.depthHistogram, COLORS.success, COLORS.successSoft);
    renderHistogram("configsHistChart", data.configurationsHistogram, COLORS.warning, COLORS.warningSoft);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}
