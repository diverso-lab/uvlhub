import { FeatureModel } from "uvl-parser";

/*
    Dropzone pagination
*/

document.addEventListener('DOMContentLoaded', function () {

    // Pagination settings
    const filesPerPage = 5; // Number of files per page
    let currentPage = 1; // Current page
    let totalPages = 1; // Total number of pages

    // Create the pagination container
    let paginationContainer = document.querySelector('.pagination'); // Unique selector to avoid duplicates
    if (!paginationContainer) {
        paginationContainer = document.createElement('ul');
        paginationContainer.classList.add('pagination', 'mt-3');
        document.querySelector("#uvl_dropzone").parentNode.appendChild(paginationContainer);
    }

    /*
        Dropzone
    */

    // set the dropzone container id
    const id = "#uvl_dropzone";
    const dropzone = document.querySelector(id);

    // set the preview element template
    var previewNode = dropzone.querySelector(".dropzone-item");
    previewNode.id = "";
    var previewTemplate = previewNode.parentNode.innerHTML;
    previewNode.parentNode.removeChild(previewNode);

    window.myDropzone = new Dropzone(id, {
        url: "/hubfile/upload",
        parallelUploads: 20,
        maxFilesize: 1,
        previewTemplate: previewTemplate,
        previewsContainer: id + " .dropzone-items",
        clickable: id + " .dropzone-select",
        acceptedFiles: ".uvl"
    });

    // Set a global flag to indicate the readiness of myDropzone
    window.myDropzoneReady = true;

    // Dispatch the custom event
    document.dispatchEvent(new Event("myDropzoneReady"));

    updateStep2Summary();

    // Update the visibility of the files according to the current page
    function updatePagination(files) {
        const totalFiles = files.length;
        totalPages = Math.ceil(totalFiles / filesPerPage);

        // Adjust the current page if it's out of range
        if (currentPage > totalPages) {
            currentPage = totalPages || 1; // If no more pages, go back to page 1
        }

        // Display only the files for the current page
        files.forEach((file, index) => {
            const start = (currentPage - 1) * filesPerPage;
            const end = currentPage * filesPerPage;
            file.previewElement.style.display = index >= start && index < end ? '' : 'none';
        });

        // Render the pagination
        renderPagination();
    }

    // Function to render pagination buttons
    function renderPagination() {
        paginationContainer.innerHTML = ''; // Clear existing pagination

        // If no files, hide the pagination container
        if (myDropzone.files.length === 0) {
            paginationContainer.style.display = 'none';
            return;
        } else {
            paginationContainer.style.display = 'flex'; // Ensure it's visible if there are files
        }

        // "Previous" button
        const prevButton = document.createElement('li');
        prevButton.classList.add('page-item', 'previous');
        if (currentPage === 1) prevButton.classList.add('disabled');
        prevButton.innerHTML = `<a href="#" class="page-link"><i class="previous"></i></a>`;
        prevButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                updatePagination(myDropzone.files);
            }
        });
        paginationContainer.appendChild(prevButton);

        // Page buttons
        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement('li');
            pageButton.classList.add('page-item');
            if (i === currentPage) pageButton.classList.add('active');
            pageButton.innerHTML = `<a href="#" class="page-link">${i}</a>`;
            pageButton.addEventListener('click', (e) => {
                e.preventDefault();
                currentPage = i;
                updatePagination(myDropzone.files);
            });
            paginationContainer.appendChild(pageButton);
        }

        // "Next" button
        const nextButton = document.createElement('li');
        nextButton.classList.add('page-item', 'next');
        if (currentPage === totalPages || totalPages === 0) nextButton.classList.add('disabled');
        nextButton.innerHTML = `<a href="#" class="page-link"><i class="next"></i></a>`;
        nextButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination(myDropzone.files);
            }
        });
        paginationContainer.appendChild(nextButton);
    }

    // Función para actualizar el resumen de archivos UVL
    function updateStep2Summary() {
        const step2SummaryDiv = document.getElementById('step_2_summary');
        const fileCount = myDropzone.files.length;
    
        if (fileCount > 0) {
            step2SummaryDiv.innerHTML = `
                <span class="badge badge-circle badge-outline badge-primary" style="text-color: white;">${fileCount}</span> UVL file${fileCount > 1 ? 's' : ''} uploaded
            `;
        } else {
            step2SummaryDiv.innerHTML = 'No UVL files uploaded yet';
        }
    }

    myDropzone.on("addedfile", function (file) {
        file.upload = file.upload || {};
        file.upload.uuid = crypto.randomUUID(); // Generate a unique UUID

        // Validate file extension
        let ext = file.name.split('.').pop();
        if (ext !== 'uvl') {
            this.removeFile(file); // Remove the file from the list

            // Show error message below the file
            let fileError = document.createElement('div');
            fileError.classList.add('dropzone-file-error');
            fileError.innerHTML = `<span class="badge bg-danger">Invalid file extension: ${file.name}</span>`;
            file.previewElement.appendChild(fileError);
            return;
        }

        // Read the content of the file
        let reader = new FileReader();
        reader.onload = (event) => {
            const fileContent = event.target.result; // UVL file content

            try {
                // Attempt to parse the UVL content
                const featureModel = new FeatureModel(fileContent);
                const tree = featureModel.getFeatureModel(); // Parsed UVL tree
                console.log("Parsed UVL Feature Model:", tree);

                // If the file is valid, add a "valid syntax" message
                let fileSuccess = document.createElement('div');
                fileSuccess.classList.add('dropzone-file-success');
                fileSuccess.innerHTML = `<span class="badge bg-success">Valid syntax</span>`;
                file.previewElement.querySelector('.dropzone-file').appendChild(fileSuccess);
                updateStep2Summary();
            } catch (error) {
                console.error("Error parsing UVL file:", error.message);

                // Create a persistent error message
                const persistentError = document.createElement('div');
                persistentError.classList.add('alert', 'alert-danger', 'mt-2', 'p-2');
                persistentError.innerHTML = `<strong>Error:</strong> Syntax error: ${error.message}`;
                file.previewElement.querySelector('.dropzone-file').appendChild(persistentError);

                // Mark the file as invalid in the UI
                file.previewElement.classList.add('dropzone-invalid');

                // Remove the file from Dropzone but keep the error message visible
                setTimeout(() => {
                    this.removeFile(file);
                    dropzone.querySelector('.dropzone-items').appendChild(file.previewElement);
                }, 500); // Small delay to visually show the addition
            }
        };

        // Read the file as text
        reader.readAsText(file);

        // Update pagination at the end
        updatePagination(myDropzone.files);
    });


    myDropzone.on("removedfile", function (file) {
        fetch('/hubfile/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name, uuid: file.upload.uuid }),
        })
            .then(response => {
                if (!response.ok) throw new Error("Error deleting file from server");
                updatePagination(myDropzone.files);
                updateStep2Summary();
            })
            .catch(error => console.error("Error deleting the file:", error));
    });

    myDropzone.on("totaluploadprogress", function (progress) {
        const progressBars = dropzone.querySelectorAll('.progress-bar');
        progressBars.forEach(progressBar => {
            progressBar.style.width = progress + "%";
        });
    });

    myDropzone.on("sending", function (file, xhr, formData) {
        const progressBars = dropzone.querySelectorAll('.progress-bar');
        progressBars.forEach(progressBar => {
            progressBar.style.opacity = "1";
        });

        file.upload = file.upload || {};
        if (!file.upload.uuid) {
            file.upload.uuid = crypto.randomUUID();
        }

        formData.append("uuid", file.upload.uuid);
    });

    myDropzone.on("complete", function () {
        const progressBars = dropzone.querySelectorAll('.dz-complete');

        setTimeout(function () {
            progressBars.forEach(progressBar => {
                progressBar.querySelector('.progress-bar').style.opacity = "0";
                progressBar.querySelector('.progress').style.opacity = "0";
            });
        }, 300);
    });
});
