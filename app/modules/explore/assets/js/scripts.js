import Mustache from 'mustache';

Mustache.tags = ['[[', ']]'];

document.addEventListener('DOMContentLoaded', () => {
    bindFilters();
    runSearch();  // initial load
});

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

function runSearch() {
    const query = document.getElementById('search-query').value;
    const publication_type = document.getElementById('filter-publication-type').value;
    const sorting = document.getElementById('filter-sorting').value;
    const tags = document.getElementById('filter-tags').value;
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;

    const params = new URLSearchParams();

    if (query) params.append("q", query);
    if (publication_type) params.append("publication_type", publication_type);
    if (sorting) params.append("sorting", sorting);
    if (tags) params.append("tags", tags);
    if (dateFrom) params.append("date_from", dateFrom);
    if (dateTo) params.append("date_to", dateTo);

    fetch(`/api/v1/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            renderResults(data);
        })
        .catch(err => {
            console.error("Search failed", err);
        });
}


function renderResults(data) {
    const container = document.getElementById('results-container');
    const notFound = document.getElementById('no-results');

    container.innerHTML = '';

    if (!data || data.length === 0) {
        notFound.classList.remove('d-none');
        return;
    }

    notFound.classList.add('d-none');

    const datasetTemplate = document.getElementById('result-template').innerHTML;
    const hubfileTemplate = document.getElementById('hubfile-template').innerHTML;

    data.forEach(result => {
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
