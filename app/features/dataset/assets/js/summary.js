export function initializeSummary() {
    // Select every radio button with the name="dataset_type" attribute.
    const datasetRadios = document.querySelectorAll('input[name="dataset_type"]');
    const summaryDiv = document.getElementById('step_1_summary');

    // Attach a listener to each radio button.
    datasetRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            // Find the label matching the selected radio.
            const selectedLabel = document.querySelector(`label[for="${radio.id}"]`);

            if (selectedLabel) {
                // Extract only the visible text of the label.
                const labelText = selectedLabel.querySelector('.text-gray-900').innerText;
                // Update the div content with the selected text.
                summaryDiv.textContent = labelText;
            }
        });
    });

    // Fire the initial event so the default selected value is displayed.
    document.querySelector('input[name="dataset_type"]:checked').dispatchEvent(new Event('change'));
}
