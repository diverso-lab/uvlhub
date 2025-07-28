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
        document.querySelectorAll("#authors-container .draggable").forEach(authorCard => {
            const id = authorCard.id.replace("author-", "");
            formData.append("authors[][name]", document.querySelector(`#name_${id}`).value);
            formData.append("authors[][affiliation]", document.querySelector(`#affiliation_${id}`).value);
            formData.append("authors[][orcid]", document.querySelector(`#orcid_${id}`).value);
        });

        // Submit to backend
        try {
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
