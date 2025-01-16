import ClassicEditor from '@ckeditor/ckeditor5-build-classic';

// Initialize CKEditor
export function initializeCKEditor() {
    ClassicEditor
        .create(document.querySelector('#kt_docs_ckeditor_classic'), {
            // List of plugins to include in the editor
            plugins: [
                'Essentials', 'Paragraph', 'Heading', 'Bold', 'Italic', 'List', 'Link'
            ],
            // Configure the toolbar options
            toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|', 'undo', 'redo'],
            // Markdown-specific configuration (optional)
            markdown: {
                // Optional: Set specific options for Markdown if needed
            }
        })
        .then(editor => {
            console.log('CKEditor initialized:', editor);

            // Example: Log the Markdown content whenever the data changes
            editor.model.document.on('change:data', () => {
                console.log('CKEditor Content:', editor.getData());
            });
        })
        .catch(error => {
            console.error('Error initializing CKEditor:', error);
        });
}
