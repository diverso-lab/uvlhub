import Mustache from 'mustache';

// Configure Mustache delimiters
Mustache.tags = ['[[', ']]'];

// Generate a unique ID
function generateUniqueId() {
    return '_' + Math.random().toString(36).slice(2, 11);
}

// Initialize logic for adding and removing authors
export function initializeAuthors() {
    // Button to add authors
    document.getElementById('add-author-btn').addEventListener('click', function () {
        const uniqueId = generateUniqueId();
        const template = document.getElementById('author-template').innerHTML;
        const rendered = Mustache.render(template, { id: uniqueId });

        // Add the new author to the container
        document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);
    });

    // Delegated event to remove authors
    document.getElementById('authors-container').addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-author') || e.target.closest('.remove-author')) {
            const button = e.target.closest('.remove-author');
            const authorId = button.getAttribute('data-id');
            document.getElementById(`author-${authorId}`).remove(); // Remove the author
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
}
