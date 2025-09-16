import Mustache from 'mustache';

// Configure Mustache delimiters
Mustache.tags = ['[[', ']]'];

// Generate a unique ID for HTML IDs (not used in form field names)
function generateUniqueId() {
    return '_' + Math.random().toString(36).slice(2, 11);
}

// Global index counter for authors (used in name attributes)
let authorIndex = 0;

// Initialize logic for adding and removing authors

export function initializeAuthors() {
    // Button to add authors
    document.getElementById('add-author-btn').addEventListener('click', function () {
        const uniqueId = generateUniqueId();
        const template = document.getElementById('author-template').innerHTML;

        // Render template with both a unique ID and an index
        const rendered = Mustache.render(template, {
            id: uniqueId,
            index: authorIndex
        });

        // Add the new author to the container
        document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);

        // Increment index for next author
        authorIndex++;
    });

    // Delegated event to remove authors
    document.getElementById('authors-container').addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-author') || e.target.closest('.remove-author')) {
            const button = e.target.closest('.remove-author');
            const authorId = button.getAttribute('data-id');
            const node = document.getElementById(`author-${authorId}`);
            if (node) node.remove();

            // Si el borrado corresponde al bloque "myself", reactivar botón
            const myselfBtn = document.getElementById('add-myself-btn');
            if (myselfBtn.dataset.myselfId === authorId) {
                myselfBtn.disabled = false;
                delete myselfBtn.dataset.myselfId;
            }
        }
    });

    // Initialize the draggable zone
    const containers = document.querySelectorAll(".draggable-zone");

    new Draggable.Sortable(containers, {
        draggable: ".draggable",
        handle: ".draggable .draggable-handle",
        mirror: {
            appendTo: "body",
            constrainDimensions: true
        }
    });

    document.getElementById('add-myself-btn').addEventListener('click', async function () {
        const btn = this;
        try {
            const res = await fetch('/api/me');
            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Backend error ${res.status}: ${text}`);
            }
            const data = await res.json();

            // Verificar si ya existe un autor con ese ORCID
            const existing = Array.from(document.querySelectorAll("#authors-container input[name*='[orcid]']"))
                .some(input => input.value === data.orcid);
            if (existing) {
                alert("You already added yourself!");
                return;
            }

            const uniqueId = generateUniqueId();
            const template = document.getElementById('author-template').innerHTML;
            const rendered = Mustache.render(template, {
                id: uniqueId,
                index: authorIndex
            });

            document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);

            // Rellenar campos dentro del bloque recién creado
            const base = document.getElementById(`author-${uniqueId}`);
            base.querySelector(`input[name="authors${authorIndex}[name]"]`).value = `${data.name} ${data.surname}`;
            base.querySelector(`input[name="authors${authorIndex}[affiliation]"]`).value = data.affiliation || "";
            base.querySelector(`input[name="authors${authorIndex}[orcid]"]`).value = data.orcid || "";

            // Guardar id de "myself" en el botón y deshabilitarlo
            btn.dataset.myselfId = uniqueId;
            btn.disabled = true;

            authorIndex++;
        } catch (err) {
            console.error("Add myself failed:", err);
            alert(`Error fetching your profile: ${err.message}`);
        }
    });
}
