export function initializeSubmit() {
    const submitBtn = document.querySelector('[data-kt-stepper-action="submit"]');
    const continueBtn = document.querySelector('[data-kt-stepper-action="next"]');
    const errorContainer = document.getElementById("upload-error");

    submitBtn.addEventListener('click', async function () {
        // Reset errores visuales
        errorContainer.classList.add("d-none");
        errorContainer.innerHTML = "";

        // Mostrar mensaje y bloquear botones
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = "Submitting...";
        submitBtn.disabled = true;
        continueBtn.disabled = true;

        const formData = new FormData();

        // Dataset type
        const datasetType = document.querySelector('input[name="dataset_type"]:checked')?.value || 'draft';
        formData.append("dataset_type", datasetType);

        // Dataset fields
        formData.append("title", document.querySelector('input[name="title"]').value);
        formData.append("description", tinymce.get("dataset_editor").getContent());
        formData.append("publication_type", document.querySelector('select[name="publication_type"]').value);
        formData.append("publication_doi", document.querySelector('input[name="publication_doi"]').value);

        // Tags
        const tagsRaw = document.querySelector("#tags").value;
        try {
            const parsed = JSON.parse(tagsRaw);
            parsed.forEach(tag => formData.append("tags[]", tag.value));
        } catch (e) {
            console.warn("Invalid tags JSON");
        }

        // Authors
        let index = 0;
        document.querySelectorAll('#authors-container input[name$="[name]"]').forEach(nameInput => {
            const authorRoot = nameInput.closest('.draggable');
            const affInput = authorRoot.querySelector('input[name$="[affiliation]"]');
            const orcidInput = authorRoot.querySelector('input[name$="[orcid]"]');

            const name = nameInput.value.trim();
            const affiliation = affInput?.value.trim() || "";
            const orcid = orcidInput?.value.trim() || "";

            if (name) {
                formData.append(`authors[${index}][name]`, name);
                formData.append(`authors[${index}][affiliation]`, affiliation);
                formData.append(`authors[${index}][orcid]`, orcid);
                index++;
            }
        });

        try {
            const response = await fetch("/datasets/upload", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                window.location.href = "/datasets/list";
            } else {
                errorContainer.innerHTML = `❌ Error creating dataset:<br><code>${JSON.stringify(result)}</code>`;
                errorContainer.classList.remove("d-none");
            }

        } catch (error) {
            console.error("Error on submit:", error);
            errorContainer.innerHTML = "❌ Error connecting to the server. Please try again.";
            errorContainer.classList.remove("d-none");
        } finally {
            // Restaurar estado del botón
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            continueBtn.disabled = false;
        }
    });
}
