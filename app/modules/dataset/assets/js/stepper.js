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
};

// Function to enable or disable the Continue button
function toggleContinueButton(enable) {
    if (enable) {
        continueButton.classList.remove("disabled");
    } else {
        continueButton.classList.add("disabled");
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
function handleNextStep(event) {
    const currentStep = stepper.getCurrentStepIndex();
    if (currentStep === stepToValidateFiles && myDropzone.files.length === 0) {
        console.log("Validation failed: No files uploaded.");
        alert("Please upload at least one file before continuing.");
        event.preventDefault();
        return;
    }
    console.log("Validation passed. Moving to the next step.");
    stepper.goNext();
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

    updateDropzoneStatus();
}

function removeDropzoneListeners() {
    console.log("Removing Dropzone listeners...");

    myDropzone.off("addedfile", updateDropzoneStatus);
    myDropzone.off("removedfile", updateDropzoneStatus);
}

function updateDropzoneStatus() {
    console.log("Updating Dropzone status...");
    toggleContinueButton(myDropzone.files.length > 0);
}
