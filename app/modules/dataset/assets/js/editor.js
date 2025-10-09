import tinymce from 'tinymce';
import 'tinymce/icons/default';
import 'tinymce/themes/silver';
import 'tinymce/plugins/lists';
import 'tinymce/plugins/link';

export function initializeTinyMCE() {
  tinymce.init({
    selector: '#dataset_editor',
    plugins: 'lists link',
    toolbar: 'undo redo | bold italic underline | bullist numlist | link removeformat',
    menubar: false,
    branding: false,
    license_key: 'gpl',

    base_url: '/dataset/dist',
    skin_url: '/dataset/dist/skins/ui/oxide',
    content_css: false, // 🚫 Desactivamos el CSS por defecto de TinyMCE

    // 🔹 Usamos las variables de Keen para respetar el tema (light/dark)
    content_style: `
      body {
        font-family: var(--bs-body-font-family);
        font-size: var(--bs-body-font-size);
        color: var(--bs-body-color);
        background-color: transparent;
        line-height: 1.5;
      }
      a {
        color: var(--bs-primary);
        text-decoration: underline;
      }
      ul, ol {
        margin-left: 1rem;
      }
      p {
        margin-bottom: 0.5rem;
      }
    `,

    // 🔒 Evita estilos inline o fuentes personalizadas
    valid_elements: 'p,strong,em,b,i,ul,ol,li,a[href|title|target]',
    invalid_styles: {
      '*': 'color,font,font-size,font-family,background,background-color'
    },
    // Evita que al pegar texto con formato traiga estilos externos
    paste_as_text: true,

    setup: (editor) => {
      editor.on('change', () => {
        console.log('TinyMCE Content:', editor.getContent());
      });
    },
  });
}
