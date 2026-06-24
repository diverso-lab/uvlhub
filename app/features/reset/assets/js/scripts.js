console.log("Hi, I am a script loaded from reset module");

document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('reset_password_form');
    if (form) {
        var password = document.getElementById('password');
        var confirm_password = document.getElementById('confirm_password');
        var submit_button = document.getElementById('submit_button');

        function validatePasswords() {
            if (password.value && confirm_password.value && password.value === confirm_password.value) {
                submit_button.disabled = false;
            } else {
                submit_button.disabled = true;
            }
        }

        password.addEventListener('input', validatePasswords);
        confirm_password.addEventListener('input', validatePasswords);
    }
});