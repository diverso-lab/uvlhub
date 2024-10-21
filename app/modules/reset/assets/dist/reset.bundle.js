/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./app/modules/reset/assets/js/scripts.js":
/*!************************************************!*\
  !*** ./app/modules/reset/assets/js/scripts.js ***!
  \************************************************/
/***/ (() => {

eval("console.log(\"Hi, I am a script loaded from reset module\");\n\ndocument.addEventListener('DOMContentLoaded', function () {\n    var form = document.getElementById('reset_password_form');\n    if (form) {\n        var password = document.getElementById('password');\n        var confirm_password = document.getElementById('confirm_password');\n        var submit_button = document.getElementById('submit_button');\n\n        function validatePasswords() {\n            if (password.value && confirm_password.value && password.value === confirm_password.value) {\n                submit_button.disabled = false;\n            } else {\n                submit_button.disabled = true;\n            }\n        }\n\n        password.addEventListener('input', validatePasswords);\n        confirm_password.addEventListener('input', validatePasswords);\n    }\n});\n\n//# sourceURL=webpack://uvlhub/./app/modules/reset/assets/js/scripts.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./app/modules/reset/assets/js/scripts.js"]();
/******/ 	
/******/ })()
;