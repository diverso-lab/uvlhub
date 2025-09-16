import { FeatureModel } from "uvl-parser";

document.addEventListener("DOMContentLoaded", function () {
    Dropzone.autoDiscover = false;

    const id = "#uvl_dropzone";
    const zoneEl = document.querySelector(id);

    // Template de preview
    const previewNode = zoneEl.querySelector(".dropzone-item");
    previewNode.id = "";
    const previewTemplate = previewNode.parentNode.innerHTML;
    previewNode.parentNode.removeChild(previewNode);

    // Crear Dropzone
    window.myDropzone = new Dropzone(id, {
        url: "/hubfile/upload",
        autoProcessQueue: true,
        acceptedFiles: ".uvl,.zip",
        parallelUploads: 20,
        previewTemplate: previewTemplate,
        previewsContainer: id + " .dropzone-items",
        clickable: id + " .dropzone-select",
        accept: function (file, done) {
            // límite en bytes (100 MB decimales)
            const maxZipSize = 100 * 1000 * 1000;

            if (file.name.toLowerCase().endsWith(".zip") && file.size > maxZipSize) {
                const sizeMB = (file.size / 1000000).toFixed(1); // en MB con 1 decimal
                done(`ZIP file too big (${sizeMB} MB). Max size is 100 MB.`);
                return;
            }

            const uvlFiles = this.files.filter(f => f.name?.toLowerCase().endsWith(".uvl"));
            if (uvlFiles.length > 20) {
                done("You tried to upload more than 20 .uvl files. Please use a ZIP instead.");
            } else {
                done();
            }
        }

    });


    window.myDropzoneReady = true;
    document.dispatchEvent(new Event("myDropzoneReady"));

    myDropzone.on("removedfile", function () {
    // ¿Quedan archivos con error?
    const hasErrors = this.files.some(f => f.status === Dropzone.ERROR);

    if (!hasErrors) {
        const errBox = document.getElementById("upload-error");
        if (errBox) {
            errBox.classList.add("d-none");
            errBox.innerHTML = "";
        }
    }
});


    /*
     * Botón "Clear all"
     */
    const clearBtn = document.getElementById("clear-all-btn");
    if (clearBtn) {
        clearBtn.style.display = "none";

        clearBtn.addEventListener("click", function (e) {
            e.preventDefault();

            // 🚀 Limpieza en el backend
            fetch("/hubfile/clear_temp", { method: "POST" })
                .catch(err => console.error("Error limpiando backend:", err));

            // 🧹 Limpieza visual
            myDropzone.removeAllFiles(true);
            updateStep2Summary();
            updatePagination(myDropzone.files);
            clearBtn.style.display = "none";

            // 🔕 Ocultar mensaje de error
            const errBox = document.getElementById("upload-error");
            if (errBox) {
                errBox.classList.add("d-none");
                errBox.innerHTML = "";
            }
        });

        myDropzone.on("addedfile", function () {
            if (myDropzone.files.length > 0) {
                clearBtn.style.display = "inline-block";
            }
        });

        myDropzone.on("removedfile", function () {
            if (myDropzone.files.length === 0) {
                clearBtn.style.display = "none";
            }
        });
    }

    /*
     * Paginación
     */
    const filesPerPage = 5;
    let currentPage = 1;
    let totalPages = 1;
    let paginationContainer = document.querySelector(".pagination");
    if (!paginationContainer) {
        paginationContainer = document.createElement("ul");
        paginationContainer.classList.add("pagination", "mt-3");
        document.querySelector("#uvl_dropzone").parentNode.appendChild(paginationContainer);
    }

    function updatePagination(files) {
        const totalFiles = files.length;
        totalPages = Math.ceil(totalFiles / filesPerPage);
        if (currentPage > totalPages) currentPage = totalPages || 1;

        files.forEach((file, index) => {
            const start = (currentPage - 1) * filesPerPage;
            const end = currentPage * filesPerPage;
            file.previewElement.style.display = index >= start && index < end ? "" : "none";
        });

        renderPagination();
    }

    function renderPagination() {
        paginationContainer.innerHTML = "";
        if (myDropzone.files.length === 0) {
            paginationContainer.style.display = "none";
            return;
        } else {
            paginationContainer.style.display = "flex";
        }

        const prevButton = document.createElement("li");
        prevButton.classList.add("page-item", "previous");
        if (currentPage === 1) prevButton.classList.add("disabled");
        prevButton.innerHTML = `<a href="#" class="page-link"><i class="previous"></i></a>`;
        prevButton.addEventListener("click", e => {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                updatePagination(myDropzone.files);
            }
        });
        paginationContainer.appendChild(prevButton);

        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement("li");
            pageButton.classList.add("page-item");
            if (i === currentPage) pageButton.classList.add("active");
            pageButton.innerHTML = `<a href="#" class="page-link">${i}</a>`;
            pageButton.addEventListener("click", e => {
                e.preventDefault();
                currentPage = i;
                updatePagination(myDropzone.files);
            });
            paginationContainer.appendChild(pageButton);
        }

        const nextButton = document.createElement("li");
        nextButton.classList.add("page-item", "next");
        if (currentPage === totalPages || totalPages === 0) nextButton.classList.add("disabled");
        nextButton.innerHTML = `<a href="#" class="page-link"><i class="next"></i></a>`;
        nextButton.addEventListener("click", e => {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination(myDropzone.files);
            }
        });
        paginationContainer.appendChild(nextButton);
    }

    function updateStep2Summary() {
        const step2SummaryDiv = document.getElementById("step_2_summary");
        const fileCount = myDropzone.files.length;
        if (fileCount > 0) {
            step2SummaryDiv.innerHTML = `
                <span class="badge badge-circle badge-outline badge-primary">${fileCount}</span>
                UVL file${fileCount > 1 ? "s" : ""} uploaded
            `;
        } else {
            step2SummaryDiv.innerHTML = "No UVL files uploaded yet";
        }
    }

    /*
     * Validación de archivos .uvl en sintaxis
     */
    myDropzone.on("addedfile", function (file) {
        // Guardar UUID
        file.upload = file.upload || {};
        if (!file.upload.uuid) file.upload.uuid = crypto.randomUUID();

        const ext = (file.name.split(".").pop() || "").toLowerCase();

        if (ext === "uvl") {
            const reader = new FileReader();
            reader.onload = event => {
                try {
                    const fm = new FeatureModel(event.target.result);
                    fm.getFeatureModel();

                    const ok = document.createElement("div");
                    ok.classList.add("dropzone-file-success");
                    ok.innerHTML = `<span class="badge bg-success">Valid syntax</span>`;
                    file.previewElement.querySelector(".dropzone-file").appendChild(ok);

                    updateStep2Summary();
                } catch (error) {
                    const persistentError = document.createElement("div");
                    persistentError.classList.add("alert", "alert-danger", "mt-2", "p-2");
                    persistentError.innerHTML = `<strong>Error:</strong> Syntax error: ${error.message}`;
                    file.previewElement.querySelector(".dropzone-file").appendChild(persistentError);
                    file.previewElement.classList.add("dropzone-invalid");
                }
            };
            reader.readAsText(file);
        }

        updatePagination(this.files);
    });

    // Adjuntar uuid en la subida
    myDropzone.on("sending", function (file, xhr, formData) {
        file.upload = file.upload || {};
        formData.append("uuid", file.upload.uuid);
    });

    // Marcar subidos
    myDropzone.on("success", function (file, response) {
        // ✅ confiar en que el backend devuelve siempre { filename: "..." }
        file.serverFilename = response.filename;
        file.uploadedToServer = true;
    });

    // Eliminar en servidor
    myDropzone.on("removedfile", function (file) {
        if (!file.uploadedToServer) return;

        fetch("/hubfile/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filename: file.serverFilename,
                uuid: file.upload.uuid
            }),
        })
            .then(res => {
                if (!res.ok) throw new Error("Error deleting file from server");
                updatePagination(myDropzone.files);
                updateStep2Summary();
            })
            .catch(err => console.error("Error deleting the file:", err));
    });

    /*
     * Mostrar banner cuando se rechacen archivos
     */
    myDropzone.on("error", function (file, message) {
        const errBox = document.getElementById("upload-error");
        if (errBox) {
            errBox.classList.remove("d-none");
            errBox.innerHTML = message;
        }
        // 🔕 quitar el archivo rechazado del preview
        //this.removeFile(file);
    });
});
