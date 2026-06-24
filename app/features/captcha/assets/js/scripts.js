console.log("Hi, I am a script loaded from recaptcha module");

function loadCaptcha() {
    fetch('/captcha/generate')
        .then(response => response.text())
        .then(data => {
            document.getElementById('captcha_image').src = data;
        });
}
window.onload = loadCaptcha;