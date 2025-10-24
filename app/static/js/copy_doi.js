function copyText(id) {
    const text = document.getElementById(id).innerText;
    navigator.clipboard.writeText(text).then(() => {
        const icon = document.querySelector(`[onclick="copyText('${id}')"]`);
        const tooltip = bootstrap.Tooltip.getInstance(icon);

        // Cambia el texto a "Copied!" temporalmente
        icon.setAttribute('data-bs-original-title', 'Copied!');
        tooltip.show();

        // Espera 2 segundos, luego restaura el título original y oculta el tooltip
        setTimeout(() => {
            icon.setAttribute('data-bs-original-title', 'Copy DOI');
            tooltip.hide();
        }, 1500);
    });
}
				