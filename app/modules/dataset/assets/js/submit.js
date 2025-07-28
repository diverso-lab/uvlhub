export function initializeSubmit() {
    document.querySelector('[data-kt-stepper-action="submit"]').addEventListener('click', async function () {
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

        // Submit to backend
        try {

            console.log("[DEBUG] FormData entries:");
            for (const [key, value] of formData.entries()) {
                console.log(`${key} -> ${value}`);
            }

            const response = await fetch("/datasets/upload", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                alert("Dataset created successfully");
                window.location.href = "/datasets/list";
            } else {
                alert("Error creating dataset: " + JSON.stringify(result));
            }

        } catch (error) {
            console.error("Error on submit:", error);
            alert("Error in the connection to the server");
        }
    });
}
