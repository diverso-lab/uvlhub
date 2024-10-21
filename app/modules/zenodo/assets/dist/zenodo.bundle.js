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

/***/ "./app/modules/zenodo/assets/js/scripts.js":
/*!*************************************************!*\
  !*** ./app/modules/zenodo/assets/js/scripts.js ***!
  \*************************************************/
/***/ (() => {

eval("const testZenodoConnection = () => {\n    console.log('Testing Zenodo connection...');\n    const xhr = new XMLHttpRequest();\n    xhr.open('GET', '/zenodo/test', true);\n    xhr.setRequestHeader('Content-Type', 'application/json');\n    xhr.onreadystatechange = () => {\n        if (xhr.readyState === 4 && xhr.status === 200) {\n            const response = JSON.parse(xhr.responseText);\n            if (!response.success) {\n                document.getElementById(\"test_zenodo_connection_error\").style.display = \"block\";\n                console.log(response);\n                console.log(response.success);\n                console.log(response.messages);\n            }\n            console.log('Testing Zenodo connection... OK');\n        } else if (xhr.readyState === 4 && xhr.status !== 200) {\n            console.error('Error:', xhr.status);\n        }\n    };\n    xhr.send();\n};\n\n\n//# sourceURL=webpack://uvlhub/./app/modules/zenodo/assets/js/scripts.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./app/modules/zenodo/assets/js/scripts.js"]();
/******/ 	
/******/ })()
;