import Mustache from 'mustache';

// Configure Mustache delimiters
Mustache.tags = ['[[', ']]'];

// ----------------- VALIDADORES -----------------

function validateNameInput(input) {
    const value = input.value.trim();
    if (value.length < 2) {
        showFieldError(input, "Name must have at least 2 characters");
    } else if (value.length > 120) {
        showFieldError(input, "Name too long (max 120 chars)");
    } else {
        clearFieldError(input);
    }
}

function validateAffiliationInput(input) {
    const value = input.value.trim();
    if (value.length > 120) {
        showFieldError(input, "Affiliation too long (max 120 chars)");
    } else {
        clearFieldError(input);
    }
}

async function validateOrcidInput(input) {
    const value = input.value.trim();

    if (value === "") {
        clearFieldError(input); // vacío es válido
        return true;
    }

    // ORCID formato estándar con guiones
    const regex = /^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$/;
    if (!regex.test(value)) {
        showFieldError(input, "Invalid ORCID format (expected 0000-0000-0000-0000)");
        return false;
    }

    // Chequeo contra API pública de ORCID
    try {
        const res = await fetch(`https://pub.orcid.org/v3.0/${value}`, {
            headers: { "Accept": "application/json" }
        });

        if (res.status === 200) {
            clearFieldError(input);
            return true;
        } else {
            showFieldError(input, "ORCID not found");
            return false;
        }
    } catch (err) {
        showFieldError(input, "Error contacting ORCID");
        return false;
    }
}


// ----------------- HELPERS DE ERRORES -----------------

function showFieldError(input, message) {
    input.classList.add("is-invalid");
    let feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains("invalid-feedback")) {
        feedback.textContent = message;
    }
}

function clearFieldError(input) {
    input.classList.remove("is-invalid");
    let feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains("invalid-feedback")) {
        feedback.textContent = "";
    }
}

// ----------------- VALIDAR TODOS LOS AUTORES -----------------

export async function validateAllAuthors() {
    let isValid = true;

    // Validar nombres
    document.querySelectorAll("#authors-container .author-name").forEach(input => {
        validateNameInput(input);
        if (input.classList.contains("is-invalid")) isValid = false;
    });

    // Validar afiliaciones
    document.querySelectorAll("#authors-container .author-affiliation").forEach(input => {
        validateAffiliationInput(input);
        if (input.classList.contains("is-invalid")) isValid = false;
    });

    // Validar ORCID (async porque consulta la API)
    for (const input of document.querySelectorAll("#authors-container .orcid-input")) {
        const valid = await validateOrcidInput(input);
        if (!valid) isValid = false;
    }

    return isValid;
}

// ----------------- LÓGICA DE AUTORES (Mustache, botones, drag & drop) -----------------

// Generate a unique ID for HTML IDs (not used in form field names)
function generateUniqueId() {
    return '_' + Math.random().toString(36).slice(2, 11);
}

// Global index counter for authors (used in name attributes)
let authorIndex = 0;

export function initializeAuthors() {
    // Botón "Add author"
    document.getElementById('add-author-btn').addEventListener('click', function () {
        const uniqueId = generateUniqueId();
        const template = document.getElementById('author-template').innerHTML;

        const rendered = Mustache.render(template, {
            id: uniqueId,
            index: authorIndex
        });

        document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);

        authorIndex++;
    });

    // Botón "Remove author"
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

    // Drag & drop
    const containers = document.querySelectorAll(".draggable-zone");
    new Draggable.Sortable(containers, {
        draggable: ".draggable",
        handle: ".draggable .draggable-handle",
        mirror: {
            appendTo: "body",
            constrainDimensions: true
        }
    });

    // Botón "Add myself"
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

            // Rellenar campos del bloque recién creado
            const base = document.getElementById(`author-${uniqueId}`);
            base.querySelector(`input[name="authors${authorIndex}[name]"]`).value = `${data.name} ${data.surname}`;
            base.querySelector(`input[name="authors${authorIndex}[affiliation]"]`).value = data.affiliation || "";
            base.querySelector(`input[name="authors${authorIndex}[orcid]"]`).value = data.orcid || "";

            // Deshabilitar botón "myself" hasta que se borre
            btn.dataset.myselfId = uniqueId;
            btn.disabled = true;

            authorIndex++;
        } catch (err) {
            console.error("Add myself failed:", err);
            alert(`Error fetching your profile: ${err.message}`);
        }
    });

    // Validación en blur
    document.addEventListener("blur", (e) => {
        if (e.target.classList.contains("author-name")) {
            validateNameInput(e.target);
        }
        if (e.target.classList.contains("author-affiliation")) {
            validateAffiliationInput(e.target);
        }
        if (e.target.classList.contains("orcid-input")) {
            // lanzamos validación completa (formato + API)
            validateAllAuthors();
        }
    }, true);
}
