import tinymce from 'tinymce';
import 'tinymce/icons/default';
import 'tinymce/themes/silver';
import 'tinymce/plugins/lists';
import 'tinymce/plugins/link';

export function initializeTinyMCE() {
  tinymce.init({
    selector: '#dataset_editor',
    plugins: 'lists link',
    toolbar: 'undo redo | bold italic | bullist numlist | link',
    base_url: '/dataset/dist', // Ruta base para los recursos de TinyMCE del módulo
    skin: 'default',
    skin_url: '/dataset/dist/skins/ui/oxide', // Ruta para los skins
    content_css: '/dataset/dist/skins/content/default/content.css', // Ruta para el CSS de contenido
    license_key: 'gpl', // Acepta la licencia GPL
    setup: (editor) => {
      editor.on('change', () => {
        console.log('TinyMCE Content:', editor.getContent());
      });
    },
  });
}
