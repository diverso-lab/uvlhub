import { validateAllAuthors } from './authors.js';

// Select the Stepper element
const stepperElement = document.querySelector("#stepper_upload_dataset");

// Initialize Stepper
const stepper = new KTStepper(stepperElement);

// Global Continue button
const continueButton = document.querySelector("#continue_button");

// Step where file validation occurs
const stepToValidateFiles = 2;

// Step logic handlers
const stepHandlers = {
    1: {
        onEnter: () => {
            console.log("Entering Step 1");
            toggleContinueButton(true);
        },
        onExit: () => {
            console.log("Exiting Step 1");
        },
    },
    2: {
        onEnter: () => {
            console.log("Entering Step 2");
            initializeDropzoneListeners();
            toggleContinueButton(myDropzone.files.length > 0);
        },
        onExit: () => {
            console.log("Exiting Step 2");
            removeDropzoneListeners();
        },
    },
    3: {
        onEnter: () => {
            console.log("Entering Step 3");
            validateStep3(); // comprobar al entrar
            initializeStep3Listeners(); // activar listeners
        },
        onExit: () => {
            console.log("Exiting Step 3");
            removeStep3Listeners();
        },
    },
    5: {
        onEnter: () => {
            console.log("Entering Step 5");
            get_summary();
        },
    },
};

function validateStep3() {
    const title = document.querySelector('input[name="title"]')?.value.trim();
    const description = tinymce.get('dataset_editor')?.getContent({ format: 'text' }).trim();

    if (title && description) {
        toggleContinueButton(true);
    } else {
        toggleContinueButton(false);
    }
}

function initializeStep3Listeners() {
    const titleInput = document.querySelector('input[name="title"]');
    if (titleInput) {
        titleInput.addEventListener("input", validateStep3);
    }

    // TinyMCE necesita listener especial
    if (tinymce.get('dataset_editor')) {
        tinymce.get('dataset_editor').on('input', validateStep3);
        tinymce.get('dataset_editor').on('keyup', validateStep3);
    }
}

function removeStep3Listeners() {
    const titleInput = document.querySelector('input[name="title"]');
    if (titleInput) {
        titleInput.removeEventListener("input", validateStep3);
    }

    if (tinymce.get('dataset_editor')) {
        tinymce.get('dataset_editor').off('input', validateStep3);
        tinymce.get('dataset_editor').off('keyup', validateStep3);
    }
}

// Function to enable or disable the Continue button
function toggleContinueButton(enable) {
    if (enable) {
        continueButton.classList.remove("disabled");
        continueButton.disabled = false;
    } else {
        continueButton.classList.add("disabled");
        continueButton.disabled = true;
    }
}

// Handle step change events
function handleStepChange() {
    const currentStep = stepper.getCurrentStepIndex();
    const previousStep = stepper.getPreviousStepIndex();

    if (stepHandlers[previousStep]?.onExit) {
        stepHandlers[previousStep].onExit();
    }

    if (stepHandlers[currentStep]?.onEnter) {
        stepHandlers[currentStep].onEnter();
    }
}

// Prevent advancing without validation
async function handleNextStep(stepperObj) {
    const currentStep = stepperObj.getCurrentStepIndex();

    // Step 2 → Dropzone files
    if (currentStep === stepToValidateFiles) {
        const files = myDropzone.files;

        if (
            files.length === 0 ||
            files.some(f => f.status === Dropzone.ERROR || f.status === Dropzone.CANCELED)
        ) {
            console.log("Validation failed: cannot continue.");
            updateDropzoneStatus();
            return; // no avanzamos
        }
    }

    // Step 3 → if the dataset is anonymous, we skip authors (step 4)
    if (currentStep === 3) {
        const datasetTypeElement = document.querySelector('input[name="dataset_type"]:checked');
        if (datasetTypeElement?.value === "zenodo_anonymous") {
            console.log("Anonymous upload → skipping authors step.");
            stepperObj.goNext(); // go to step 4
            stepperObj.goNext(); // go to step 5
            return;
        }
    }


    // Step 4 → Authors (async validation)
    if (currentStep === 4) {
        const valid = await validateAllAuthors();
        if (!valid) {
            console.log("Validation failed: authors have errors.");
            return; // no avanzamos
        }
    }

    console.log("Validation passed. Moving to the next step.");
    stepperObj.goNext();
}

// Initialize Stepper logic
export function initializeStepper() {
    console.log("Initializing Stepper...");

    stepper.on("kt.stepper.changed", handleStepChange);

    stepper.on("kt.stepper.next", handleNextStep);

    stepper.on("kt.stepper.previous", () => {
        console.log("Moving to the previous step.");
        stepper.goPrevious();
    });

    // Trigger the initial step logic
    handleStepChange();
}

