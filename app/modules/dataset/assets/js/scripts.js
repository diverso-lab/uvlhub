import Mustache from 'mustache';
import ClassicEditor from '@ckeditor/ckeditor5-build-classic';

document.addEventListener('DOMContentLoaded', function () {

    Mustache.tags = ['[[', ']]']; // Establece los nuevos delimitadores
    
    // Función para generar un ID aleatorio
    function generateUniqueId() {
        return '_' + Math.random().toString(36).slice(2, 11);
    }
    
    // Botón para agregar autores
    document.getElementById('add-author-btn').addEventListener('click', function () {
        const uniqueId = generateUniqueId(); // Genera un ID único
        const template = document.getElementById('author-template').innerHTML; // Obtiene el template
        const rendered = Mustache.render(template, { id: uniqueId }); // Renderiza el template con Mustache

        // Agrega el nuevo autor al contenedor
        document.getElementById('authors-container').insertAdjacentHTML('beforeend', rendered);
    });

    // Evento delegado para eliminar autores
    document.getElementById('authors-container').addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-author') || e.target.closest('.remove-author')) {
            const button = e.target.closest('.remove-author');
            const authorId = button.getAttribute('data-id');
            document.getElementById(`author-${authorId}`).remove(); // Elimina el autor
        }
    });

    /*
        Stepper
    */

    // Stepper element
    var element = document.querySelector("#stepper_upload_dataset");

    // Initialize Stepper
    var stepper = new KTStepper(element);

    // Continue button (global)
    var continueButton = document.querySelector('#continue_button');

    // Step index for file validation
    const stepToValidateFiles = 2; // Define the step where file validation should occur

    // Function to enable/disable the Continue button
    function toggleContinueButton(enable) {
        if (enable) {
            continueButton.classList.remove("disabled"); // Remove the 'disabled' class
        } else {
            continueButton.classList.add("disabled"); // Add the 'disabled' class
        }
    }    

    // Function to handle step changes
    function handleStepChange() {
        console.log("detectada funcion handleStepChange");
        const currentStep = stepper.getCurrentStepIndex(); // Get current step index (1-based)

        if (currentStep === stepToValidateFiles) {
            // On the defined step, disable the Continue button if no files are uploaded
            toggleContinueButton(myDropzone.files.length > 0);
            console.log(`Esto aquí salta en el paso ${stepToValidateFiles}`);
        } else {
            // Enable the button for other steps
            toggleContinueButton(true);
        }
    }

    // Wait for myDropzone to be available
    console.log("dataset.js DOMContentLoaded triggered");

    if (window.myDropzoneReady) {
        console.log("myDropzone is already ready (retroactively detected).");
        initializeDropzoneLogic();
    } else {
        console.log("myDropzoneReady not detected yet. Adding event listener.");
        document.addEventListener("myDropzoneReady", function () {
            console.log("myDropzoneReady event detected.");
            initializeDropzoneLogic();
        });
    }

    // Function to initialize Dropzone-related logic
    function initializeDropzoneLogic() {
        console.log("Initializing Dropzone logic...");

        myDropzone.on("addedfile", function () {
            console.log("File added to Dropzone. Current step:", stepper.getCurrentStepIndex());
            if (stepper.getCurrentStepIndex() === stepToValidateFiles) {
                toggleContinueButton(myDropzone.files.length > 0);
                console.log("Continue button updated. Files in Dropzone:", myDropzone.files.length);
            }
        });

        myDropzone.on("removedfile", function () {
            console.log("File removed from Dropzone. Current step:", stepper.getCurrentStepIndex());
            if (stepper.getCurrentStepIndex() === stepToValidateFiles) {
                toggleContinueButton(myDropzone.files.length > 0);
                console.log("Continue button updated. Files in Dropzone:", myDropzone.files.length);
            }
        });

        stepper.on("kt.stepper.changed", function () {
            console.log("Stepper changed. Current step:", stepper.getCurrentStepIndex());
            handleStepChange();
        });

        stepper.on("kt.stepper.next", function (stepper) {
            const currentStep = stepper.getCurrentStepIndex();
            console.log("Attempting to move to the next step. Current step:", currentStep);
            if (currentStep === stepToValidateFiles && myDropzone.files.length === 0) {
                console.log(`Prevented moving to step ${stepToValidateFiles + 1}. No files uploaded.`);
                alert("Please upload at least one file before continuing.");
                return;
            }
            console.log("Moving to the next step.");
            stepper.goNext();
        });
    }

    stepper.on("kt.stepper.previous", function (stepper) {
        stepper.goPrevious(); // go previous step
    });

    /*
        Tagify
    */
    new Tagify(document.querySelector("#tags"));

    /*
        Editor
    */
    ClassicEditor
    .create(document.querySelector('#kt_docs_ckeditor_classic'), {
        plugins: [
            'Essentials', 'Paragraph', 'Heading', 'Bold', 'Italic', 'List', 'Link'
        ],
        toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|', 'undo', 'redo'],
        markdown: {
            // Optional: Set specific options for Markdown if needed
        }
    })
    .then(editor => {
        console.log('CKEditor initialized with Markdown support:', editor);

        // Example: Log the Markdown content on change
        editor.model.document.on('change:data', () => {
            console.log('Markdown Content:', editor.getData());
        });
    })
    .catch(error => {
        console.error('Error initializing CKEditor:', error);
    });
    
    /*
        Authors
    */

    var containers = document.querySelectorAll(".draggable-zone");

    var swappable = new Draggable.Sortable(containers, {
        draggable: ".draggable",
        handle: ".draggable .draggable-handle",
        mirror: {
            appendTo: "body",
            constrainDimensions: true
        }
    });
});
