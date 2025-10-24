import Mustache from 'mustache';

Mustache.tags = ['[[', ']]'];

document.addEventListener('DOMContentLoaded', () => {
    bindFilters();
    setupDateValidation();
    runSearch(); // initial load
});

function setupDateValidation() {
    const fromInput = document.getElementById('filter-date-from');
    const toInput = document.getElementById('filter-date-to');
    const dateError = document.getElementById('date-error');

    if (!fromInput || !toInput) return;

    const validate = () => {
        const from = new Date(fromInput.value);
        const to = new Date(toInput.value);

        if (fromInput.value && toInput.value && to < from) {
            dateError.classList.remove('d-none');
            toInput.classList.add('is-invalid');
        } else {
            dateError.classList.add('d-none');
            toInput.classList.remove('is-invalid');
        }
    };

    fromInput.addEventListener('change', validate);
    toInput.addEventListener('change', validate);
}

function bindFilters() {
    const filters = [
        '#search-query',
        '#filter-publication-type',
        '#filter-sorting',
        '#filter-tags',
        '#filter-date-from',
        '#filter-date-to'
    ];

    filters.forEach(selector => {
        const el = document.querySelector(selector);
        if (el) {
            el.addEventListener('input', runSearch);
            el.addEventListener('change', runSearch);
        }
    });

    document.getElementById('clear-filters').addEventListener('click', () => {
        document.getElementById('search-query').value = '';
        document.getElementById('filter-publication-type').value = '';
        document.getElementById('filter-sorting').value = 'newest';
        document.getElementById('filter-tags').value = '';
        document.getElementById('filter-date-from').value = '';
        document.getElementById('filter-date-to').value = '';
        runSearch();
    });
}



export function setPublicationTypeFilter(type) {
    document.getElementById('filter-publication-type').value = type;
    runSearch();
}

export function addTagToQuery(tag) {
    document.getElementById('search-query').value = tag;
    runSearch();
}

let currentPage = 1;
const pageSize = 10;
let loading = false;

function runSearch(reset = true) {
    const fromInput = document.getElementById('filter-date-from');
    const toInput = document.getElementById('filter-date-to');
    const dateError = document.getElementById('date-error');

    // Validación del rango de fechas
    const fromDate = fromInput.value ? new Date(fromInput.value) : null;
    const toDate = toInput.value ? new Date(toInput.value) : null;

    if (fromDate && toDate && toDate < fromDate) {
        dateError?.classList.remove('d-none');
        toInput.classList.add('is-invalid');
        return;
    } else {
        dateError?.classList.add('d-none');
        toInput.classList.remove('is-invalid');
    }

    if (reset) {
        currentPage = 1;
        document.getElementById('results-container').innerHTML = '';
    }

    const query = document.getElementById('search-query').value.trim();
    const publication_type = document.getElementById('filter-publication-type').value;
    const sorting = document.getElementById('filter-sorting').value;
    const tags = document.getElementById('filter-tags').value.trim();
    const date_from = fromInput.value;
    const date_to = toInput.value;

    const params = new URLSearchParams({
        q: query,
        publication_type: publication_type,
        sorting: sorting,
        page: currentPage,
        size: pageSize
    });

    if (tags) params.append('tags', tags);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);

    if (loading) return;
    loading = true;

    fetch(`/api/v1/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            renderResults(data.results, !reset);
            loading = false;
            if (data.results.length > 0) currentPage++;
        })
        .catch(err => {
            console.error("Search failed", err);
            loading = false;
        });
}


window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
        runSearch(false); // carga más sin resetear
    }
});


function renderResults(results, append = false) {
    const container = document.getElementById('results-container');
    const notFound = document.getElementById('no-results');

    if (!append) {
        container.innerHTML = '';
    }

    if (!results || results.length === 0) {
        if (!append) notFound.classList.remove('d-none');
        return;
    }

    notFound.classList.add('d-none');

    const datasetTemplate = document.getElementById('result-template').innerHTML;
    const hubfileTemplate = document.getElementById('hubfile-template').innerHTML;

    results.forEach(result => {
        let html = '';
        if (result.type === 'dataset') {
            html = Mustache.render(datasetTemplate, result);
        } else if (result.type === 'hubfile') {
            html = Mustache.render(hubfileTemplate, result);
        }
        container.insertAdjacentHTML('beforeend', html);
    });

    // Reprocesar iconos Keen
    if (typeof KTIcon !== 'undefined' && KTIcon.update) {
        KTIcon.update();
    }

    // Reprocesar tooltips Bootstrap
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
}
