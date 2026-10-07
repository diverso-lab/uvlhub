function copyText(id) {
    const text = document.getElementById(id).innerText;
    navigator.clipboard.writeText(text).then(() => {
        const icon = document.querySelector(`[onclick="copyText('${id}')"]`);
        const tooltip = bootstrap.Tooltip.getInstance(icon);

        // Temporarily switch the label to "Copied!"
        icon.setAttribute('data-bs-original-title', 'Copied!');
        tooltip.show();

        // Wait 1.5s, then restore the original title and hide the tooltip.
        setTimeout(() => {
            icon.setAttribute('data-bs-original-title', 'Copy DOI');
            tooltip.hide();
        }, 1500);
    });
}
				