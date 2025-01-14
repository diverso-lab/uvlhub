import Mustache from 'mustache';

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
});