// Dropzone event listeners
function initializeDropzoneListeners() {
    console.log("Initializing Dropzone listeners...");

    myDropzone.on("addedfile", updateDropzoneStatus);
    myDropzone.on("removedfile", updateDropzoneStatus);

    myDropzone.on("error", updateDropzoneStatus);
    myDropzone.on("success", updateDropzoneStatus);
    myDropzone.on("canceled", updateDropzoneStatus);
    myDropzone.on("complete", updateDropzoneStatus);

    updateDropzoneStatus();
}

function removeDropzoneListeners() {
    console.log("Removing Dropzone listeners...");

    myDropzone.off("addedfile", updateDropzoneStatus);
    myDropzone.off("removedfile", updateDropzoneStatus);
}

function updateDropzoneStatus() {
    console.log("Updating Dropzone status...");

    const files = myDropzone.files;

    if (files.length === 0) {
        toggleContinueButton(false);
        return;
    }

    const hasInvalid = files.some(
        f => f.status === Dropzone.ERROR || f.status === Dropzone.CANCELED
    );
    if (hasInvalid) {
        toggleContinueButton(false);
        return;
    }

    toggleContinueButton(true);
}

function get_summary() {
    const datasetTypeElement = document.querySelector('input[name="dataset_type"]:checked');
    const datasetType = datasetTypeElement 
        ? document.querySelector(`label[for="${datasetTypeElement.id}"]`)?.innerText.trim() || "Not selected"
        : "Not selected";

    const title = document.querySelector('input[name="title"]')?.value.trim() || "No title provided";
    const description = tinymce.get('dataset_editor')?.getContent({ format: 'text' }).trim() || "No description provided";

    const publicationTypeElement = document.querySelector('select[name="publication_type"]');
    const publicationType = publicationTypeElement 
        ? publicationTypeElement.options[publicationTypeElement.selectedIndex]?.text.trim() || "Not selected"
        : "Not selected";

    const publicationDoi = document.querySelector('input[name="publication_doi"]')?.value.trim() || "No DOI provided";

    const tagsInput = document.querySelector('input#tags');
    let tags = [];
    if (tagsInput?.value.trim()) {
        try {
            const parsedTags = JSON.parse(tagsInput.value);
            tags = parsedTags.map(tag => tag.value.trim());
        } catch (error) {
            console.error("Invalid JSON in tags input:", error);
        }
    }

    const authorsContainer = document.getElementById('authors-container');
    const authorCards = authorsContainer ? authorsContainer.querySelectorAll('.draggable') : [];
    const authors = Array.from(authorCards).map((authorCard) => {
        const name = authorCard.querySelector('input[name*="[name]"]')?.value.trim() || "No name provided";
        const affiliation = authorCard.querySelector('input[name*="[affiliation]"]')?.value.trim() || "No affiliation provided";
        const orcid = authorCard.querySelector('input[name*="[orcid]"]')?.value.trim() || "No ORCID provided";

        return { name, affiliation, orcid };
    });

    let summaryContent = `
        <h3>Summary</h3>
        <p><strong>Dataset Type:</strong><br>${datasetType}</p>
        <p><strong>Title:</strong> ${title}</p>
        <p><strong>Description:</strong> ${description}</p>
        <p><strong>Publication Type:</strong> ${publicationType}</p>
        <p><strong>Publication DOI:</strong> ${publicationDoi}</p>
        <p><strong>Tags:</strong> ${
            tags.length > 0
                ? tags.map(tag => `<span class="badge bg-primary me-1">${tag}</span>`).join('')
                : "No tags provided"
        }</p>
        <h4>Authors</h4>
    `;

    if (authors.length > 0) {
        summaryContent += '<ul>';
        authors.forEach((author, index) => {
            summaryContent += `
                <li>
                    <strong>Author ${index + 1}:</strong>
                    <ul>
                        <li><strong>Name:</strong> ${author.name}</li>
                        <li><strong>Affiliation:</strong> ${author.affiliation}</li>
                        <li><strong>ORCID:</strong> ${author.orcid}</li>
                    </ul>
                </li>
            `;
        });
        summaryContent += '</ul>';
    } else {
        summaryContent += '<p>No authors added.</p>';
    }

    const summaryDiv = document.getElementById('summary');
    if (summaryDiv) {
        summaryDiv.innerHTML = summaryContent;
    } else {
        console.error('Div with ID "summary" not found.');
    }
}
