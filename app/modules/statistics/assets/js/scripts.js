// Dashboard chart bootstrap. The server renders the series as JSON inside
// `<script id="dashboard-data">` so this module has a single parse step and
// no template-interpolation inside JS (safer, easier to cache, no CSP hacks).

import Chart from "chart.js/auto";

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

function renderUploads(data) {
    const canvas = document.getElementById("uploadsChart");
    if (!canvas || !data.months?.length) return;
    new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
            labels: data.months,
            datasets: [
                {
                    label: "Datasets uploaded",
                    data: data.uploads || [],
                    backgroundColor: "rgba(54, 153, 255, 0.2)",
                    borderColor: "rgba(54, 153, 255, 1)",
                    borderWidth: 2,
                    borderRadius: 4,
                },
            ],
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
                    backgroundColor: "rgba(246, 78, 96, 0.1)",
                    borderColor: "rgba(246, 78, 96, 1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                },
                {
                    label: "Views",
                    data: data.views || [],
                    backgroundColor: "rgba(80, 205, 137, 0.1)",
                    borderColor: "rgba(80, 205, 137, 1)",
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

function init() {
    const data = readData();
    if (!data) return;
    renderUploads(data);
    renderActivity(data);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}
