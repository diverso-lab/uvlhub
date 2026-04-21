import Mustache from 'mustache';

// Configure Mustache delimiters
Mustache.tags = ['[[', ']]'];

// ----------------- VALIDATORS -----------------

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
        clearFieldError(input); // empty is valid
        return true;
    }

    // Standard ORCID format with dashes
    const regex = /^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$/;
    if (!regex.test(value)) {
        showFieldError(input, "Invalid ORCID format (expected 0000-0000-0000-0000)");
        return false;
    }

    // Check against the public ORCID API
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


// ----------------- ERROR HELPERS -----------------

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

// ----------------- VALIDATE ALL AUTHORS -----------------

export async function validateAllAuthors() {
    let isValid = true;

    // Validate names
    document.querySelectorAll("#authors-container .author-name").forEach(input => {
        validateNameInput(input);
        if (input.classList.contains("is-invalid")) isValid = false;
    });

    // Validate affiliations
    document.querySelectorAll("#authors-container .author-affiliation").forEach(input => {
        validateAffiliationInput(input);
        if (input.classList.contains("is-invalid")) isValid = false;
    });

    // Validate ORCID (async because it queries the API)
    for (const input of document.querySelectorAll("#authors-container .orcid-input")) {
        const valid = await validateOrcidInput(input);
        if (!valid) isValid = false;
    }

    return isValid;
}

// ----------------- AUTHORS LOGIC (Mustache, buttons, drag & drop) -----------------

// Generate a unique ID for HTML IDs (not used in form field names)
function generateUniqueId() {
    return '_' + Math.random().toString(36).slice(2, 11);
}

// Global index counter for authors (used in name attributes)
let authorIndex = Number(window.initialAuthorIndex || 0);

export function initializeAuthors() {
    // "Add author" button
    document.getElementById('add-author-btn').addEventListener('click', function () {
        const uniqueId = generateUniqueId();
        const template = document.getElementById('author-template').innerHTML;

        const rendered = Mustache.render(template, {
            id: uniqueId,
            nameField: `authors[${authorIndex}][name]`,
            affiliationField: `authors[${authorIndex}][affiliation]`,
            orcidField: `authors[${authorIndex}][orcid]`
        });

        document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);

        authorIndex++;
    });

    // "Remove author" button
    document.getElementById('authors-container').addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-author') || e.target.closest('.remove-author')) {
            const button = e.target.closest('.remove-author');
            const authorId = button.getAttribute('data-id');
            const node = document.getElementById(`author-${authorId}`);
            if (node) node.remove();

            // If the deletion targets the "myself" block, re-enable its button.
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

    // "Add myself" button
    document.getElementById('add-myself-btn').addEventListener('click', async function () {
        const btn = this;
        try {
            const res = await fetch('/api/me');
            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Backend error ${res.status}: ${text}`);
            }
            const data = await res.json();

            // Check whether an author with this ORCID is already present.
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
                nameField: `authors[${authorIndex}][name]`,
                affiliationField: `authors[${authorIndex}][affiliation]`,
                orcidField: `authors[${authorIndex}][orcid]`
            });

            document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);

            // Fill in the fields of the newly created block.
            const base = document.getElementById(`author-${uniqueId}`);
            base.querySelector('.author-name').value = `${data.name} ${data.surname}`;
            base.querySelector('.author-affiliation').value = data.affiliation || "";
            base.querySelector('.orcid-input').value = data.orcid || "";

            // Disable the "myself" button until the block is removed.
            btn.dataset.myselfId = uniqueId;
            btn.disabled = true;

            authorIndex++;
        } catch (err) {
            console.error("Add myself failed:", err);
            alert(`Error fetching your profile: ${err.message}`);
        }
    });

    // Blur validation
    document.addEventListener("blur", (e) => {
        if (e.target.classList.contains("author-name")) {
            validateNameInput(e.target);
        }
        if (e.target.classList.contains("author-affiliation")) {
            validateAffiliationInput(e.target);
        }
        if (e.target.classList.contains("orcid-input")) {
            // Run the full validation (format + API).
            validateAllAuthors();
        }
    }, true);
}
