export function initializeSummary() {
    // Selecciona todos los radio buttons con el atributo name="dataset_type"
    const datasetRadios = document.querySelectorAll('input[name="dataset_type"]');
    const summaryDiv = document.getElementById('step_1_summary');

    // Añade un listener a cada radio button
    datasetRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            // Encuentra el label correspondiente al radio seleccionado
            const selectedLabel = document.querySelector(`label[for="${radio.id}"]`);

            if (selectedLabel) {
                // Extrae solo el texto visible del label
                const labelText = selectedLabel.querySelector('.text-gray-900').innerText;
                // Actualiza el contenido del div con el texto seleccionado
                summaryDiv.textContent = labelText;
            }
        });
    });

    // Disparar el evento inicial para mostrar el valor seleccionado por defecto
    document.querySelector('input[name="dataset_type"]:checked').dispatchEvent(new Event('change'));
}