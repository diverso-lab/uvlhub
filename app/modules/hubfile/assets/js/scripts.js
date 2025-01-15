/*
    Dropzone
*/

import { FeatureModel } from "uvl-parser";

// set the dropzone container id
const id = "#uvl_dropzone";
const dropzone = document.querySelector(id);

// set the preview element template
var previewNode = dropzone.querySelector(".dropzone-item");
previewNode.id = "";
var previewTemplate = previewNode.parentNode.innerHTML;
previewNode.parentNode.removeChild(previewNode);

var myDropzone = new Dropzone(id, { // Make the whole body a dropzone
    url: "/hubfile/upload", // Set the url for your upload script location
    parallelUploads: 20,
    maxFilesize: 1, // Max filesize in MB
    previewTemplate: previewTemplate,
    previewsContainer: id + " .dropzone-items", // Define the container to display the previews
    clickable: id + " .dropzone-select", // Define the element that should be used as click trigger to select files.
    acceptedFiles: ".uvl" // Only accept files with .uvl extension
});

myDropzone.on("addedfile", function (file) {

    // Generar un identificador único para el archivo
    file.upload = file.upload || {};
    file.upload.uuid = crypto.randomUUID(); // Generar un UUID único

    // Validar extensión del archivo
    let ext = file.name.split('.').pop();
    if (ext !== 'uvl') {
        this.removeFile(file); // Elimina el archivo de la lista

        // Mostrar mensaje de error debajo del archivo
        let fileError = document.createElement('div');
        fileError.classList.add('dropzone-file-error');
        fileError.innerHTML = `<span class="badge bg-danger">Invalid file extension: ${file.name}</span>`;
        file.previewElement.appendChild(fileError);
        return;
    }

    // Leer el contenido del archivo
    let reader = new FileReader();
    reader.onload = (event) => {
        const fileContent = event.target.result; // Contenido del archivo UVL

        try {
            // Intentar parsear el contenido UVL
            const featureModel = new FeatureModel(fileContent);
            const tree = featureModel.getFeatureModel(); // El árbol parseado del UVL
            console.log("Parsed UVL Feature Model:", tree);

            // Si el archivo es válido, agregar un mensaje "sintaxis válida"
            let fileSuccess = document.createElement('div');
            fileSuccess.classList.add('dropzone-file-success');
            fileSuccess.innerHTML = `<span class="badge bg-success">Valid syntax</span>`;
            file.previewElement.querySelector('.dropzone-file').appendChild(fileSuccess);
        } catch (error) {
            // Si hay un error de sintaxis, mostrar mensaje debajo del archivo
            console.error("Error parsing UVL file:", error.message);

            let fileError = document.createElement('div');
            fileError.classList.add('alert', 'alert-danger', 'mt-2', 'p-2'); // Estilos de KeenThemes
            fileError.innerHTML = `<strong>Error:</strong> Syntax error: ${error.message}`;
            file.previewElement.querySelector('.dropzone-file').appendChild(fileError);

            file.previewElement.classList.add('dropzone-invalid'); // Marcar como inválido

            // this.removeFile(file); // Elimina el archivo de Dropzone
        }

        // Si el archivo es válido, mantenerlo en Dropzone
        const dropzoneItems = dropzone.querySelectorAll('.dropzone-item');
        dropzoneItems.forEach(dropzoneItem => {
            dropzoneItem.style.display = '';
        });
    };

    // Leer el archivo como texto
    reader.readAsText(file);
});

myDropzone.on("removedfile", function (file) {
    console.log("Archivo eliminado:", file.name);

    // Realizar una llamada al servidor para eliminar el archivo
    fetch('/hubfile/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            filename: file.name, // Nombre original del archivo
            uuid: file.upload.uuid // UUID generado al subir
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Error al eliminar el archivo del servidor");
        }
        console.log("Archivo eliminado del servidor con éxito");
    })
    .catch(error => {
        console.error("Error al eliminar el archivo:", error);
    });
});

// Update the total progress bar
myDropzone.on("totaluploadprogress", function (progress) {
    const progressBars = dropzone.querySelectorAll('.progress-bar');
    progressBars.forEach(progressBar => {
        progressBar.style.width = progress + "%";
    });
});

myDropzone.on("sending", function (file, xhr, formData) {
    // Show the total progress bar when upload starts
    const progressBars = dropzone.querySelectorAll('.progress-bar');
    progressBars.forEach(progressBar => {
        progressBar.style.opacity = "1";
    });

    // Generar un identificador único si no existe
    file.upload = file.upload || {};
    if (!file.upload.uuid) {
        file.upload.uuid = crypto.randomUUID(); // Generar un UUID único
    }

    // Agregar el UUID al FormData que se envía al servidor
    formData.append("uuid", file.upload.uuid);
});


// Hide the total progress bar when nothing"s uploading anymore
myDropzone.on("complete", function (progress) {
    const progressBars = dropzone.querySelectorAll('.dz-complete');

    setTimeout(function () {
        progressBars.forEach(progressBar => {
            progressBar.querySelector('.progress-bar').style.opacity = "0";
            progressBar.querySelector('.progress').style.opacity = "0";
        });
    }, 300);
});
