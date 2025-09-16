// stepper.js

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
            toggleContinueButton(true);
        },
        onExit: () => {
            console.log("Exiting Step 3");
        },
    },
    5: {
        onEnter: () => {
            console.log("Entering Step 5");
            get_summary();
        },
    },
};

// Function to enable or disable the Continue button
function toggleContinueButton(enable) {
    if (enable) {
        continueButton.classList.remove("disabled");
        continueButton.disabled = false; // ← Esto lo hace de verdad
    } else {
        continueButton.classList.add("disabled");
        continueButton.disabled = true;  // ← Esto lo bloquea
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

// Prevent advancing without files in Step 2
function handleNextStep(stepperObj) {
  const currentStep = stepperObj.getCurrentStepIndex();

  if (currentStep === stepToValidateFiles) {
    const files = myDropzone.files;

    // No archivos o hay inválidos => no avanzamos
    if (
      files.length === 0 ||
      files.some(f => f.status === Dropzone.ERROR || f.status === Dropzone.CANCELED)
    ) {
      console.log("Validation failed: cannot continue.");
      // refuerza estado del botón por si acaso
      updateDropzoneStatus();
      return; // ← no llamamos a goNext()
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

  // ⚠️ Imprescindibles para que el botón se desactive cuando el ZIP pasa a ERROR
  myDropzone.on("error", updateDropzoneStatus);
  myDropzone.on("success", updateDropzoneStatus);
  myDropzone.on("canceled", updateDropzoneStatus);
  myDropzone.on("complete", updateDropzoneStatus); // opcional

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

    // 1. No archivos => botón deshabilitado
    if (files.length === 0) {
        toggleContinueButton(false);
        return;
    }

    // 2. Archivos inválidos (ERROR o CANCELED) => botón deshabilitado
    const hasInvalid = files.some(
        f => f.status === Dropzone.ERROR || f.status === Dropzone.CANCELED
    );
    if (hasInvalid) {
        toggleContinueButton(false);
        return;
    }

    // 3. Todo bien => botón habilitado
    toggleContinueButton(true);
}


function get_summary() {
    // Recoger valores básicos
    const datasetTypeElement = document.querySelector('input[name="dataset_type"]:checked');
    const datasetType = datasetTypeElement 
        ? document.querySelector(`label[for="${datasetTypeElement.id}"]`)?.innerText.trim() || "Not selected"
        : "Not selected";
    

    const title = document.querySelector('input[name="title"]')?.value.trim() || "No title provided";
    const description = document.querySelector('textarea[name="description"]')?.value.trim() || "No description provided";

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

    // Recoger autores
    const authorsContainer = document.getElementById('authors-container');
    const authorCards = authorsContainer ? authorsContainer.querySelectorAll('.draggable') : [];
    const authors = Array.from(authorCards).map((authorCard) => {
        const authorId = authorCard.id.replace('author-', '');
        const name = document.querySelector(`#name_${authorId}`)?.value.trim() || "No name provided";
        const affiliation = document.querySelector(`#affiliation_${authorId}`)?.value.trim() || "No affiliation provided";
        const orcid = document.querySelector(`#orcid_${authorId}`)?.value.trim() || "No ORCID provided";

        return { name, affiliation, orcid };
    });

    // Crear contenido estructurado
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

    // Insertar en el div con ID summary
    const summaryDiv = document.getElementById('summary');
    if (summaryDiv) {
        summaryDiv.innerHTML = summaryContent;
    } else {
        console.error('Div with ID "summary" not found.');
    }
}


