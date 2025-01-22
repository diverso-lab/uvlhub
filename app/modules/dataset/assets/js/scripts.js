
import { initializeStepper } from './stepper.js';
import { initializeAuthors } from './authors.js';
import { initializeTinyMCE } from './editor.js';
import { initializeTagify } from './tagify.js';
import { initializeSummary } from './summary.js';

document.addEventListener('DOMContentLoaded', function () {

    initializeStepper();
    initializeAuthors();
    initializeTinyMCE();
    initializeTagify();
    initializeSummary();

});
