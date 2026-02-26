document.addEventListener('DOMContentLoaded', function () {
    const menu = document.querySelector('[data-kt-search-element="content"]');
    const toggle = document.getElementById('kt_header_search_toggle');

    if (menu && toggle) {
        // Escucha el evento de clic en el toggle
        toggle.addEventListener('click', function () {
            // Obtén las coordenadas del toggle
            const toggleRect = toggle.getBoundingClientRect();

            // Ajusta el menú para que esté justo debajo del icono de búsqueda
            menu.style.position = 'fixed';
            menu.style.top = `${toggleRect.bottom}px`; // Posición justo debajo
            menu.style.left = `${toggleRect.left}px`; // Alineado con el icono
            menu.style.transform = 'none'; // Elimina cualquier transformación previa
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const input = document.querySelector('[data-kt-search-element="input"]');
    if (!input) return;

    const getResultsWrapper = () => document.querySelector('[data-kt-search-element="results"]');
    const getResultsContainer = () => document.querySelector('[data-kt-search-element="results"] .scroll-y');
    const getEmptyWrapper = () => document.querySelector('[data-kt-search-element="empty"]');

    let timeout;
    let currentController = null;
    let lastQuerySent = "";

    input.addEventListener("input", function () {
        const rawQuery = input.value;
        const query = rawQuery.trim();

        if (timeout) clearTimeout(timeout);

        const resultsWrapper = getResultsWrapper();
        const resultsContainer = getResultsContainer();
        const emptyWrapper = getEmptyWrapper();

        if (!resultsWrapper || !resultsContainer || !emptyWrapper) return;

        if (query.length >= 2) {
            timeout = setTimeout(() => {
                if (query === lastQuerySent) return;

                if (currentController) currentController.abort();
                currentController = new AbortController();
                lastQuerySent = query;

                fetch(`/search?q=${encodeURIComponent(query)}`, {
                    signal: currentController.signal
                })
                .then(response => {
                    if (!response.ok) throw new Error("Network error");
                    return response.json();
                })
                .then(data => {
                    console.log(data.results)
                    if (data.results && data.results.length > 0) {
                        resultsWrapper.classList.remove("d-none");
                        emptyWrapper.classList.add("d-none");

                        let resultsArray = Array.isArray(data.results[0]) ? data.results[0] : data.results;

                        resultsContainer.innerHTML = "";
                        for (const item of resultsArray) {
                            const title = item.title || item.filename || item.content || "Untitled";
                            const icon = item.type === "dataset" ? "ki-folder" : "ki-file";

                            const href = item.type === "dataset"
                                ? (item.dataset_doi ? `/doi/${item.dataset_doi}` : "#")
                                : (item.url || "#");

                            let subtitle = "";
                            if (item.type === "dataset") {
                                if (item.dataset_doi) {
                                    subtitle = `DOI: ${item.dataset_doi}`;
                                } else if (item.dataset_id) {
                                    subtitle = `Dataset ID: ${item.dataset_id}`;
                                } else {
                                    subtitle = "Dataset";
                                }
                            } else {
                                // Archivo → pertenece a un dataset
                                if (item.dataset_title) {
                                    subtitle = `Belongs to dataset: ${item.dataset_title}`;
                                } else if (item.dataset_doi) {
                                    subtitle = `Belongs to dataset: ${item.dataset_doi}`;
                                } else if (item.dataset_id) {
                                    subtitle = `Belongs to dataset: ${item.dataset_id}`;
                                } else {
                                    subtitle = "File";
                                }
                            }

                            resultsContainer.innerHTML += `
                                <div class="d-flex align-items-center mb-5">
                                    <div class="symbol symbol-40px me-4">
                                        <span class="symbol-label bg-light">
                                            <i class="ki-duotone ${icon} fs-2 text-primary">
                                                <span class="path1"></span><span class="path2"></span>
                                            </i>
                                        </span>
                                    </div>
                                    <div class="d-flex flex-column">
                                        <a href="${href}" class="fs-6 text-gray-800 text-hover-primary fw-semibold">${title}</a>
                                        ${subtitle ? `<span class="fs-7 text-muted fw-semibold">${subtitle}</span>` : ""}
                                    </div>
                                </div>
                            `;
                        }

                    } else {
                        resultsWrapper.classList.add("d-none");
                        emptyWrapper.classList.remove("d-none");
                    }
                })
                .catch(err => {
                    if (err.name === "AbortError") return;
                    console.error("Search failed", err);
                    resultsWrapper.classList.add("d-none");
                    emptyWrapper.classList.remove("d-none");
                });
            }, 300);
        } else {
            if (currentController) currentController.abort();
            lastQuerySent = "";
            resultsWrapper.classList.add("d-none");
            emptyWrapper.classList.add("d-none");
        }
    });
});