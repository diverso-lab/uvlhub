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

/***/ "./app/modules/downloadqueue/assets/js/scripts.js":
/*!********************************************************!*\
  !*** ./app/modules/downloadqueue/assets/js/scripts.js ***!
  \********************************************************/
/***/ (() => {

eval("function getMyCart() {\n  const myCart = localStorage.getItem('myCart');\n  if (myCart) {\n    return JSON.parse(myCart);\n  }\n  return [];\n}\n\nfunction addToCart(id) {\n  const myCart = getMyCart();\n  if (myCart.includes(id)) {\n    return;\n  }\n  myCart.push(id);\n  localStorage.setItem('myCart', JSON.stringify(myCart));\n  setCart();\n}\n\nfunction rmFromCart(id) {\n  const myCart = getMyCart();\n  const index = myCart.indexOf(id);\n  if (index > -1) {\n    myCart.splice(index, 1);\n    localStorage.setItem('myCart', JSON.stringify(myCart));\n  }\n  setCart();\n}\n\nfunction clearCart() {\n  localStorage.removeItem('myCart');\n  setCart();\n}\n\nfunction countCart() {\n  return getMyCart().length;\n}\n\nfunction setCart() {\n  document.getElementById('amount-cart').innerText = countCart();\n}\n\nfunction goToMyCart() {\n  let baseUrl = \"/downloadqueue\";\n  let params = \"?files=\" + encodeURIComponent(getMyCart().toString());\n  window.location.href = baseUrl + params;\n}\n\nsetCart()\n\n\nfunction removeElement(event, id) {\n    event.parentElement.remove();\n    rmFromCart(id);\n}\n\nfunction downloadAll() {\n  let baseUrl = \"/dataset/build/download/\";\n  let params = \"?files=\" + encodeURIComponent(getMyCart().toString());\n  window.location.href = baseUrl + params;\n}\n\nfunction clearAll() {\n  clearCart();\n  document.getElementById(\"cart\").innerHTML = \"\";\n}\n\nfunction buildDataset() {\n  let baseUrl = \"/dataset/upload\";\n  let params = \"?with_hubfiles=\" + encodeURIComponent(getMyCart().toString());\n  window.location.href = baseUrl + params;\n}\n\n//# sourceURL=webpack://uvlhub/./app/modules/downloadqueue/assets/js/scripts.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./app/modules/downloadqueue/assets/js/scripts.js"]();
/******/ 	
/******/ })()
;