/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "?025b":
/*!********************!*\
  !*** fs (ignored) ***!
  \********************/
/***/ (() => {

/* (ignored) */

/***/ }),

/***/ "./node_modules/antlr4/dist/antlr4.web.js":
/*!************************************************!*\
  !*** ./node_modules/antlr4/dist/antlr4.web.js ***!
  \************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   ATN: () => (/* binding */ o),
/* harmony export */   ATNDeserializer: () => (/* binding */ i),
/* harmony export */   BailErrorStrategy: () => (/* binding */ u),
/* harmony export */   CharStream: () => (/* binding */ c),
/* harmony export */   CharStreams: () => (/* binding */ a),
/* harmony export */   CommonToken: () => (/* binding */ l),
/* harmony export */   CommonTokenStream: () => (/* binding */ s),
/* harmony export */   DFA: () => (/* binding */ f),
/* harmony export */   DiagnosticErrorListener: () => (/* binding */ p),
/* harmony export */   ErrorListener: () => (/* binding */ y),
/* harmony export */   FailedPredicateException: () => (/* binding */ h),
/* harmony export */   InputStream: () => (/* binding */ b),
/* harmony export */   Interval: () => (/* binding */ v),
/* harmony export */   IntervalSet: () => (/* binding */ d),
/* harmony export */   LL1Analyzer: () => (/* binding */ m),
/* harmony export */   Lexer: () => (/* binding */ g),
/* harmony export */   LexerATNSimulator: () => (/* binding */ S),
/* harmony export */   NoViableAltException: () => (/* binding */ O),
/* harmony export */   ParseTreeListener: () => (/* binding */ w),
/* harmony export */   ParseTreeVisitor: () => (/* binding */ _),
/* harmony export */   ParseTreeWalker: () => (/* binding */ P),
/* harmony export */   Parser: () => (/* binding */ T),
/* harmony export */   ParserATNSimulator: () => (/* binding */ E),
/* harmony export */   ParserRuleContext: () => (/* binding */ j),
/* harmony export */   PredictionContextCache: () => (/* binding */ k),
/* harmony export */   PredictionMode: () => (/* binding */ x),
/* harmony export */   RecognitionException: () => (/* binding */ R),
/* harmony export */   RuleContext: () => (/* binding */ C),
/* harmony export */   RuleNode: () => (/* binding */ A),
/* harmony export */   TerminalNode: () => (/* binding */ N),
/* harmony export */   Token: () => (/* binding */ I),
/* harmony export */   arrayToString: () => (/* binding */ L),
/* harmony export */   "default": () => (/* binding */ D)
/* harmony export */ });
/*! For license information please see antlr4.web.js.LICENSE.txt */
var t={92:()=>{}},e={};function n(r){var o=e[r];if(void 0!==o)return o.exports;var i=e[r]={exports:{}};return t[r](i,i.exports,n),i.exports}n.d=(t,e)=>{for(var r in e)n.o(e,r)&&!n.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},n.o=(t,e)=>Object.prototype.hasOwnProperty.call(t,e);var r={};(()=>{function t(e){return t="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},t(e)}function e(e,n){for(var r=0;r<n.length;r++){var o=n[r];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(e,(void 0,i=function(e,n){if("object"!==t(e)||null===e)return e;var r=e[Symbol.toPrimitive];if(void 0!==r){var o=r.call(e,"string");if("object"!==t(o))return o;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(e)}(o.key),"symbol"===t(i)?i:String(i)),o)}var i}n.d(r,{dx:()=>Ie,q2:()=>qo,FO:()=>Zc,xf:()=>aa,Gy:()=>va,s4:()=>fi,c7:()=>Ra,_7:()=>ic,gp:()=>Ac,cK:()=>Yo,zs:()=>Ec,AV:()=>aa,Xp:()=>L,VS:()=>B,ul:()=>Ce,hW:()=>Bi,x1:()=>Pu,z5:()=>Du,oN:()=>fc,TB:()=>hc,u1:()=>dc,_b:()=>Ua,$F:()=>zu,_T:()=>el,db:()=>Gu,Zx:()=>Au,_x:()=>ji,r8:()=>Zt,JI:()=>Ft,TP:()=>Vt,WU:()=>o,Nj:()=>p,ZP:()=>rl});var o=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.source=null,this.type=null,this.channel=null,this.start=null,this.stop=null,this.tokenIndex=null,this.line=null,this.column=null,this._text=null}var n,r;return n=t,(r=[{key:"getTokenSource",value:function(){return this.source[0]}},{key:"getInputStream",value:function(){return this.source[1]}},{key:"text",get:function(){return this._text},set:function(t){this._text=t}}])&&e(n.prototype,r),Object.defineProperty(n,"prototype",{writable:!1}),t}();function i(t,e){if(!Array.isArray(t)||!Array.isArray(e))return!1;if(t===e)return!0;if(t.length!==e.length)return!1;for(var n=0;n<t.length;n++)if(!(t[n]===e[n]||t[n].equals&&t[n].equals(e[n])))return!1;return!0}function u(t){return u="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},u(t)}function c(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==u(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==u(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===u(o)?o:String(o)),r)}var o}o.INVALID_TYPE=0,o.EPSILON=-2,o.MIN_USER_TOKEN_TYPE=1,o.EOF=-1,o.DEFAULT_CHANNEL=0,o.HIDDEN_CHANNEL=1;var a=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.count=0,this.hash=0}var e,n,r;return e=t,n=[{key:"update",value:function(){for(var t=0;t<arguments.length;t++){var e=arguments[t];if(null!=e)if(Array.isArray(e))this.update.apply(this,e);else{var n=0;switch(u(e)){case"undefined":case"function":continue;case"number":case"boolean":n=e;break;case"string":n=e.hashCode();break;default:e.updateHashCode?e.updateHashCode(this):console.log("No updateHashCode for "+e.toString());continue}n=(n*=3432918353)<<15|n>>>17,n*=461845907,this.count=this.count+1;var r=this.hash^n;r=5*(r=r<<13|r>>>19)+3864292196,this.hash=r}}}},{key:"finish",value:function(){var t=this.hash^4*this.count;return t^=t>>>16,t*=2246822507,t^=t>>>13,(t*=3266489909)^t>>>16}}],r=[{key:"hashStuff",value:function(){var e=new t;return e.update.apply(e,arguments),e.finish()}}],n&&c(e.prototype,n),r&&c(e,r),Object.defineProperty(e,"prototype",{writable:!1}),t}();function l(t){return t?t.hashCode():-1}function s(t,e){return t?t.equals(e):t===e}function f(t){return null===t?"null":t}function p(t){return Array.isArray(t)?"["+t.map(f).join(", ")+"]":"null"}function y(t){return y="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},y(t)}function h(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==y(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==y(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===y(o)?o:String(o)),r)}var o}var b="h-",v=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.data={},this.hashFunction=e||l,this.equalsFunction=n||s}var e,n;return e=t,(n=[{key:"add",value:function(t){var e=b+this.hashFunction(t);if(e in this.data){for(var n=this.data[e],r=0;r<n.length;r++)if(this.equalsFunction(t,n[r]))return n[r];return n.push(t),t}return this.data[e]=[t],t}},{key:"has",value:function(t){return null!=this.get(t)}},{key:"get",value:function(t){var e=b+this.hashFunction(t);if(e in this.data)for(var n=this.data[e],r=0;r<n.length;r++)if(this.equalsFunction(t,n[r]))return n[r];return null}},{key:"values",value:function(){var t=this;return Object.keys(this.data).filter((function(t){return t.startsWith(b)})).flatMap((function(e){return t.data[e]}),this)}},{key:"toString",value:function(){return p(this.values())}},{key:"length",get:function(){var t=this;return Object.keys(this.data).filter((function(t){return t.startsWith(b)})).map((function(e){return t.data[e].length}),this).reduce((function(t,e){return t+e}),0)}}])&&h(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function d(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&m(t,e)}function m(t,e){return m=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},m(t,e)}function g(t){var e=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}();return function(){var n,r=S(t);if(e){var o=S(this).constructor;n=Reflect.construct(r,arguments,o)}else n=r.apply(this,arguments);return function(t,e){if(e&&("object"===O(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,n)}}function S(t){return S=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},S(t)}function O(t){return O="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},O(t)}function w(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}function _(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==O(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==O(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===O(o)?o:String(o)),r)}var o}function P(t,e,n){return e&&_(t.prototype,e),n&&_(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}var T=function(){function t(){w(this,t)}return P(t,[{key:"hashCode",value:function(){var t=new a;return this.updateHashCode(t),t.finish()}},{key:"evaluate",value:function(t,e){}},{key:"evalPrecedence",value:function(t,e){return this}}],[{key:"andContext",value:function(e,n){if(null===e||e===t.NONE)return n;if(null===n||n===t.NONE)return e;var r=new E(e,n);return 1===r.opnds.length?r.opnds[0]:r}},{key:"orContext",value:function(e,n){if(null===e)return n;if(null===n)return e;if(e===t.NONE||n===t.NONE)return t.NONE;var r=new j(e,n);return 1===r.opnds.length?r.opnds[0]:r}}]),t}(),E=function(t){d(n,t);var e=g(n);function n(t,r){var o;w(this,n),o=e.call(this);var i=new v;t instanceof n?t.opnds.map((function(t){i.add(t)})):i.add(t),r instanceof n?r.opnds.map((function(t){i.add(t)})):i.add(r);var u=k(i);if(u.length>0){var c=null;u.map((function(t){(null===c||t.precedence<c.precedence)&&(c=t)})),i.add(c)}return o.opnds=Array.from(i.values()),o}return P(n,[{key:"equals",value:function(t){return this===t||t instanceof n&&i(this.opnds,t.opnds)}},{key:"updateHashCode",value:function(t){t.update(this.opnds,"AND")}},{key:"evaluate",value:function(t,e){for(var n=0;n<this.opnds.length;n++)if(!this.opnds[n].evaluate(t,e))return!1;return!0}},{key:"evalPrecedence",value:function(t,e){for(var n=!1,r=[],o=0;o<this.opnds.length;o++){var i=this.opnds[o],u=i.evalPrecedence(t,e);if(n|=u!==i,null===u)return null;u!==T.NONE&&r.push(u)}if(!n)return this;if(0===r.length)return T.NONE;var c=null;return r.map((function(t){c=null===c?t:T.andContext(c,t)})),c}},{key:"toString",value:function(){var t=this.opnds.map((function(t){return t.toString()}));return(t.length>3?t.slice(3):t).join("&&")}}]),n}(T),j=function(t){d(n,t);var e=g(n);function n(t,r){var o;w(this,n),o=e.call(this);var i=new v;t instanceof n?t.opnds.map((function(t){i.add(t)})):i.add(t),r instanceof n?r.opnds.map((function(t){i.add(t)})):i.add(r);var u=k(i);if(u.length>0){var c=u.sort((function(t,e){return t.compareTo(e)})),a=c[c.length-1];i.add(a)}return o.opnds=Array.from(i.values()),o}return P(n,[{key:"equals",value:function(t){return this===t||t instanceof n&&i(this.opnds,t.opnds)}},{key:"updateHashCode",value:function(t){t.update(this.opnds,"OR")}},{key:"evaluate",value:function(t,e){for(var n=0;n<this.opnds.length;n++)if(this.opnds[n].evaluate(t,e))return!0;return!1}},{key:"evalPrecedence",value:function(t,e){for(var n=!1,r=[],o=0;o<this.opnds.length;o++){var i=this.opnds[o],u=i.evalPrecedence(t,e);if(n|=u!==i,u===T.NONE)return T.NONE;null!==u&&r.push(u)}if(!n)return this;if(0===r.length)return null;return r.map((function(t){return t})),null}},{key:"toString",value:function(){var t=this.opnds.map((function(t){return t.toString()}));return(t.length>3?t.slice(3):t).join("||")}}]),n}(T);function k(t){var e=[];return t.values().map((function(t){t instanceof T.PrecedencePredicate&&e.push(t)})),e}function x(t){return x="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},x(t)}function R(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==x(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==x(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===x(o)?o:String(o)),r)}var o}function C(t,e){if(null===t){var n={state:null,alt:null,context:null,semanticContext:null};return e&&(n.reachesIntoOuterContext=0),n}var r={};return r.state=t.state||null,r.alt=void 0===t.alt?null:t.alt,r.context=t.context||null,r.semanticContext=t.semanticContext||null,e&&(r.reachesIntoOuterContext=t.reachesIntoOuterContext||0,r.precedenceFilterSuppressed=t.precedenceFilterSuppressed||!1),r}var A=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.checkContext(e,n),e=C(e),n=C(n,!0),this.state=null!==e.state?e.state:n.state,this.alt=null!==e.alt?e.alt:n.alt,this.context=null!==e.context?e.context:n.context,this.semanticContext=null!==e.semanticContext?e.semanticContext:null!==n.semanticContext?n.semanticContext:T.NONE,this.reachesIntoOuterContext=n.reachesIntoOuterContext,this.precedenceFilterSuppressed=n.precedenceFilterSuppressed}var e,n;return e=t,(n=[{key:"checkContext",value:function(t,e){null!==t.context&&void 0!==t.context||null!==e&&null!==e.context&&void 0!==e.context||(this.context=null)}},{key:"hashCode",value:function(){var t=new a;return this.updateHashCode(t),t.finish()}},{key:"updateHashCode",value:function(t){t.update(this.state.stateNumber,this.alt,this.context,this.semanticContext)}},{key:"equals",value:function(e){return this===e||e instanceof t&&this.state.stateNumber===e.state.stateNumber&&this.alt===e.alt&&(null===this.context?null===e.context:this.context.equals(e.context))&&this.semanticContext.equals(e.semanticContext)&&this.precedenceFilterSuppressed===e.precedenceFilterSuppressed}},{key:"hashCodeForConfigSet",value:function(){var t=new a;return t.update(this.state.stateNumber,this.alt,this.semanticContext),t.finish()}},{key:"equalsForConfigSet",value:function(e){return this===e||e instanceof t&&this.state.stateNumber===e.state.stateNumber&&this.alt===e.alt&&this.semanticContext.equals(e.semanticContext)}},{key:"toString",value:function(){return"("+this.state+","+this.alt+(null!==this.context?",["+this.context.toString()+"]":"")+(this.semanticContext!==T.NONE?","+this.semanticContext.toString():"")+(this.reachesIntoOuterContext>0?",up="+this.reachesIntoOuterContext:"")+")"}}])&&R(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function N(t){return N="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},N(t)}function I(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==N(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==N(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===N(o)?o:String(o)),r)}var o}var L=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.start=e,this.stop=n}var e,n;return e=t,(n=[{key:"clone",value:function(){return new t(this.start,this.stop)}},{key:"contains",value:function(t){return t>=this.start&&t<this.stop}},{key:"toString",value:function(){return this.start===this.stop-1?this.start.toString():this.start.toString()+".."+(this.stop-1).toString()}},{key:"length",get:function(){return this.stop-this.start}}])&&I(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function D(t){return D="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},D(t)}function F(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==D(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==D(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===D(o)?o:String(o)),r)}var o}L.INVALID_INTERVAL=new L(-1,-2);var B=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.intervals=null,this.readOnly=!1}var e,n;return e=t,(n=[{key:"first",value:function(t){return null===this.intervals||0===this.intervals.length?o.INVALID_TYPE:this.intervals[0].start}},{key:"addOne",value:function(t){this.addInterval(new L(t,t+1))}},{key:"addRange",value:function(t,e){this.addInterval(new L(t,e+1))}},{key:"addInterval",value:function(t){if(null===this.intervals)this.intervals=[],this.intervals.push(t.clone());else{for(var e=0;e<this.intervals.length;e++){var n=this.intervals[e];if(t.stop<n.start)return void this.intervals.splice(e,0,t);if(t.stop===n.start)return void(this.intervals[e]=new L(t.start,n.stop));if(t.start<=n.stop)return this.intervals[e]=new L(Math.min(n.start,t.start),Math.max(n.stop,t.stop)),void this.reduce(e)}this.intervals.push(t.clone())}}},{key:"addSet",value:function(t){var e=this;return null!==t.intervals&&t.intervals.forEach((function(t){return e.addInterval(t)}),this),this}},{key:"reduce",value:function(t){if(t<this.intervals.length-1){var e=this.intervals[t],n=this.intervals[t+1];e.stop>=n.stop?(this.intervals.splice(t+1,1),this.reduce(t)):e.stop>=n.start&&(this.intervals[t]=new L(e.start,n.stop),this.intervals.splice(t+1,1))}}},{key:"complement",value:function(e,n){var r=new t;return r.addInterval(new L(e,n+1)),null!==this.intervals&&this.intervals.forEach((function(t){return r.removeRange(t)})),r}},{key:"contains",value:function(t){if(null===this.intervals)return!1;for(var e=0;e<this.intervals.length;e++)if(this.intervals[e].contains(t))return!0;return!1}},{key:"removeRange",value:function(t){if(t.start===t.stop-1)this.removeOne(t.start);else if(null!==this.intervals)for(var e=0,n=0;n<this.intervals.length;n++){var r=this.intervals[e];if(t.stop<=r.start)return;if(t.start>r.start&&t.stop<r.stop){this.intervals[e]=new L(r.start,t.start);var o=new L(t.stop,r.stop);return void this.intervals.splice(e,0,o)}t.start<=r.start&&t.stop>=r.stop?(this.intervals.splice(e,1),e-=1):t.start<r.stop?this.intervals[e]=new L(r.start,t.start):t.stop<r.stop&&(this.intervals[e]=new L(t.stop,r.stop)),e+=1}}},{key:"removeOne",value:function(t){if(null!==this.intervals)for(var e=0;e<this.intervals.length;e++){var n=this.intervals[e];if(t<n.start)return;if(t===n.start&&t===n.stop-1)return void this.intervals.splice(e,1);if(t===n.start)return void(this.intervals[e]=new L(n.start+1,n.stop));if(t===n.stop-1)return void(this.intervals[e]=new L(n.start,n.stop-1));if(t<n.stop-1){var r=new L(n.start,t);return n.start=t+1,void this.intervals.splice(e,0,r)}}}},{key:"toString",value:function(t,e,n){return t=t||null,e=e||null,n=n||!1,null===this.intervals?"{}":null!==t||null!==e?this.toTokenString(t,e):n?this.toCharString():this.toIndexString()}},{key:"toCharString",value:function(){for(var t=[],e=0;e<this.intervals.length;e++){var n=this.intervals[e];n.stop===n.start+1?n.start===o.EOF?t.push("<EOF>"):t.push("'"+String.fromCharCode(n.start)+"'"):t.push("'"+String.fromCharCode(n.start)+"'..'"+String.fromCharCode(n.stop-1)+"'")}return t.length>1?"{"+t.join(", ")+"}":t[0]}},{key:"toIndexString",value:function(){for(var t=[],e=0;e<this.intervals.length;e++){var n=this.intervals[e];n.stop===n.start+1?n.start===o.EOF?t.push("<EOF>"):t.push(n.start.toString()):t.push(n.start.toString()+".."+(n.stop-1).toString())}return t.length>1?"{"+t.join(", ")+"}":t[0]}},{key:"toTokenString",value:function(t,e){for(var n=[],r=0;r<this.intervals.length;r++)for(var o=this.intervals[r],i=o.start;i<o.stop;i++)n.push(this.elementName(t,e,i));return n.length>1?"{"+n.join(", ")+"}":n[0]}},{key:"elementName",value:function(t,e,n){return n===o.EOF?"<EOF>":n===o.EPSILON?"<EPSILON>":t[n]||e[n]}},{key:"length",get:function(){return this.intervals.map((function(t){return t.length})).reduce((function(t,e){return t+e}))}}])&&F(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function M(t){return M="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},M(t)}function U(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==M(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==M(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===M(o)?o:String(o)),r)}var o}var V=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.atn=null,this.stateNumber=t.INVALID_STATE_NUMBER,this.stateType=null,this.ruleIndex=0,this.epsilonOnlyTransitions=!1,this.transitions=[],this.nextTokenWithinRule=null}var e,n;return e=t,(n=[{key:"toString",value:function(){return this.stateNumber}},{key:"equals",value:function(e){return e instanceof t&&this.stateNumber===e.stateNumber}},{key:"isNonGreedyExitState",value:function(){return!1}},{key:"addTransition",value:function(t,e){void 0===e&&(e=-1),0===this.transitions.length?this.epsilonOnlyTransitions=t.isEpsilon:this.epsilonOnlyTransitions!==t.isEpsilon&&(this.epsilonOnlyTransitions=!1),-1===e?this.transitions.push(t):this.transitions.splice(e,1,t)}}])&&U(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function q(t){return q="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},q(t)}function H(t,e){return H=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},H(t,e)}function z(t,e){if(e&&("object"===q(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Y(t)}function Y(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function K(t){return K=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},K(t)}V.INVALID_TYPE=0,V.BASIC=1,V.RULE_START=2,V.BLOCK_START=3,V.PLUS_BLOCK_START=4,V.STAR_BLOCK_START=5,V.TOKEN_START=6,V.RULE_STOP=7,V.BLOCK_END=8,V.STAR_LOOP_BACK=9,V.STAR_LOOP_ENTRY=10,V.PLUS_LOOP_BACK=11,V.LOOP_END=12,V.serializationNames=["INVALID","BASIC","RULE_START","BLOCK_START","PLUS_BLOCK_START","STAR_BLOCK_START","TOKEN_START","RULE_STOP","BLOCK_END","STAR_LOOP_BACK","STAR_LOOP_ENTRY","PLUS_LOOP_BACK","LOOP_END"],V.INVALID_STATE_NUMBER=-1;var G=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&H(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=K(n);if(r){var o=K(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return z(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.RULE_STOP,z(t,Y(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function W(t){return W="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},W(t)}function X(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==W(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==W(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===W(o)?o:String(o)),r)}var o}function J(t,e,n){return e&&X(t.prototype,e),n&&X(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}var $=J((function t(e){if(function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),null==e)throw"target cannot be null.";this.target=e,this.isEpsilon=!1,this.label=null}));function Z(t){return Z="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Z(t)}function Q(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Z(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Z(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Z(o)?o:String(o)),r)}var o}function tt(t,e){return tt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},tt(t,e)}function et(t){return et=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},et(t)}$.EPSILON=1,$.RANGE=2,$.RULE=3,$.PREDICATE=4,$.ATOM=5,$.ACTION=6,$.SET=7,$.NOT_SET=8,$.WILDCARD=9,$.PRECEDENCE=10,$.serializationNames=["INVALID","EPSILON","RANGE","RULE","PREDICATE","ATOM","ACTION","SET","NOT_SET","WILDCARD","PRECEDENCE"],$.serializationTypes={EpsilonTransition:$.EPSILON,RangeTransition:$.RANGE,RuleTransition:$.RULE,PredicateTransition:$.PREDICATE,AtomTransition:$.ATOM,ActionTransition:$.ACTION,SetTransition:$.SET,NotSetTransition:$.NOT_SET,WildcardTransition:$.WILDCARD,PrecedencePredicateTransition:$.PRECEDENCE};var nt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&tt(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=et(r);if(o){var n=et(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Z(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n,r){var o;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(o=i.call(this,t)).ruleIndex=e,o.precedence=n,o.followState=r,o.serializationType=$.RULE,o.isEpsilon=!0,o}return e=u,(n=[{key:"matches",value:function(t,e,n){return!1}}])&&Q(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function rt(t){return rt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},rt(t)}function ot(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==rt(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==rt(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===rt(o)?o:String(o)),r)}var o}function it(t,e){return it=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},it(t,e)}function ut(t){return ut=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ut(t)}var ct=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&it(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ut(r);if(i){var n=ut(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===rt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(n=u.call(this,t)).serializationType=$.SET,null!=e?n.label=e:(n.label=new B,n.label.addOne(o.INVALID_TYPE)),n}return e=c,(n=[{key:"matches",value:function(t,e,n){return this.label.contains(t)}},{key:"toString",value:function(){return this.label.toString()}}])&&ot(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}($);function at(t){return at="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},at(t)}function lt(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==at(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==at(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===at(o)?o:String(o)),r)}var o}function st(){return st="undefined"!=typeof Reflect&&Reflect.get?Reflect.get.bind():function(t,e,n){var r=function(t,e){for(;!Object.prototype.hasOwnProperty.call(t,e)&&null!==(t=pt(t)););return t}(t,e);if(r){var o=Object.getOwnPropertyDescriptor(r,e);return o.get?o.get.call(arguments.length<3?t:n):o.value}},st.apply(this,arguments)}function ft(t,e){return ft=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ft(t,e)}function pt(t){return pt=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},pt(t)}var yt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ft(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=pt(r);if(o){var n=pt(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===at(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,t,e)).serializationType=$.NOT_SET,n}return e=u,(n=[{key:"matches",value:function(t,e,n){return t>=e&&t<=n&&!st(pt(u.prototype),"matches",this).call(this,t,e,n)}},{key:"toString",value:function(){return"~"+st(pt(u.prototype),"toString",this).call(this)}}])&&lt(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(ct);function ht(t){return ht="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ht(t)}function bt(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ht(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ht(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ht(o)?o:String(o)),r)}var o}function vt(t,e){return vt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},vt(t,e)}function dt(t){return dt=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},dt(t)}var mt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&vt(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=dt(r);if(o){var n=dt(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ht(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this,t)).serializationType=$.WILDCARD,e}return e=u,(n=[{key:"matches",value:function(t,e,n){return t>=e&&t<=n}},{key:"toString",value:function(){return"."}}])&&bt(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function gt(t){return gt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},gt(t)}function St(t,e){return St=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},St(t,e)}function Ot(t){return Ot=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ot(t)}var wt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&St(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ot(n);if(r){var o=Ot(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===gt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.call(this,t)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}($);function _t(t){return _t="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},_t(t)}function Pt(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==_t(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==_t(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===_t(o)?o:String(o)),r)}var o}function Tt(t,e,n){return e&&Pt(t.prototype,e),n&&Pt(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}function Et(t){return Et="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Et(t)}function jt(t,e){return jt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},jt(t,e)}function kt(t){return kt=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},kt(t)}function xt(t){return xt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},xt(t)}function Rt(t,e){return Rt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Rt(t,e)}function Ct(t){return Ct=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ct(t)}var At=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Rt(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ct(n);if(r){var o=Ct(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===xt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.apply(this,arguments)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&jt(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=kt(n);if(r){var o=kt(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Et(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.apply(this,arguments)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Tt((function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}))));function Nt(t){return Nt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Nt(t)}function It(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Nt(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Nt(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Nt(o)?o:String(o)),r)}var o}function Lt(t,e){return Lt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Lt(t,e)}function Dt(t){return Dt=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Dt(t)}var Ft=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Lt(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Dt(r);if(o){var n=Dt(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Nt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.apply(this,arguments)}return e=u,(n=[{key:"ruleContext",get:function(){throw new Error("missing interface implementation")}}])&&It(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(At);function Bt(t){return Bt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Bt(t)}function Mt(t,e){return Mt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Mt(t,e)}function Ut(t){return Ut=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ut(t)}var Vt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Mt(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ut(n);if(r){var o=Ut(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Bt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.apply(this,arguments)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(At);function qt(t){return qt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},qt(t)}function Ht(t,e){return Ht=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ht(t,e)}function zt(t){return zt=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},zt(t)}var Yt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ht(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=zt(n);if(r){var o=zt(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===qt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.apply(this,arguments)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Vt),Kt={toStringTree:function(t,e,n){e=e||null,null!==(n=n||null)&&(e=n.ruleNames);var r=Kt.getNodeText(t,e);r=function(t,e){return t=t.replace(/\t/g,"\\t").replace(/\n/g,"\\n").replace(/\r/g,"\\r")}(r);var o=t.getChildCount();if(0===o)return r;var i="("+r+" ";o>0&&(r=Kt.toStringTree(t.getChild(0),e),i=i.concat(r));for(var u=1;u<o;u++)r=Kt.toStringTree(t.getChild(u),e),i=i.concat(" "+r);return i.concat(")")},getNodeText:function(t,e,n){if(e=e||null,null!==(n=n||null)&&(e=n.ruleNames),null!==e){if(t instanceof Ft){var r=t.ruleContext.getAltNumber();return 0!=r?e[t.ruleIndex]+":"+r:e[t.ruleIndex]}if(t instanceof Yt)return t.toString();if(t instanceof Vt&&null!==t.symbol)return t.symbol.text}var i=t.getPayload();return i instanceof o?i.text:t.getPayload().toString()},getChildren:function(t){for(var e=[],n=0;n<t.getChildCount();n++)e.push(t.getChild(n));return e},getAncestors:function(t){var e=[];for(t=t.getParent();null!==t;)e=[t].concat(e),t=t.getParent();return e},findAllTokenNodes:function(t,e){return Kt.findAllNodes(t,e,!0)},findAllRuleNodes:function(t,e){return Kt.findAllNodes(t,e,!1)},findAllNodes:function(t,e,n){var r=[];return Kt._findAllNodes(t,e,n,r),r},_findAllNodes:function(t,e,n,r){n&&t instanceof Vt?t.symbol.type===e&&r.push(t):!n&&t instanceof Ft&&t.ruleIndex===e&&r.push(t);for(var o=0;o<t.getChildCount();o++)Kt._findAllNodes(t.getChild(o),e,n,r)},descendants:function(t){for(var e=[t],n=0;n<t.getChildCount();n++)e=e.concat(Kt.descendants(t.getChild(n)));return e}};const Gt=Kt;function Wt(t){return Wt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Wt(t)}function Xt(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Wt(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Wt(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Wt(o)?o:String(o)),r)}var o}function Jt(t,e){return Jt=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Jt(t,e)}function $t(t){return $t=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},$t(t)}var Zt=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Jt(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=$t(r);if(o){var n=$t(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Wt(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this)).parentCtx=t||null,n.invokingState=e||-1,n}return e=u,(n=[{key:"depth",value:function(){for(var t=0,e=this;null!==e;)e=e.parentCtx,t+=1;return t}},{key:"isEmpty",value:function(){return-1===this.invokingState}},{key:"getSourceInterval",value:function(){return L.INVALID_INTERVAL}},{key:"ruleContext",get:function(){return this}},{key:"getPayload",value:function(){return this}},{key:"getText",value:function(){return 0===this.getChildCount()?"":this.children.map((function(t){return t.getText()})).join("")}},{key:"getAltNumber",value:function(){return 0}},{key:"setAltNumber",value:function(t){}},{key:"getChild",value:function(t){return null}},{key:"getChildCount",value:function(){return 0}},{key:"accept",value:function(t){return t.visitChildren(this)}},{key:"toStringTree",value:function(t,e){return Gt.toStringTree(this,t,e)}},{key:"toString",value:function(t,e){t=t||null,e=e||null;for(var n=this,r="[";null!==n&&n!==e;){if(null===t)n.isEmpty()||(r+=n.invokingState);else{var o=n.ruleIndex;r+=o>=0&&o<t.length?t[o]:""+o}null===n.parentCtx||null===t&&n.parentCtx.isEmpty()||(r+=" "),n=n.parentCtx}return r+"]"}}])&&Xt(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Ft);function Qt(t){return Qt="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Qt(t)}function te(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Qt(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Qt(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Qt(o)?o:String(o)),r)}var o}var ee=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.cachedHashCode=e}var e,n;return e=t,(n=[{key:"isEmpty",value:function(){return this===t.EMPTY}},{key:"hasEmptyPath",value:function(){return this.getReturnState(this.length-1)===t.EMPTY_RETURN_STATE}},{key:"hashCode",value:function(){return this.cachedHashCode}},{key:"updateHashCode",value:function(t){t.update(this.cachedHashCode)}}])&&te(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function ne(t){return ne="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ne(t)}function re(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ne(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ne(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ne(o)?o:String(o)),r)}var o}function oe(t,e){return oe=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},oe(t,e)}function ie(t,e){if(e&&("object"===ne(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return ue(t)}function ue(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function ce(t){return ce=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ce(t)}ee.EMPTY=null,ee.EMPTY_RETURN_STATE=2147483647,ee.globalNodeCount=1,ee.id=ee.globalNodeCount,ee.trace_atn_sim=!1;var ae=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&oe(t,e)}(c,t);var e,n,r,o,u=(r=c,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ce(r);if(o){var n=ce(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return ie(this,t)});function c(t,e){var n;!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c);var r=new a;r.update(t,e);var o=r.finish();return(n=u.call(this,o)).parents=t,n.returnStates=e,ie(n,ue(n))}return e=c,(n=[{key:"isEmpty",value:function(){return this.returnStates[0]===ee.EMPTY_RETURN_STATE}},{key:"getParent",value:function(t){return this.parents[t]}},{key:"getReturnState",value:function(t){return this.returnStates[t]}},{key:"equals",value:function(t){return this===t||t instanceof c&&this.hashCode()===t.hashCode()&&i(this.returnStates,t.returnStates)&&i(this.parents,t.parents)}},{key:"toString",value:function(){if(this.isEmpty())return"[]";for(var t="[",e=0;e<this.returnStates.length;e++)e>0&&(t+=", "),this.returnStates[e]!==ee.EMPTY_RETURN_STATE?(t+=this.returnStates[e],null!==this.parents[e]?t=t+" "+this.parents[e]:t+="null"):t+="$";return t+"]"}},{key:"length",get:function(){return this.returnStates.length}}])&&re(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(ee);function le(t){return le="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},le(t)}function se(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==le(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==le(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===le(o)?o:String(o)),r)}var o}function fe(t,e){return fe=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},fe(t,e)}function pe(t){return pe=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},pe(t)}var ye=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&fe(t,e)}(c,t);var e,n,r,o,i,u=(o=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=pe(o);if(i){var n=pe(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===le(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t,e){var n;!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c);var r,o=new a;return null!==t?o.update(t,e):o.update(1),r=o.finish(),(n=u.call(this,r)).parentCtx=t,n.returnState=e,n}return e=c,r=[{key:"create",value:function(t,e){return e===ee.EMPTY_RETURN_STATE&&null===t?ee.EMPTY:new c(t,e)}}],(n=[{key:"getParent",value:function(t){return this.parentCtx}},{key:"getReturnState",value:function(t){return this.returnState}},{key:"equals",value:function(t){return this===t||t instanceof c&&this.hashCode()===t.hashCode()&&this.returnState===t.returnState&&(null==this.parentCtx?null==t.parentCtx:this.parentCtx.equals(t.parentCtx))}},{key:"toString",value:function(){var t=null===this.parentCtx?"":this.parentCtx.toString();return 0===t.length?this.returnState===ee.EMPTY_RETURN_STATE?"$":""+this.returnState:this.returnState+" "+t}},{key:"length",get:function(){return 1}}])&&se(e.prototype,n),r&&se(e,r),Object.defineProperty(e,"prototype",{writable:!1}),c}(ee);function he(t){return he="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},he(t)}function be(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==he(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==he(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===he(o)?o:String(o)),r)}var o}function ve(t,e){return ve=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ve(t,e)}function de(t){return de=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},de(t)}var me=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ve(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=de(r);if(o){var n=de(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===he(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,null,ee.EMPTY_RETURN_STATE)}return e=u,(n=[{key:"isEmpty",value:function(){return!0}},{key:"getParent",value:function(t){return null}},{key:"getReturnState",value:function(t){return this.returnState}},{key:"equals",value:function(t){return this===t}},{key:"toString",value:function(){return"$"}}])&&be(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(ye);function ge(t){return ge="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ge(t)}function Se(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ge(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ge(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ge(o)?o:String(o)),r)}var o}ee.EMPTY=new me;var Oe="h-",we=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.data={},this.hashFunction=e||l,this.equalsFunction=n||s}var e,n;return e=t,(n=[{key:"set",value:function(t,e){var n=Oe+this.hashFunction(t);if(n in this.data){for(var r=this.data[n],o=0;o<r.length;o++){var i=r[o];if(this.equalsFunction(t,i.key)){var u=i.value;return i.value=e,u}}return r.push({key:t,value:e}),e}return this.data[n]=[{key:t,value:e}],e}},{key:"containsKey",value:function(t){var e=Oe+this.hashFunction(t);if(e in this.data)for(var n=this.data[e],r=0;r<n.length;r++){var o=n[r];if(this.equalsFunction(t,o.key))return!0}return!1}},{key:"get",value:function(t){var e=Oe+this.hashFunction(t);if(e in this.data)for(var n=this.data[e],r=0;r<n.length;r++){var o=n[r];if(this.equalsFunction(t,o.key))return o.value}return null}},{key:"entries",value:function(){var t=this;return Object.keys(this.data).filter((function(t){return t.startsWith(Oe)})).flatMap((function(e){return t.data[e]}),this)}},{key:"getKeys",value:function(){return this.entries().map((function(t){return t.key}))}},{key:"getValues",value:function(){return this.entries().map((function(t){return t.value}))}},{key:"toString",value:function(){return"["+this.entries().map((function(t){return"{"+t.key+":"+t.value+"}"})).join(", ")+"]"}},{key:"length",get:function(){var t=this;return Object.keys(this.data).filter((function(t){return t.startsWith(Oe)})).map((function(e){return t.data[e].length}),this).reduce((function(t,e){return t+e}),0)}}])&&Se(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function _e(t,e){if(null==e&&(e=Zt.EMPTY),null===e.parentCtx||e===Zt.EMPTY)return ee.EMPTY;var n=_e(t,e.parentCtx),r=t.states[e.invokingState].transitions[0];return ye.create(n,r.followState.stateNumber)}function Pe(t,e,n){if(t.isEmpty())return t;var r=n.get(t)||null;if(null!==r)return r;if(null!==(r=e.get(t)))return n.set(t,r),r;for(var o=!1,i=[],u=0;u<i.length;u++){var c=Pe(t.getParent(u),e,n);if(o||c!==t.getParent(u)){if(!o){i=[];for(var a=0;a<t.length;a++)i[a]=t.getParent(a);o=!0}i[u]=c}}if(!o)return e.add(t),n.set(t,t),t;var l;return l=0===i.length?ee.EMPTY:1===i.length?ye.create(i[0],t.getReturnState(0)):new ae(i,t.returnStates),e.add(l),n.set(l,l),n.set(t,l),l}function Te(t,e,n,r){if(t===e)return t;if(t instanceof ye&&e instanceof ye)return function(t,e,n,r){if(null!==r){var o=r.get(t,e);if(null!==o)return o;if(null!==(o=r.get(e,t)))return o}var i=function(t,e,n){if(n){if(t===ee.EMPTY)return ee.EMPTY;if(e===ee.EMPTY)return ee.EMPTY}else{if(t===ee.EMPTY&&e===ee.EMPTY)return ee.EMPTY;if(t===ee.EMPTY){var r=[e.returnState,ee.EMPTY_RETURN_STATE],o=[e.parentCtx,null];return new ae(o,r)}if(e===ee.EMPTY){var i=[t.returnState,ee.EMPTY_RETURN_STATE],u=[t.parentCtx,null];return new ae(u,i)}}return null}(t,e,n);if(null!==i)return null!==r&&r.set(t,e,i),i;if(t.returnState===e.returnState){var u=Te(t.parentCtx,e.parentCtx,n,r);if(u===t.parentCtx)return t;if(u===e.parentCtx)return e;var c=ye.create(u,t.returnState);return null!==r&&r.set(t,e,c),c}var a=null;if((t===e||null!==t.parentCtx&&t.parentCtx===e.parentCtx)&&(a=t.parentCtx),null!==a){var l=[t.returnState,e.returnState];t.returnState>e.returnState&&(l[0]=e.returnState,l[1]=t.returnState);var s=new ae([a,a],l);return null!==r&&r.set(t,e,s),s}var f=[t.returnState,e.returnState],p=[t.parentCtx,e.parentCtx];t.returnState>e.returnState&&(f[0]=e.returnState,f[1]=t.returnState,p=[e.parentCtx,t.parentCtx]);var y=new ae(p,f);return null!==r&&r.set(t,e,y),y}(t,e,n,r);if(n){if(t instanceof me)return t;if(e instanceof me)return e}return t instanceof ye&&(t=new ae([t.getParent()],[t.returnState])),e instanceof ye&&(e=new ae([e.getParent()],[e.returnState])),function(t,e,n,r){if(null!==r){var o=r.get(t,e);if(null!==o)return ee.trace_atn_sim&&console.log("mergeArrays a="+t+",b="+e+" -> previous"),o;if(null!==(o=r.get(e,t)))return ee.trace_atn_sim&&console.log("mergeArrays a="+t+",b="+e+" -> previous"),o}for(var i=0,u=0,c=0,a=new Array(t.returnStates.length+e.returnStates.length).fill(0),l=new Array(t.returnStates.length+e.returnStates.length).fill(null);i<t.returnStates.length&&u<e.returnStates.length;){var s=t.parents[i],f=e.parents[u];if(t.returnStates[i]===e.returnStates[u]){var p=t.returnStates[i];p===ee.EMPTY_RETURN_STATE&&null===s&&null===f||null!==s&&null!==f&&s===f?(l[c]=s,a[c]=p):(l[c]=Te(s,f,n,r),a[c]=p),i+=1,u+=1}else t.returnStates[i]<e.returnStates[u]?(l[c]=s,a[c]=t.returnStates[i],i+=1):(l[c]=f,a[c]=e.returnStates[u],u+=1);c+=1}if(i<t.returnStates.length)for(var y=i;y<t.returnStates.length;y++)l[c]=t.parents[y],a[c]=t.returnStates[y],c+=1;else for(var h=u;h<e.returnStates.length;h++)l[c]=e.parents[h],a[c]=e.returnStates[h],c+=1;if(c<l.length){if(1===c){var b=ye.create(l[0],a[0]);return null!==r&&r.set(t,e,b),b}l=l.slice(0,c),a=a.slice(0,c)}var v=new ae(l,a);return v.equals(t)?(null!==r&&r.set(t,e,t),ee.trace_atn_sim&&console.log("mergeArrays a="+t+",b="+e+" -> a"),t):v.equals(e)?(null!==r&&r.set(t,e,e),ee.trace_atn_sim&&console.log("mergeArrays a="+t+",b="+e+" -> b"),e):(function(t){for(var e=new we,n=0;n<t.length;n++){var r=t[n];e.containsKey(r)||e.set(r,r)}for(var o=0;o<t.length;o++)t[o]=e.get(t[o])}(l),null!==r&&r.set(t,e,v),ee.trace_atn_sim&&console.log("mergeArrays a="+t+",b="+e+" -> "+v),v)}(t,e,n,r)}function Ee(t){return Ee="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ee(t)}function je(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ee(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ee(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ee(o)?o:String(o)),r)}var o}var ke=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.data=[]}var e,n;return e=t,(n=[{key:"add",value:function(t){this.data[t]=!0}},{key:"or",value:function(t){var e=this;Object.keys(t.data).map((function(t){return e.add(t)}),this)}},{key:"remove",value:function(t){delete this.data[t]}},{key:"has",value:function(t){return!0===this.data[t]}},{key:"values",value:function(){return Object.keys(this.data)}},{key:"minValue",value:function(){return Math.min.apply(null,this.values())}},{key:"hashCode",value:function(){return a.hashStuff(this.values())}},{key:"equals",value:function(e){return e instanceof t&&i(this.data,e.data)}},{key:"toString",value:function(){return"{"+this.values().join(", ")+"}"}},{key:"length",get:function(){return this.values().length}}])&&je(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function xe(t){return xe="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},xe(t)}function Re(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==xe(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==xe(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===xe(o)?o:String(o)),r)}var o}var Ce=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.atn=e}var e,n;return e=t,(n=[{key:"getDecisionLookahead",value:function(e){if(null===e)return null;for(var n=e.transitions.length,r=[],o=0;o<n;o++){r[o]=new B;var i=new v;this._LOOK(e.transition(o).target,null,ee.EMPTY,r[o],i,new ke,!1,!1),(0===r[o].length||r[o].contains(t.HIT_PRED))&&(r[o]=null)}return r}},{key:"LOOK",value:function(t,e,n){var r=new B,o=null!==(n=n||null)?_e(t.atn,n):null;return this._LOOK(t,e,o,r,new v,new ke,!0,!0),r}},{key:"_LOOK",value:function(e,n,r,i,u,c,a,l){var s=new A({state:e,alt:0,context:r},null);if(!u.has(s)){if(u.add(s),e===n){if(null===r)return void i.addOne(o.EPSILON);if(r.isEmpty()&&l)return void i.addOne(o.EOF)}if(e instanceof G){if(null===r)return void i.addOne(o.EPSILON);if(r.isEmpty()&&l)return void i.addOne(o.EOF);if(r!==ee.EMPTY){var f=c.has(e.ruleIndex);try{c.remove(e.ruleIndex);for(var p=0;p<r.length;p++){var y=this.atn.states[r.getReturnState(p)];this._LOOK(y,n,r.getParent(p),i,u,c,a,l)}}finally{f&&c.add(e.ruleIndex)}return}}for(var h=0;h<e.transitions.length;h++){var b=e.transitions[h];if(b.constructor===nt){if(c.has(b.target.ruleIndex))continue;var v=ye.create(r,b.followState.stateNumber);try{c.add(b.target.ruleIndex),this._LOOK(b.target,n,v,i,u,c,a,l)}finally{c.remove(b.target.ruleIndex)}}else if(b instanceof wt)a?this._LOOK(b.target,n,r,i,u,c,a,l):i.addOne(t.HIT_PRED);else if(b.isEpsilon)this._LOOK(b.target,n,r,i,u,c,a,l);else if(b.constructor===mt)i.addRange(o.MIN_USER_TOKEN_TYPE,this.atn.maxTokenType);else{var d=b.label;null!==d&&(b instanceof yt&&(d=d.complement(o.MIN_USER_TOKEN_TYPE,this.atn.maxTokenType)),i.addSet(d))}}}}}])&&Re(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Ae(t){return Ae="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ae(t)}function Ne(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ae(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ae(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ae(o)?o:String(o)),r)}var o}Ce.HIT_PRED=o.INVALID_TYPE;var Ie=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.grammarType=e,this.maxTokenType=n,this.states=[],this.decisionToState=[],this.ruleToStartState=[],this.ruleToStopState=null,this.modeNameToStartState={},this.ruleToTokenType=null,this.lexerActions=null,this.modeToStartState=[]}var e,n;return e=t,(n=[{key:"nextTokensInContext",value:function(t,e){return new Ce(this).LOOK(t,null,e)}},{key:"nextTokensNoContext",value:function(t){return null!==t.nextTokenWithinRule||(t.nextTokenWithinRule=this.nextTokensInContext(t,null),t.nextTokenWithinRule.readOnly=!0),t.nextTokenWithinRule}},{key:"nextTokens",value:function(t,e){return void 0===e?this.nextTokensNoContext(t):this.nextTokensInContext(t,e)}},{key:"addState",value:function(t){null!==t&&(t.atn=this,t.stateNumber=this.states.length),this.states.push(t)}},{key:"removeState",value:function(t){this.states[t.stateNumber]=null}},{key:"defineDecisionState",value:function(t){return this.decisionToState.push(t),t.decision=this.decisionToState.length-1,t.decision}},{key:"getDecisionState",value:function(t){return 0===this.decisionToState.length?null:this.decisionToState[t]}},{key:"getExpectedTokens",value:function(t,e){if(t<0||t>=this.states.length)throw"Invalid state number.";var n=this.states[t],r=this.nextTokens(n);if(!r.contains(o.EPSILON))return r;var i=new B;for(i.addSet(r),i.removeOne(o.EPSILON);null!==e&&e.invokingState>=0&&r.contains(o.EPSILON);){var u=this.states[e.invokingState].transitions[0];r=this.nextTokens(u.followState),i.addSet(r),i.removeOne(o.EPSILON),e=e.parentCtx}return r.contains(o.EPSILON)&&i.addOne(o.EOF),i}}])&&Ne(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();Ie.INVALID_ALT_NUMBER=0;function Le(t){return Le="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Le(t)}function De(t,e){return De=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},De(t,e)}function Fe(t){return Fe=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Fe(t)}var Be=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&De(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Fe(n);if(r){var o=Fe(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Le(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.BASIC,t}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function Me(t){return Me="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Me(t)}function Ue(t,e){return Ue=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ue(t,e)}function Ve(t,e){if(e&&("object"===Me(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return qe(t)}function qe(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function He(t){return He=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},He(t)}var ze=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ue(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=He(n);if(r){var o=He(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Ve(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).decision=-1,t.nonGreedy=!1,Ve(t,qe(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function Ye(t){return Ye="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ye(t)}function Ke(t,e){return Ke=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ke(t,e)}function Ge(t,e){if(e&&("object"===Ye(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return We(t)}function We(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Xe(t){return Xe=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Xe(t)}var Je=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ke(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Xe(n);if(r){var o=Xe(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Ge(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).endState=null,Ge(t,We(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ze);function $e(t){return $e="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},$e(t)}function Ze(t,e){return Ze=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ze(t,e)}function Qe(t,e){if(e&&("object"===$e(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return tn(t)}function tn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function en(t){return en=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},en(t)}var nn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ze(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=en(n);if(r){var o=en(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Qe(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.BLOCK_END,t.startState=null,Qe(t,tn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function rn(t){return rn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},rn(t)}function on(t,e){return on=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},on(t,e)}function un(t,e){if(e&&("object"===rn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return cn(t)}function cn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function an(t){return an=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},an(t)}var ln=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&on(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=an(n);if(r){var o=an(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return un(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.LOOP_END,t.loopBackState=null,un(t,cn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function sn(t){return sn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},sn(t)}function fn(t,e){return fn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},fn(t,e)}function pn(t,e){if(e&&("object"===sn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return yn(t)}function yn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function hn(t){return hn=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},hn(t)}var bn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&fn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=hn(n);if(r){var o=hn(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return pn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.RULE_START,t.stopState=null,t.isPrecedenceRule=!1,pn(t,yn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function vn(t){return vn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},vn(t)}function dn(t,e){return dn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},dn(t,e)}function mn(t,e){if(e&&("object"===vn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return gn(t)}function gn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Sn(t){return Sn=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Sn(t)}var On=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&dn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Sn(n);if(r){var o=Sn(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return mn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.TOKEN_START,mn(t,gn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ze);function wn(t){return wn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},wn(t)}function _n(t,e){return _n=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},_n(t,e)}function Pn(t,e){if(e&&("object"===wn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Tn(t)}function Tn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function En(t){return En=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},En(t)}var jn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&_n(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=En(n);if(r){var o=En(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Pn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.PLUS_LOOP_BACK,Pn(t,Tn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ze);function kn(t){return kn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},kn(t)}function xn(t,e){return xn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},xn(t,e)}function Rn(t,e){if(e&&("object"===kn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Cn(t)}function Cn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function An(t){return An=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},An(t)}var Nn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&xn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=An(n);if(r){var o=An(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Rn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.STAR_LOOP_BACK,Rn(t,Cn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(V);function In(t){return In="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},In(t)}function Ln(t,e){return Ln=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ln(t,e)}function Dn(t,e){if(e&&("object"===In(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Fn(t)}function Fn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Bn(t){return Bn=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Bn(t)}var Mn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ln(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Bn(n);if(r){var o=Bn(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Dn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.STAR_LOOP_ENTRY,t.loopBackState=null,t.isPrecedenceDecision=null,Dn(t,Fn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ze);function Un(t){return Un="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Un(t)}function Vn(t,e){return Vn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Vn(t,e)}function qn(t,e){if(e&&("object"===Un(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Hn(t)}function Hn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function zn(t){return zn=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},zn(t)}var Yn=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Vn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=zn(n);if(r){var o=zn(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return qn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.PLUS_BLOCK_START,t.loopBackState=null,qn(t,Hn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Je);function Kn(t){return Kn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Kn(t)}function Gn(t,e){return Gn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Gn(t,e)}function Wn(t,e){if(e&&("object"===Kn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Xn(t)}function Xn(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Jn(t){return Jn=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Jn(t)}var $n=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Gn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Jn(n);if(r){var o=Jn(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return Wn(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.STAR_BLOCK_START,Wn(t,Xn(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Je);function Zn(t){return Zn="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Zn(t)}function Qn(t,e){return Qn=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Qn(t,e)}function tr(t,e){if(e&&("object"===Zn(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return er(t)}function er(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function nr(t){return nr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},nr(t)}var rr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Qn(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=nr(n);if(r){var o=nr(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return tr(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).stateType=V.BLOCK_START,tr(t,er(t))}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Je);function or(t){return or="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},or(t)}function ir(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==or(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==or(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===or(o)?o:String(o)),r)}var o}function ur(t,e){return ur=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ur(t,e)}function cr(t){return cr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},cr(t)}var ar=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ur(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=cr(r);if(o){var n=cr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===or(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,t)).label_=e,n.label=n.makeLabel(),n.serializationType=$.ATOM,n}return e=u,(n=[{key:"makeLabel",value:function(){var t=new B;return t.addOne(this.label_),t}},{key:"matches",value:function(t,e,n){return this.label_===t}},{key:"toString",value:function(){return this.label_}}])&&ir(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function lr(t){return lr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},lr(t)}function sr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==lr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==lr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===lr(o)?o:String(o)),r)}var o}function fr(t,e){return fr=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},fr(t,e)}function pr(t){return pr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},pr(t)}var yr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&fr(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=pr(r);if(o){var n=pr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===lr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n){var r;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(r=i.call(this,t)).serializationType=$.RANGE,r.start=e,r.stop=n,r.label=r.makeLabel(),r}return e=u,(n=[{key:"makeLabel",value:function(){var t=new B;return t.addRange(this.start,this.stop),t}},{key:"matches",value:function(t,e,n){return t>=this.start&&t<=this.stop}},{key:"toString",value:function(){return"'"+String.fromCharCode(this.start)+"'..'"+String.fromCharCode(this.stop)+"'"}}])&&sr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function hr(t){return hr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},hr(t)}function br(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==hr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==hr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===hr(o)?o:String(o)),r)}var o}function vr(t,e){return vr=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},vr(t,e)}function dr(t){return dr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},dr(t)}var mr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&vr(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=dr(r);if(o){var n=dr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===hr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n,r){var o;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(o=i.call(this,t)).serializationType=$.ACTION,o.ruleIndex=e,o.actionIndex=void 0===n?-1:n,o.isCtxDependent=void 0!==r&&r,o.isEpsilon=!0,o}return e=u,(n=[{key:"matches",value:function(t,e,n){return!1}},{key:"toString",value:function(){return"action_"+this.ruleIndex+":"+this.actionIndex}}])&&br(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function gr(t){return gr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},gr(t)}function Sr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==gr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==gr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===gr(o)?o:String(o)),r)}var o}function Or(t,e){return Or=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Or(t,e)}function wr(t){return wr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},wr(t)}var _r=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Or(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=wr(r);if(o){var n=wr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===gr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,t)).serializationType=$.EPSILON,n.isEpsilon=!0,n.outermostPrecedenceReturn=e,n}return e=u,(n=[{key:"matches",value:function(t,e,n){return!1}},{key:"toString",value:function(){return"epsilon"}}])&&Sr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($);function Pr(t){return Pr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Pr(t)}function Tr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Pr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Pr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Pr(o)?o:String(o)),r)}var o}function Er(t,e){return Er=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Er(t,e)}function jr(t){return jr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},jr(t)}var kr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Er(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=jr(r);if(o){var n=jr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Pr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n){var r;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(r=i.call(this)).ruleIndex=void 0===t?-1:t,r.predIndex=void 0===e?-1:e,r.isCtxDependent=void 0!==n&&n,r}return e=u,(n=[{key:"evaluate",value:function(t,e){var n=this.isCtxDependent?e:null;return t.sempred(n,this.ruleIndex,this.predIndex)}},{key:"updateHashCode",value:function(t){t.update(this.ruleIndex,this.predIndex,this.isCtxDependent)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.ruleIndex===t.ruleIndex&&this.predIndex===t.predIndex&&this.isCtxDependent===t.isCtxDependent}},{key:"toString",value:function(){return"{"+this.ruleIndex+":"+this.predIndex+"}?"}}])&&Tr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(T);function xr(t){return xr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},xr(t)}function Rr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==xr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==xr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===xr(o)?o:String(o)),r)}var o}function Cr(t,e){return Cr=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Cr(t,e)}function Ar(t){return Ar=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ar(t)}T.NONE=new kr;var Nr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Cr(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ar(r);if(o){var n=Ar(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===xr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n,r){var o;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(o=i.call(this,t)).serializationType=$.PREDICATE,o.ruleIndex=e,o.predIndex=n,o.isCtxDependent=r,o.isEpsilon=!0,o}return e=u,(n=[{key:"matches",value:function(t,e,n){return!1}},{key:"getPredicate",value:function(){return new kr(this.ruleIndex,this.predIndex,this.isCtxDependent)}},{key:"toString",value:function(){return"pred_"+this.ruleIndex+":"+this.predIndex}}])&&Rr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(wt);function Ir(t){return Ir="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ir(t)}function Lr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ir(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ir(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ir(o)?o:String(o)),r)}var o}function Dr(t,e){return Dr=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Dr(t,e)}function Fr(t){return Fr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Fr(t)}var Br=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Dr(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Fr(r);if(o){var n=Fr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ir(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this)).precedence=void 0===t?0:t,e}return e=u,(n=[{key:"evaluate",value:function(t,e){return t.precpred(e,this.precedence)}},{key:"evalPrecedence",value:function(t,e){return t.precpred(e,this.precedence)?T.NONE:null}},{key:"compareTo",value:function(t){return this.precedence-t.precedence}},{key:"updateHashCode",value:function(t){t.update(this.precedence)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.precedence===t.precedence}},{key:"toString",value:function(){return"{"+this.precedence+">=prec}?"}}])&&Lr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(T);function Mr(t){return Mr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Mr(t)}function Ur(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Mr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Mr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Mr(o)?o:String(o)),r)}var o}function Vr(t,e){return Vr=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Vr(t,e)}function qr(t){return qr=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},qr(t)}T.PrecedencePredicate=Br;var Hr=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Vr(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=qr(r);if(o){var n=qr(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Mr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,t)).serializationType=$.PRECEDENCE,n.precedence=e,n.isEpsilon=!0,n}return e=u,(n=[{key:"matches",value:function(t,e,n){return!1}},{key:"getPredicate",value:function(){return new Br(this.precedence)}},{key:"toString",value:function(){return this.precedence+" >= _p"}}])&&Ur(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(wt);function zr(t){return zr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},zr(t)}function Yr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==zr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==zr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===zr(o)?o:String(o)),r)}var o}function Kr(t,e,n){return e&&Yr(t.prototype,e),n&&Yr(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}var Gr=Kr((function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),void 0===e&&(e=null),this.readOnly=!1,this.verifyATN=null===e||e.verifyATN,this.generateRuleBypassTransitions=null!==e&&e.generateRuleBypassTransitions}));Gr.defaultOptions=new Gr,Gr.defaultOptions.readOnly=!0;const Wr={CHANNEL:0,CUSTOM:1,MODE:2,MORE:3,POP_MODE:4,PUSH_MODE:5,SKIP:6,TYPE:7};function Xr(t){return Xr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Xr(t)}function Jr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Xr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Xr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Xr(o)?o:String(o)),r)}var o}var $r=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.actionType=e,this.isPositionDependent=!1}var e,n;return e=t,(n=[{key:"hashCode",value:function(){var t=new a;return this.updateHashCode(t),t.finish()}},{key:"updateHashCode",value:function(t){t.update(this.actionType)}},{key:"equals",value:function(t){return this===t}}])&&Jr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Zr(t){return Zr="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Zr(t)}function Qr(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Zr(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Zr(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Zr(o)?o:String(o)),r)}var o}function to(t,e){return to=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},to(t,e)}function eo(t){return eo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},eo(t)}var no=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&to(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=eo(r);if(o){var n=eo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Zr(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,Wr.SKIP)}return e=u,(n=[{key:"execute",value:function(t){t.skip()}},{key:"toString",value:function(){return"skip"}}])&&Qr(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function ro(t){return ro="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ro(t)}function oo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ro(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ro(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ro(o)?o:String(o)),r)}var o}function io(t,e){return io=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},io(t,e)}function uo(t){return uo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},uo(t)}no.INSTANCE=new no;var co=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&io(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=uo(r);if(o){var n=uo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ro(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this,Wr.CHANNEL)).channel=t,e}return e=u,(n=[{key:"execute",value:function(t){t._channel=this.channel}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.channel)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.channel===t.channel}},{key:"toString",value:function(){return"channel("+this.channel+")"}}])&&oo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function ao(t){return ao="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ao(t)}function lo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ao(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ao(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ao(o)?o:String(o)),r)}var o}function so(t,e){return so=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},so(t,e)}function fo(t){return fo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},fo(t)}var po=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&so(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=fo(r);if(o){var n=fo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ao(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,Wr.CUSTOM)).ruleIndex=t,n.actionIndex=e,n.isPositionDependent=!0,n}return e=u,(n=[{key:"execute",value:function(t){t.action(null,this.ruleIndex,this.actionIndex)}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.ruleIndex,this.actionIndex)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.ruleIndex===t.ruleIndex&&this.actionIndex===t.actionIndex}}])&&lo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function yo(t){return yo="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},yo(t)}function ho(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==yo(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==yo(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===yo(o)?o:String(o)),r)}var o}function bo(t,e){return bo=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},bo(t,e)}function vo(t){return vo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},vo(t)}var mo=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&bo(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=vo(r);if(o){var n=vo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===yo(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,Wr.MORE)}return e=u,(n=[{key:"execute",value:function(t){t.more()}},{key:"toString",value:function(){return"more"}}])&&ho(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function go(t){return go="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},go(t)}function So(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==go(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==go(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===go(o)?o:String(o)),r)}var o}function Oo(t,e){return Oo=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Oo(t,e)}function wo(t){return wo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},wo(t)}mo.INSTANCE=new mo;var _o=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Oo(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=wo(r);if(o){var n=wo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===go(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this,Wr.TYPE)).type=t,e}return e=u,(n=[{key:"execute",value:function(t){t.type=this.type}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.type)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.type===t.type}},{key:"toString",value:function(){return"type("+this.type+")"}}])&&So(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function Po(t){return Po="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Po(t)}function To(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Po(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Po(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Po(o)?o:String(o)),r)}var o}function Eo(t,e){return Eo=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Eo(t,e)}function jo(t){return jo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},jo(t)}var ko=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Eo(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=jo(r);if(o){var n=jo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Po(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this,Wr.PUSH_MODE)).mode=t,e}return e=u,(n=[{key:"execute",value:function(t){t.pushMode(this.mode)}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.mode)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.mode===t.mode}},{key:"toString",value:function(){return"pushMode("+this.mode+")"}}])&&To(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function xo(t){return xo="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},xo(t)}function Ro(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==xo(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==xo(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===xo(o)?o:String(o)),r)}var o}function Co(t,e){return Co=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Co(t,e)}function Ao(t){return Ao=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ao(t)}var No=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Co(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ao(r);if(o){var n=Ao(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===xo(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,Wr.POP_MODE)}return e=u,(n=[{key:"execute",value:function(t){t.popMode()}},{key:"toString",value:function(){return"popMode"}}])&&Ro(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function Io(t){return Io="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Io(t)}function Lo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Io(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Io(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Io(o)?o:String(o)),r)}var o}function Do(t,e){return Do=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Do(t,e)}function Fo(t){return Fo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Fo(t)}No.INSTANCE=new No;var Bo=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Do(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Fo(r);if(o){var n=Fo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Io(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this,Wr.MODE)).mode=t,e}return e=u,(n=[{key:"execute",value:function(t){t.mode(this.mode)}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.mode)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.mode===t.mode}},{key:"toString",value:function(){return"mode("+this.mode+")"}}])&&Lo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function Mo(t){return Mo="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Mo(t)}function Uo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Mo(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Mo(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Mo(o)?o:String(o)),r)}var o}function Vo(t,e){var n=[];return n[t-1]=e,n.map((function(t){return e}))}var qo=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),null==e&&(e=Gr.defaultOptions),this.deserializationOptions=e,this.stateFactories=null,this.actionFactories=null}var e,n;return e=t,n=[{key:"deserialize",value:function(t){var e=this.reset(t);this.checkVersion(e),e&&this.skipUUID();var n=this.readATN();this.readStates(n,e),this.readRules(n,e),this.readModes(n);var r=[];return this.readSets(n,r,this.readInt.bind(this)),e&&this.readSets(n,r,this.readInt32.bind(this)),this.readEdges(n,r),this.readDecisions(n),this.readLexerActions(n,e),this.markPrecedenceDecisions(n),this.verifyATN(n),this.deserializationOptions.generateRuleBypassTransitions&&1===n.grammarType&&(this.generateRuleBypassTransitions(n),this.verifyATN(n)),n}},{key:"reset",value:function(t){if(3===(t.charCodeAt?t.charCodeAt(0):t[0])){var e=t.split("").map((function(t){var e=t.charCodeAt(0);return e>1?e-2:e+65534}));return e[0]=t.charCodeAt(0),this.data=e,this.pos=0,!0}return this.data=t,this.pos=0,!1}},{key:"skipUUID",value:function(){for(var t=0;t++<8;)this.readInt()}},{key:"checkVersion",value:function(t){var e=this.readInt();if(!t&&4!==e)throw"Could not deserialize ATN with version "+e+" (expected 4)."}},{key:"readATN",value:function(){var t=this.readInt(),e=this.readInt();return new Ie(t,e)}},{key:"readStates",value:function(t,e){for(var n,r,o,i=[],u=[],c=this.readInt(),a=0;a<c;a++){var l=this.readInt();if(l!==V.INVALID_TYPE){var s=this.readInt();e&&65535===s&&(s=-1);var f=this.stateFactory(l,s);if(l===V.LOOP_END){var p=this.readInt();i.push([f,p])}else if(f instanceof Je){var y=this.readInt();u.push([f,y])}t.addState(f)}else t.addState(null)}for(n=0;n<i.length;n++)(r=i[n])[0].loopBackState=t.states[r[1]];for(n=0;n<u.length;n++)(r=u[n])[0].endState=t.states[r[1]];var h=this.readInt();for(n=0;n<h;n++)o=this.readInt(),t.states[o].nonGreedy=!0;var b=this.readInt();for(n=0;n<b;n++)o=this.readInt(),t.states[o].isPrecedenceRule=!0}},{key:"readRules",value:function(t,e){var n,r=this.readInt();for(0===t.grammarType&&(t.ruleToTokenType=Vo(r,0)),t.ruleToStartState=Vo(r,0),n=0;n<r;n++){var i=this.readInt();if(t.ruleToStartState[n]=t.states[i],0===t.grammarType){var u=this.readInt();e&&65535===u&&(u=o.EOF),t.ruleToTokenType[n]=u}}for(t.ruleToStopState=Vo(r,0),n=0;n<t.states.length;n++){var c=t.states[n];c instanceof G&&(t.ruleToStopState[c.ruleIndex]=c,t.ruleToStartState[c.ruleIndex].stopState=c)}}},{key:"readModes",value:function(t){for(var e=this.readInt(),n=0;n<e;n++){var r=this.readInt();t.modeToStartState.push(t.states[r])}}},{key:"readSets",value:function(t,e,n){for(var r=this.readInt(),o=0;o<r;o++){var i=new B;e.push(i);var u=this.readInt();0!==this.readInt()&&i.addOne(-1);for(var c=0;c<u;c++){var a=n(),l=n();i.addRange(a,l)}}}},{key:"readEdges",value:function(t,e){var n,r,o,i,u,c=this.readInt();for(n=0;n<c;n++){var a=this.readInt(),l=this.readInt(),s=this.readInt(),f=this.readInt(),p=this.readInt(),y=this.readInt();i=this.edgeFactory(t,s,a,l,f,p,y,e),t.states[a].addTransition(i)}for(n=0;n<t.states.length;n++)for(o=t.states[n],r=0;r<o.transitions.length;r++){var h=o.transitions[r];if(h instanceof nt){var b=-1;t.ruleToStartState[h.target.ruleIndex].isPrecedenceRule&&0===h.precedence&&(b=h.target.ruleIndex),i=new _r(h.followState,b),t.ruleToStopState[h.target.ruleIndex].addTransition(i)}}for(n=0;n<t.states.length;n++){if((o=t.states[n])instanceof Je){if(null===o.endState)throw"IllegalState";if(null!==o.endState.startState)throw"IllegalState";o.endState.startState=o}if(o instanceof jn)for(r=0;r<o.transitions.length;r++)(u=o.transitions[r].target)instanceof Yn&&(u.loopBackState=o);else if(o instanceof Nn)for(r=0;r<o.transitions.length;r++)(u=o.transitions[r].target)instanceof Mn&&(u.loopBackState=o)}}},{key:"readDecisions",value:function(t){for(var e=this.readInt(),n=0;n<e;n++){var r=this.readInt(),o=t.states[r];t.decisionToState.push(o),o.decision=n}}},{key:"readLexerActions",value:function(t,e){if(0===t.grammarType){var n=this.readInt();t.lexerActions=Vo(n,null);for(var r=0;r<n;r++){var o=this.readInt(),i=this.readInt();e&&65535===i&&(i=-1);var u=this.readInt();e&&65535===u&&(u=-1),t.lexerActions[r]=this.lexerActionFactory(o,i,u)}}}},{key:"generateRuleBypassTransitions",value:function(t){var e,n=t.ruleToStartState.length;for(e=0;e<n;e++)t.ruleToTokenType[e]=t.maxTokenType+e+1;for(e=0;e<n;e++)this.generateRuleBypassTransition(t,e)}},{key:"generateRuleBypassTransition",value:function(t,e){var n,r,o=new rr;o.ruleIndex=e,t.addState(o);var i=new nn;i.ruleIndex=e,t.addState(i),o.endState=i,t.defineDecisionState(o),i.startState=o;var u=null,c=null;if(t.ruleToStartState[e].isPrecedenceRule){for(c=null,n=0;n<t.states.length;n++)if(r=t.states[n],this.stateIsEndStateFor(r,e)){c=r,u=r.loopBackState.transitions[0];break}if(null===u)throw"Couldn't identify final state of the precedence rule prefix section."}else c=t.ruleToStopState[e];for(n=0;n<t.states.length;n++){r=t.states[n];for(var a=0;a<r.transitions.length;a++){var l=r.transitions[a];l!==u&&l.target===c&&(l.target=i)}}for(var s=t.ruleToStartState[e],f=s.transitions.length;f>0;)o.addTransition(s.transitions[f-1]),s.transitions=s.transitions.slice(-1);t.ruleToStartState[e].addTransition(new _r(o)),i.addTransition(new _r(c));var p=new Be;t.addState(p),p.addTransition(new ar(i,t.ruleToTokenType[e])),o.addTransition(new _r(p))}},{key:"stateIsEndStateFor",value:function(t,e){if(t.ruleIndex!==e)return null;if(!(t instanceof Mn))return null;var n=t.transitions[t.transitions.length-1].target;return n instanceof ln&&n.epsilonOnlyTransitions&&n.transitions[0].target instanceof G?t:null}},{key:"markPrecedenceDecisions",value:function(t){for(var e=0;e<t.states.length;e++){var n=t.states[e];if(n instanceof Mn&&t.ruleToStartState[n.ruleIndex].isPrecedenceRule){var r=n.transitions[n.transitions.length-1].target;r instanceof ln&&r.epsilonOnlyTransitions&&r.transitions[0].target instanceof G&&(n.isPrecedenceDecision=!0)}}}},{key:"verifyATN",value:function(t){if(this.deserializationOptions.verifyATN)for(var e=0;e<t.states.length;e++){var n=t.states[e];if(null!==n)if(this.checkCondition(n.epsilonOnlyTransitions||n.transitions.length<=1),n instanceof Yn)this.checkCondition(null!==n.loopBackState);else if(n instanceof Mn)if(this.checkCondition(null!==n.loopBackState),this.checkCondition(2===n.transitions.length),n.transitions[0].target instanceof $n)this.checkCondition(n.transitions[1].target instanceof ln),this.checkCondition(!n.nonGreedy);else{if(!(n.transitions[0].target instanceof ln))throw"IllegalState";this.checkCondition(n.transitions[1].target instanceof $n),this.checkCondition(n.nonGreedy)}else n instanceof Nn?(this.checkCondition(1===n.transitions.length),this.checkCondition(n.transitions[0].target instanceof Mn)):n instanceof ln?this.checkCondition(null!==n.loopBackState):n instanceof bn?this.checkCondition(null!==n.stopState):n instanceof Je?this.checkCondition(null!==n.endState):n instanceof nn?this.checkCondition(null!==n.startState):n instanceof ze?this.checkCondition(n.transitions.length<=1||n.decision>=0):this.checkCondition(n.transitions.length<=1||n instanceof G)}}},{key:"checkCondition",value:function(t,e){if(!t)throw null==e&&(e="IllegalState"),e}},{key:"readInt",value:function(){return this.data[this.pos++]}},{key:"readInt32",value:function(){return this.readInt()|this.readInt()<<16}},{key:"edgeFactory",value:function(t,e,n,r,i,u,c,a){var l=t.states[r];switch(e){case $.EPSILON:return new _r(l);case $.RANGE:return new yr(l,0!==c?o.EOF:i,u);case $.RULE:return new nt(t.states[i],u,c,l);case $.PREDICATE:return new Nr(l,i,u,0!==c);case $.PRECEDENCE:return new Hr(l,i);case $.ATOM:return new ar(l,0!==c?o.EOF:i);case $.ACTION:return new mr(l,i,u,0!==c);case $.SET:return new ct(l,a[i]);case $.NOT_SET:return new yt(l,a[i]);case $.WILDCARD:return new mt(l);default:throw"The specified transition type: "+e+" is not valid."}}},{key:"stateFactory",value:function(t,e){if(null===this.stateFactories){var n=[];n[V.INVALID_TYPE]=null,n[V.BASIC]=function(){return new Be},n[V.RULE_START]=function(){return new bn},n[V.BLOCK_START]=function(){return new rr},n[V.PLUS_BLOCK_START]=function(){return new Yn},n[V.STAR_BLOCK_START]=function(){return new $n},n[V.TOKEN_START]=function(){return new On},n[V.RULE_STOP]=function(){return new G},n[V.BLOCK_END]=function(){return new nn},n[V.STAR_LOOP_BACK]=function(){return new Nn},n[V.STAR_LOOP_ENTRY]=function(){return new Mn},n[V.PLUS_LOOP_BACK]=function(){return new jn},n[V.LOOP_END]=function(){return new ln},this.stateFactories=n}if(t>this.stateFactories.length||null===this.stateFactories[t])throw"The specified state type "+t+" is not valid.";var r=this.stateFactories[t]();if(null!==r)return r.ruleIndex=e,r}},{key:"lexerActionFactory",value:function(t,e,n){if(null===this.actionFactories){var r=[];r[Wr.CHANNEL]=function(t,e){return new co(t)},r[Wr.CUSTOM]=function(t,e){return new po(t,e)},r[Wr.MODE]=function(t,e){return new Bo(t)},r[Wr.MORE]=function(t,e){return mo.INSTANCE},r[Wr.POP_MODE]=function(t,e){return No.INSTANCE},r[Wr.PUSH_MODE]=function(t,e){return new ko(t)},r[Wr.SKIP]=function(t,e){return no.INSTANCE},r[Wr.TYPE]=function(t,e){return new _o(t)},this.actionFactories=r}if(t>this.actionFactories.length||null===this.actionFactories[t])throw"The specified lexer action type "+t+" is not valid.";return this.actionFactories[t](e,n)}}],n&&Uo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Ho(t){return Ho="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ho(t)}function zo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ho(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ho(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ho(o)?o:String(o)),r)}var o}var Yo=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}var e,n;return e=t,(n=[{key:"syntaxError",value:function(t,e,n,r,o,i){}},{key:"reportAmbiguity",value:function(t,e,n,r,o,i,u){}},{key:"reportAttemptingFullContext",value:function(t,e,n,r,o,i){}},{key:"reportContextSensitivity",value:function(t,e,n,r,o,i){}}])&&zo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Ko(t){return Ko="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ko(t)}function Go(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ko(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ko(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ko(o)?o:String(o)),r)}var o}function Wo(t,e){return Wo=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Wo(t,e)}function Xo(t){return Xo=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Xo(t)}var Jo=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Wo(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Xo(r);if(o){var n=Xo(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ko(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this)}return e=u,(n=[{key:"syntaxError",value:function(t,e,n,r,o,i){console.error("line "+n+":"+r+" "+o)}}])&&Go(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Yo);function $o(t){return $o="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},$o(t)}function Zo(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==$o(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==$o(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===$o(o)?o:String(o)),r)}var o}function Qo(t,e){return Qo=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Qo(t,e)}function ti(t,e){if(e&&("object"===$o(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return ei(t)}function ei(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function ni(t){return ni=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ni(t)}Jo.INSTANCE=new Jo;var ri=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Qo(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ni(r);if(o){var n=ni(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return ti(this,t)});function u(t){var e;if(function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),e=i.call(this),null===t)throw"delegates";return e.delegates=t,ti(e,ei(e))}return e=u,n=[{key:"syntaxError",value:function(t,e,n,r,o,i){this.delegates.map((function(u){return u.syntaxError(t,e,n,r,o,i)}))}},{key:"reportAmbiguity",value:function(t,e,n,r,o,i,u){this.delegates.map((function(c){return c.reportAmbiguity(t,e,n,r,o,i,u)}))}},{key:"reportAttemptingFullContext",value:function(t,e,n,r,o,i){this.delegates.map((function(u){return u.reportAttemptingFullContext(t,e,n,r,o,i)}))}},{key:"reportContextSensitivity",value:function(t,e,n,r,o,i){this.delegates.map((function(u){return u.reportContextSensitivity(t,e,n,r,o,i)}))}}],n&&Zo(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Yo);function oi(t){return oi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},oi(t)}function ii(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==oi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==oi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===oi(o)?o:String(o)),r)}var o}var ui=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this._listeners=[Jo.INSTANCE],this._interp=null,this._stateNumber=-1}var e,n;return e=t,(n=[{key:"checkVersion",value:function(t){var e="4.12.0";e!==t&&console.log("ANTLR runtime and generated code versions disagree: "+e+"!="+t)}},{key:"addErrorListener",value:function(t){this._listeners.push(t)}},{key:"removeErrorListeners",value:function(){this._listeners=[]}},{key:"getLiteralNames",value:function(){return Object.getPrototypeOf(this).constructor.literalNames||[]}},{key:"getSymbolicNames",value:function(){return Object.getPrototypeOf(this).constructor.symbolicNames||[]}},{key:"getTokenNames",value:function(){if(!this.tokenNames){var t=this.getLiteralNames(),e=this.getSymbolicNames(),n=t.length>e.length?t.length:e.length;this.tokenNames=[];for(var r=0;r<n;r++)this.tokenNames[r]=t[r]||e[r]||"<INVALID"}return this.tokenNames}},{key:"getTokenTypeMap",value:function(){var t=this.getTokenNames();if(null===t)throw"The current recognizer does not provide a list of token names.";var e=this.tokenTypeMapCache[t];return void 0===e&&((e=t.reduce((function(t,e,n){t[e]=n}))).EOF=o.EOF,this.tokenTypeMapCache[t]=e),e}},{key:"getRuleIndexMap",value:function(){var t=this.ruleNames;if(null===t)throw"The current recognizer does not provide a list of rule names.";var e=this.ruleIndexMapCache[t];return void 0===e&&(e=t.reduce((function(t,e,n){t[e]=n})),this.ruleIndexMapCache[t]=e),e}},{key:"getTokenType",value:function(t){var e=this.getTokenTypeMap()[t];return void 0!==e?e:o.INVALID_TYPE}},{key:"getErrorHeader",value:function(t){return"line "+t.getOffendingToken().line+":"+t.getOffendingToken().column}},{key:"getTokenErrorDisplay",value:function(t){if(null===t)return"<no token>";var e=t.text;return null===e&&(e=t.type===o.EOF?"<EOF>":"<"+t.type+">"),"'"+(e=e.replace("\n","\\n").replace("\r","\\r").replace("\t","\\t"))+"'"}},{key:"getErrorListenerDispatch",value:function(){return new ri(this._listeners)}},{key:"sempred",value:function(t,e,n){return!0}},{key:"precpred",value:function(t,e){return!0}},{key:"atn",get:function(){return this._interp.atn}},{key:"state",get:function(){return this._stateNumber},set:function(t){this._stateNumber=t}}])&&ii(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function ci(t){return ci="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ci(t)}function ai(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ci(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ci(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ci(o)?o:String(o)),r)}var o}function li(t,e){return li=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},li(t,e)}function si(t){return si=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},si(t)}ui.tokenTypeMapCache={},ui.ruleIndexMapCache={};var fi=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&li(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=si(r);if(i){var n=si(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ci(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t,e,n,r,i){var a;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(a=u.call(this)).source=void 0!==t?t:c.EMPTY_SOURCE,a.type=void 0!==e?e:null,a.channel=void 0!==n?n:o.DEFAULT_CHANNEL,a.start=void 0!==r?r:-1,a.stop=void 0!==i?i:-1,a.tokenIndex=-1,null!==a.source[0]?(a.line=t[0].line,a.column=t[0].column):a.column=-1,a}return e=c,(n=[{key:"clone",value:function(){var t=new c(this.source,this.type,this.channel,this.start,this.stop);return t.tokenIndex=this.tokenIndex,t.line=this.line,t.column=this.column,t.text=this.text,t}},{key:"cloneWithType",value:function(t){var e=new c(this.source,t,this.channel,this.start,this.stop);return e.tokenIndex=this.tokenIndex,e.line=this.line,e.column=this.column,t===o.EOF&&(e.text=""),e}},{key:"toString",value:function(){var t=this.text;return t=null!==t?t.replace(/\n/g,"\\n").replace(/\r/g,"\\r").replace(/\t/g,"\\t"):"<no text>","[@"+this.tokenIndex+","+this.start+":"+this.stop+"='"+t+"',<"+this.type+">"+(this.channel>0?",channel="+this.channel:"")+","+this.line+":"+this.column+"]"}},{key:"text",get:function(){if(null!==this._text)return this._text;var t=this.getInputStream();if(null===t)return null;var e=t.size;return this.start<e&&this.stop<e?t.getText(this.start,this.stop):"<EOF>"},set:function(t){this._text=t}}])&&ai(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(o);function pi(t){return pi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},pi(t)}function yi(t,e){return yi=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},yi(t,e)}function hi(t){return hi=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},hi(t)}function bi(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==pi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==pi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===pi(o)?o:String(o)),r)}var o}function vi(t,e,n){return e&&bi(t.prototype,e),n&&bi(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}function di(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}fi.EMPTY_SOURCE=[null,null];var mi=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&yi(t,e)}(o,t);var e,n,r=(e=o,n=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,r=hi(e);if(n){var o=hi(this).constructor;t=Reflect.construct(r,arguments,o)}else t=r.apply(this,arguments);return function(t,e){if(e&&("object"===pi(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function o(t){var e;return di(this,o),(e=r.call(this)).copyText=void 0!==t&&t,e}return vi(o,[{key:"create",value:function(t,e,n,r,o,i,u,c){var a=new fi(t,e,r,o,i);return a.line=u,a.column=c,null!==n?a.text=n:this.copyText&&null!==t[1]&&(a.text=t[1].getText(o,i)),a}},{key:"createThin",value:function(t,e){var n=new fi(null,t);return n.text=e,n}}]),o}(vi((function t(){di(this,t)})));function gi(t){return gi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},gi(t)}function Si(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==gi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==gi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===gi(o)?o:String(o)),r)}var o}function Oi(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function wi(t){var e="function"==typeof Map?new Map:void 0;return wi=function(t){if(null===t||(n=t,-1===Function.toString.call(n).indexOf("[native code]")))return t;var n;if("function"!=typeof t)throw new TypeError("Super expression must either be null or a function");if(void 0!==e){if(e.has(t))return e.get(t);e.set(t,r)}function r(){return _i(t,arguments,Ei(this).constructor)}return r.prototype=Object.create(t.prototype,{constructor:{value:r,enumerable:!1,writable:!0,configurable:!0}}),Ti(r,t)},wi(t)}function _i(t,e,n){return _i=Pi()?Reflect.construct.bind():function(t,e,n){var r=[null];r.push.apply(r,e);var o=new(Function.bind.apply(t,r));return n&&Ti(o,n.prototype),o},_i.apply(null,arguments)}function Pi(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}function Ti(t,e){return Ti=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ti(t,e)}function Ei(t){return Ei=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ei(t)}mi.DEFAULT=new mi;var ji=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ti(t,e)}(u,t);var e,n,r,o,i=(r=u,o=Pi(),function(){var t,e=Ei(r);if(o){var n=Ei(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===gi(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Oi(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),e=i.call(this,t.message),Error.captureStackTrace&&Error.captureStackTrace(Oi(e),u),e.message=t.message,e.recognizer=t.recognizer,e.input=t.input,e.ctx=t.ctx,e.offendingToken=null,e.offendingState=-1,null!==e.recognizer&&(e.offendingState=e.recognizer.state),e}return e=u,(n=[{key:"getExpectedTokens",value:function(){return null!==this.recognizer?this.recognizer.atn.getExpectedTokens(this.offendingState,this.ctx):null}},{key:"toString",value:function(){return this.message}}])&&Si(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(wi(Error));function ki(t){return ki="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ki(t)}function xi(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ki(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ki(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ki(o)?o:String(o)),r)}var o}function Ri(t,e){return Ri=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ri(t,e)}function Ci(t){return Ci=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ci(t)}var Ai=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ri(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ci(r);if(o){var n=Ci(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ki(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n,r){var o;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(o=i.call(this,{message:"",recognizer:t,input:e,ctx:null})).startIndex=n,o.deadEndConfigs=r,o}return e=u,(n=[{key:"toString",value:function(){var t="";return this.startIndex>=0&&this.startIndex<this.input.size&&(t=this.input.getText(new L(this.startIndex,this.startIndex))),"LexerNoViableAltException"+t}}])&&xi(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(ji);function Ni(t){return Ni="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ni(t)}function Ii(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ni(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ni(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ni(o)?o:String(o)),r)}var o}function Li(t,e){return Li=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Li(t,e)}function Di(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Fi(t){return Fi=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Fi(t)}var Bi=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Li(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Fi(r);if(i){var n=Fi(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ni(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Di(t)}(this,t)});function c(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(e=u.call(this))._input=t,e._factory=mi.DEFAULT,e._tokenFactorySourcePair=[Di(e),t],e._interp=null,e._token=null,e._tokenStartCharIndex=-1,e._tokenStartLine=-1,e._tokenStartColumn=-1,e._hitEOF=!1,e._channel=o.DEFAULT_CHANNEL,e._type=o.INVALID_TYPE,e._modeStack=[],e._mode=c.DEFAULT_MODE,e._text=null,e}return e=c,(n=[{key:"reset",value:function(){null!==this._input&&this._input.seek(0),this._token=null,this._type=o.INVALID_TYPE,this._channel=o.DEFAULT_CHANNEL,this._tokenStartCharIndex=-1,this._tokenStartColumn=-1,this._tokenStartLine=-1,this._text=null,this._hitEOF=!1,this._mode=c.DEFAULT_MODE,this._modeStack=[],this._interp.reset()}},{key:"nextToken",value:function(){if(null===this._input)throw"nextToken requires a non-null input stream.";var t=this._input.mark();try{for(;;){if(this._hitEOF)return this.emitEOF(),this._token;this._token=null,this._channel=o.DEFAULT_CHANNEL,this._tokenStartCharIndex=this._input.index,this._tokenStartColumn=this._interp.column,this._tokenStartLine=this._interp.line,this._text=null;for(var e=!1;;){this._type=o.INVALID_TYPE;var n=c.SKIP;try{n=this._interp.match(this._input,this._mode)}catch(t){if(!(t instanceof ji))throw console.log(t.stack),t;this.notifyListeners(t),this.recover(t)}if(this._input.LA(1)===o.EOF&&(this._hitEOF=!0),this._type===o.INVALID_TYPE&&(this._type=n),this._type===c.SKIP){e=!0;break}if(this._type!==c.MORE)break}if(!e)return null===this._token&&this.emit(),this._token}}finally{this._input.release(t)}}},{key:"skip",value:function(){this._type=c.SKIP}},{key:"more",value:function(){this._type=c.MORE}},{key:"mode",value:function(t){this._mode=t}},{key:"pushMode",value:function(t){this._interp.debug&&console.log("pushMode "+t),this._modeStack.push(this._mode),this.mode(t)}},{key:"popMode",value:function(){if(0===this._modeStack.length)throw"Empty Stack";return this._interp.debug&&console.log("popMode back to "+this._modeStack.slice(0,-1)),this.mode(this._modeStack.pop()),this._mode}},{key:"emitToken",value:function(t){this._token=t}},{key:"emit",value:function(){var t=this._factory.create(this._tokenFactorySourcePair,this._type,this._text,this._channel,this._tokenStartCharIndex,this.getCharIndex()-1,this._tokenStartLine,this._tokenStartColumn);return this.emitToken(t),t}},{key:"emitEOF",value:function(){var t=this.column,e=this.line,n=this._factory.create(this._tokenFactorySourcePair,o.EOF,null,o.DEFAULT_CHANNEL,this._input.index,this._input.index-1,e,t);return this.emitToken(n),n}},{key:"getCharIndex",value:function(){return this._input.index}},{key:"getAllTokens",value:function(){for(var t=[],e=this.nextToken();e.type!==o.EOF;)t.push(e),e=this.nextToken();return t}},{key:"notifyListeners",value:function(t){var e=this._tokenStartCharIndex,n=this._input.index,r=this._input.getText(e,n),o="token recognition error at: '"+this.getErrorDisplay(r)+"'";this.getErrorListenerDispatch().syntaxError(this,null,this._tokenStartLine,this._tokenStartColumn,o,t)}},{key:"getErrorDisplay",value:function(t){for(var e=[],n=0;n<t.length;n++)e.push(t[n]);return e.join("")}},{key:"getErrorDisplayForChar",value:function(t){return t.charCodeAt(0)===o.EOF?"<EOF>":"\n"===t?"\\n":"\t"===t?"\\t":"\r"===t?"\\r":t}},{key:"getCharErrorDisplay",value:function(t){return"'"+this.getErrorDisplayForChar(t)+"'"}},{key:"recover",value:function(t){this._input.LA(1)!==o.EOF&&(t instanceof Ai?this._interp.consume(this._input):this._input.consume())}},{key:"inputStream",get:function(){return this._input},set:function(t){this._input=null,this._tokenFactorySourcePair=[this,this._input],this.reset(),this._input=t,this._tokenFactorySourcePair=[this,this._input]}},{key:"sourceName",get:function(){return this._input.sourceName}},{key:"type",get:function(){return this._type},set:function(t){this._type=t}},{key:"line",get:function(){return this._interp.line},set:function(t){this._interp.line=t}},{key:"column",get:function(){return this._interp.column},set:function(t){this._interp.column=t}},{key:"text",get:function(){return null!==this._text?this._text:this._interp.getText(this._input)},set:function(t){this._text=t}}])&&Ii(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(ui);function Mi(t){return Mi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Mi(t)}function Ui(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Mi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Mi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Mi(o)?o:String(o)),r)}var o}function Vi(t){return t.hashCodeForConfigSet()}function qi(t,e){return t===e||null!==t&&null!==e&&t.equalsForConfigSet(e)}Bi.DEFAULT_MODE=0,Bi.MORE=-2,Bi.SKIP=-3,Bi.DEFAULT_TOKEN_CHANNEL=o.DEFAULT_CHANNEL,Bi.HIDDEN=o.HIDDEN_CHANNEL,Bi.MIN_CHAR_VALUE=0,Bi.MAX_CHAR_VALUE=1114111;var Hi=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.configLookup=new v(Vi,qi),this.fullCtx=void 0===e||e,this.readOnly=!1,this.configs=[],this.uniqueAlt=0,this.conflictingAlts=null,this.hasSemanticContext=!1,this.dipsIntoOuterContext=!1,this.cachedHashCode=-1}var e,n;return e=t,(n=[{key:"add",value:function(t,e){if(void 0===e&&(e=null),this.readOnly)throw"This set is readonly";t.semanticContext!==T.NONE&&(this.hasSemanticContext=!0),t.reachesIntoOuterContext>0&&(this.dipsIntoOuterContext=!0);var n=this.configLookup.add(t);if(n===t)return this.cachedHashCode=-1,this.configs.push(t),!0;var r=!this.fullCtx,o=Te(n.context,t.context,r,e);return n.reachesIntoOuterContext=Math.max(n.reachesIntoOuterContext,t.reachesIntoOuterContext),t.precedenceFilterSuppressed&&(n.precedenceFilterSuppressed=!0),n.context=o,!0}},{key:"getStates",value:function(){for(var t=new v,e=0;e<this.configs.length;e++)t.add(this.configs[e].state);return t}},{key:"getPredicates",value:function(){for(var t=[],e=0;e<this.configs.length;e++){var n=this.configs[e].semanticContext;n!==T.NONE&&t.push(n.semanticContext)}return t}},{key:"optimizeConfigs",value:function(t){if(this.readOnly)throw"This set is readonly";if(0!==this.configLookup.length)for(var e=0;e<this.configs.length;e++){var n=this.configs[e];n.context=t.getCachedContext(n.context)}}},{key:"addAll",value:function(t){for(var e=0;e<t.length;e++)this.add(t[e]);return!1}},{key:"equals",value:function(e){return this===e||e instanceof t&&i(this.configs,e.configs)&&this.fullCtx===e.fullCtx&&this.uniqueAlt===e.uniqueAlt&&this.conflictingAlts===e.conflictingAlts&&this.hasSemanticContext===e.hasSemanticContext&&this.dipsIntoOuterContext===e.dipsIntoOuterContext}},{key:"hashCode",value:function(){var t=new a;return t.update(this.configs),t.finish()}},{key:"updateHashCode",value:function(t){this.readOnly?(-1===this.cachedHashCode&&(this.cachedHashCode=this.hashCode()),t.update(this.cachedHashCode)):t.update(this.hashCode())}},{key:"isEmpty",value:function(){return 0===this.configs.length}},{key:"contains",value:function(t){if(null===this.configLookup)throw"This method is not implemented for readonly sets.";return this.configLookup.contains(t)}},{key:"containsFast",value:function(t){if(null===this.configLookup)throw"This method is not implemented for readonly sets.";return this.configLookup.containsFast(t)}},{key:"clear",value:function(){if(this.readOnly)throw"This set is readonly";this.configs=[],this.cachedHashCode=-1,this.configLookup=new v}},{key:"setReadonly",value:function(t){this.readOnly=t,t&&(this.configLookup=null)}},{key:"toString",value:function(){return p(this.configs)+(this.hasSemanticContext?",hasSemanticContext="+this.hasSemanticContext:"")+(this.uniqueAlt!==Ie.INVALID_ALT_NUMBER?",uniqueAlt="+this.uniqueAlt:"")+(null!==this.conflictingAlts?",conflictingAlts="+this.conflictingAlts:"")+(this.dipsIntoOuterContext?",dipsIntoOuterContext":"")}},{key:"items",get:function(){return this.configs}},{key:"length",get:function(){return this.configs.length}}])&&Ui(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function zi(t){return zi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},zi(t)}function Yi(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==zi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==zi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===zi(o)?o:String(o)),r)}var o}var Ki=function(){function t(e,n){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),null===e&&(e=-1),null===n&&(n=new Hi),this.stateNumber=e,this.configs=n,this.edges=null,this.isAcceptState=!1,this.prediction=0,this.lexerActionExecutor=null,this.requiresFullContext=!1,this.predicates=null,this}var e,n;return e=t,(n=[{key:"getAltSet",value:function(){var t=new v;if(null!==this.configs)for(var e=0;e<this.configs.length;e++){var n=this.configs[e];t.add(n.alt)}return 0===t.length?null:t}},{key:"equals",value:function(e){return this===e||e instanceof t&&this.configs.equals(e.configs)}},{key:"toString",value:function(){var t=this.stateNumber+":"+this.configs;return this.isAcceptState&&(t+="=>",null!==this.predicates?t+=this.predicates:t+=this.prediction),t}},{key:"hashCode",value:function(){var t=new a;return t.update(this.configs),t.finish()}}])&&Yi(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Gi(t){return Gi="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Gi(t)}function Wi(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Gi(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Gi(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Gi(o)?o:String(o)),r)}var o}var Xi=function(){function t(e,n){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.atn=e,this.sharedContextCache=n,this}var e,n;return e=t,n=[{key:"getCachedContext",value:function(t){if(null===this.sharedContextCache)return t;var e=new we;return Pe(t,this.sharedContextCache,e)}}],n&&Wi(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Ji(t){return Ji="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ji(t)}function $i(t,e){return $i=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},$i(t,e)}function Zi(t){return Zi=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Zi(t)}Xi.ERROR=new Ki(2147483647,new Hi);var Qi=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&$i(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Zi(n);if(r){var o=Zi(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ji(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(t=o.call(this)).configLookup=new v,t}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Hi);function tu(t){return tu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},tu(t)}function eu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==tu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==tu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===tu(o)?o:String(o)),r)}var o}function nu(){return nu="undefined"!=typeof Reflect&&Reflect.get?Reflect.get.bind():function(t,e,n){var r=function(t,e){for(;!Object.prototype.hasOwnProperty.call(t,e)&&null!==(t=uu(t)););return t}(t,e);if(r){var o=Object.getOwnPropertyDescriptor(r,e);return o.get?o.get.call(arguments.length<3?t:n):o.value}},nu.apply(this,arguments)}function ru(t,e){return ru=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ru(t,e)}function ou(t,e){if(e&&("object"===tu(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return iu(t)}function iu(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function uu(t){return uu=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},uu(t)}var cu=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ru(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=uu(r);if(o){var n=uu(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return ou(this,t)});function u(t,e){var n;!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),n=i.call(this,t,e);var r=t.lexerActionExecutor||null;return n.lexerActionExecutor=r||(null!==e?e.lexerActionExecutor:null),n.passedThroughNonGreedyDecision=null!==e&&n.checkNonGreedyDecision(e,n.state),n.hashCodeForConfigSet=u.prototype.hashCode,n.equalsForConfigSet=u.prototype.equals,ou(n,iu(n))}return e=u,(n=[{key:"updateHashCode",value:function(t){t.update(this.state.stateNumber,this.alt,this.context,this.semanticContext,this.passedThroughNonGreedyDecision,this.lexerActionExecutor)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.passedThroughNonGreedyDecision===t.passedThroughNonGreedyDecision&&(this.lexerActionExecutor?this.lexerActionExecutor.equals(t.lexerActionExecutor):!t.lexerActionExecutor)&&nu(uu(u.prototype),"equals",this).call(this,t)}},{key:"checkNonGreedyDecision",value:function(t,e){return t.passedThroughNonGreedyDecision||e instanceof ze&&e.nonGreedy}}])&&eu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(A);function au(t){return au="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},au(t)}function lu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==au(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==au(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===au(o)?o:String(o)),r)}var o}function su(t,e){return su=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},su(t,e)}function fu(t){return fu=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},fu(t)}var pu=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&su(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=fu(r);if(o){var n=fu(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===au(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,e.actionType)).offset=t,n.action=e,n.isPositionDependent=!0,n}return e=u,(n=[{key:"execute",value:function(t){this.action.execute(t)}},{key:"updateHashCode",value:function(t){t.update(this.actionType,this.offset,this.action)}},{key:"equals",value:function(t){return this===t||t instanceof u&&this.offset===t.offset&&this.action===t.action}}])&&lu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($r);function yu(t){return yu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},yu(t)}function hu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==yu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==yu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===yu(o)?o:String(o)),r)}var o}var bu=function(){function t(e){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.lexerActions=null===e?[]:e,this.cachedHashCode=a.hashStuff(e),this}var e,n,r;return e=t,r=[{key:"append",value:function(e,n){return new t(null===e?[n]:e.lexerActions.concat([n]))}}],(n=[{key:"fixOffsetBeforeMatch",value:function(e){for(var n=null,r=0;r<this.lexerActions.length;r++)!this.lexerActions[r].isPositionDependent||this.lexerActions[r]instanceof pu||(null===n&&(n=this.lexerActions.concat([])),n[r]=new pu(e,this.lexerActions[r]));return null===n?this:new t(n)}},{key:"execute",value:function(t,e,n){var r=!1,o=e.index;try{for(var i=0;i<this.lexerActions.length;i++){var u=this.lexerActions[i];if(u instanceof pu){var c=u.offset;e.seek(n+c),u=u.action,r=n+c!==o}else u.isPositionDependent&&(e.seek(o),r=!1);u.execute(t)}}finally{r&&e.seek(o)}}},{key:"hashCode",value:function(){return this.cachedHashCode}},{key:"updateHashCode",value:function(t){t.update(this.cachedHashCode)}},{key:"equals",value:function(e){if(this===e)return!0;if(e instanceof t){if(this.cachedHashCode!=e.cachedHashCode)return!1;if(this.lexerActions.length!=e.lexerActions.length)return!1;for(var n=this.lexerActions.length,r=0;r<n;++r)if(!this.lexerActions[r].equals(e.lexerActions[r]))return!1;return!0}return!1}}])&&hu(e.prototype,n),r&&hu(e,r),Object.defineProperty(e,"prototype",{writable:!1}),t}();function vu(t,e){return vu=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},vu(t,e)}function du(t){return du=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},du(t)}function mu(t){return mu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},mu(t)}function gu(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}function Su(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==mu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==mu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===mu(o)?o:String(o)),r)}var o}function Ou(t,e,n){return e&&Su(t.prototype,e),n&&Su(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}function wu(t){t.index=-1,t.line=0,t.column=-1,t.dfaState=null}var _u=function(){function t(){gu(this,t),wu(this)}return Ou(t,[{key:"reset",value:function(){wu(this)}}]),t}(),Pu=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&vu(t,e)}(i,t);var e,n,r=(e=i,n=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,r=du(e);if(n){var o=du(this).constructor;t=Reflect.construct(r,arguments,o)}else t=r.apply(this,arguments);return function(t,e){if(e&&("object"===mu(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t,e,n,o){var u;return gu(this,i),(u=r.call(this,e,o)).decisionToDFA=n,u.recog=t,u.startIndex=-1,u.line=1,u.column=0,u.mode=Bi.DEFAULT_MODE,u.prevAccept=new _u,u}return Ou(i,[{key:"copyState",value:function(t){this.column=t.column,this.line=t.line,this.mode=t.mode,this.startIndex=t.startIndex}},{key:"match",value:function(t,e){this.mode=e;var n=t.mark();try{this.startIndex=t.index,this.prevAccept.reset();var r=this.decisionToDFA[e];return null===r.s0?this.matchATN(t):this.execATN(t,r.s0)}finally{t.release(n)}}},{key:"reset",value:function(){this.prevAccept.reset(),this.startIndex=-1,this.line=1,this.column=0,this.mode=Bi.DEFAULT_MODE}},{key:"matchATN",value:function(t){var e=this.atn.modeToStartState[this.mode];i.debug&&console.log("matchATN mode "+this.mode+" start: "+e);var n=this.mode,r=this.computeStartState(t,e),o=r.hasSemanticContext;r.hasSemanticContext=!1;var u=this.addDFAState(r);o||(this.decisionToDFA[this.mode].s0=u);var c=this.execATN(t,u);return i.debug&&console.log("DFA after matchATN: "+this.decisionToDFA[n].toLexerString()),c}},{key:"execATN",value:function(t,e){i.debug&&console.log("start state closure="+e.configs),e.isAcceptState&&this.captureSimState(this.prevAccept,t,e);for(var n=t.LA(1),r=e;;){i.debug&&console.log("execATN loop starting closure: "+r.configs);var u=this.getExistingTargetState(r,n);if(null===u&&(u=this.computeTargetState(t,r,n)),u===Xi.ERROR)break;if(n!==o.EOF&&this.consume(t),u.isAcceptState&&(this.captureSimState(this.prevAccept,t,u),n===o.EOF))break;n=t.LA(1),r=u}return this.failOrAccept(this.prevAccept,t,r.configs,n)}},{key:"getExistingTargetState",value:function(t,e){if(null===t.edges||e<i.MIN_DFA_EDGE||e>i.MAX_DFA_EDGE)return null;var n=t.edges[e-i.MIN_DFA_EDGE];return void 0===n&&(n=null),i.debug&&null!==n&&console.log("reuse state "+t.stateNumber+" edge to "+n.stateNumber),n}},{key:"computeTargetState",value:function(t,e,n){var r=new Qi;return this.getReachableConfigSet(t,e.configs,r,n),0===r.items.length?(r.hasSemanticContext||this.addDFAEdge(e,n,Xi.ERROR),Xi.ERROR):this.addDFAEdge(e,n,null,r)}},{key:"failOrAccept",value:function(t,e,n,r){if(null!==this.prevAccept.dfaState){var i=t.dfaState.lexerActionExecutor;return this.accept(e,i,this.startIndex,t.index,t.line,t.column),t.dfaState.prediction}if(r===o.EOF&&e.index===this.startIndex)return o.EOF;throw new Ai(this.recog,e,this.startIndex,n)}},{key:"getReachableConfigSet",value:function(t,e,n,r){for(var u=Ie.INVALID_ALT_NUMBER,c=0;c<e.items.length;c++){var a=e.items[c],l=a.alt===u;if(!l||!a.passedThroughNonGreedyDecision){i.debug&&console.log("testing %s at %s\n",this.getTokenName(r),a.toString(this.recog,!0));for(var s=0;s<a.state.transitions.length;s++){var f=a.state.transitions[s],p=this.getReachableTarget(f,r);if(null!==p){var y=a.lexerActionExecutor;null!==y&&(y=y.fixOffsetBeforeMatch(t.index-this.startIndex));var h=r===o.EOF,b=new cu({state:p,lexerActionExecutor:y},a);this.closure(t,b,n,l,!0,h)&&(u=a.alt)}}}}}},{key:"accept",value:function(t,e,n,r,o,u){i.debug&&console.log("ACTION %s\n",e),t.seek(r),this.line=o,this.column=u,null!==e&&null!==this.recog&&e.execute(this.recog,t,n)}},{key:"getReachableTarget",value:function(t,e){return t.matches(e,0,Bi.MAX_CHAR_VALUE)?t.target:null}},{key:"computeStartState",value:function(t,e){for(var n=ee.EMPTY,r=new Qi,o=0;o<e.transitions.length;o++){var i=e.transitions[o].target,u=new cu({state:i,alt:o+1,context:n},null);this.closure(t,u,r,!1,!1,!1)}return r}},{key:"closure",value:function(t,e,n,r,o,u){var c=null;if(i.debug&&console.log("closure("+e.toString(this.recog,!0)+")"),e.state instanceof G){if(i.debug&&(null!==this.recog?console.log("closure at %s rule stop %s\n",this.recog.ruleNames[e.state.ruleIndex],e):console.log("closure at rule stop %s\n",e)),null===e.context||e.context.hasEmptyPath()){if(null===e.context||e.context.isEmpty())return n.add(e),!0;n.add(new cu({state:e.state,context:ee.EMPTY},e)),r=!0}if(null!==e.context&&!e.context.isEmpty())for(var a=0;a<e.context.length;a++)if(e.context.getReturnState(a)!==ee.EMPTY_RETURN_STATE){var l=e.context.getParent(a),s=this.atn.states[e.context.getReturnState(a)];c=new cu({state:s,context:l},e),r=this.closure(t,c,n,r,o,u)}return r}e.state.epsilonOnlyTransitions||r&&e.passedThroughNonGreedyDecision||n.add(e);for(var f=0;f<e.state.transitions.length;f++){var p=e.state.transitions[f];null!==(c=this.getEpsilonTarget(t,e,p,n,o,u))&&(r=this.closure(t,c,n,r,o,u))}return r}},{key:"getEpsilonTarget",value:function(t,e,n,r,u,c){var a=null;if(n.serializationType===$.RULE){var l=ye.create(e.context,n.followState.stateNumber);a=new cu({state:n.target,context:l},e)}else{if(n.serializationType===$.PRECEDENCE)throw"Precedence predicates are not supported in lexers.";if(n.serializationType===$.PREDICATE)i.debug&&console.log("EVAL rule "+n.ruleIndex+":"+n.predIndex),r.hasSemanticContext=!0,this.evaluatePredicate(t,n.ruleIndex,n.predIndex,u)&&(a=new cu({state:n.target},e));else if(n.serializationType===$.ACTION)if(null===e.context||e.context.hasEmptyPath()){var s=bu.append(e.lexerActionExecutor,this.atn.lexerActions[n.actionIndex]);a=new cu({state:n.target,lexerActionExecutor:s},e)}else a=new cu({state:n.target},e);else n.serializationType===$.EPSILON?a=new cu({state:n.target},e):n.serializationType!==$.ATOM&&n.serializationType!==$.RANGE&&n.serializationType!==$.SET||c&&n.matches(o.EOF,0,Bi.MAX_CHAR_VALUE)&&(a=new cu({state:n.target},e))}return a}},{key:"evaluatePredicate",value:function(t,e,n,r){if(null===this.recog)return!0;if(!r)return this.recog.sempred(null,e,n);var o=this.column,i=this.line,u=t.index,c=t.mark();try{return this.consume(t),this.recog.sempred(null,e,n)}finally{this.column=o,this.line=i,t.seek(u),t.release(c)}}},{key:"captureSimState",value:function(t,e,n){t.index=e.index,t.line=this.line,t.column=this.column,t.dfaState=n}},{key:"addDFAEdge",value:function(t,e,n,r){if(void 0===n&&(n=null),void 0===r&&(r=null),null===n&&null!==r){var o=r.hasSemanticContext;if(r.hasSemanticContext=!1,n=this.addDFAState(r),o)return n}return e<i.MIN_DFA_EDGE||e>i.MAX_DFA_EDGE||(i.debug&&console.log("EDGE "+t+" -> "+n+" upon "+e),null===t.edges&&(t.edges=[]),t.edges[e-i.MIN_DFA_EDGE]=n),n}},{key:"addDFAState",value:function(t){for(var e=new Ki(null,t),n=null,r=0;r<t.items.length;r++){var o=t.items[r];if(o.state instanceof G){n=o;break}}null!==n&&(e.isAcceptState=!0,e.lexerActionExecutor=n.lexerActionExecutor,e.prediction=this.atn.ruleToTokenType[n.state.ruleIndex]);var i=this.decisionToDFA[this.mode],u=i.states.get(e);if(null!==u)return u;var c=e;return c.stateNumber=i.states.length,t.setReadonly(!0),c.configs=t,i.states.add(c),c}},{key:"getDFA",value:function(t){return this.decisionToDFA[t]}},{key:"getText",value:function(t){return t.getText(this.startIndex,t.index-1)}},{key:"consume",value:function(t){t.LA(1)==="\n".charCodeAt(0)?(this.line+=1,this.column=0):this.column+=1,t.consume()}},{key:"getTokenName",value:function(t){return-1===t?"EOF":"'"+String.fromCharCode(t)+"'"}}]),i}(Xi);function Tu(t){return Tu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Tu(t)}function Eu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Tu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Tu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Tu(o)?o:String(o)),r)}var o}Pu.debug=!1,Pu.dfa_debug=!1,Pu.MIN_DFA_EDGE=0,Pu.MAX_DFA_EDGE=127;var ju=function(){function t(e,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.alt=n,this.pred=e}var e,n;return e=t,(n=[{key:"toString",value:function(){return"("+this.pred+", "+this.alt+")"}}])&&Eu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function ku(t){return ku="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ku(t)}function xu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ku(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ku(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ku(o)?o:String(o)),r)}var o}var Ru=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.data={}}var e,n;return e=t,(n=[{key:"get",value:function(t){return this.data["k-"+t]||null}},{key:"set",value:function(t,e){this.data["k-"+t]=e}},{key:"values",value:function(){var t=this;return Object.keys(this.data).filter((function(t){return t.startsWith("k-")})).map((function(e){return t.data[e]}),this)}}])&&xu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}(),Cu={SLL:0,LL:1,LL_EXACT_AMBIG_DETECTION:2,hasSLLConflictTerminatingPrediction:function(t,e){if(Cu.allConfigsInRuleStopStates(e))return!0;if(t===Cu.SLL&&e.hasSemanticContext){for(var n=new Hi,r=0;r<e.items.length;r++){var o=e.items[r];o=new A({semanticContext:T.NONE},o),n.add(o)}e=n}var i=Cu.getConflictingAltSubsets(e);return Cu.hasConflictingAltSet(i)&&!Cu.hasStateAssociatedWithOneAlt(e)},hasConfigInRuleStopState:function(t){for(var e=0;e<t.items.length;e++)if(t.items[e].state instanceof G)return!0;return!1},allConfigsInRuleStopStates:function(t){for(var e=0;e<t.items.length;e++)if(!(t.items[e].state instanceof G))return!1;return!0},resolvesToJustOneViableAlt:function(t){return Cu.getSingleViableAlt(t)},allSubsetsConflict:function(t){return!Cu.hasNonConflictingAltSet(t)},hasNonConflictingAltSet:function(t){for(var e=0;e<t.length;e++)if(1===t[e].length)return!0;return!1},hasConflictingAltSet:function(t){for(var e=0;e<t.length;e++)if(t[e].length>1)return!0;return!1},allSubsetsEqual:function(t){for(var e=null,n=0;n<t.length;n++){var r=t[n];if(null===e)e=r;else if(r!==e)return!1}return!0},getUniqueAlt:function(t){var e=Cu.getAlts(t);return 1===e.length?e.minValue():Ie.INVALID_ALT_NUMBER},getAlts:function(t){var e=new ke;return t.map((function(t){e.or(t)})),e},getConflictingAltSubsets:function(t){var e=new we;return e.hashFunction=function(t){a.hashStuff(t.state.stateNumber,t.context)},e.equalsFunction=function(t,e){return t.state.stateNumber===e.state.stateNumber&&t.context.equals(e.context)},t.items.map((function(t){var n=e.get(t);null===n&&(n=new ke,e.set(t,n)),n.add(t.alt)})),e.getValues()},getStateToAltMap:function(t){var e=new Ru;return t.items.map((function(t){var n=e.get(t.state);null===n&&(n=new ke,e.set(t.state,n)),n.add(t.alt)})),e},hasStateAssociatedWithOneAlt:function(t){for(var e=Cu.getStateToAltMap(t).values(),n=0;n<e.length;n++)if(1===e[n].length)return!0;return!1},getSingleViableAlt:function(t){for(var e=null,n=0;n<t.length;n++){var r=t[n].minValue();if(null===e)e=r;else if(e!==r)return Ie.INVALID_ALT_NUMBER}return e}};const Au=Cu;function Nu(t){return Nu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Nu(t)}function Iu(t,e){return Iu=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Iu(t,e)}function Lu(t){return Lu=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Lu(t)}var Du=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Iu(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Lu(n);if(r){var o=Lu(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Nu(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t,e,n,r,u,c){var a;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),c=c||t._ctx,r=r||t.getCurrentToken(),n=n||t.getCurrentToken(),e=e||t.getInputStream(),(a=o.call(this,{message:"",recognizer:t,input:e,ctx:c})).deadEndConfigs=u,a.startToken=n,a.offendingToken=r,a}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ji);function Fu(t){return Fu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Fu(t)}function Bu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Fu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Fu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Fu(o)?o:String(o)),r)}var o}var Mu=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.defaultMapCtor=e||we,this.cacheMap=new this.defaultMapCtor}var e,n;return e=t,(n=[{key:"get",value:function(t,e){var n=this.cacheMap.get(t)||null;return null===n?null:n.get(e)||null}},{key:"set",value:function(t,e,n){var r=this.cacheMap.get(t)||null;null===r&&(r=new this.defaultMapCtor,this.cacheMap.set(t,r)),r.set(e,n)}}])&&Bu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Uu(t){return Uu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Uu(t)}function Vu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Uu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Uu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Uu(o)?o:String(o)),r)}var o}function qu(t,e){return qu=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},qu(t,e)}function Hu(t){return Hu=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Hu(t)}var zu=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&qu(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Hu(r);if(i){var n=Hu(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Uu(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t,e,n,r){var o;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(o=u.call(this,e,r)).parser=t,o.decisionToDFA=n,o.predictionMode=Au.LL,o._input=null,o._startIndex=0,o._outerContext=null,o._dfa=null,o.mergeCache=null,o.debug=!1,o.debug_closure=!1,o.debug_add=!1,o.trace_atn_sim=!1,o.dfa_debug=!1,o.retry_debug=!1,o}return e=c,n=[{key:"reset",value:function(){}},{key:"adaptivePredict",value:function(t,e,n){(this.debug||this.trace_atn_sim)&&console.log("adaptivePredict decision "+e+" exec LA(1)=="+this.getLookaheadName(t)+" line "+t.LT(1).line+":"+t.LT(1).column),this._input=t,this._startIndex=t.index,this._outerContext=n;var r=this.decisionToDFA[e];this._dfa=r;var o=t.mark(),i=t.index;try{var u;if(null===(u=r.precedenceDfa?r.getPrecedenceStartState(this.parser.getPrecedence()):r.s0)){null===n&&(n=Zt.EMPTY),this.debug&&console.log("predictATN decision "+r.decision+" exec LA(1)=="+this.getLookaheadName(t)+", outerContext="+n.toString(this.parser.ruleNames));var c=this.computeStartState(r.atnStartState,Zt.EMPTY,!1);r.precedenceDfa?(r.s0.configs=c,c=this.applyPrecedenceFilter(c),u=this.addDFAState(r,new Ki(null,c)),r.setPrecedenceStartState(this.parser.getPrecedence(),u)):(u=this.addDFAState(r,new Ki(null,c)),r.s0=u)}var a=this.execATN(r,u,t,i,n);return this.debug&&console.log("DFA after predictATN: "+r.toString(this.parser.literalNames,this.parser.symbolicNames)),a}finally{this._dfa=null,this.mergeCache=null,t.seek(i),t.release(o)}}},{key:"execATN",value:function(t,e,n,r,i){var u;(this.debug||this.trace_atn_sim)&&console.log("execATN decision "+t.decision+", DFA state "+e+", LA(1)=="+this.getLookaheadName(n)+" line "+n.LT(1).line+":"+n.LT(1).column);var c=e;this.debug&&console.log("s0 = "+e);for(var a=n.LA(1);;){var l=this.getExistingTargetState(c,a);if(null===l&&(l=this.computeTargetState(t,c,a)),l===Xi.ERROR){var s=this.noViableAlt(n,i,c.configs,r);if(n.seek(r),(u=this.getSynValidOrSemInvalidAltThatFinishedDecisionEntryRule(c.configs,i))!==Ie.INVALID_ALT_NUMBER)return u;throw s}if(l.requiresFullContext&&this.predictionMode!==Au.SLL){var f=null;if(null!==l.predicates){this.debug&&console.log("DFA state has preds in DFA sim LL failover");var p=n.index;if(p!==r&&n.seek(r),1===(f=this.evalSemanticContext(l.predicates,i,!0)).length)return this.debug&&console.log("Full LL avoided"),f.minValue();p!==r&&n.seek(p)}this.dfa_debug&&console.log("ctx sensitive state "+i+" in "+l);var y=this.computeStartState(t.atnStartState,i,!0);return this.reportAttemptingFullContext(t,f,l.configs,r,n.index),this.execATNWithFullContext(t,l,y,n,r,i)}if(l.isAcceptState){if(null===l.predicates)return l.prediction;var h=n.index;n.seek(r);var b=this.evalSemanticContext(l.predicates,i,!0);if(0===b.length)throw this.noViableAlt(n,i,l.configs,r);return 1===b.length||this.reportAmbiguity(t,l,r,h,!1,b,l.configs),b.minValue()}c=l,a!==o.EOF&&(n.consume(),a=n.LA(1))}}},{key:"getExistingTargetState",value:function(t,e){var n=t.edges;return null===n?null:n[e+1]||null}},{key:"computeTargetState",value:function(t,e,n){var r=this.computeReachSet(e.configs,n,!1);if(null===r)return this.addDFAEdge(t,e,n,Xi.ERROR),Xi.ERROR;var o=new Ki(null,r),i=this.getUniqueAlt(r);if(this.debug){var u=Au.getConflictingAltSubsets(r);console.log("SLL altSubSets="+p(u)+", configs="+r+", predict="+i+", allSubsetsConflict="+Au.allSubsetsConflict(u)+", conflictingAlts="+this.getConflictingAlts(r))}return i!==Ie.INVALID_ALT_NUMBER?(o.isAcceptState=!0,o.configs.uniqueAlt=i,o.prediction=i):Au.hasSLLConflictTerminatingPrediction(this.predictionMode,r)&&(o.configs.conflictingAlts=this.getConflictingAlts(r),o.requiresFullContext=!0,o.isAcceptState=!0,o.prediction=o.configs.conflictingAlts.minValue()),o.isAcceptState&&o.configs.hasSemanticContext&&(this.predicateDFAState(o,this.atn.getDecisionState(t.decision)),null!==o.predicates&&(o.prediction=Ie.INVALID_ALT_NUMBER)),this.addDFAEdge(t,e,n,o)}},{key:"predicateDFAState",value:function(t,e){var n=e.transitions.length,r=this.getConflictingAltsOrUniqueAlt(t.configs),o=this.getPredsForAmbigAlts(r,t.configs,n);null!==o?(t.predicates=this.getPredicatePredictions(r,o),t.prediction=Ie.INVALID_ALT_NUMBER):t.prediction=r.minValue()}},{key:"execATNWithFullContext",value:function(t,e,n,r,i,u){(this.debug||this.trace_atn_sim)&&console.log("execATNWithFullContext "+n);var c,a=!1,l=n;r.seek(i);for(var s=r.LA(1),f=-1;;){if(null===(c=this.computeReachSet(l,s,!0))){var p=this.noViableAlt(r,u,l,i);r.seek(i);var y=this.getSynValidOrSemInvalidAltThatFinishedDecisionEntryRule(l,u);if(y!==Ie.INVALID_ALT_NUMBER)return y;throw p}var h=Au.getConflictingAltSubsets(c);if(this.debug&&console.log("LL altSubSets="+h+", predict="+Au.getUniqueAlt(h)+", resolvesToJustOneViableAlt="+Au.resolvesToJustOneViableAlt(h)),c.uniqueAlt=this.getUniqueAlt(c),c.uniqueAlt!==Ie.INVALID_ALT_NUMBER){f=c.uniqueAlt;break}if(this.predictionMode!==Au.LL_EXACT_AMBIG_DETECTION){if((f=Au.resolvesToJustOneViableAlt(h))!==Ie.INVALID_ALT_NUMBER)break}else if(Au.allSubsetsConflict(h)&&Au.allSubsetsEqual(h)){a=!0,f=Au.getSingleViableAlt(h);break}l=c,s!==o.EOF&&(r.consume(),s=r.LA(1))}return c.uniqueAlt!==Ie.INVALID_ALT_NUMBER?(this.reportContextSensitivity(t,f,c,i,r.index),f):(this.reportAmbiguity(t,e,i,r.index,a,null,c),f)}},{key:"computeReachSet",value:function(t,e,n){this.debug&&console.log("in computeReachSet, starting closure: "+t),null===this.mergeCache&&(this.mergeCache=new Mu);for(var r=new Hi(n),i=null,u=0;u<t.items.length;u++){var c=t.items[u];if(this.debug&&console.log("testing "+this.getTokenName(e)+" at "+c),c.state instanceof G)(n||e===o.EOF)&&(null===i&&(i=[]),i.push(c),this.debug_add&&console.log("added "+c+" to skippedStopStates"));else for(var a=0;a<c.state.transitions.length;a++){var l=c.state.transitions[a],s=this.getReachableTarget(l,e);if(null!==s){var f=new A({state:s},c);r.add(f,this.mergeCache),this.debug_add&&console.log("added "+f+" to intermediate")}}}var p=null;if(null===i&&e!==o.EOF&&(1===r.items.length||this.getUniqueAlt(r)!==Ie.INVALID_ALT_NUMBER)&&(p=r),null===p){p=new Hi(n);for(var y=new v,h=e===o.EOF,b=0;b<r.items.length;b++)this.closure(r.items[b],p,y,!1,n,h)}if(e===o.EOF&&(p=this.removeAllConfigsNotInRuleStopState(p,p===r)),!(null===i||n&&Au.hasConfigInRuleStopState(p)))for(var d=0;d<i.length;d++)p.add(i[d],this.mergeCache);return this.trace_atn_sim&&console.log("computeReachSet "+t+" -> "+p),0===p.items.length?null:p}},{key:"removeAllConfigsNotInRuleStopState",value:function(t,e){if(Au.allConfigsInRuleStopStates(t))return t;for(var n=new Hi(t.fullCtx),r=0;r<t.items.length;r++){var i=t.items[r];if(i.state instanceof G)n.add(i,this.mergeCache);else if(e&&i.state.epsilonOnlyTransitions&&this.atn.nextTokens(i.state).contains(o.EPSILON)){var u=this.atn.ruleToStopState[i.state.ruleIndex];n.add(new A({state:u},i),this.mergeCache)}}return n}},{key:"computeStartState",value:function(t,e,n){var r=_e(this.atn,e),o=new Hi(n);this.trace_atn_sim&&console.log("computeStartState from ATN state "+t+" initialContext="+r.toString(this.parser));for(var i=0;i<t.transitions.length;i++){var u=t.transitions[i].target,c=new A({state:u,alt:i+1,context:r},null),a=new v;this.closure(c,o,a,!0,n,!1)}return o}},{key:"applyPrecedenceFilter",value:function(t){for(var e,n=[],r=new Hi(t.fullCtx),o=0;o<t.items.length;o++)if(1===(e=t.items[o]).alt){var i=e.semanticContext.evalPrecedence(this.parser,this._outerContext);null!==i&&(n[e.state.stateNumber]=e.context,i!==e.semanticContext?r.add(new A({semanticContext:i},e),this.mergeCache):r.add(e,this.mergeCache))}for(var u=0;u<t.items.length;u++)if(1!==(e=t.items[u]).alt){if(!e.precedenceFilterSuppressed){var c=n[e.state.stateNumber]||null;if(null!==c&&c.equals(e.context))continue}r.add(e,this.mergeCache)}return r}},{key:"getReachableTarget",value:function(t,e){return t.matches(e,0,this.atn.maxTokenType)?t.target:null}},{key:"getPredsForAmbigAlts",value:function(t,e,n){for(var r=[],o=0;o<e.items.length;o++){var i=e.items[o];t.has(i.alt)&&(r[i.alt]=T.orContext(r[i.alt]||null,i.semanticContext))}for(var u=0,c=1;c<n+1;c++){var a=r[c]||null;null===a?r[c]=T.NONE:a!==T.NONE&&(u+=1)}return 0===u&&(r=null),this.debug&&console.log("getPredsForAmbigAlts result "+p(r)),r}},{key:"getPredicatePredictions",value:function(t,e){for(var n=[],r=!1,o=1;o<e.length;o++){var i=e[o];null!==t&&t.has(o)&&n.push(new ju(i,o)),i!==T.NONE&&(r=!0)}return r?n:null}},{key:"getSynValidOrSemInvalidAltThatFinishedDecisionEntryRule",value:function(t,e){var n=this.splitAccordingToSemanticValidity(t,e),r=n[0],o=n[1],i=this.getAltThatFinishedDecisionEntryRule(r);return i!==Ie.INVALID_ALT_NUMBER||o.items.length>0&&(i=this.getAltThatFinishedDecisionEntryRule(o))!==Ie.INVALID_ALT_NUMBER?i:Ie.INVALID_ALT_NUMBER}},{key:"getAltThatFinishedDecisionEntryRule",value:function(t){for(var e=[],n=0;n<t.items.length;n++){var r=t.items[n];(r.reachesIntoOuterContext>0||r.state instanceof G&&r.context.hasEmptyPath())&&e.indexOf(r.alt)<0&&e.push(r.alt)}return 0===e.length?Ie.INVALID_ALT_NUMBER:Math.min.apply(null,e)}},{key:"splitAccordingToSemanticValidity",value:function(t,e){for(var n=new Hi(t.fullCtx),r=new Hi(t.fullCtx),o=0;o<t.items.length;o++){var i=t.items[o];i.semanticContext!==T.NONE?i.semanticContext.evaluate(this.parser,e)?n.add(i):r.add(i):n.add(i)}return[n,r]}},{key:"evalSemanticContext",value:function(t,e,n){for(var r=new ke,o=0;o<t.length;o++){var i=t[o];if(i.pred!==T.NONE){var u=i.pred.evaluate(this.parser,e);if((this.debug||this.dfa_debug)&&console.log("eval pred "+i+"="+u),u&&((this.debug||this.dfa_debug)&&console.log("PREDICT "+i.alt),r.add(i.alt),!n))break}else if(r.add(i.alt),!n)break}return r}},{key:"closure",value:function(t,e,n,r,o,i){this.closureCheckingStopState(t,e,n,r,o,0,i)}},{key:"closureCheckingStopState",value:function(t,e,n,r,o,i,u){if((this.trace_atn_sim||this.debug_closure)&&console.log("closure("+t.toString(this.parser,!0)+")"),t.state instanceof G){if(!t.context.isEmpty()){for(var c=0;c<t.context.length;c++)if(t.context.getReturnState(c)!==ee.EMPTY_RETURN_STATE){var a=this.atn.states[t.context.getReturnState(c)],l=t.context.getParent(c),s={state:a,alt:t.alt,context:l,semanticContext:t.semanticContext},f=new A(s,null);f.reachesIntoOuterContext=t.reachesIntoOuterContext,this.closureCheckingStopState(f,e,n,r,o,i-1,u)}else{if(o){e.add(new A({state:t.state,context:ee.EMPTY},t),this.mergeCache);continue}this.debug&&console.log("FALLING off rule "+this.getRuleName(t.state.ruleIndex)),this.closure_(t,e,n,r,o,i,u)}return}if(o)return void e.add(t,this.mergeCache);this.debug&&console.log("FALLING off rule "+this.getRuleName(t.state.ruleIndex))}this.closure_(t,e,n,r,o,i,u)}},{key:"closure_",value:function(t,e,n,r,o,i,u){var c=t.state;c.epsilonOnlyTransitions||e.add(t,this.mergeCache);for(var a=0;a<c.transitions.length;a++)if(0!==a||!this.canDropLoopEntryEdgeInLeftRecursiveRule(t)){var l=c.transitions[a],s=r&&!(l instanceof mr),f=this.getEpsilonTarget(t,l,s,0===i,o,u);if(null!==f){var p=i;if(t.state instanceof G){if(null!==this._dfa&&this._dfa.precedenceDfa&&l.outermostPrecedenceReturn===this._dfa.atnStartState.ruleIndex&&(f.precedenceFilterSuppressed=!0),f.reachesIntoOuterContext+=1,n.add(f)!==f)continue;e.dipsIntoOuterContext=!0,p-=1,this.debug&&console.log("dips into outer ctx: "+f)}else{if(!l.isEpsilon&&n.add(f)!==f)continue;l instanceof nt&&p>=0&&(p+=1)}this.closureCheckingStopState(f,e,n,s,o,p,u)}}}},{key:"canDropLoopEntryEdgeInLeftRecursiveRule",value:function(t){var e=t.state;if(e.stateType!==V.STAR_LOOP_ENTRY)return!1;if(e.stateType!==V.STAR_LOOP_ENTRY||!e.isPrecedenceDecision||t.context.isEmpty()||t.context.hasEmptyPath())return!1;for(var n=t.context.length,r=0;r<n;r++)if(this.atn.states[t.context.getReturnState(r)].ruleIndex!==e.ruleIndex)return!1;for(var o=e.transitions[0].target.endState.stateNumber,i=this.atn.states[o],u=0;u<n;u++){var c=t.context.getReturnState(u),a=this.atn.states[c];if(1!==a.transitions.length||!a.transitions[0].isEpsilon)return!1;var l=a.transitions[0].target;if(!(a.stateType===V.BLOCK_END&&l===e||a===i||l===i||l.stateType===V.BLOCK_END&&1===l.transitions.length&&l.transitions[0].isEpsilon&&l.transitions[0].target===e))return!1}return!0}},{key:"getRuleName",value:function(t){return null!==this.parser&&t>=0?this.parser.ruleNames[t]:"<rule "+t+">"}},{key:"getEpsilonTarget",value:function(t,e,n,r,i,u){switch(e.serializationType){case $.RULE:return this.ruleTransition(t,e);case $.PRECEDENCE:return this.precedenceTransition(t,e,n,r,i);case $.PREDICATE:return this.predTransition(t,e,n,r,i);case $.ACTION:return this.actionTransition(t,e);case $.EPSILON:return new A({state:e.target},t);case $.ATOM:case $.RANGE:case $.SET:return u&&e.matches(o.EOF,0,1)?new A({state:e.target},t):null;default:return null}}},{key:"actionTransition",value:function(t,e){if(this.debug){var n=-1===e.actionIndex?65535:e.actionIndex;console.log("ACTION edge "+e.ruleIndex+":"+n)}return new A({state:e.target},t)}},{key:"precedenceTransition",value:function(t,e,n,r,o){this.debug&&(console.log("PRED (collectPredicates="+n+") "+e.precedence+">=_p, ctx dependent=true"),null!==this.parser&&console.log("context surrounding pred is "+p(this.parser.getRuleInvocationStack())));var i=null;if(n&&r)if(o){var u=this._input.index;this._input.seek(this._startIndex);var c=e.getPredicate().evaluate(this.parser,this._outerContext);this._input.seek(u),c&&(i=new A({state:e.target},t))}else{var a=T.andContext(t.semanticContext,e.getPredicate());i=new A({state:e.target,semanticContext:a},t)}else i=new A({state:e.target},t);return this.debug&&console.log("config from pred transition="+i),i}},{key:"predTransition",value:function(t,e,n,r,o){this.debug&&(console.log("PRED (collectPredicates="+n+") "+e.ruleIndex+":"+e.predIndex+", ctx dependent="+e.isCtxDependent),null!==this.parser&&console.log("context surrounding pred is "+p(this.parser.getRuleInvocationStack())));var i=null;if(n&&(e.isCtxDependent&&r||!e.isCtxDependent))if(o){var u=this._input.index;this._input.seek(this._startIndex);var c=e.getPredicate().evaluate(this.parser,this._outerContext);this._input.seek(u),c&&(i=new A({state:e.target},t))}else{var a=T.andContext(t.semanticContext,e.getPredicate());i=new A({state:e.target,semanticContext:a},t)}else i=new A({state:e.target},t);return this.debug&&console.log("config from pred transition="+i),i}},{key:"ruleTransition",value:function(t,e){this.debug&&console.log("CALL rule "+this.getRuleName(e.target.ruleIndex)+", ctx="+t.context);var n=e.followState,r=ye.create(t.context,n.stateNumber);return new A({state:e.target,context:r},t)}},{key:"getConflictingAlts",value:function(t){var e=Au.getConflictingAltSubsets(t);return Au.getAlts(e)}},{key:"getConflictingAltsOrUniqueAlt",value:function(t){var e=null;return t.uniqueAlt!==Ie.INVALID_ALT_NUMBER?(e=new ke).add(t.uniqueAlt):e=t.conflictingAlts,e}},{key:"getTokenName",value:function(t){if(t===o.EOF)return"EOF";if(null!==this.parser&&null!==this.parser.literalNames){if(!(t>=this.parser.literalNames.length&&t>=this.parser.symbolicNames.length))return(this.parser.literalNames[t]||this.parser.symbolicNames[t])+"<"+t+">";console.log(t+" ttype out of range: "+this.parser.literalNames),console.log(""+this.parser.getInputStream().getTokens())}return""+t}},{key:"getLookaheadName",value:function(t){return this.getTokenName(t.LA(1))}},{key:"dumpDeadEndConfigs",value:function(t){console.log("dead end configs: ");for(var e=t.getDeadEndConfigs(),n=0;n<e.length;n++){var r=e[n],o="no edges";if(r.state.transitions.length>0){var i=r.state.transitions[0];i instanceof ar?o="Atom "+this.getTokenName(i.label):i instanceof ct&&(o=(i instanceof yt?"~":"")+"Set "+i.set)}console.error(r.toString(this.parser,!0)+":"+o)}}},{key:"noViableAlt",value:function(t,e,n,r){return new Du(this.parser,t,t.get(r),t.LT(1),n,e)}},{key:"getUniqueAlt",value:function(t){for(var e=Ie.INVALID_ALT_NUMBER,n=0;n<t.items.length;n++){var r=t.items[n];if(e===Ie.INVALID_ALT_NUMBER)e=r.alt;else if(r.alt!==e)return Ie.INVALID_ALT_NUMBER}return e}},{key:"addDFAEdge",value:function(t,e,n,r){if(this.debug&&console.log("EDGE "+e+" -> "+r+" upon "+this.getTokenName(n)),null===r)return null;if(r=this.addDFAState(t,r),null===e||n<-1||n>this.atn.maxTokenType)return r;if(null===e.edges&&(e.edges=[]),e.edges[n+1]=r,this.debug){var o=null===this.parser?null:this.parser.literalNames,i=null===this.parser?null:this.parser.symbolicNames;console.log("DFA=\n"+t.toString(o,i))}return r}},{key:"addDFAState",value:function(t,e){if(e===Xi.ERROR)return e;var n=t.states.get(e);return null!==n?(this.trace_atn_sim&&console.log("addDFAState "+e+" exists"),n):(e.stateNumber=t.states.length,e.configs.readOnly||(e.configs.optimizeConfigs(this),e.configs.setReadonly(!0)),this.trace_atn_sim&&console.log("addDFAState new "+e),t.states.add(e),this.debug&&console.log("adding new DFA state: "+e),e)}},{key:"reportAttemptingFullContext",value:function(t,e,n,r,o){if(this.debug||this.retry_debug){var i=new L(r,o+1);console.log("reportAttemptingFullContext decision="+t.decision+":"+n+", input="+this.parser.getTokenStream().getText(i))}null!==this.parser&&this.parser.getErrorListenerDispatch().reportAttemptingFullContext(this.parser,t,r,o,e,n)}},{key:"reportContextSensitivity",value:function(t,e,n,r,o){if(this.debug||this.retry_debug){var i=new L(r,o+1);console.log("reportContextSensitivity decision="+t.decision+":"+n+", input="+this.parser.getTokenStream().getText(i))}null!==this.parser&&this.parser.getErrorListenerDispatch().reportContextSensitivity(this.parser,t,r,o,e,n)}},{key:"reportAmbiguity",value:function(t,e,n,r,o,i,u){if(this.debug||this.retry_debug){var c=new L(n,r+1);console.log("reportAmbiguity "+i+":"+u+", input="+this.parser.getTokenStream().getText(c))}null!==this.parser&&this.parser.getErrorListenerDispatch().reportAmbiguity(this.parser,t,n,r,o,i,u)}}],n&&Vu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(Xi);function Yu(t){return Yu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Yu(t)}function Ku(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Yu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Yu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Yu(o)?o:String(o)),r)}var o}var Gu=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.cache=new we}var e,n;return e=t,(n=[{key:"add",value:function(t){if(t===ee.EMPTY)return ee.EMPTY;var e=this.cache.get(t)||null;return null!==e?e:(this.cache.set(t,t),t)}},{key:"get",value:function(t){return this.cache.get(t)||null}},{key:"length",get:function(){return this.cache.length}}])&&Ku(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();const Wu={ATN:Ie,ATNDeserializer:qo,LexerATNSimulator:Pu,ParserATNSimulator:zu,PredictionMode:Au,PredictionContextCache:Gu};function Xu(t){return Xu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Xu(t)}function Ju(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Xu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Xu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Xu(o)?o:String(o)),r)}var o}var $u=function(){function t(e,n,r){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.dfa=e,this.literalNames=n||[],this.symbolicNames=r||[]}var e,n;return e=t,(n=[{key:"toString",value:function(){if(null===this.dfa.s0)return null;for(var t="",e=this.dfa.sortedStates(),n=0;n<e.length;n++){var r=e[n];if(null!==r.edges)for(var o=r.edges.length,i=0;i<o;i++){var u=r.edges[i]||null;null!==u&&2147483647!==u.stateNumber&&(t=(t=(t=(t=(t=(t=t.concat(this.getStateString(r))).concat("-")).concat(this.getEdgeLabel(i))).concat("->")).concat(this.getStateString(u))).concat("\n"))}}return 0===t.length?null:t}},{key:"getEdgeLabel",value:function(t){return 0===t?"EOF":null!==this.literalNames||null!==this.symbolicNames?this.literalNames[t-1]||this.symbolicNames[t-1]:String.fromCharCode(t-1)}},{key:"getStateString",value:function(t){var e=(t.isAcceptState?":":"")+"s"+t.stateNumber+(t.requiresFullContext?"^":"");return t.isAcceptState?null!==t.predicates?e+"=>"+p(t.predicates):e+"=>"+t.prediction.toString():e}}])&&Ju(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function Zu(t){return Zu="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Zu(t)}function Qu(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Zu(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Zu(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Zu(o)?o:String(o)),r)}var o}function tc(t,e){return tc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},tc(t,e)}function ec(t){return ec=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ec(t)}var nc=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&tc(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ec(r);if(o){var n=ec(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Zu(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,t,null)}return e=u,(n=[{key:"getEdgeLabel",value:function(t){return"'"+String.fromCharCode(t)+"'"}}])&&Qu(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}($u);function rc(t){return rc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},rc(t)}function oc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==rc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==rc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===rc(o)?o:String(o)),r)}var o}var ic=function(){function t(e,n){if(function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),void 0===n&&(n=0),this.atnStartState=e,this.decision=n,this._states=new v,this.s0=null,this.precedenceDfa=!1,e instanceof Mn&&e.isPrecedenceDecision){this.precedenceDfa=!0;var r=new Ki(null,new Hi);r.edges=[],r.isAcceptState=!1,r.requiresFullContext=!1,this.s0=r}}var e,n;return e=t,(n=[{key:"getPrecedenceStartState",value:function(t){if(!this.precedenceDfa)throw"Only precedence DFAs may contain a precedence start state.";return t<0||t>=this.s0.edges.length?null:this.s0.edges[t]||null}},{key:"setPrecedenceStartState",value:function(t,e){if(!this.precedenceDfa)throw"Only precedence DFAs may contain a precedence start state.";t<0||(this.s0.edges[t]=e)}},{key:"setPrecedenceDfa",value:function(t){if(this.precedenceDfa!==t){if(this._states=new v,t){var e=new Ki(null,new Hi);e.edges=[],e.isAcceptState=!1,e.requiresFullContext=!1,this.s0=e}else this.s0=null;this.precedenceDfa=t}}},{key:"sortedStates",value:function(){return this._states.values().sort((function(t,e){return t.stateNumber-e.stateNumber}))}},{key:"toString",value:function(t,e){return t=t||null,e=e||null,null===this.s0?"":new $u(this,t,e).toString()}},{key:"toLexerString",value:function(){return null===this.s0?"":new nc(this).toString()}},{key:"states",get:function(){return this._states}}])&&oc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();const uc={DFA:ic,DFASerializer:$u,LexerDFASerializer:nc,PredPrediction:ju},cc={PredictionContext:ee},ac={Interval:L,IntervalSet:B};function lc(t){return lc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},lc(t)}function sc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==lc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==lc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===lc(o)?o:String(o)),r)}var o}var fc=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}var e,n;return e=t,(n=[{key:"visitTerminal",value:function(t){}},{key:"visitErrorNode",value:function(t){}},{key:"enterEveryRule",value:function(t){}},{key:"exitEveryRule",value:function(t){}}])&&sc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function pc(t){return pc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},pc(t)}function yc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==pc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==pc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===pc(o)?o:String(o)),r)}var o}var hc=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}var e,n;return e=t,(n=[{key:"visit",value:function(t){return Array.isArray(t)?t.map((function(t){return t.accept(this)}),this):t.accept(this)}},{key:"visitChildren",value:function(t){return t.children?this.visit(t.children):null}},{key:"visitTerminal",value:function(t){}},{key:"visitErrorNode",value:function(t){}}])&&yc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function bc(t){return bc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},bc(t)}function vc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==bc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==bc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===bc(o)?o:String(o)),r)}var o}var dc=function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}var e,n;return e=t,(n=[{key:"walk",value:function(t,e){if(e instanceof Yt||void 0!==e.isErrorNode&&e.isErrorNode())t.visitErrorNode(e);else if(e instanceof Vt)t.visitTerminal(e);else{this.enterRule(t,e);for(var n=0;n<e.getChildCount();n++){var r=e.getChild(n);this.walk(t,r)}this.exitRule(t,e)}}},{key:"enterRule",value:function(t,e){var n=e.ruleContext;t.enterEveryRule(n),n.enterRule(t)}},{key:"exitRule",value:function(t,e){var n=e.ruleContext;n.exitRule(t),t.exitEveryRule(n)}}])&&vc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();dc.DEFAULT=new dc;const mc={Trees:Gt,RuleNode:Ft,ErrorNode:Yt,TerminalNode:Vt,ParseTreeListener:fc,ParseTreeVisitor:hc,ParseTreeWalker:dc};function gc(t){return gc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},gc(t)}function Sc(t,e){return Sc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Sc(t,e)}function Oc(t){return Oc=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Oc(t)}var wc=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Sc(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Oc(n);if(r){var o=Oc(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===gc(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(e=o.call(this,{message:"",recognizer:t,input:t.getInputStream(),ctx:t._ctx})).offendingToken=t.getCurrentToken(),e}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ji);function _c(t){return _c="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},_c(t)}function Pc(t,e){return Pc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Pc(t,e)}function Tc(t){return Tc=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Tc(t)}var Ec=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Pc(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Tc(n);if(r){var o=Tc(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===_c(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t,e,n){var r;!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),r=o.call(this,{message:jc(e,n||null),recognizer:t,input:t.getInputStream(),ctx:t._ctx});var u=t._interp.atn.states[t.state].transitions[0];return u instanceof Nr?(r.ruleIndex=u.ruleIndex,r.predicateIndex=u.predIndex):(r.ruleIndex=0,r.predicateIndex=0),r.predicate=e,r.offendingToken=t.getCurrentToken(),r}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(ji);function jc(t,e){return null!==e?e:"failed predicate: {"+t+"}?"}function kc(t){return kc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},kc(t)}function xc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==kc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==kc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===kc(o)?o:String(o)),r)}var o}function Rc(t,e){return Rc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Rc(t,e)}function Cc(t){return Cc=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Cc(t)}var Ac=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Rc(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Cc(r);if(o){var n=Cc(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===kc(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),t=t||!0,(e=i.call(this)).exactOnly=t,e}return e=u,n=[{key:"reportAmbiguity",value:function(t,e,n,r,o,i,u){if(!this.exactOnly||o){var c="reportAmbiguity d="+this.getDecisionDescription(t,e)+": ambigAlts="+this.getConflictingAlts(i,u)+", input='"+t.getTokenStream().getText(new L(n,r))+"'";t.notifyErrorListeners(c)}}},{key:"reportAttemptingFullContext",value:function(t,e,n,r,o,i){var u="reportAttemptingFullContext d="+this.getDecisionDescription(t,e)+", input='"+t.getTokenStream().getText(new L(n,r))+"'";t.notifyErrorListeners(u)}},{key:"reportContextSensitivity",value:function(t,e,n,r,o,i){var u="reportContextSensitivity d="+this.getDecisionDescription(t,e)+", input='"+t.getTokenStream().getText(new L(n,r))+"'";t.notifyErrorListeners(u)}},{key:"getDecisionDescription",value:function(t,e){var n=e.decision,r=e.atnStartState.ruleIndex,o=t.ruleNames;if(r<0||r>=o.length)return""+n;var i=o[r]||null;return null===i||0===i.length?""+n:"".concat(n," (").concat(i,")")}},{key:"getConflictingAlts",value:function(t,e){if(null!==t)return t;for(var n=new ke,r=0;r<e.items.length;r++)n.add(e.items[r].alt);return"{".concat(n.values().join(", "),"}")}}],n&&xc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Yo);function Nc(t){return Nc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Nc(t)}function Ic(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}function Lc(t){var e="function"==typeof Map?new Map:void 0;return Lc=function(t){if(null===t||(n=t,-1===Function.toString.call(n).indexOf("[native code]")))return t;var n;if("function"!=typeof t)throw new TypeError("Super expression must either be null or a function");if(void 0!==e){if(e.has(t))return e.get(t);e.set(t,r)}function r(){return Dc(t,arguments,Mc(this).constructor)}return r.prototype=Object.create(t.prototype,{constructor:{value:r,enumerable:!1,writable:!0,configurable:!0}}),Bc(r,t)},Lc(t)}function Dc(t,e,n){return Dc=Fc()?Reflect.construct.bind():function(t,e,n){var r=[null];r.push.apply(r,e);var o=new(Function.bind.apply(t,r));return n&&Bc(o,n.prototype),o},Dc.apply(null,arguments)}function Fc(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}function Bc(t,e){return Bc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Bc(t,e)}function Mc(t){return Mc=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Mc(t)}var Uc=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Bc(t,e)}(i,t);var e,n,r,o=(n=i,r=Fc(),function(){var t,e=Mc(n);if(r){var o=Mc(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Nc(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return Ic(t)}(this,t)});function i(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),t=o.call(this),Error.captureStackTrace(Ic(t),i),t}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(Lc(Error));function Vc(t){return Vc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Vc(t)}function qc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Vc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Vc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Vc(o)?o:String(o)),r)}var o}function Hc(t){return Hc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Hc(t)}function zc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Hc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Hc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Hc(o)?o:String(o)),r)}var o}function Yc(t,e){return Yc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Yc(t,e)}function Kc(t){return Kc=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Kc(t)}var Gc=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Yc(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Kc(r);if(i){var n=Kc(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Hc(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(){var t;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(t=u.call(this)).errorRecoveryMode=!1,t.lastErrorIndex=-1,t.lastErrorStates=null,t.nextTokensContext=null,t.nextTokenState=0,t}return e=c,n=[{key:"reset",value:function(t){this.endErrorCondition(t)}},{key:"beginErrorCondition",value:function(t){this.errorRecoveryMode=!0}},{key:"inErrorRecoveryMode",value:function(t){return this.errorRecoveryMode}},{key:"endErrorCondition",value:function(t){this.errorRecoveryMode=!1,this.lastErrorStates=null,this.lastErrorIndex=-1}},{key:"reportMatch",value:function(t){this.endErrorCondition(t)}},{key:"reportError",value:function(t,e){this.inErrorRecoveryMode(t)||(this.beginErrorCondition(t),e instanceof Du?this.reportNoViableAlternative(t,e):e instanceof wc?this.reportInputMismatch(t,e):e instanceof Ec?this.reportFailedPredicate(t,e):(console.log("unknown recognition error type: "+e.constructor.name),console.log(e.stack),t.notifyErrorListeners(e.getOffendingToken(),e.getMessage(),e)))}},{key:"recover",value:function(t,e){this.lastErrorIndex===t.getInputStream().index&&null!==this.lastErrorStates&&this.lastErrorStates.indexOf(t.state)>=0&&t.consume(),this.lastErrorIndex=t._input.index,null===this.lastErrorStates&&(this.lastErrorStates=[]),this.lastErrorStates.push(t.state);var n=this.getErrorRecoverySet(t);this.consumeUntil(t,n)}},{key:"sync",value:function(t){if(!this.inErrorRecoveryMode(t)){var e=t._interp.atn.states[t.state],n=t.getTokenStream().LA(1),r=t.atn.nextTokens(e);if(r.contains(n))return this.nextTokensContext=null,void(this.nextTokenState=V.INVALID_STATE_NUMBER);if(r.contains(o.EPSILON))null===this.nextTokensContext&&(this.nextTokensContext=t._ctx,this.nextTokensState=t._stateNumber);else switch(e.stateType){case V.BLOCK_START:case V.STAR_BLOCK_START:case V.PLUS_BLOCK_START:case V.STAR_LOOP_ENTRY:if(null!==this.singleTokenDeletion(t))return;throw new wc(t);case V.PLUS_LOOP_BACK:case V.STAR_LOOP_BACK:this.reportUnwantedToken(t);var i=new B;i.addSet(t.getExpectedTokens());var u=i.addSet(this.getErrorRecoverySet(t));this.consumeUntil(t,u)}}}},{key:"reportNoViableAlternative",value:function(t,e){var n,r=t.getTokenStream();n=null!==r?e.startToken.type===o.EOF?"<EOF>":r.getText(new L(e.startToken.tokenIndex,e.offendingToken.tokenIndex)):"<unknown input>";var i="no viable alternative at input "+this.escapeWSAndQuote(n);t.notifyErrorListeners(i,e.offendingToken,e)}},{key:"reportInputMismatch",value:function(t,e){var n="mismatched input "+this.getTokenErrorDisplay(e.offendingToken)+" expecting "+e.getExpectedTokens().toString(t.literalNames,t.symbolicNames);t.notifyErrorListeners(n,e.offendingToken,e)}},{key:"reportFailedPredicate",value:function(t,e){var n="rule "+t.ruleNames[t._ctx.ruleIndex]+" "+e.message;t.notifyErrorListeners(n,e.offendingToken,e)}},{key:"reportUnwantedToken",value:function(t){if(!this.inErrorRecoveryMode(t)){this.beginErrorCondition(t);var e=t.getCurrentToken(),n="extraneous input "+this.getTokenErrorDisplay(e)+" expecting "+this.getExpectedTokens(t).toString(t.literalNames,t.symbolicNames);t.notifyErrorListeners(n,e,null)}}},{key:"reportMissingToken",value:function(t){if(!this.inErrorRecoveryMode(t)){this.beginErrorCondition(t);var e=t.getCurrentToken(),n="missing "+this.getExpectedTokens(t).toString(t.literalNames,t.symbolicNames)+" at "+this.getTokenErrorDisplay(e);t.notifyErrorListeners(n,e,null)}}},{key:"recoverInline",value:function(t){var e=this.singleTokenDeletion(t);if(null!==e)return t.consume(),e;if(this.singleTokenInsertion(t))return this.getMissingSymbol(t);throw new wc(t)}},{key:"singleTokenInsertion",value:function(t){var e=t.getTokenStream().LA(1),n=t._interp.atn,r=n.states[t.state].transitions[0].target;return!!n.nextTokens(r,t._ctx).contains(e)&&(this.reportMissingToken(t),!0)}},{key:"singleTokenDeletion",value:function(t){var e=t.getTokenStream().LA(2);if(this.getExpectedTokens(t).contains(e)){this.reportUnwantedToken(t),t.consume();var n=t.getCurrentToken();return this.reportMatch(t),n}return null}},{key:"getMissingSymbol",value:function(t){var e,n=t.getCurrentToken(),r=this.getExpectedTokens(t).first();e=r===o.EOF?"<missing EOF>":"<missing "+t.literalNames[r]+">";var i=n,u=t.getTokenStream().LT(-1);return i.type===o.EOF&&null!==u&&(i=u),t.getTokenFactory().create(i.source,r,e,o.DEFAULT_CHANNEL,-1,-1,i.line,i.column)}},{key:"getExpectedTokens",value:function(t){return t.getExpectedTokens()}},{key:"getTokenErrorDisplay",value:function(t){if(null===t)return"<no token>";var e=t.text;return null===e&&(e=t.type===o.EOF?"<EOF>":"<"+t.type+">"),this.escapeWSAndQuote(e)}},{key:"escapeWSAndQuote",value:function(t){return"'"+(t=(t=(t=t.replace(/\n/g,"\\n")).replace(/\r/g,"\\r")).replace(/\t/g,"\\t"))+"'"}},{key:"getErrorRecoverySet",value:function(t){for(var e=t._interp.atn,n=t._ctx,r=new B;null!==n&&n.invokingState>=0;){var i=e.states[n.invokingState].transitions[0],u=e.nextTokens(i.followState);r.addSet(u),n=n.parentCtx}return r.removeOne(o.EPSILON),r}},{key:"consumeUntil",value:function(t,e){for(var n=t.getTokenStream().LA(1);n!==o.EOF&&!e.contains(n);)t.consume(),n=t.getTokenStream().LA(1)}}],n&&zc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(function(){function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)}var e,n;return e=t,(n=[{key:"reset",value:function(t){}},{key:"recoverInline",value:function(t){}},{key:"recover",value:function(t,e){}},{key:"sync",value:function(t){}},{key:"inErrorRecoveryMode",value:function(t){}},{key:"reportError",value:function(t){}}])&&qc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}());function Wc(t){return Wc="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Wc(t)}function Xc(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Wc(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Wc(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Wc(o)?o:String(o)),r)}var o}function Jc(t,e){return Jc=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Jc(t,e)}function $c(t){return $c=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},$c(t)}var Zc=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Jc(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=$c(r);if(o){var n=$c(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Wc(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this)}return e=u,n=[{key:"recover",value:function(t,e){for(var n=t._ctx;null!==n;)n.exception=e,n=n.parentCtx;throw new Uc(e)}},{key:"recoverInline",value:function(t){this.recover(t,new wc(t))}},{key:"sync",value:function(t){}}],n&&Xc(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Gc);const Qc={RecognitionException:ji,NoViableAltException:Du,LexerNoViableAltException:Ai,InputMismatchException:wc,FailedPredicateException:Ec,DiagnosticErrorListener:Ac,BailErrorStrategy:Zc,DefaultErrorStrategy:Gc,ErrorListener:Yo};var ta,ea;function na(t){return na="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},na(t)}function ra(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==na(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==na(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===na(o)?o:String(o)),r)}var o}String.prototype.codePointAt||(ea=function(t){if(null==this)throw TypeError();var e=String(this),n=e.length,r=t?Number(t):0;if(r!=r&&(r=0),!(r<0||r>=n)){var o,i=e.charCodeAt(r);return i>=55296&&i<=56319&&n>r+1&&(o=e.charCodeAt(r+1))>=56320&&o<=57343?1024*(i-55296)+o-56320+65536:i}},(ta=function(){var t;try{var e={},n=Object.defineProperty;t=n(e,e,e)&&n}catch(t){}return t}())?ta(String.prototype,"codePointAt",{value:ea,configurable:!0,writable:!0}):String.prototype.codePointAt=ea),String.prototype.codePointAt,String.fromCodePoint||function(){var t=function(){var t;try{var e={},n=Object.defineProperty;t=n(e,e,e)&&n}catch(t){}return t}(),e=String.fromCharCode,n=Math.floor,r=function(t){var r,o,i=[],u=-1,c=arguments.length;if(!c)return"";for(var a="";++u<c;){var l=Number(arguments[u]);if(!isFinite(l)||l<0||l>1114111||n(l)!==l)throw RangeError("Invalid code point: "+l);l<=65535?i.push(l):(r=55296+((l-=65536)>>10),o=l%1024+56320,i.push(r,o)),(u+1===c||i.length>16384)&&(a+=e.apply(null,i),i.length=0)}return a};t?t(String,"fromCodePoint",{value:r,configurable:!0,writable:!0}):String.fromCodePoint=r}(),String.prototype.fromCodePoint;var oa=function(){function t(e,n){if(function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.name="<empty>",this.strdata=e,this.decodeToUnicodeCodePoints=n||!1,this._index=0,this.data=[],this.decodeToUnicodeCodePoints)for(var r=0;r<this.strdata.length;){var o=this.strdata.codePointAt(r);this.data.push(o),r+=o<=65535?1:2}else{this.data=new Array(this.strdata.length);for(var i=0;i<this.strdata.length;i++)this.data[i]=this.strdata.charCodeAt(i)}this._size=this.data.length}var e,n;return e=t,(n=[{key:"reset",value:function(){this._index=0}},{key:"consume",value:function(){if(this._index>=this._size)throw"cannot consume EOF";this._index+=1}},{key:"LA",value:function(t){if(0===t)return 0;t<0&&(t+=1);var e=this._index+t-1;return e<0||e>=this._size?o.EOF:this.data[e]}},{key:"LT",value:function(t){return this.LA(t)}},{key:"mark",value:function(){return-1}},{key:"release",value:function(t){}},{key:"seek",value:function(t){t<=this._index?this._index=t:this._index=Math.min(t,this._size)}},{key:"getText",value:function(t,e){if(e>=this._size&&(e=this._size-1),t>=this._size)return"";if(this.decodeToUnicodeCodePoints){for(var n="",r=t;r<=e;r++)n+=String.fromCodePoint(this.data[r]);return n}return this.strdata.slice(t,e+1)}},{key:"toString",value:function(){return this.strdata}},{key:"index",get:function(){return this._index}},{key:"size",get:function(){return this._size}}])&&ra(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),t}();function ia(t){return ia="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ia(t)}function ua(t,e){return ua=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ua(t,e)}function ca(t){return ca=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ca(t)}var aa=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ua(t,e)}(i,t);var e,n,r,o=(n=i,r=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ca(n);if(r){var o=ca(this).constructor;t=Reflect.construct(e,arguments,o)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===ia(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function i(t,e){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),o.call(this,t,e)}return e=i,Object.defineProperty(e,"prototype",{writable:!1}),e}(oa),la=n(92);function sa(t){return sa="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},sa(t)}function fa(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==sa(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==sa(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===sa(o)?o:String(o)),r)}var o}function pa(t,e){return pa=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},pa(t,e)}function ya(t){return ya=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},ya(t)}var ha="undefined"!=typeof process&&null!=process.versions&&null!=process.versions.node,ba=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&pa(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=ya(r);if(o){var n=ya(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===sa(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e,n){var r;if(function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),!ha)throw new Error("FileStream is only available when running in Node!");var o=la.readFileSync(t,e||"utf-8");return(r=i.call(this,o,n)).fileName=t,r}return e=u,n=[{key:"fromPath",value:function(t,e,n){if(!ha)throw new Error("FileStream is only available when running in Node!");la.readFile(t,e,(function(t,e){var r=null;null!==e&&(r=new oa(e,!0)),n(t,r)}))}}],null&&0,n&&fa(e,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(aa);const va={fromString:function(t){return new oa(t,!0)},fromBlob:function(t,e,n,r){var o=new window.FileReader;o.onload=function(t){var e=new oa(t.target.result,!0);n(e)},o.onerror=r,o.readAsText(t,e)},fromBuffer:function(t,e){return new oa(t.toString(e),!0)},fromPath:function(t,e,n){ba.fromPath(t,e,n)},fromPathSync:function(t,e){return new ba(t,e)}},da={arrayToString:p,stringToCharArray:function(t){for(var e=new Uint16Array(t.length),n=0;n<t.length;n++)e[n]=t.charCodeAt(n);return e}};function ma(t){return ma="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},ma(t)}function ga(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==ma(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==ma(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===ma(o)?o:String(o)),r)}var o}function Sa(t,e,n){return e&&ga(t.prototype,e),n&&ga(t,n),Object.defineProperty(t,"prototype",{writable:!1}),t}function Oa(t){return Oa="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Oa(t)}function wa(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Oa(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Oa(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Oa(o)?o:String(o)),r)}var o}function _a(t,e){return _a=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},_a(t,e)}function Pa(t){return Pa=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Pa(t)}var Ta=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&_a(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Pa(r);if(i){var n=Pa(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Oa(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(e=u.call(this)).tokenSource=t,e.tokens=[],e.index=-1,e.fetchedEOF=!1,e}return e=c,(n=[{key:"mark",value:function(){return 0}},{key:"release",value:function(t){}},{key:"reset",value:function(){this.seek(0)}},{key:"seek",value:function(t){this.lazyInit(),this.index=this.adjustSeekIndex(t)}},{key:"get",value:function(t){return this.lazyInit(),this.tokens[t]}},{key:"consume",value:function(){if(!(this.index>=0&&(this.fetchedEOF?this.index<this.tokens.length-1:this.index<this.tokens.length))&&this.LA(1)===o.EOF)throw"cannot consume EOF";this.sync(this.index+1)&&(this.index=this.adjustSeekIndex(this.index+1))}},{key:"sync",value:function(t){var e=t-this.tokens.length+1;return!(e>0)||this.fetch(e)>=e}},{key:"fetch",value:function(t){if(this.fetchedEOF)return 0;for(var e=0;e<t;e++){var n=this.tokenSource.nextToken();if(n.tokenIndex=this.tokens.length,this.tokens.push(n),n.type===o.EOF)return this.fetchedEOF=!0,e+1}return t}},{key:"getTokens",value:function(t,e,n){if(void 0===n&&(n=null),t<0||e<0)return null;this.lazyInit();var r=[];e>=this.tokens.length&&(e=this.tokens.length-1);for(var i=t;i<e;i++){var u=this.tokens[i];if(u.type===o.EOF)break;(null===n||n.contains(u.type))&&r.push(u)}return r}},{key:"LA",value:function(t){return this.LT(t).type}},{key:"LB",value:function(t){return this.index-t<0?null:this.tokens[this.index-t]}},{key:"LT",value:function(t){if(this.lazyInit(),0===t)return null;if(t<0)return this.LB(-t);var e=this.index+t-1;return this.sync(e),e>=this.tokens.length?this.tokens[this.tokens.length-1]:this.tokens[e]}},{key:"adjustSeekIndex",value:function(t){return t}},{key:"lazyInit",value:function(){-1===this.index&&this.setup()}},{key:"setup",value:function(){this.sync(0),this.index=this.adjustSeekIndex(0)}},{key:"setTokenSource",value:function(t){this.tokenSource=t,this.tokens=[],this.index=-1,this.fetchedEOF=!1}},{key:"nextTokenOnChannel",value:function(t,e){if(this.sync(t),t>=this.tokens.length)return-1;for(var n=this.tokens[t];n.channel!==this.channel;){if(n.type===o.EOF)return-1;t+=1,this.sync(t),n=this.tokens[t]}return t}},{key:"previousTokenOnChannel",value:function(t,e){for(;t>=0&&this.tokens[t].channel!==e;)t-=1;return t}},{key:"getHiddenTokensToRight",value:function(t,e){if(void 0===e&&(e=-1),this.lazyInit(),t<0||t>=this.tokens.length)throw t+" not in 0.."+this.tokens.length-1;var n=this.nextTokenOnChannel(t+1,Bi.DEFAULT_TOKEN_CHANNEL),r=t+1,o=-1===n?this.tokens.length-1:n;return this.filterForChannel(r,o,e)}},{key:"getHiddenTokensToLeft",value:function(t,e){if(void 0===e&&(e=-1),this.lazyInit(),t<0||t>=this.tokens.length)throw t+" not in 0.."+this.tokens.length-1;var n=this.previousTokenOnChannel(t-1,Bi.DEFAULT_TOKEN_CHANNEL);if(n===t-1)return null;var r=n+1,o=t-1;return this.filterForChannel(r,o,e)}},{key:"filterForChannel",value:function(t,e,n){for(var r=[],o=t;o<e+1;o++){var i=this.tokens[o];-1===n?i.channel!==Bi.DEFAULT_TOKEN_CHANNEL&&r.push(i):i.channel===n&&r.push(i)}return 0===r.length?null:r}},{key:"getSourceName",value:function(){return this.tokenSource.getSourceName()}},{key:"getText",value:function(t){this.lazyInit(),this.fill(),t||(t=new L(0,this.tokens.length-1));var e=t.start;e instanceof o&&(e=e.tokenIndex);var n=t.stop;if(n instanceof o&&(n=n.tokenIndex),null===e||null===n||e<0||n<0)return"";n>=this.tokens.length&&(n=this.tokens.length-1);for(var r="",i=e;i<n+1;i++){var u=this.tokens[i];if(u.type===o.EOF)break;r+=u.text}return r}},{key:"fill",value:function(){for(this.lazyInit();1e3===this.fetch(1e3););}}])&&wa(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(Sa((function t(){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t)})));function Ea(t){return Ea="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ea(t)}function ja(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ea(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ea(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ea(o)?o:String(o)),r)}var o}function ka(t,e){return ka=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},ka(t,e)}function xa(t){return xa=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},xa(t)}Object.defineProperty(Ta,"size",{get:function(){return this.tokens.length}});var Ra=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&ka(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=xa(r);if(i){var n=xa(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ea(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(n=u.call(this,t)).channel=void 0===e?o.DEFAULT_CHANNEL:e,n}return e=c,(n=[{key:"adjustSeekIndex",value:function(t){return this.nextTokenOnChannel(t,this.channel)}},{key:"LB",value:function(t){if(0===t||this.index-t<0)return null;for(var e=this.index,n=1;n<=t;)e=this.previousTokenOnChannel(e-1,this.channel),n+=1;return e<0?null:this.tokens[e]}},{key:"LT",value:function(t){if(this.lazyInit(),0===t)return null;if(t<0)return this.LB(-t);for(var e=this.index,n=1;n<t;)this.sync(e+1)&&(e=this.nextTokenOnChannel(e+1,this.channel)),n+=1;return this.tokens[e]}},{key:"getNumberOfOnChannelTokens",value:function(){var t=0;this.fill();for(var e=0;e<this.tokens.length;e++){var n=this.tokens[e];if(n.channel===this.channel&&(t+=1),n.type===o.EOF)break}return t}}])&&ja(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(Ta);function Ca(t){return Ca="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ca(t)}function Aa(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ca(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ca(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ca(o)?o:String(o)),r)}var o}function Na(t,e){return Na=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Na(t,e)}function Ia(t){return Ia=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ia(t)}var La=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Na(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ia(r);if(o){var n=Ia(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ca(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(e=i.call(this)).parser=t,e}return e=u,(n=[{key:"enterEveryRule",value:function(t){console.log("enter   "+this.parser.ruleNames[t.ruleIndex]+", LT(1)="+this.parser._input.LT(1).text)}},{key:"visitTerminal",value:function(t){console.log("consume "+t.symbol+" rule "+this.parser.ruleNames[this.parser._ctx.ruleIndex])}},{key:"exitEveryRule",value:function(t){console.log("exit    "+this.parser.ruleNames[t.ruleIndex]+", LT(1)="+this.parser._input.LT(1).text)}}])&&Aa(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(fc);function Da(t){return Da="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Da(t)}function Fa(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Da(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Da(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Da(o)?o:String(o)),r)}var o}function Ba(t,e){return Ba=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ba(t,e)}function Ma(t){return Ma=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Ma(t)}var Ua=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ba(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Ma(r);if(i){var n=Ma(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Da(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(e=u.call(this))._input=null,e._errHandler=new Gc,e._precedenceStack=[],e._precedenceStack.push(0),e._ctx=null,e.buildParseTrees=!0,e._tracer=null,e._parseListeners=null,e._syntaxErrors=0,e.setInputStream(t),e}return e=c,n=[{key:"reset",value:function(){null!==this._input&&this._input.seek(0),this._errHandler.reset(this),this._ctx=null,this._syntaxErrors=0,this.setTrace(!1),this._precedenceStack=[],this._precedenceStack.push(0),null!==this._interp&&this._interp.reset()}},{key:"match",value:function(t){var e=this.getCurrentToken();return e.type===t?(this._errHandler.reportMatch(this),this.consume()):(e=this._errHandler.recoverInline(this),this.buildParseTrees&&-1===e.tokenIndex&&this._ctx.addErrorNode(e)),e}},{key:"matchWildcard",value:function(){var t=this.getCurrentToken();return t.type>0?(this._errHandler.reportMatch(this),this.consume()):(t=this._errHandler.recoverInline(this),this.buildParseTrees&&-1===t.tokenIndex&&this._ctx.addErrorNode(t)),t}},{key:"getParseListeners",value:function(){return this._parseListeners||[]}},{key:"addParseListener",value:function(t){if(null===t)throw"listener";null===this._parseListeners&&(this._parseListeners=[]),this._parseListeners.push(t)}},{key:"removeParseListener",value:function(t){if(null!==this._parseListeners){var e=this._parseListeners.indexOf(t);e>=0&&this._parseListeners.splice(e,1),0===this._parseListeners.length&&(this._parseListeners=null)}}},{key:"removeParseListeners",value:function(){this._parseListeners=null}},{key:"triggerEnterRuleEvent",value:function(){if(null!==this._parseListeners){var t=this._ctx;this._parseListeners.forEach((function(e){e.enterEveryRule(t),t.enterRule(e)}))}}},{key:"triggerExitRuleEvent",value:function(){if(null!==this._parseListeners){var t=this._ctx;this._parseListeners.slice(0).reverse().forEach((function(e){t.exitRule(e),e.exitEveryRule(t)}))}}},{key:"getTokenFactory",value:function(){return this._input.tokenSource._factory}},{key:"setTokenFactory",value:function(t){this._input.tokenSource._factory=t}},{key:"getATNWithBypassAlts",value:function(){var t=this.getSerializedATN();if(null===t)throw"The current parser does not support an ATN with bypass alternatives.";var e=this.bypassAltsAtnCache[t];if(null===e){var n=new Gr;n.generateRuleBypassTransitions=!0,e=new qo(n).deserialize(t),this.bypassAltsAtnCache[t]=e}return e}},{key:"getInputStream",value:function(){return this.getTokenStream()}},{key:"setInputStream",value:function(t){this.setTokenStream(t)}},{key:"getTokenStream",value:function(){return this._input}},{key:"setTokenStream",value:function(t){this._input=null,this.reset(),this._input=t}},{key:"getCurrentToken",value:function(){return this._input.LT(1)}},{key:"notifyErrorListeners",value:function(t,e,n){n=n||null,null===(e=e||null)&&(e=this.getCurrentToken()),this._syntaxErrors+=1;var r=e.line,o=e.column;this.getErrorListenerDispatch().syntaxError(this,e,r,o,t,n)}},{key:"consume",value:function(){var t=this.getCurrentToken();t.type!==o.EOF&&this.getInputStream().consume();var e,n=null!==this._parseListeners&&this._parseListeners.length>0;return(this.buildParseTrees||n)&&((e=this._errHandler.inErrorRecoveryMode(this)?this._ctx.addErrorNode(t):this._ctx.addTokenNode(t)).invokingState=this.state,n&&this._parseListeners.forEach((function(t){e instanceof Yt||void 0!==e.isErrorNode&&e.isErrorNode()?t.visitErrorNode(e):e instanceof Vt&&t.visitTerminal(e)}))),t}},{key:"addContextToParseTree",value:function(){null!==this._ctx.parentCtx&&this._ctx.parentCtx.addChild(this._ctx)}},{key:"enterRule",value:function(t,e,n){this.state=e,this._ctx=t,this._ctx.start=this._input.LT(1),this.buildParseTrees&&this.addContextToParseTree(),this.triggerEnterRuleEvent()}},{key:"exitRule",value:function(){this._ctx.stop=this._input.LT(-1),this.triggerExitRuleEvent(),this.state=this._ctx.invokingState,this._ctx=this._ctx.parentCtx}},{key:"enterOuterAlt",value:function(t,e){t.setAltNumber(e),this.buildParseTrees&&this._ctx!==t&&null!==this._ctx.parentCtx&&(this._ctx.parentCtx.removeLastChild(),this._ctx.parentCtx.addChild(t)),this._ctx=t}},{key:"getPrecedence",value:function(){return 0===this._precedenceStack.length?-1:this._precedenceStack[this._precedenceStack.length-1]}},{key:"enterRecursionRule",value:function(t,e,n,r){this.state=e,this._precedenceStack.push(r),this._ctx=t,this._ctx.start=this._input.LT(1),this.triggerEnterRuleEvent()}},{key:"pushNewRecursionContext",value:function(t,e,n){var r=this._ctx;r.parentCtx=t,r.invokingState=e,r.stop=this._input.LT(-1),this._ctx=t,this._ctx.start=r.start,this.buildParseTrees&&this._ctx.addChild(r),this.triggerEnterRuleEvent()}},{key:"unrollRecursionContexts",value:function(t){this._precedenceStack.pop(),this._ctx.stop=this._input.LT(-1);var e=this._ctx,n=this.getParseListeners();if(null!==n&&n.length>0)for(;this._ctx!==t;)this.triggerExitRuleEvent(),this._ctx=this._ctx.parentCtx;else this._ctx=t;e.parentCtx=t,this.buildParseTrees&&null!==t&&t.addChild(e)}},{key:"getInvokingContext",value:function(t){for(var e=this._ctx;null!==e;){if(e.ruleIndex===t)return e;e=e.parentCtx}return null}},{key:"precpred",value:function(t,e){return e>=this._precedenceStack[this._precedenceStack.length-1]}},{key:"inContext",value:function(t){return!1}},{key:"isExpectedToken",value:function(t){var e=this._interp.atn,n=this._ctx,r=e.states[this.state],i=e.nextTokens(r);if(i.contains(t))return!0;if(!i.contains(o.EPSILON))return!1;for(;null!==n&&n.invokingState>=0&&i.contains(o.EPSILON);){var u=e.states[n.invokingState].transitions[0];if((i=e.nextTokens(u.followState)).contains(t))return!0;n=n.parentCtx}return!(!i.contains(o.EPSILON)||t!==o.EOF)}},{key:"getExpectedTokens",value:function(){return this._interp.atn.getExpectedTokens(this.state,this._ctx)}},{key:"getExpectedTokensWithinCurrentRule",value:function(){var t=this._interp.atn,e=t.states[this.state];return t.nextTokens(e)}},{key:"getRuleIndex",value:function(t){var e=this.getRuleIndexMap()[t];return null!==e?e:-1}},{key:"getRuleInvocationStack",value:function(t){null===(t=t||null)&&(t=this._ctx);for(var e=[];null!==t;){var n=t.ruleIndex;n<0?e.push("n/a"):e.push(this.ruleNames[n]),t=t.parentCtx}return e}},{key:"getDFAStrings",value:function(){return this._interp.decisionToDFA.toString()}},{key:"dumpDFA",value:function(){for(var t=!1,e=0;e<this._interp.decisionToDFA.length;e++){var n=this._interp.decisionToDFA[e];n.states.length>0&&(t&&console.log(),this.printer.println("Decision "+n.decision+":"),this.printer.print(n.toString(this.literalNames,this.symbolicNames)),t=!0)}}},{key:"getSourceName",value:function(){return this._input.sourceName}},{key:"setTrace",value:function(t){t?(null!==this._tracer&&this.removeParseListener(this._tracer),this._tracer=new La(this),this.addParseListener(this._tracer)):(this.removeParseListener(this._tracer),this._tracer=null)}}],n&&Fa(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(ui);function Va(t){return Va="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Va(t)}function qa(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Va(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Va(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Va(o)?o:String(o)),r)}var o}function Ha(t,e){return Ha=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ha(t,e)}function za(t){return za=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},za(t)}Ua.bypassAltsAtnCache={};var Ya=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Ha(t,e)}(c,t);var e,n,r,i,u=(r=c,i=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=za(r);if(i){var n=za(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Va(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function c(t){var e;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,c),(e=u.call(this)).parentCtx=null,e.symbol=t,e}return e=c,(n=[{key:"getChild",value:function(t){return null}},{key:"getSymbol",value:function(){return this.symbol}},{key:"getParent",value:function(){return this.parentCtx}},{key:"getPayload",value:function(){return this.symbol}},{key:"getSourceInterval",value:function(){if(null===this.symbol)return L.INVALID_INTERVAL;var t=this.symbol.tokenIndex;return new L(t,t)}},{key:"getChildCount",value:function(){return 0}},{key:"accept",value:function(t){return t.visitTerminal(this)}},{key:"getText",value:function(){return this.symbol.text}},{key:"toString",value:function(){return this.symbol.type===o.EOF?"<EOF>":this.symbol.text}}])&&qa(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),c}(Vt);function Ka(t){return Ka="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},Ka(t)}function Ga(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==Ka(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==Ka(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===Ka(o)?o:String(o)),r)}var o}function Wa(t,e){return Wa=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Wa(t,e)}function Xa(t){return Xa=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},Xa(t)}var Ja=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Wa(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=Xa(r);if(o){var n=Xa(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===Ka(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t){return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),i.call(this,t)}return e=u,(n=[{key:"isErrorNode",value:function(){return!0}},{key:"accept",value:function(t){return t.visitErrorNode(this)}}])&&Ga(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Ya);function $a(t){return $a="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},$a(t)}function Za(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,(void 0,o=function(t,e){if("object"!==$a(t)||null===t)return t;var n=t[Symbol.toPrimitive];if(void 0!==n){var r=n.call(t,"string");if("object"!==$a(r))return r;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(t)}(r.key),"symbol"===$a(o)?o:String(o)),r)}var o}function Qa(t,e){return Qa=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Qa(t,e)}function tl(t){return tl=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(t){return t.__proto__||Object.getPrototypeOf(t)},tl(t)}var el=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),Object.defineProperty(t,"prototype",{writable:!1}),e&&Qa(t,e)}(u,t);var e,n,r,o,i=(r=u,o=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],(function(){}))),!0}catch(t){return!1}}(),function(){var t,e=tl(r);if(o){var n=tl(this).constructor;t=Reflect.construct(e,arguments,n)}else t=e.apply(this,arguments);return function(t,e){if(e&&("object"===$a(e)||"function"==typeof e))return e;if(void 0!==e)throw new TypeError("Derived constructors may only return object or undefined");return function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t)}(this,t)});function u(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,u),(n=i.call(this,t,e)).children=null,n.start=null,n.stop=null,n.exception=null,n}return e=u,(n=[{key:"copyFrom",value:function(t){this.parentCtx=t.parentCtx,this.invokingState=t.invokingState,this.children=null,this.start=t.start,this.stop=t.stop,t.children&&(this.children=[],t.children.map((function(t){t instanceof Ja&&(this.children.push(t),t.parentCtx=this)}),this))}},{key:"enterRule",value:function(t){}},{key:"exitRule",value:function(t){}},{key:"addChild",value:function(t){return null===this.children&&(this.children=[]),this.children.push(t),t}},{key:"removeLastChild",value:function(){null!==this.children&&this.children.pop()}},{key:"addTokenNode",value:function(t){var e=new Ya(t);return this.addChild(e),e.parentCtx=this,e}},{key:"addErrorNode",value:function(t){var e=new Ja(t);return this.addChild(e),e.parentCtx=this,e}},{key:"getChild",value:function(t,e){if(e=e||null,null===this.children||t<0||t>=this.children.length)return null;if(null===e)return this.children[t];for(var n=0;n<this.children.length;n++){var r=this.children[n];if(r instanceof e){if(0===t)return r;t-=1}}return null}},{key:"getToken",value:function(t,e){if(null===this.children||e<0||e>=this.children.length)return null;for(var n=0;n<this.children.length;n++){var r=this.children[n];if(r instanceof Vt&&r.symbol.type===t){if(0===e)return r;e-=1}}return null}},{key:"getTokens",value:function(t){if(null===this.children)return[];for(var e=[],n=0;n<this.children.length;n++){var r=this.children[n];r instanceof Vt&&r.symbol.type===t&&e.push(r)}return e}},{key:"getTypedRuleContext",value:function(t,e){return this.getChild(e,t)}},{key:"getTypedRuleContexts",value:function(t){if(null===this.children)return[];for(var e=[],n=0;n<this.children.length;n++){var r=this.children[n];r instanceof t&&e.push(r)}return e}},{key:"getChildCount",value:function(){return null===this.children?0:this.children.length}},{key:"getSourceInterval",value:function(){return null===this.start||null===this.stop?L.INVALID_INTERVAL:new L(this.start.tokenIndex,this.stop.tokenIndex)}}])&&Za(e.prototype,n),Object.defineProperty(e,"prototype",{writable:!1}),u}(Zt);Zt.EMPTY=new el;var nl=Math.round(Math.random()*Math.pow(2,32));String.prototype.seed=nl,String.prototype.hashCode=function(){for(var t,e,n=this.toString(),r=3&n.length,o=n.length-r,i=String.prototype.seed,u=3432918353,c=461845907,a=0;a<o;)e=255&n.charCodeAt(a)|(255&n.charCodeAt(++a))<<8|(255&n.charCodeAt(++a))<<16|(255&n.charCodeAt(++a))<<24,++a,i=27492+(65535&(t=5*(65535&(i=(i^=e=(65535&(e=(e=(65535&e)*u+(((e>>>16)*u&65535)<<16)&4294967295)<<15|e>>>17))*c+(((e>>>16)*c&65535)<<16)&4294967295)<<13|i>>>19))+((5*(i>>>16)&65535)<<16)&4294967295))+((58964+(t>>>16)&65535)<<16);switch(e=0,r){case 3:e^=(255&n.charCodeAt(a+2))<<16;case 2:e^=(255&n.charCodeAt(a+1))<<8;case 1:i^=e=(65535&(e=(e=(65535&(e^=255&n.charCodeAt(a)))*u+(((e>>>16)*u&65535)<<16)&4294967295)<<15|e>>>17))*c+(((e>>>16)*c&65535)<<16)&4294967295}return i^=n.length,i=2246822507*(65535&(i^=i>>>16))+((2246822507*(i>>>16)&65535)<<16)&4294967295,i=3266489909*(65535&(i^=i>>>13))+((3266489909*(i>>>16)&65535)<<16)&4294967295,(i^=i>>>16)>>>0};const rl={atn:Wu,dfa:uc,context:cc,misc:ac,tree:mc,error:Qc,Token:o,CommonToken:fi,CharStreams:va,CharStream:aa,InputStream:aa,CommonTokenStream:Ra,Lexer:Bi,Parser:Ua,ParserRuleContext:el,Interval:L,IntervalSet:B,LL1Analyzer:Ce,Utils:da}})();var o=r.dx,i=r.q2,u=r.FO,c=r.xf,a=r.Gy,l=r.s4,s=r.c7,f=r._7,p=r.gp,y=r.cK,h=r.zs,b=r.AV,v=r.Xp,d=r.VS,m=r.ul,g=r.hW,S=r.x1,O=r.z5,w=r.oN,_=r.TB,P=r.u1,T=r._b,E=r.$F,j=r._T,k=r.db,x=r.Zx,R=r._x,C=r.r8,A=r.JI,N=r.TP,I=r.WU,L=r.Nj,D=r.ZP;
//# sourceMappingURL=antlr4.web.js.map

/***/ }),

/***/ "./node_modules/uvl-parser/index.js":
/*!******************************************!*\
  !*** ./node_modules/uvl-parser/index.js ***!
  \******************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   FeatureModel: () => (/* reexport safe */ _src_FeatureModel_js__WEBPACK_IMPORTED_MODULE_0__["default"]),
/* harmony export */   UVLJavaScriptParser: () => (/* reexport safe */ _src_lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__["default"])
/* harmony export */ });
/* harmony import */ var _src_FeatureModel_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./src/FeatureModel.js */ "./node_modules/uvl-parser/src/FeatureModel.js");
/* harmony import */ var _src_lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./src/lib/UVLJavaScriptParser.js */ "./node_modules/uvl-parser/src/lib/UVLJavaScriptParser.js");






/***/ }),

/***/ "./node_modules/uvl-parser/src/FeatureModel.js":
/*!*****************************************************!*\
  !*** ./node_modules/uvl-parser/src/FeatureModel.js ***!
  \*****************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   UVLJavaScriptParser: () => (/* reexport safe */ _lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__["default"]),
/* harmony export */   "default": () => (/* binding */ FeatureModel)
/* harmony export */ });
/* harmony import */ var _UVLJavaScriptCustomLexer_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./UVLJavaScriptCustomLexer.js */ "./node_modules/uvl-parser/src/UVLJavaScriptCustomLexer.js");
/* harmony import */ var _lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./lib/UVLJavaScriptParser.js */ "./node_modules/uvl-parser/src/lib/UVLJavaScriptParser.js");
/* harmony import */ var _errors_ErrorListener_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./errors/ErrorListener.js */ "./node_modules/uvl-parser/src/errors/ErrorListener.js");
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");
/* harmony import */ var fs__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! fs */ "?025b");









class FeatureModel {

  constructor(param) {
    this.featureModel = '';
    let chars = '';
    if (this.isFile(param)) {
      chars = new antlr4__WEBPACK_IMPORTED_MODULE_3__["default"].FileStream(param);
    } else {
      chars = antlr4__WEBPACK_IMPORTED_MODULE_3__["default"].CharStreams.fromString(param);
    }
    this.getTree(chars);
  }

  isFile(str) {
    try {
      return fs__WEBPACK_IMPORTED_MODULE_4__.statSync(str);
    } catch (e) {
      console.error('Error: ' + e);
      return false;
    }
  }

  getTree(chars) {
    const lexer = new _UVLJavaScriptCustomLexer_js__WEBPACK_IMPORTED_MODULE_0__["default"](chars);
    const tokens = new antlr4__WEBPACK_IMPORTED_MODULE_3__["default"].CommonTokenStream(lexer);
    const errorListener = new _errors_ErrorListener_js__WEBPACK_IMPORTED_MODULE_2__["default"]();
    let parser = new _lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__["default"](tokens);
    parser.removeErrorListeners();
    parser.addErrorListener(errorListener);
    const tree = parser.featureModel();
    this.featureModel = tree;
  }

  getFeatureModel() {
    return this.featureModel;
  }

  toString() {
    return this.featureModel.getText();
  }
}





/***/ }),

/***/ "./node_modules/uvl-parser/src/UVLJavaScriptCustomLexer.js":
/*!*****************************************************************!*\
  !*** ./node_modules/uvl-parser/src/UVLJavaScriptCustomLexer.js ***!
  \*****************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ UVLJavaScriptCustomLexer)
/* harmony export */ });
/* harmony import */ var _lib_UVLJavaScriptLexer_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./lib/UVLJavaScriptLexer.js */ "./node_modules/uvl-parser/src/lib/UVLJavaScriptLexer.js");
/* harmony import */ var _lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./lib/UVLJavaScriptParser.js */ "./node_modules/uvl-parser/src/lib/UVLJavaScriptParser.js");
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");




class UVLJavaScriptCustomLexer extends _lib_UVLJavaScriptLexer_js__WEBPACK_IMPORTED_MODULE_0__["default"] {

    constructor(input_stream) {
        super(input_stream);
        this.tokens = [];
        this.indents = [];
        this.opened = 0;
        this.lastToken = null;
    }

    emitToken(t) {
        super.emitToken(t);
        this.tokens.push(t);
    }

    nextToken() {
        if (this._input.LA(1) === antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].Token.EOF && this.indents.length !== 0) {
            while (this.tokens.length > 0 && this.tokens[this.tokens.length - 1].type === antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].Token.EOF) {
                this.tokens.pop();
            }

            this.emitToken(this.commonToken(_lib_UVLJavaScriptLexer_js__WEBPACK_IMPORTED_MODULE_0__["default"].NEWLINE, "\n"));

            while (this.indents.length !== 0) {
                this.emitToken(this.createDedent());
                this.indents.pop();
            }

            this.emitToken(this.commonToken(antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].Token.EOF, "<EOF>"));
        }

        const nextToken = super.nextToken();

        if (nextToken.channel === antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].Token.DEFAULT_CHANNEL) {
            this.lastToken = nextToken;
        }

        return this.tokens.length > 0 ? this.tokens.shift() : nextToken;
    }

    createDedent() {
        const dedent = this.commonToken(_lib_UVLJavaScriptLexer_js__WEBPACK_IMPORTED_MODULE_0__["default"].DEDENT, "");
        dedent.line = this.lastToken.line;
        return dedent;
    }

    commonToken(type, text) {
        const stop = this.getCharIndex() - 1;
        const start = text ? stop - text.length + 1 : stop;
        return new antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].CommonToken(this._tokenFactorySourcePair, type, antlr4__WEBPACK_IMPORTED_MODULE_2__["default"].Token.DEFAULT_CHANNEL, start, stop);
    }

    static getIndentationCount(spaces) {
        let count = 0;
        for (const ch of spaces) {
            if (ch === '\t') {
                count += 8 - (count % 8);
            } else {
                count += 1;
            }
        }
        return count;
    }

    skipToken() {
        this.skip();
    }

    atStartOfInput() {
        return this._interp.column === 0 && this._interp.line === 1;
    }

    handleNewline() {
        const newLine = this._interp.getText(this._input).replace(/[^\r\n\f]+/g, "");
        const spaces = this._interp.getText(this._input).replace(/[\r\n\f]+/g, "");
        const next = String.fromCharCode(this._input.LA(1));

        if (this.opened > 0 || next === '\r' || next === '\n' || next === '\f' || next === '#') {
            this.skip();
        } else {
            this.emitToken(this.commonToken(_lib_UVLJavaScriptLexer_js__WEBPACK_IMPORTED_MODULE_0__["default"].NEWLINE, newLine));

            const indent = UVLJavaScriptCustomLexer.getIndentationCount(spaces);
            const previous = this.indents.length === 0 ? 0 : this.indents[this.indents.length - 1];

            if (indent === previous) {
                this.skip();
            } else if (indent > previous) {
                this.indents.push(indent);
                this.emitToken(this.commonToken(_lib_UVLJavaScriptParser_js__WEBPACK_IMPORTED_MODULE_1__["default"].INDENT, spaces));
            } else {
                while (this.indents.length > 0 && this.indents[this.indents.length - 1] > indent) {
                    this.emitToken(this.createDedent());
                    this.indents.pop();
                }
            }
        }
    }
}


/***/ }),

/***/ "./node_modules/uvl-parser/src/errors/ErrorListener.js":
/*!*************************************************************!*\
  !*** ./node_modules/uvl-parser/src/errors/ErrorListener.js ***!
  \*************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");
/* harmony import */ var _SyntaxGenericError_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./SyntaxGenericError.js */ "./node_modules/uvl-parser/src/errors/SyntaxGenericError.js");




/**
 * Custom Error Listener
 *
 * @returns {object}
 */
class ErrorListener extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.ErrorListener {
  /**
   * Checks syntax error
   *
   * @param {object} recognizer The parsing support code essentially. Most of it is error recovery stuff
   * @param {object} symbol Offending symbol
   * @param {int} line Line of offending symbol
   * @param {int} column Position in line of offending symbol
   * @param {string} message Error message
   * @param {string} payload Stack trace
   */
  syntaxError(recognizer, symbol, line, column, message) {
    throw new _SyntaxGenericError_js__WEBPACK_IMPORTED_MODULE_1__["default"]({ line, column, message });
  }
}

/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (ErrorListener);


/***/ }),

/***/ "./node_modules/uvl-parser/src/errors/SyntaxGenericError.js":
/*!******************************************************************!*\
  !*** ./node_modules/uvl-parser/src/errors/SyntaxGenericError.js ***!
  \******************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ SyntaxGenericError)
/* harmony export */ });
class SyntaxGenericError extends Error {
  constructor(payload) {
    super(payload);

    this.code = "E_SYNTAX_GENERIC";
    this.message = "Something went wrong";

    if (typeof payload !== "undefined") {
      this.message = payload.message || this.message;
      this.payload = payload;
    }

    console.error(
      `line ${this.payload.line}, col ${this.payload.column}: ${this.payload.message}`,
    );
    Error.captureStackTrace(this, SyntaxGenericError);
  }
}


/***/ }),

/***/ "./node_modules/uvl-parser/src/lib/UVLJavaScriptLexer.js":
/*!***************************************************************!*\
  !*** ./node_modules/uvl-parser/src/lib/UVLJavaScriptLexer.js ***!
  \***************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ UVLJavaScriptLexer)
/* harmony export */ });
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");
// Generated from ../uvl/UVLJavaScript.g4 by ANTLR 4.13.2
// jshint ignore: start



const serializedATN = [4,0,63,590,6,-1,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,
4,7,4,2,5,7,5,2,6,7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,
12,2,13,7,13,2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,
2,20,7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,2,
27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,7,33,2,34,
7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,39,2,40,7,40,2,41,7,
41,2,42,7,42,2,43,7,43,2,44,7,44,2,45,7,45,2,46,7,46,2,47,7,47,2,48,7,48,
2,49,7,49,2,50,7,50,2,51,7,51,2,52,7,52,2,53,7,53,2,54,7,54,2,55,7,55,2,
56,7,56,2,57,7,57,2,58,7,58,2,59,7,59,2,60,7,60,2,61,7,61,2,62,7,62,2,63,
7,63,2,64,7,64,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,
1,1,1,1,1,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,3,1,3,1,3,1,4,1,4,1,4,1,
4,1,4,1,4,1,4,1,4,1,4,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,5,1,
6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,
7,1,7,1,7,1,7,1,7,1,8,1,8,1,8,1,8,1,9,1,9,1,9,1,9,1,10,1,10,1,10,1,10,1,
11,1,11,1,11,1,11,1,11,1,11,1,12,1,12,1,12,1,12,1,12,1,13,1,13,1,14,1,14,
1,14,1,14,1,14,1,14,1,14,1,15,1,15,1,15,1,15,1,15,1,15,1,15,1,15,1,16,1,
16,1,16,1,16,1,16,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,
1,18,1,18,1,18,1,18,1,18,1,19,1,19,1,19,1,19,1,19,1,19,1,19,1,19,1,19,1,
19,1,19,1,19,1,19,1,19,1,19,1,19,1,19,1,19,1,20,1,20,1,20,1,20,1,20,1,20,
1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,
21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,
1,21,1,21,1,21,1,21,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,
22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,23,1,23,1,23,1,24,1,24,1,24,
1,25,1,25,1,25,1,26,1,26,1,26,1,27,1,27,1,27,1,28,1,28,1,28,1,29,1,29,1,
29,1,29,1,29,1,30,1,30,1,30,1,30,1,30,1,31,1,31,1,31,3,31,373,8,31,1,31,
1,31,3,31,377,8,31,1,31,3,31,380,8,31,3,31,382,8,31,1,31,1,31,1,32,1,32,
1,32,1,32,1,32,1,32,1,32,1,32,1,32,1,33,1,33,1,33,1,33,1,33,1,33,1,33,1,
33,1,33,1,34,1,34,1,34,1,35,1,35,1,35,1,35,1,35,1,35,1,35,1,35,1,35,1,35,
1,35,1,35,1,36,1,36,1,36,1,36,1,36,1,36,1,36,1,36,1,36,1,37,1,37,1,37,1,
37,1,37,1,37,1,37,1,37,1,37,1,37,1,38,1,38,1,38,1,38,1,38,1,38,1,38,3,38,
445,8,38,3,38,447,8,38,1,38,1,38,1,39,1,39,1,40,1,40,1,41,1,41,1,42,1,42,
1,42,1,42,1,43,1,43,1,43,1,44,1,44,1,44,1,45,1,45,1,46,1,46,1,46,1,47,1,
47,1,48,1,48,1,48,1,49,1,49,1,49,1,50,1,50,1,51,1,51,1,52,1,52,1,53,1,53,
1,54,3,54,489,8,54,1,54,5,54,492,8,54,10,54,12,54,495,9,54,1,54,1,54,4,54,
499,8,54,11,54,12,54,500,1,55,1,55,3,55,505,8,55,1,55,1,55,5,55,509,8,55,
10,55,12,55,512,9,55,3,55,514,8,55,1,56,1,56,1,56,1,56,1,56,1,56,1,56,1,
56,1,56,3,56,525,8,56,1,57,1,57,1,57,1,57,1,57,1,57,1,57,1,57,1,58,1,58,
1,59,1,59,4,59,539,8,59,11,59,12,59,540,1,59,1,59,1,60,1,60,5,60,547,8,60,
10,60,12,60,550,9,60,1,61,1,61,4,61,554,8,61,11,61,12,61,555,1,61,1,61,1,
62,1,62,3,62,562,8,62,1,62,1,62,1,63,1,63,1,63,1,63,5,63,570,8,63,10,63,
12,63,573,9,63,1,63,1,63,5,63,577,8,63,10,63,12,63,580,9,63,1,63,1,63,3,
63,584,8,63,1,64,4,64,587,8,64,11,64,12,64,588,0,0,65,1,1,3,2,5,3,7,4,9,
5,11,6,13,7,15,8,17,9,19,10,21,11,23,12,25,13,27,14,29,15,31,16,33,17,35,
18,37,19,39,20,41,21,43,22,45,23,47,24,49,25,51,26,53,27,55,28,57,29,59,
30,61,31,63,32,65,33,67,34,69,35,71,36,73,37,75,38,77,39,79,40,81,41,83,
42,85,43,87,44,89,45,91,46,93,47,95,48,97,49,99,50,101,51,103,52,105,53,
107,54,109,55,111,56,113,57,115,58,117,59,119,60,121,61,123,62,125,63,127,
0,129,0,1,0,9,1,0,48,57,1,0,46,46,1,0,49,57,4,0,10,10,13,13,34,34,46,46,
2,0,65,90,97,122,15,0,35,35,37,37,39,39,48,57,59,59,63,63,65,90,92,92,95,
95,97,122,167,167,223,223,228,228,246,246,252,252,4,0,10,10,13,13,39,39,
46,46,2,0,10,10,12,13,2,0,9,9,32,32,608,0,1,1,0,0,0,0,3,1,0,0,0,0,5,1,0,
0,0,0,7,1,0,0,0,0,9,1,0,0,0,0,11,1,0,0,0,0,13,1,0,0,0,0,15,1,0,0,0,0,17,
1,0,0,0,0,19,1,0,0,0,0,21,1,0,0,0,0,23,1,0,0,0,0,25,1,0,0,0,0,27,1,0,0,0,
0,29,1,0,0,0,0,31,1,0,0,0,0,33,1,0,0,0,0,35,1,0,0,0,0,37,1,0,0,0,0,39,1,
0,0,0,0,41,1,0,0,0,0,43,1,0,0,0,0,45,1,0,0,0,0,47,1,0,0,0,0,49,1,0,0,0,0,
51,1,0,0,0,0,53,1,0,0,0,0,55,1,0,0,0,0,57,1,0,0,0,0,59,1,0,0,0,0,61,1,0,
0,0,0,63,1,0,0,0,0,65,1,0,0,0,0,67,1,0,0,0,0,69,1,0,0,0,0,71,1,0,0,0,0,73,
1,0,0,0,0,75,1,0,0,0,0,77,1,0,0,0,0,79,1,0,0,0,0,81,1,0,0,0,0,83,1,0,0,0,
0,85,1,0,0,0,0,87,1,0,0,0,0,89,1,0,0,0,0,91,1,0,0,0,0,93,1,0,0,0,0,95,1,
0,0,0,0,97,1,0,0,0,0,99,1,0,0,0,0,101,1,0,0,0,0,103,1,0,0,0,0,105,1,0,0,
0,0,107,1,0,0,0,0,109,1,0,0,0,0,111,1,0,0,0,0,113,1,0,0,0,0,115,1,0,0,0,
0,117,1,0,0,0,0,119,1,0,0,0,0,121,1,0,0,0,0,123,1,0,0,0,0,125,1,0,0,0,1,
131,1,0,0,0,3,139,1,0,0,0,5,149,1,0,0,0,7,157,1,0,0,0,9,160,1,0,0,0,11,169,
1,0,0,0,13,181,1,0,0,0,15,192,1,0,0,0,17,204,1,0,0,0,19,208,1,0,0,0,21,212,
1,0,0,0,23,216,1,0,0,0,25,222,1,0,0,0,27,227,1,0,0,0,29,229,1,0,0,0,31,236,
1,0,0,0,33,244,1,0,0,0,35,249,1,0,0,0,37,260,1,0,0,0,39,265,1,0,0,0,41,283,
1,0,0,0,43,303,1,0,0,0,45,322,1,0,0,0,47,341,1,0,0,0,49,344,1,0,0,0,51,347,
1,0,0,0,53,350,1,0,0,0,55,353,1,0,0,0,57,356,1,0,0,0,59,359,1,0,0,0,61,364,
1,0,0,0,63,381,1,0,0,0,65,385,1,0,0,0,67,394,1,0,0,0,69,403,1,0,0,0,71,406,
1,0,0,0,73,418,1,0,0,0,75,427,1,0,0,0,77,437,1,0,0,0,79,450,1,0,0,0,81,452,
1,0,0,0,83,454,1,0,0,0,85,456,1,0,0,0,87,460,1,0,0,0,89,463,1,0,0,0,91,466,
1,0,0,0,93,468,1,0,0,0,95,471,1,0,0,0,97,473,1,0,0,0,99,476,1,0,0,0,101,
479,1,0,0,0,103,481,1,0,0,0,105,483,1,0,0,0,107,485,1,0,0,0,109,488,1,0,
0,0,111,513,1,0,0,0,113,524,1,0,0,0,115,526,1,0,0,0,117,534,1,0,0,0,119,
536,1,0,0,0,121,544,1,0,0,0,123,551,1,0,0,0,125,561,1,0,0,0,127,583,1,0,
0,0,129,586,1,0,0,0,131,132,5,105,0,0,132,133,5,110,0,0,133,134,5,99,0,0,
134,135,5,108,0,0,135,136,5,117,0,0,136,137,5,100,0,0,137,138,5,101,0,0,
138,2,1,0,0,0,139,140,5,110,0,0,140,141,5,97,0,0,141,142,5,109,0,0,142,143,
5,101,0,0,143,144,5,115,0,0,144,145,5,112,0,0,145,146,5,97,0,0,146,147,5,
99,0,0,147,148,5,101,0,0,148,4,1,0,0,0,149,150,5,105,0,0,150,151,5,109,0,
0,151,152,5,112,0,0,152,153,5,111,0,0,153,154,5,114,0,0,154,155,5,116,0,
0,155,156,5,115,0,0,156,6,1,0,0,0,157,158,5,97,0,0,158,159,5,115,0,0,159,
8,1,0,0,0,160,161,5,102,0,0,161,162,5,101,0,0,162,163,5,97,0,0,163,164,5,
116,0,0,164,165,5,117,0,0,165,166,5,114,0,0,166,167,5,101,0,0,167,168,5,
115,0,0,168,10,1,0,0,0,169,170,5,99,0,0,170,171,5,97,0,0,171,172,5,114,0,
0,172,173,5,100,0,0,173,174,5,105,0,0,174,175,5,110,0,0,175,176,5,97,0,0,
176,177,5,108,0,0,177,178,5,105,0,0,178,179,5,116,0,0,179,180,5,121,0,0,
180,12,1,0,0,0,181,182,5,99,0,0,182,183,5,111,0,0,183,184,5,110,0,0,184,
185,5,115,0,0,185,186,5,116,0,0,186,187,5,114,0,0,187,188,5,97,0,0,188,189,
5,105,0,0,189,190,5,110,0,0,190,191,5,116,0,0,191,14,1,0,0,0,192,193,5,99,
0,0,193,194,5,111,0,0,194,195,5,110,0,0,195,196,5,115,0,0,196,197,5,116,
0,0,197,198,5,114,0,0,198,199,5,97,0,0,199,200,5,105,0,0,200,201,5,110,0,
0,201,202,5,116,0,0,202,203,5,115,0,0,203,16,1,0,0,0,204,205,5,115,0,0,205,
206,5,117,0,0,206,207,5,109,0,0,207,18,1,0,0,0,208,209,5,97,0,0,209,210,
5,118,0,0,210,211,5,103,0,0,211,20,1,0,0,0,212,213,5,108,0,0,213,214,5,101,
0,0,214,215,5,110,0,0,215,22,1,0,0,0,216,217,5,102,0,0,217,218,5,108,0,0,
218,219,5,111,0,0,219,220,5,111,0,0,220,221,5,114,0,0,221,24,1,0,0,0,222,
223,5,99,0,0,223,224,5,101,0,0,224,225,5,105,0,0,225,226,5,108,0,0,226,26,
1,0,0,0,227,228,5,46,0,0,228,28,1,0,0,0,229,230,5,83,0,0,230,231,5,116,0,
0,231,232,5,114,0,0,232,233,5,105,0,0,233,234,5,110,0,0,234,235,5,103,0,
0,235,30,1,0,0,0,236,237,5,73,0,0,237,238,5,110,0,0,238,239,5,116,0,0,239,
240,5,101,0,0,240,241,5,103,0,0,241,242,5,101,0,0,242,243,5,114,0,0,243,
32,1,0,0,0,244,245,5,82,0,0,245,246,5,101,0,0,246,247,5,97,0,0,247,248,5,
108,0,0,248,34,1,0,0,0,249,250,5,65,0,0,250,251,5,114,0,0,251,252,5,105,
0,0,252,253,5,116,0,0,253,254,5,104,0,0,254,255,5,109,0,0,255,256,5,101,
0,0,256,257,5,116,0,0,257,258,5,105,0,0,258,259,5,99,0,0,259,36,1,0,0,0,
260,261,5,84,0,0,261,262,5,121,0,0,262,263,5,112,0,0,263,264,5,101,0,0,264,
38,1,0,0,0,265,266,5,103,0,0,266,267,5,114,0,0,267,268,5,111,0,0,268,269,
5,117,0,0,269,270,5,112,0,0,270,271,5,45,0,0,271,272,5,99,0,0,272,273,5,
97,0,0,273,274,5,114,0,0,274,275,5,100,0,0,275,276,5,105,0,0,276,277,5,110,
0,0,277,278,5,97,0,0,278,279,5,108,0,0,279,280,5,105,0,0,280,281,5,116,0,
0,281,282,5,121,0,0,282,40,1,0,0,0,283,284,5,102,0,0,284,285,5,101,0,0,285,
286,5,97,0,0,286,287,5,116,0,0,287,288,5,117,0,0,288,289,5,114,0,0,289,290,
5,101,0,0,290,291,5,45,0,0,291,292,5,99,0,0,292,293,5,97,0,0,293,294,5,114,
0,0,294,295,5,100,0,0,295,296,5,105,0,0,296,297,5,110,0,0,297,298,5,97,0,
0,298,299,5,108,0,0,299,300,5,105,0,0,300,301,5,116,0,0,301,302,5,121,0,
0,302,42,1,0,0,0,303,304,5,97,0,0,304,305,5,103,0,0,305,306,5,103,0,0,306,
307,5,114,0,0,307,308,5,101,0,0,308,309,5,103,0,0,309,310,5,97,0,0,310,311,
5,116,0,0,311,312,5,101,0,0,312,313,5,45,0,0,313,314,5,102,0,0,314,315,5,
117,0,0,315,316,5,110,0,0,316,317,5,99,0,0,317,318,5,116,0,0,318,319,5,105,
0,0,319,320,5,111,0,0,320,321,5,110,0,0,321,44,1,0,0,0,322,323,5,115,0,0,
323,324,5,116,0,0,324,325,5,114,0,0,325,326,5,105,0,0,326,327,5,110,0,0,
327,328,5,103,0,0,328,329,5,45,0,0,329,330,5,99,0,0,330,331,5,111,0,0,331,
332,5,110,0,0,332,333,5,115,0,0,333,334,5,116,0,0,334,335,5,114,0,0,335,
336,5,97,0,0,336,337,5,105,0,0,337,338,5,110,0,0,338,339,5,116,0,0,339,340,
5,115,0,0,340,46,1,0,0,0,341,342,5,40,0,0,342,343,6,23,0,0,343,48,1,0,0,
0,344,345,5,41,0,0,345,346,6,24,1,0,346,50,1,0,0,0,347,348,5,91,0,0,348,
349,6,25,2,0,349,52,1,0,0,0,350,351,5,93,0,0,351,352,6,26,3,0,352,54,1,0,
0,0,353,354,5,123,0,0,354,355,6,27,4,0,355,56,1,0,0,0,356,357,5,125,0,0,
357,358,6,28,5,0,358,58,1,0,0,0,359,360,5,47,0,0,360,361,5,42,0,0,361,362,
1,0,0,0,362,363,6,29,6,0,363,60,1,0,0,0,364,365,5,42,0,0,365,366,5,47,0,
0,366,367,1,0,0,0,367,368,6,30,7,0,368,62,1,0,0,0,369,370,4,31,0,0,370,382,
3,129,64,0,371,373,5,13,0,0,372,371,1,0,0,0,372,373,1,0,0,0,373,374,1,0,
0,0,374,377,5,10,0,0,375,377,5,13,0,0,376,372,1,0,0,0,376,375,1,0,0,0,377,
379,1,0,0,0,378,380,3,129,64,0,379,378,1,0,0,0,379,380,1,0,0,0,380,382,1,
0,0,0,381,369,1,0,0,0,381,376,1,0,0,0,382,383,1,0,0,0,383,384,6,31,8,0,384,
64,1,0,0,0,385,386,5,60,0,0,386,387,5,73,0,0,387,388,5,78,0,0,388,389,5,
68,0,0,389,390,5,69,0,0,390,391,5,78,0,0,391,392,5,84,0,0,392,393,5,62,0,
0,393,66,1,0,0,0,394,395,5,60,0,0,395,396,5,68,0,0,396,397,5,69,0,0,397,
398,5,68,0,0,398,399,5,69,0,0,399,400,5,78,0,0,400,401,5,84,0,0,401,402,
5,62,0,0,402,68,1,0,0,0,403,404,5,111,0,0,404,405,5,114,0,0,405,70,1,0,0,
0,406,407,5,97,0,0,407,408,5,108,0,0,408,409,5,116,0,0,409,410,5,101,0,0,
410,411,5,114,0,0,411,412,5,110,0,0,412,413,5,97,0,0,413,414,5,116,0,0,414,
415,5,105,0,0,415,416,5,118,0,0,416,417,5,101,0,0,417,72,1,0,0,0,418,419,
5,111,0,0,419,420,5,112,0,0,420,421,5,116,0,0,421,422,5,105,0,0,422,423,
5,111,0,0,423,424,5,110,0,0,424,425,5,97,0,0,425,426,5,108,0,0,426,74,1,
0,0,0,427,428,5,109,0,0,428,429,5,97,0,0,429,430,5,110,0,0,430,431,5,100,
0,0,431,432,5,97,0,0,432,433,5,116,0,0,433,434,5,111,0,0,434,435,5,114,0,
0,435,436,5,121,0,0,436,76,1,0,0,0,437,438,3,51,25,0,438,446,3,111,55,0,
439,440,5,46,0,0,440,441,5,46,0,0,441,444,1,0,0,0,442,445,3,111,55,0,443,
445,5,42,0,0,444,442,1,0,0,0,444,443,1,0,0,0,445,447,1,0,0,0,446,439,1,0,
0,0,446,447,1,0,0,0,447,448,1,0,0,0,448,449,3,53,26,0,449,78,1,0,0,0,450,
451,5,33,0,0,451,80,1,0,0,0,452,453,5,38,0,0,453,82,1,0,0,0,454,455,5,124,
0,0,455,84,1,0,0,0,456,457,5,60,0,0,457,458,5,61,0,0,458,459,5,62,0,0,459,
86,1,0,0,0,460,461,5,61,0,0,461,462,5,62,0,0,462,88,1,0,0,0,463,464,5,61,
0,0,464,465,5,61,0,0,465,90,1,0,0,0,466,467,5,60,0,0,467,92,1,0,0,0,468,
469,5,60,0,0,469,470,5,61,0,0,470,94,1,0,0,0,471,472,5,62,0,0,472,96,1,0,
0,0,473,474,5,62,0,0,474,475,5,61,0,0,475,98,1,0,0,0,476,477,5,33,0,0,477,
478,5,61,0,0,478,100,1,0,0,0,479,480,5,47,0,0,480,102,1,0,0,0,481,482,5,
42,0,0,482,104,1,0,0,0,483,484,5,43,0,0,484,106,1,0,0,0,485,486,5,45,0,0,
486,108,1,0,0,0,487,489,5,45,0,0,488,487,1,0,0,0,488,489,1,0,0,0,489,493,
1,0,0,0,490,492,7,0,0,0,491,490,1,0,0,0,492,495,1,0,0,0,493,491,1,0,0,0,
493,494,1,0,0,0,494,496,1,0,0,0,495,493,1,0,0,0,496,498,7,1,0,0,497,499,
7,0,0,0,498,497,1,0,0,0,499,500,1,0,0,0,500,498,1,0,0,0,500,501,1,0,0,0,
501,110,1,0,0,0,502,514,5,48,0,0,503,505,5,45,0,0,504,503,1,0,0,0,504,505,
1,0,0,0,505,506,1,0,0,0,506,510,7,2,0,0,507,509,7,0,0,0,508,507,1,0,0,0,
509,512,1,0,0,0,510,508,1,0,0,0,510,511,1,0,0,0,511,514,1,0,0,0,512,510,
1,0,0,0,513,502,1,0,0,0,513,504,1,0,0,0,514,112,1,0,0,0,515,516,5,116,0,
0,516,517,5,114,0,0,517,518,5,117,0,0,518,525,5,101,0,0,519,520,5,102,0,
0,520,521,5,97,0,0,521,522,5,108,0,0,522,523,5,115,0,0,523,525,5,101,0,0,
524,515,1,0,0,0,524,519,1,0,0,0,525,114,1,0,0,0,526,527,5,66,0,0,527,528,
5,111,0,0,528,529,5,111,0,0,529,530,5,108,0,0,530,531,5,101,0,0,531,532,
5,97,0,0,532,533,5,110,0,0,533,116,1,0,0,0,534,535,5,44,0,0,535,118,1,0,
0,0,536,538,5,34,0,0,537,539,8,3,0,0,538,537,1,0,0,0,539,540,1,0,0,0,540,
538,1,0,0,0,540,541,1,0,0,0,541,542,1,0,0,0,542,543,5,34,0,0,543,120,1,0,
0,0,544,548,7,4,0,0,545,547,7,5,0,0,546,545,1,0,0,0,547,550,1,0,0,0,548,
546,1,0,0,0,548,549,1,0,0,0,549,122,1,0,0,0,550,548,1,0,0,0,551,553,5,39,
0,0,552,554,8,6,0,0,553,552,1,0,0,0,554,555,1,0,0,0,555,553,1,0,0,0,555,
556,1,0,0,0,556,557,1,0,0,0,557,558,5,39,0,0,558,124,1,0,0,0,559,562,3,129,
64,0,560,562,3,127,63,0,561,559,1,0,0,0,561,560,1,0,0,0,562,563,1,0,0,0,
563,564,6,62,9,0,564,126,1,0,0,0,565,566,5,47,0,0,566,567,5,47,0,0,567,571,
1,0,0,0,568,570,8,7,0,0,569,568,1,0,0,0,570,573,1,0,0,0,571,569,1,0,0,0,
571,572,1,0,0,0,572,584,1,0,0,0,573,571,1,0,0,0,574,578,3,59,29,0,575,577,
9,0,0,0,576,575,1,0,0,0,577,580,1,0,0,0,578,576,1,0,0,0,578,579,1,0,0,0,
579,581,1,0,0,0,580,578,1,0,0,0,581,582,3,61,30,0,582,584,1,0,0,0,583,565,
1,0,0,0,583,574,1,0,0,0,584,128,1,0,0,0,585,587,7,8,0,0,586,585,1,0,0,0,
587,588,1,0,0,0,588,586,1,0,0,0,588,589,1,0,0,0,589,130,1,0,0,0,23,0,372,
376,379,381,444,446,488,493,500,504,510,513,524,540,546,548,555,561,571,
578,583,588,10,1,23,0,1,24,1,1,25,2,1,26,3,1,27,4,1,28,5,1,29,6,1,30,7,1,
31,8,6,0,0];


const atn = new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ATNDeserializer().deserialize(serializedATN);

const decisionsToDFA = atn.decisionToState.map( (ds, index) => new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].dfa.DFA(ds, index) );

class UVLJavaScriptLexer extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].Lexer {

    static grammarFileName = "UVLJavaScript.g4";
    static channelNames = [ "DEFAULT_TOKEN_CHANNEL", "HIDDEN" ];
	static modeNames = [ "DEFAULT_MODE" ];
	static literalNames = [ null, "'include'", "'namespace'", "'imports'", 
                         "'as'", "'features'", "'cardinality'", "'constraint'", 
                         "'constraints'", "'sum'", "'avg'", "'len'", "'floor'", 
                         "'ceil'", "'.'", "'String'", "'Integer'", "'Real'", 
                         "'Arithmetic'", "'Type'", "'group-cardinality'", 
                         "'feature-cardinality'", "'aggregate-function'", 
                         "'string-constraints'", "'('", "')'", "'['", "']'", 
                         "'{'", "'}'", "'/*'", "'*/'", null, "'<INDENT>'", 
                         "'<DEDENT>'", "'or'", "'alternative'", "'optional'", 
                         "'mandatory'", null, "'!'", "'&'", "'|'", "'<=>'", 
                         "'=>'", "'=='", "'<'", "'<='", "'>'", "'>='", "'!='", 
                         "'/'", "'*'", "'+'", "'-'", null, null, null, "'Boolean'", 
                         "','" ];
	static symbolicNames = [ null, null, null, null, null, null, null, null, 
                          null, null, null, null, null, null, null, null, 
                          null, null, null, null, null, null, null, null, 
                          "OPEN_PAREN", "CLOSE_PAREN", "OPEN_BRACK", "CLOSE_BRACK", 
                          "OPEN_BRACE", "CLOSE_BRACE", "OPEN_COMMENT", "CLOSE_COMMENT", 
                          "NEWLINE", "INDENT", "DEDENT", "ORGROUP", "ALTERNATIVE", 
                          "OPTIONAL", "MANDATORY", "CARDINALITY", "NOT", 
                          "AND", "OR", "EQUIVALENCE", "IMPLICATION", "EQUAL", 
                          "LOWER", "LOWER_EQUALS", "GREATER", "GREATER_EQUALS", 
                          "NOT_EQUALS", "DIV", "MUL", "ADD", "SUB", "FLOAT", 
                          "INTEGER", "BOOLEAN", "BOOLEAN_KEY", "COMMA", 
                          "ID_NOT_STRICT", "ID_STRICT", "STRING", "SKIP_" ];
	static ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                      "T__7", "T__8", "T__9", "T__10", "T__11", "T__12", 
                      "T__13", "T__14", "T__15", "T__16", "T__17", "T__18", 
                      "T__19", "T__20", "T__21", "T__22", "OPEN_PAREN", 
                      "CLOSE_PAREN", "OPEN_BRACK", "CLOSE_BRACK", "OPEN_BRACE", 
                      "CLOSE_BRACE", "OPEN_COMMENT", "CLOSE_COMMENT", "NEWLINE", 
                      "INDENT", "DEDENT", "ORGROUP", "ALTERNATIVE", "OPTIONAL", 
                      "MANDATORY", "CARDINALITY", "NOT", "AND", "OR", "EQUIVALENCE", 
                      "IMPLICATION", "EQUAL", "LOWER", "LOWER_EQUALS", "GREATER", 
                      "GREATER_EQUALS", "NOT_EQUALS", "DIV", "MUL", "ADD", 
                      "SUB", "FLOAT", "INTEGER", "BOOLEAN", "BOOLEAN_KEY", 
                      "COMMA", "ID_NOT_STRICT", "ID_STRICT", "STRING", "SKIP_", 
                      "COMMENT", "SPACES" ];

    constructor(input) {
        super(input)
        this._interp = new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.LexerATNSimulator(this, atn, decisionsToDFA, new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.PredictionContextCache());

          // Una cola donde se empujan los tokens adicionales (ver la regla del lexer NEWLINE).
          let tokens = [];
          // La pila que lleva un registro del nivel de indentación.
          let indents = [];
          // La cantidad de paréntesis, corchetes y llaves abiertos.
          let opened = 0;
          // El token más recientemente producido.
          let lastToken = null;

    }
}

UVLJavaScriptLexer.EOF = antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].Token.EOF;
UVLJavaScriptLexer.T__0 = 1;
UVLJavaScriptLexer.T__1 = 2;
UVLJavaScriptLexer.T__2 = 3;
UVLJavaScriptLexer.T__3 = 4;
UVLJavaScriptLexer.T__4 = 5;
UVLJavaScriptLexer.T__5 = 6;
UVLJavaScriptLexer.T__6 = 7;
UVLJavaScriptLexer.T__7 = 8;
UVLJavaScriptLexer.T__8 = 9;
UVLJavaScriptLexer.T__9 = 10;
UVLJavaScriptLexer.T__10 = 11;
UVLJavaScriptLexer.T__11 = 12;
UVLJavaScriptLexer.T__12 = 13;
UVLJavaScriptLexer.T__13 = 14;
UVLJavaScriptLexer.T__14 = 15;
UVLJavaScriptLexer.T__15 = 16;
UVLJavaScriptLexer.T__16 = 17;
UVLJavaScriptLexer.T__17 = 18;
UVLJavaScriptLexer.T__18 = 19;
UVLJavaScriptLexer.T__19 = 20;
UVLJavaScriptLexer.T__20 = 21;
UVLJavaScriptLexer.T__21 = 22;
UVLJavaScriptLexer.T__22 = 23;
UVLJavaScriptLexer.OPEN_PAREN = 24;
UVLJavaScriptLexer.CLOSE_PAREN = 25;
UVLJavaScriptLexer.OPEN_BRACK = 26;
UVLJavaScriptLexer.CLOSE_BRACK = 27;
UVLJavaScriptLexer.OPEN_BRACE = 28;
UVLJavaScriptLexer.CLOSE_BRACE = 29;
UVLJavaScriptLexer.OPEN_COMMENT = 30;
UVLJavaScriptLexer.CLOSE_COMMENT = 31;
UVLJavaScriptLexer.NEWLINE = 32;
UVLJavaScriptLexer.INDENT = 33;
UVLJavaScriptLexer.DEDENT = 34;
UVLJavaScriptLexer.ORGROUP = 35;
UVLJavaScriptLexer.ALTERNATIVE = 36;
UVLJavaScriptLexer.OPTIONAL = 37;
UVLJavaScriptLexer.MANDATORY = 38;
UVLJavaScriptLexer.CARDINALITY = 39;
UVLJavaScriptLexer.NOT = 40;
UVLJavaScriptLexer.AND = 41;
UVLJavaScriptLexer.OR = 42;
UVLJavaScriptLexer.EQUIVALENCE = 43;
UVLJavaScriptLexer.IMPLICATION = 44;
UVLJavaScriptLexer.EQUAL = 45;
UVLJavaScriptLexer.LOWER = 46;
UVLJavaScriptLexer.LOWER_EQUALS = 47;
UVLJavaScriptLexer.GREATER = 48;
UVLJavaScriptLexer.GREATER_EQUALS = 49;
UVLJavaScriptLexer.NOT_EQUALS = 50;
UVLJavaScriptLexer.DIV = 51;
UVLJavaScriptLexer.MUL = 52;
UVLJavaScriptLexer.ADD = 53;
UVLJavaScriptLexer.SUB = 54;
UVLJavaScriptLexer.FLOAT = 55;
UVLJavaScriptLexer.INTEGER = 56;
UVLJavaScriptLexer.BOOLEAN = 57;
UVLJavaScriptLexer.BOOLEAN_KEY = 58;
UVLJavaScriptLexer.COMMA = 59;
UVLJavaScriptLexer.ID_NOT_STRICT = 60;
UVLJavaScriptLexer.ID_STRICT = 61;
UVLJavaScriptLexer.STRING = 62;
UVLJavaScriptLexer.SKIP_ = 63;

UVLJavaScriptLexer.prototype.action = function(localctx, ruleIndex, actionIndex) {
	switch (ruleIndex) {
	case 23:
		this.OPEN_PAREN_action(localctx, actionIndex);
		break;
	case 24:
		this.CLOSE_PAREN_action(localctx, actionIndex);
		break;
	case 25:
		this.OPEN_BRACK_action(localctx, actionIndex);
		break;
	case 26:
		this.CLOSE_BRACK_action(localctx, actionIndex);
		break;
	case 27:
		this.OPEN_BRACE_action(localctx, actionIndex);
		break;
	case 28:
		this.CLOSE_BRACE_action(localctx, actionIndex);
		break;
	case 29:
		this.OPEN_COMMENT_action(localctx, actionIndex);
		break;
	case 30:
		this.CLOSE_COMMENT_action(localctx, actionIndex);
		break;
	case 31:
		this.NEWLINE_action(localctx, actionIndex);
		break;
	default:
		throw "No registered action for:" + ruleIndex;
	}
};


UVLJavaScriptLexer.prototype.OPEN_PAREN_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 0:
		this.opened += 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.CLOSE_PAREN_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 1:
		this.opened -= 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.OPEN_BRACK_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 2:
		this.opened += 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.CLOSE_BRACK_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 3:
		this.opened -= 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.OPEN_BRACE_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 4:
		this.opened += 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.CLOSE_BRACE_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 5:
		this.opened -= 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.OPEN_COMMENT_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 6:
		this.opened += 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.CLOSE_COMMENT_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 7:
		this.opened -= 1;
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};

UVLJavaScriptLexer.prototype.NEWLINE_action = function(localctx , actionIndex) {
	switch (actionIndex) {
	case 8:
		this.handleNewline();
		break;
	default:
		throw "No registered action for:" + actionIndex;
	}
};
UVLJavaScriptLexer.prototype.sempred = function(localctx, ruleIndex, predIndex) {
	switch (ruleIndex) {
		case 31:
			return this.NEWLINE_sempred(localctx, predIndex);
    	default:
    		throw "No registered predicate for:" + ruleIndex;
    }
};

UVLJavaScriptLexer.prototype.NEWLINE_sempred = function(localctx, predIndex) {
	switch(predIndex) {
		case 0:
			return this.atStartOfInput();
		default:
			throw "No predicate with index:" + predIndex;
	}
};






/***/ }),

/***/ "./node_modules/uvl-parser/src/lib/UVLJavaScriptListener.js":
/*!******************************************************************!*\
  !*** ./node_modules/uvl-parser/src/lib/UVLJavaScriptListener.js ***!
  \******************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ UVLJavaScriptListener)
/* harmony export */ });
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");
// Generated from ../uvl/UVLJavaScript.g4 by ANTLR 4.13.2
// jshint ignore: start


// This class defines a complete listener for a parse tree produced by UVLJavaScriptParser.
class UVLJavaScriptListener extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].tree.ParseTreeListener {

	// Enter a parse tree produced by UVLJavaScriptParser#featureModel.
	enterFeatureModel(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#featureModel.
	exitFeatureModel(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#includes.
	enterIncludes(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#includes.
	exitIncludes(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#includeLine.
	enterIncludeLine(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#includeLine.
	exitIncludeLine(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#namespace.
	enterNamespace(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#namespace.
	exitNamespace(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#imports.
	enterImports(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#imports.
	exitImports(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#importLine.
	enterImportLine(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#importLine.
	exitImportLine(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#features.
	enterFeatures(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#features.
	exitFeatures(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#OrGroup.
	enterOrGroup(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#OrGroup.
	exitOrGroup(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#AlternativeGroup.
	enterAlternativeGroup(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#AlternativeGroup.
	exitAlternativeGroup(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#OptionalGroup.
	enterOptionalGroup(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#OptionalGroup.
	exitOptionalGroup(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#MandatoryGroup.
	enterMandatoryGroup(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#MandatoryGroup.
	exitMandatoryGroup(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#CardinalityGroup.
	enterCardinalityGroup(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#CardinalityGroup.
	exitCardinalityGroup(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#groupSpec.
	enterGroupSpec(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#groupSpec.
	exitGroupSpec(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#feature.
	enterFeature(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#feature.
	exitFeature(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#featureCardinality.
	enterFeatureCardinality(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#featureCardinality.
	exitFeatureCardinality(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#attributes.
	enterAttributes(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#attributes.
	exitAttributes(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#attribute.
	enterAttribute(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#attribute.
	exitAttribute(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#valueAttribute.
	enterValueAttribute(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#valueAttribute.
	exitValueAttribute(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#key.
	enterKey(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#key.
	exitKey(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#value.
	enterValue(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#value.
	exitValue(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#vector.
	enterVector(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#vector.
	exitVector(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#SingleConstraintAttribute.
	enterSingleConstraintAttribute(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#SingleConstraintAttribute.
	exitSingleConstraintAttribute(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#ListConstraintAttribute.
	enterListConstraintAttribute(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#ListConstraintAttribute.
	exitListConstraintAttribute(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#constraintList.
	enterConstraintList(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#constraintList.
	exitConstraintList(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#constraints.
	enterConstraints(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#constraints.
	exitConstraints(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#constraintLine.
	enterConstraintLine(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#constraintLine.
	exitConstraintLine(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#OrConstraint.
	enterOrConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#OrConstraint.
	exitOrConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#EquationConstraint.
	enterEquationConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#EquationConstraint.
	exitEquationConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#LiteralConstraint.
	enterLiteralConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#LiteralConstraint.
	exitLiteralConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#ParenthesisConstraint.
	enterParenthesisConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#ParenthesisConstraint.
	exitParenthesisConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#NotConstraint.
	enterNotConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#NotConstraint.
	exitNotConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#AndConstraint.
	enterAndConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#AndConstraint.
	exitAndConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#EquivalenceConstraint.
	enterEquivalenceConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#EquivalenceConstraint.
	exitEquivalenceConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#ImplicationConstraint.
	enterImplicationConstraint(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#ImplicationConstraint.
	exitImplicationConstraint(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#EqualEquation.
	enterEqualEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#EqualEquation.
	exitEqualEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#LowerEquation.
	enterLowerEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#LowerEquation.
	exitLowerEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#GreaterEquation.
	enterGreaterEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#GreaterEquation.
	exitGreaterEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#LowerEqualsEquation.
	enterLowerEqualsEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#LowerEqualsEquation.
	exitLowerEqualsEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#GreaterEqualsEquation.
	enterGreaterEqualsEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#GreaterEqualsEquation.
	exitGreaterEqualsEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#NotEqualsEquation.
	enterNotEqualsEquation(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#NotEqualsEquation.
	exitNotEqualsEquation(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#BracketExpression.
	enterBracketExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#BracketExpression.
	exitBracketExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#AggregateFunctionExpression.
	enterAggregateFunctionExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#AggregateFunctionExpression.
	exitAggregateFunctionExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#FloatLiteralExpression.
	enterFloatLiteralExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#FloatLiteralExpression.
	exitFloatLiteralExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#StringLiteralExpression.
	enterStringLiteralExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#StringLiteralExpression.
	exitStringLiteralExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#AddExpression.
	enterAddExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#AddExpression.
	exitAddExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#IntegerLiteralExpression.
	enterIntegerLiteralExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#IntegerLiteralExpression.
	exitIntegerLiteralExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#LiteralExpression.
	enterLiteralExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#LiteralExpression.
	exitLiteralExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#DivExpression.
	enterDivExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#DivExpression.
	exitDivExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#SubExpression.
	enterSubExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#SubExpression.
	exitSubExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#MulExpression.
	enterMulExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#MulExpression.
	exitMulExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#SumAggregateFunction.
	enterSumAggregateFunction(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#SumAggregateFunction.
	exitSumAggregateFunction(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#AvgAggregateFunction.
	enterAvgAggregateFunction(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#AvgAggregateFunction.
	exitAvgAggregateFunction(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#StringAggregateFunctionExpression.
	enterStringAggregateFunctionExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#StringAggregateFunctionExpression.
	exitStringAggregateFunctionExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#NumericAggregateFunctionExpression.
	enterNumericAggregateFunctionExpression(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#NumericAggregateFunctionExpression.
	exitNumericAggregateFunctionExpression(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#LengthAggregateFunction.
	enterLengthAggregateFunction(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#LengthAggregateFunction.
	exitLengthAggregateFunction(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#FloorAggregateFunction.
	enterFloorAggregateFunction(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#FloorAggregateFunction.
	exitFloorAggregateFunction(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#CeilAggregateFunction.
	enterCeilAggregateFunction(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#CeilAggregateFunction.
	exitCeilAggregateFunction(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#reference.
	enterReference(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#reference.
	exitReference(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#id.
	enterId(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#id.
	exitId(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#featureType.
	enterFeatureType(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#featureType.
	exitFeatureType(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#languageLevel.
	enterLanguageLevel(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#languageLevel.
	exitLanguageLevel(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#majorLevel.
	enterMajorLevel(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#majorLevel.
	exitMajorLevel(ctx) {
	}


	// Enter a parse tree produced by UVLJavaScriptParser#minorLevel.
	enterMinorLevel(ctx) {
	}

	// Exit a parse tree produced by UVLJavaScriptParser#minorLevel.
	exitMinorLevel(ctx) {
	}



}

/***/ }),

/***/ "./node_modules/uvl-parser/src/lib/UVLJavaScriptParser.js":
/*!****************************************************************!*\
  !*** ./node_modules/uvl-parser/src/lib/UVLJavaScriptParser.js ***!
  \****************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ UVLJavaScriptParser)
/* harmony export */ });
/* harmony import */ var antlr4__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! antlr4 */ "./node_modules/antlr4/dist/antlr4.web.js");
/* harmony import */ var _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./UVLJavaScriptListener.js */ "./node_modules/uvl-parser/src/lib/UVLJavaScriptListener.js");
// Generated from ../uvl/UVLJavaScript.g4 by ANTLR 4.13.2
// jshint ignore: start


const serializedATN = [4,1,63,409,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,
4,2,5,7,5,2,6,7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,
2,13,7,13,2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,
20,7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,2,27,
7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,1,0,3,0,68,8,0,1,
0,3,0,71,8,0,1,0,3,0,74,8,0,1,0,3,0,77,8,0,1,0,3,0,80,8,0,1,0,3,0,83,8,0,
1,0,3,0,86,8,0,1,0,3,0,89,8,0,1,0,3,0,92,8,0,1,0,1,0,1,1,1,1,1,1,1,1,5,1,
100,8,1,10,1,12,1,103,9,1,1,1,1,1,1,2,1,2,1,2,1,3,1,3,1,3,1,4,1,4,1,4,1,
4,5,4,117,8,4,10,4,12,4,120,9,4,1,4,1,4,1,5,1,5,1,5,3,5,127,8,5,1,5,1,5,
1,6,1,6,1,6,1,6,1,6,1,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,3,7,147,
8,7,1,8,1,8,1,8,4,8,152,8,8,11,8,12,8,153,1,8,1,8,1,9,3,9,159,8,9,1,9,1,
9,3,9,163,8,9,1,9,3,9,166,8,9,1,9,1,9,1,9,4,9,171,8,9,11,9,12,9,172,1,9,
1,9,3,9,177,8,9,1,10,1,10,1,10,1,11,1,11,1,11,1,11,5,11,186,8,11,10,11,12,
11,189,9,11,3,11,191,8,11,1,11,1,11,1,12,1,12,3,12,197,8,12,1,13,1,13,3,
13,201,8,13,1,14,1,14,1,15,1,15,1,15,1,15,1,15,1,15,3,15,211,8,15,1,16,1,
16,1,16,1,16,5,16,217,8,16,10,16,12,16,220,9,16,3,16,222,8,16,1,16,1,16,
1,17,1,17,1,17,1,17,3,17,230,8,17,1,18,1,18,1,18,1,18,5,18,236,8,18,10,18,
12,18,239,9,18,3,18,241,8,18,1,18,1,18,1,19,1,19,1,19,1,19,5,19,249,8,19,
10,19,12,19,252,9,19,1,19,1,19,1,20,1,20,1,20,1,21,1,21,1,21,1,21,1,21,1,
21,1,21,1,21,1,21,3,21,268,8,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,1,21,
1,21,1,21,1,21,1,21,5,21,282,8,21,10,21,12,21,285,9,21,1,22,1,22,1,22,1,
22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,1,22,
1,22,1,22,1,22,1,22,1,22,1,22,3,22,311,8,22,1,23,1,23,1,23,1,23,1,23,1,23,
1,23,1,23,1,23,1,23,3,23,323,8,23,1,23,1,23,1,23,1,23,1,23,1,23,1,23,1,23,
1,23,1,23,1,23,1,23,5,23,337,8,23,10,23,12,23,340,9,23,1,24,1,24,1,24,1,
24,1,24,3,24,347,8,24,1,24,1,24,1,24,1,24,1,24,1,24,1,24,1,24,3,24,357,8,
24,1,24,1,24,1,24,1,24,1,24,3,24,364,8,24,1,25,1,25,1,25,1,25,1,25,1,26,
1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,1,26,3,26,381,8,26,1,27,1,27,1,27,
5,27,386,8,27,10,27,12,27,389,9,27,1,27,1,27,1,28,1,28,1,29,1,29,1,30,1,
30,1,30,1,30,3,30,401,8,30,3,30,403,8,30,1,31,1,31,1,32,1,32,1,32,0,2,42,
46,33,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,
48,50,52,54,56,58,60,62,64,0,4,1,0,60,61,2,0,15,17,58,58,2,0,18,19,58,58,
1,0,20,23,442,0,67,1,0,0,0,2,95,1,0,0,0,4,106,1,0,0,0,6,109,1,0,0,0,8,112,
1,0,0,0,10,123,1,0,0,0,12,130,1,0,0,0,14,146,1,0,0,0,16,148,1,0,0,0,18,158,
1,0,0,0,20,178,1,0,0,0,22,181,1,0,0,0,24,196,1,0,0,0,26,198,1,0,0,0,28,202,
1,0,0,0,30,210,1,0,0,0,32,212,1,0,0,0,34,229,1,0,0,0,36,231,1,0,0,0,38,244,
1,0,0,0,40,255,1,0,0,0,42,267,1,0,0,0,44,310,1,0,0,0,46,322,1,0,0,0,48,363,
1,0,0,0,50,365,1,0,0,0,52,380,1,0,0,0,54,387,1,0,0,0,56,392,1,0,0,0,58,394,
1,0,0,0,60,396,1,0,0,0,62,404,1,0,0,0,64,406,1,0,0,0,66,68,3,6,3,0,67,66,
1,0,0,0,67,68,1,0,0,0,68,70,1,0,0,0,69,71,5,32,0,0,70,69,1,0,0,0,70,71,1,
0,0,0,71,73,1,0,0,0,72,74,3,2,1,0,73,72,1,0,0,0,73,74,1,0,0,0,74,76,1,0,
0,0,75,77,5,32,0,0,76,75,1,0,0,0,76,77,1,0,0,0,77,79,1,0,0,0,78,80,3,8,4,
0,79,78,1,0,0,0,79,80,1,0,0,0,80,82,1,0,0,0,81,83,5,32,0,0,82,81,1,0,0,0,
82,83,1,0,0,0,83,85,1,0,0,0,84,86,3,12,6,0,85,84,1,0,0,0,85,86,1,0,0,0,86,
88,1,0,0,0,87,89,5,32,0,0,88,87,1,0,0,0,88,89,1,0,0,0,89,91,1,0,0,0,90,92,
3,38,19,0,91,90,1,0,0,0,91,92,1,0,0,0,92,93,1,0,0,0,93,94,5,0,0,1,94,1,1,
0,0,0,95,96,5,1,0,0,96,97,5,32,0,0,97,101,5,33,0,0,98,100,3,4,2,0,99,98,
1,0,0,0,100,103,1,0,0,0,101,99,1,0,0,0,101,102,1,0,0,0,102,104,1,0,0,0,103,
101,1,0,0,0,104,105,5,34,0,0,105,3,1,0,0,0,106,107,3,60,30,0,107,108,5,32,
0,0,108,5,1,0,0,0,109,110,5,2,0,0,110,111,3,54,27,0,111,7,1,0,0,0,112,113,
5,3,0,0,113,114,5,32,0,0,114,118,5,33,0,0,115,117,3,10,5,0,116,115,1,0,0,
0,117,120,1,0,0,0,118,116,1,0,0,0,118,119,1,0,0,0,119,121,1,0,0,0,120,118,
1,0,0,0,121,122,5,34,0,0,122,9,1,0,0,0,123,126,3,54,27,0,124,125,5,4,0,0,
125,127,3,54,27,0,126,124,1,0,0,0,126,127,1,0,0,0,127,128,1,0,0,0,128,129,
5,32,0,0,129,11,1,0,0,0,130,131,5,5,0,0,131,132,5,32,0,0,132,133,5,33,0,
0,133,134,3,18,9,0,134,135,5,34,0,0,135,13,1,0,0,0,136,137,5,35,0,0,137,
147,3,16,8,0,138,139,5,36,0,0,139,147,3,16,8,0,140,141,5,37,0,0,141,147,
3,16,8,0,142,143,5,38,0,0,143,147,3,16,8,0,144,145,5,39,0,0,145,147,3,16,
8,0,146,136,1,0,0,0,146,138,1,0,0,0,146,140,1,0,0,0,146,142,1,0,0,0,146,
144,1,0,0,0,147,15,1,0,0,0,148,149,5,32,0,0,149,151,5,33,0,0,150,152,3,18,
9,0,151,150,1,0,0,0,152,153,1,0,0,0,153,151,1,0,0,0,153,154,1,0,0,0,154,
155,1,0,0,0,155,156,5,34,0,0,156,17,1,0,0,0,157,159,3,58,29,0,158,157,1,
0,0,0,158,159,1,0,0,0,159,160,1,0,0,0,160,162,3,54,27,0,161,163,3,20,10,
0,162,161,1,0,0,0,162,163,1,0,0,0,163,165,1,0,0,0,164,166,3,22,11,0,165,
164,1,0,0,0,165,166,1,0,0,0,166,167,1,0,0,0,167,176,5,32,0,0,168,170,5,33,
0,0,169,171,3,14,7,0,170,169,1,0,0,0,171,172,1,0,0,0,172,170,1,0,0,0,172,
173,1,0,0,0,173,174,1,0,0,0,174,175,5,34,0,0,175,177,1,0,0,0,176,168,1,0,
0,0,176,177,1,0,0,0,177,19,1,0,0,0,178,179,5,6,0,0,179,180,5,39,0,0,180,
21,1,0,0,0,181,190,5,28,0,0,182,187,3,24,12,0,183,184,5,59,0,0,184,186,3,
24,12,0,185,183,1,0,0,0,186,189,1,0,0,0,187,185,1,0,0,0,187,188,1,0,0,0,
188,191,1,0,0,0,189,187,1,0,0,0,190,182,1,0,0,0,190,191,1,0,0,0,191,192,
1,0,0,0,192,193,5,29,0,0,193,23,1,0,0,0,194,197,3,26,13,0,195,197,3,34,17,
0,196,194,1,0,0,0,196,195,1,0,0,0,197,25,1,0,0,0,198,200,3,28,14,0,199,201,
3,30,15,0,200,199,1,0,0,0,200,201,1,0,0,0,201,27,1,0,0,0,202,203,3,56,28,
0,203,29,1,0,0,0,204,211,5,57,0,0,205,211,5,55,0,0,206,211,5,56,0,0,207,
211,5,62,0,0,208,211,3,22,11,0,209,211,3,32,16,0,210,204,1,0,0,0,210,205,
1,0,0,0,210,206,1,0,0,0,210,207,1,0,0,0,210,208,1,0,0,0,210,209,1,0,0,0,
211,31,1,0,0,0,212,221,5,26,0,0,213,218,3,30,15,0,214,215,5,59,0,0,215,217,
3,30,15,0,216,214,1,0,0,0,217,220,1,0,0,0,218,216,1,0,0,0,218,219,1,0,0,
0,219,222,1,0,0,0,220,218,1,0,0,0,221,213,1,0,0,0,221,222,1,0,0,0,222,223,
1,0,0,0,223,224,5,27,0,0,224,33,1,0,0,0,225,226,5,7,0,0,226,230,3,42,21,
0,227,228,5,8,0,0,228,230,3,36,18,0,229,225,1,0,0,0,229,227,1,0,0,0,230,
35,1,0,0,0,231,240,5,26,0,0,232,237,3,42,21,0,233,234,5,59,0,0,234,236,3,
42,21,0,235,233,1,0,0,0,236,239,1,0,0,0,237,235,1,0,0,0,237,238,1,0,0,0,
238,241,1,0,0,0,239,237,1,0,0,0,240,232,1,0,0,0,240,241,1,0,0,0,241,242,
1,0,0,0,242,243,5,27,0,0,243,37,1,0,0,0,244,245,5,8,0,0,245,246,5,32,0,0,
246,250,5,33,0,0,247,249,3,40,20,0,248,247,1,0,0,0,249,252,1,0,0,0,250,248,
1,0,0,0,250,251,1,0,0,0,251,253,1,0,0,0,252,250,1,0,0,0,253,254,5,34,0,0,
254,39,1,0,0,0,255,256,3,42,21,0,256,257,5,32,0,0,257,41,1,0,0,0,258,259,
6,21,-1,0,259,268,3,44,22,0,260,268,3,54,27,0,261,262,5,24,0,0,262,263,3,
42,21,0,263,264,5,25,0,0,264,268,1,0,0,0,265,266,5,40,0,0,266,268,3,42,21,
5,267,258,1,0,0,0,267,260,1,0,0,0,267,261,1,0,0,0,267,265,1,0,0,0,268,283,
1,0,0,0,269,270,10,4,0,0,270,271,5,41,0,0,271,282,3,42,21,5,272,273,10,3,
0,0,273,274,5,42,0,0,274,282,3,42,21,4,275,276,10,2,0,0,276,277,5,44,0,0,
277,282,3,42,21,3,278,279,10,1,0,0,279,280,5,43,0,0,280,282,3,42,21,2,281,
269,1,0,0,0,281,272,1,0,0,0,281,275,1,0,0,0,281,278,1,0,0,0,282,285,1,0,
0,0,283,281,1,0,0,0,283,284,1,0,0,0,284,43,1,0,0,0,285,283,1,0,0,0,286,287,
3,46,23,0,287,288,5,45,0,0,288,289,3,46,23,0,289,311,1,0,0,0,290,291,3,46,
23,0,291,292,5,46,0,0,292,293,3,46,23,0,293,311,1,0,0,0,294,295,3,46,23,
0,295,296,5,48,0,0,296,297,3,46,23,0,297,311,1,0,0,0,298,299,3,46,23,0,299,
300,5,47,0,0,300,301,3,46,23,0,301,311,1,0,0,0,302,303,3,46,23,0,303,304,
5,49,0,0,304,305,3,46,23,0,305,311,1,0,0,0,306,307,3,46,23,0,307,308,5,50,
0,0,308,309,3,46,23,0,309,311,1,0,0,0,310,286,1,0,0,0,310,290,1,0,0,0,310,
294,1,0,0,0,310,298,1,0,0,0,310,302,1,0,0,0,310,306,1,0,0,0,311,45,1,0,0,
0,312,313,6,23,-1,0,313,323,5,55,0,0,314,323,5,56,0,0,315,323,5,62,0,0,316,
323,3,48,24,0,317,323,3,54,27,0,318,319,5,24,0,0,319,320,3,46,23,0,320,321,
5,25,0,0,321,323,1,0,0,0,322,312,1,0,0,0,322,314,1,0,0,0,322,315,1,0,0,0,
322,316,1,0,0,0,322,317,1,0,0,0,322,318,1,0,0,0,323,338,1,0,0,0,324,325,
10,4,0,0,325,326,5,53,0,0,326,337,3,46,23,5,327,328,10,3,0,0,328,329,5,54,
0,0,329,337,3,46,23,4,330,331,10,2,0,0,331,332,5,52,0,0,332,337,3,46,23,
3,333,334,10,1,0,0,334,335,5,51,0,0,335,337,3,46,23,2,336,324,1,0,0,0,336,
327,1,0,0,0,336,330,1,0,0,0,336,333,1,0,0,0,337,340,1,0,0,0,338,336,1,0,
0,0,338,339,1,0,0,0,339,47,1,0,0,0,340,338,1,0,0,0,341,342,5,9,0,0,342,346,
5,24,0,0,343,344,3,54,27,0,344,345,5,59,0,0,345,347,1,0,0,0,346,343,1,0,
0,0,346,347,1,0,0,0,347,348,1,0,0,0,348,349,3,54,27,0,349,350,5,25,0,0,350,
364,1,0,0,0,351,352,5,10,0,0,352,356,5,24,0,0,353,354,3,54,27,0,354,355,
5,59,0,0,355,357,1,0,0,0,356,353,1,0,0,0,356,357,1,0,0,0,357,358,1,0,0,0,
358,359,3,54,27,0,359,360,5,25,0,0,360,364,1,0,0,0,361,364,3,50,25,0,362,
364,3,52,26,0,363,341,1,0,0,0,363,351,1,0,0,0,363,361,1,0,0,0,363,362,1,
0,0,0,364,49,1,0,0,0,365,366,5,11,0,0,366,367,5,24,0,0,367,368,3,54,27,0,
368,369,5,25,0,0,369,51,1,0,0,0,370,371,5,12,0,0,371,372,5,24,0,0,372,373,
3,54,27,0,373,374,5,25,0,0,374,381,1,0,0,0,375,376,5,13,0,0,376,377,5,24,
0,0,377,378,3,54,27,0,378,379,5,25,0,0,379,381,1,0,0,0,380,370,1,0,0,0,380,
375,1,0,0,0,381,53,1,0,0,0,382,383,3,56,28,0,383,384,5,14,0,0,384,386,1,
0,0,0,385,382,1,0,0,0,386,389,1,0,0,0,387,385,1,0,0,0,387,388,1,0,0,0,388,
390,1,0,0,0,389,387,1,0,0,0,390,391,3,56,28,0,391,55,1,0,0,0,392,393,7,0,
0,0,393,57,1,0,0,0,394,395,7,1,0,0,395,59,1,0,0,0,396,402,3,62,31,0,397,
400,5,14,0,0,398,401,3,64,32,0,399,401,5,52,0,0,400,398,1,0,0,0,400,399,
1,0,0,0,401,403,1,0,0,0,402,397,1,0,0,0,402,403,1,0,0,0,403,61,1,0,0,0,404,
405,7,2,0,0,405,63,1,0,0,0,406,407,7,3,0,0,407,65,1,0,0,0,44,67,70,73,76,
79,82,85,88,91,101,118,126,146,153,158,162,165,172,176,187,190,196,200,210,
218,221,229,237,240,250,267,281,283,310,322,336,338,346,356,363,380,387,
400,402];


const atn = new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ATNDeserializer().deserialize(serializedATN);

const decisionsToDFA = atn.decisionToState.map( (ds, index) => new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].dfa.DFA(ds, index) );

const sharedContextCache = new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.PredictionContextCache();

class UVLJavaScriptParser extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].Parser {

    static grammarFileName = "UVLJavaScript.g4";
    static literalNames = [ null, "'include'", "'namespace'", "'imports'", 
                            "'as'", "'features'", "'cardinality'", "'constraint'", 
                            "'constraints'", "'sum'", "'avg'", "'len'", 
                            "'floor'", "'ceil'", "'.'", "'String'", "'Integer'", 
                            "'Real'", "'Arithmetic'", "'Type'", "'group-cardinality'", 
                            "'feature-cardinality'", "'aggregate-function'", 
                            "'string-constraints'", "'('", "')'", "'['", 
                            "']'", "'{'", "'}'", "'/*'", "'*/'", null, "'<INDENT>'", 
                            "'<DEDENT>'", "'or'", "'alternative'", "'optional'", 
                            "'mandatory'", null, "'!'", "'&'", "'|'", "'<=>'", 
                            "'=>'", "'=='", "'<'", "'<='", "'>'", "'>='", 
                            "'!='", "'/'", "'*'", "'+'", "'-'", null, null, 
                            null, "'Boolean'", "','" ];
    static symbolicNames = [ null, null, null, null, null, null, null, null, 
                             null, null, null, null, null, null, null, null, 
                             null, null, null, null, null, null, null, null, 
                             "OPEN_PAREN", "CLOSE_PAREN", "OPEN_BRACK", 
                             "CLOSE_BRACK", "OPEN_BRACE", "CLOSE_BRACE", 
                             "OPEN_COMMENT", "CLOSE_COMMENT", "NEWLINE", 
                             "INDENT", "DEDENT", "ORGROUP", "ALTERNATIVE", 
                             "OPTIONAL", "MANDATORY", "CARDINALITY", "NOT", 
                             "AND", "OR", "EQUIVALENCE", "IMPLICATION", 
                             "EQUAL", "LOWER", "LOWER_EQUALS", "GREATER", 
                             "GREATER_EQUALS", "NOT_EQUALS", "DIV", "MUL", 
                             "ADD", "SUB", "FLOAT", "INTEGER", "BOOLEAN", 
                             "BOOLEAN_KEY", "COMMA", "ID_NOT_STRICT", "ID_STRICT", 
                             "STRING", "SKIP_" ];
    static ruleNames = [ "featureModel", "includes", "includeLine", "namespace", 
                         "imports", "importLine", "features", "group", "groupSpec", 
                         "feature", "featureCardinality", "attributes", 
                         "attribute", "valueAttribute", "key", "value", 
                         "vector", "constraintAttribute", "constraintList", 
                         "constraints", "constraintLine", "constraint", 
                         "equation", "expression", "aggregateFunction", 
                         "stringAggregateFunction", "numericAggregateFunction", 
                         "reference", "id", "featureType", "languageLevel", 
                         "majorLevel", "minorLevel" ];

    constructor(input) {
        super(input);
        this._interp = new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ParserATNSimulator(this, atn, decisionsToDFA, sharedContextCache);
        this.ruleNames = UVLJavaScriptParser.ruleNames;
        this.literalNames = UVLJavaScriptParser.literalNames;
        this.symbolicNames = UVLJavaScriptParser.symbolicNames;
    }

    sempred(localctx, ruleIndex, predIndex) {
    	switch(ruleIndex) {
    	case 21:
    	    		return this.constraint_sempred(localctx, predIndex);
    	case 23:
    	    		return this.expression_sempred(localctx, predIndex);
        default:
            throw "No predicate with index:" + ruleIndex;
       }
    }

    constraint_sempred(localctx, predIndex) {
    	switch(predIndex) {
    		case 0:
    			return this.precpred(this._ctx, 4);
    		case 1:
    			return this.precpred(this._ctx, 3);
    		case 2:
    			return this.precpred(this._ctx, 2);
    		case 3:
    			return this.precpred(this._ctx, 1);
    		default:
    			throw "No predicate with index:" + predIndex;
    	}
    };

    expression_sempred(localctx, predIndex) {
    	switch(predIndex) {
    		case 4:
    			return this.precpred(this._ctx, 4);
    		case 5:
    			return this.precpred(this._ctx, 3);
    		case 6:
    			return this.precpred(this._ctx, 2);
    		case 7:
    			return this.precpred(this._ctx, 1);
    		default:
    			throw "No predicate with index:" + predIndex;
    	}
    };




	featureModel() {
	    let localctx = new FeatureModelContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 0, UVLJavaScriptParser.RULE_featureModel);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 67;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===2) {
	            this.state = 66;
	            this.namespace();
	        }

	        this.state = 70;
	        this._errHandler.sync(this);
	        var la_ = this._interp.adaptivePredict(this._input,1,this._ctx);
	        if(la_===1) {
	            this.state = 69;
	            this.match(UVLJavaScriptParser.NEWLINE);

	        }
	        this.state = 73;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===1) {
	            this.state = 72;
	            this.includes();
	        }

	        this.state = 76;
	        this._errHandler.sync(this);
	        var la_ = this._interp.adaptivePredict(this._input,3,this._ctx);
	        if(la_===1) {
	            this.state = 75;
	            this.match(UVLJavaScriptParser.NEWLINE);

	        }
	        this.state = 79;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===3) {
	            this.state = 78;
	            this.imports();
	        }

	        this.state = 82;
	        this._errHandler.sync(this);
	        var la_ = this._interp.adaptivePredict(this._input,5,this._ctx);
	        if(la_===1) {
	            this.state = 81;
	            this.match(UVLJavaScriptParser.NEWLINE);

	        }
	        this.state = 85;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===5) {
	            this.state = 84;
	            this.features();
	        }

	        this.state = 88;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===32) {
	            this.state = 87;
	            this.match(UVLJavaScriptParser.NEWLINE);
	        }

	        this.state = 91;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===8) {
	            this.state = 90;
	            this.constraints();
	        }

	        this.state = 93;
	        this.match(UVLJavaScriptParser.EOF);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	includes() {
	    let localctx = new IncludesContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 2, UVLJavaScriptParser.RULE_includes);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 95;
	        this.match(UVLJavaScriptParser.T__0);
	        this.state = 96;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 97;
	        this.match(UVLJavaScriptParser.INDENT);
	        this.state = 101;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        while(_la===18 || _la===19 || _la===58) {
	            this.state = 98;
	            this.includeLine();
	            this.state = 103;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	        }
	        this.state = 104;
	        this.match(UVLJavaScriptParser.DEDENT);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	includeLine() {
	    let localctx = new IncludeLineContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 4, UVLJavaScriptParser.RULE_includeLine);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 106;
	        this.languageLevel();
	        this.state = 107;
	        this.match(UVLJavaScriptParser.NEWLINE);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	namespace() {
	    let localctx = new NamespaceContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 6, UVLJavaScriptParser.RULE_namespace);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 109;
	        this.match(UVLJavaScriptParser.T__1);
	        this.state = 110;
	        this.reference();
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	imports() {
	    let localctx = new ImportsContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 8, UVLJavaScriptParser.RULE_imports);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 112;
	        this.match(UVLJavaScriptParser.T__2);
	        this.state = 113;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 114;
	        this.match(UVLJavaScriptParser.INDENT);
	        this.state = 118;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        while(_la===60 || _la===61) {
	            this.state = 115;
	            this.importLine();
	            this.state = 120;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	        }
	        this.state = 121;
	        this.match(UVLJavaScriptParser.DEDENT);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	importLine() {
	    let localctx = new ImportLineContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 10, UVLJavaScriptParser.RULE_importLine);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 123;
	        localctx.ns = this.reference();
	        this.state = 126;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===4) {
	            this.state = 124;
	            this.match(UVLJavaScriptParser.T__3);
	            this.state = 125;
	            localctx.alias = this.reference();
	        }

	        this.state = 128;
	        this.match(UVLJavaScriptParser.NEWLINE);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	features() {
	    let localctx = new FeaturesContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 12, UVLJavaScriptParser.RULE_features);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 130;
	        this.match(UVLJavaScriptParser.T__4);
	        this.state = 131;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 132;
	        this.match(UVLJavaScriptParser.INDENT);
	        this.state = 133;
	        this.feature();
	        this.state = 134;
	        this.match(UVLJavaScriptParser.DEDENT);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	group() {
	    let localctx = new GroupContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 14, UVLJavaScriptParser.RULE_group);
	    try {
	        this.state = 146;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 35:
	            localctx = new OrGroupContext(this, localctx);
	            this.enterOuterAlt(localctx, 1);
	            this.state = 136;
	            this.match(UVLJavaScriptParser.ORGROUP);
	            this.state = 137;
	            this.groupSpec();
	            break;
	        case 36:
	            localctx = new AlternativeGroupContext(this, localctx);
	            this.enterOuterAlt(localctx, 2);
	            this.state = 138;
	            this.match(UVLJavaScriptParser.ALTERNATIVE);
	            this.state = 139;
	            this.groupSpec();
	            break;
	        case 37:
	            localctx = new OptionalGroupContext(this, localctx);
	            this.enterOuterAlt(localctx, 3);
	            this.state = 140;
	            this.match(UVLJavaScriptParser.OPTIONAL);
	            this.state = 141;
	            this.groupSpec();
	            break;
	        case 38:
	            localctx = new MandatoryGroupContext(this, localctx);
	            this.enterOuterAlt(localctx, 4);
	            this.state = 142;
	            this.match(UVLJavaScriptParser.MANDATORY);
	            this.state = 143;
	            this.groupSpec();
	            break;
	        case 39:
	            localctx = new CardinalityGroupContext(this, localctx);
	            this.enterOuterAlt(localctx, 5);
	            this.state = 144;
	            this.match(UVLJavaScriptParser.CARDINALITY);
	            this.state = 145;
	            this.groupSpec();
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	groupSpec() {
	    let localctx = new GroupSpecContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 16, UVLJavaScriptParser.RULE_groupSpec);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 148;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 149;
	        this.match(UVLJavaScriptParser.INDENT);
	        this.state = 151; 
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        do {
	            this.state = 150;
	            this.feature();
	            this.state = 153; 
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	        } while((((_la) & ~0x1f) === 0 && ((1 << _la) & 229376) !== 0) || ((((_la - 58)) & ~0x1f) === 0 && ((1 << (_la - 58)) & 13) !== 0));
	        this.state = 155;
	        this.match(UVLJavaScriptParser.DEDENT);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	feature() {
	    let localctx = new FeatureContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 18, UVLJavaScriptParser.RULE_feature);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 158;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if((((_la) & ~0x1f) === 0 && ((1 << _la) & 229376) !== 0) || _la===58) {
	            this.state = 157;
	            this.featureType();
	        }

	        this.state = 160;
	        this.reference();
	        this.state = 162;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===6) {
	            this.state = 161;
	            this.featureCardinality();
	        }

	        this.state = 165;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===28) {
	            this.state = 164;
	            this.attributes();
	        }

	        this.state = 167;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 176;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===33) {
	            this.state = 168;
	            this.match(UVLJavaScriptParser.INDENT);
	            this.state = 170; 
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	            do {
	                this.state = 169;
	                this.group();
	                this.state = 172; 
	                this._errHandler.sync(this);
	                _la = this._input.LA(1);
	            } while(((((_la - 35)) & ~0x1f) === 0 && ((1 << (_la - 35)) & 31) !== 0));
	            this.state = 174;
	            this.match(UVLJavaScriptParser.DEDENT);
	        }

	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	featureCardinality() {
	    let localctx = new FeatureCardinalityContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 20, UVLJavaScriptParser.RULE_featureCardinality);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 178;
	        this.match(UVLJavaScriptParser.T__5);
	        this.state = 179;
	        this.match(UVLJavaScriptParser.CARDINALITY);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	attributes() {
	    let localctx = new AttributesContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 22, UVLJavaScriptParser.RULE_attributes);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 181;
	        this.match(UVLJavaScriptParser.OPEN_BRACE);
	        this.state = 190;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===7 || _la===8 || _la===60 || _la===61) {
	            this.state = 182;
	            this.attribute();
	            this.state = 187;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	            while(_la===59) {
	                this.state = 183;
	                this.match(UVLJavaScriptParser.COMMA);
	                this.state = 184;
	                this.attribute();
	                this.state = 189;
	                this._errHandler.sync(this);
	                _la = this._input.LA(1);
	            }
	        }

	        this.state = 192;
	        this.match(UVLJavaScriptParser.CLOSE_BRACE);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	attribute() {
	    let localctx = new AttributeContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 24, UVLJavaScriptParser.RULE_attribute);
	    try {
	        this.state = 196;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 60:
	        case 61:
	            this.enterOuterAlt(localctx, 1);
	            this.state = 194;
	            this.valueAttribute();
	            break;
	        case 7:
	        case 8:
	            this.enterOuterAlt(localctx, 2);
	            this.state = 195;
	            this.constraintAttribute();
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	valueAttribute() {
	    let localctx = new ValueAttributeContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 26, UVLJavaScriptParser.RULE_valueAttribute);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 198;
	        this.key();
	        this.state = 200;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===26 || _la===28 || ((((_la - 55)) & ~0x1f) === 0 && ((1 << (_la - 55)) & 135) !== 0)) {
	            this.state = 199;
	            this.value();
	        }

	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	key() {
	    let localctx = new KeyContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 28, UVLJavaScriptParser.RULE_key);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 202;
	        this.id();
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	value() {
	    let localctx = new ValueContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 30, UVLJavaScriptParser.RULE_value);
	    try {
	        this.state = 210;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 57:
	            this.enterOuterAlt(localctx, 1);
	            this.state = 204;
	            this.match(UVLJavaScriptParser.BOOLEAN);
	            break;
	        case 55:
	            this.enterOuterAlt(localctx, 2);
	            this.state = 205;
	            this.match(UVLJavaScriptParser.FLOAT);
	            break;
	        case 56:
	            this.enterOuterAlt(localctx, 3);
	            this.state = 206;
	            this.match(UVLJavaScriptParser.INTEGER);
	            break;
	        case 62:
	            this.enterOuterAlt(localctx, 4);
	            this.state = 207;
	            this.match(UVLJavaScriptParser.STRING);
	            break;
	        case 28:
	            this.enterOuterAlt(localctx, 5);
	            this.state = 208;
	            this.attributes();
	            break;
	        case 26:
	            this.enterOuterAlt(localctx, 6);
	            this.state = 209;
	            this.vector();
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	vector() {
	    let localctx = new VectorContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 32, UVLJavaScriptParser.RULE_vector);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 212;
	        this.match(UVLJavaScriptParser.OPEN_BRACK);
	        this.state = 221;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===26 || _la===28 || ((((_la - 55)) & ~0x1f) === 0 && ((1 << (_la - 55)) & 135) !== 0)) {
	            this.state = 213;
	            this.value();
	            this.state = 218;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	            while(_la===59) {
	                this.state = 214;
	                this.match(UVLJavaScriptParser.COMMA);
	                this.state = 215;
	                this.value();
	                this.state = 220;
	                this._errHandler.sync(this);
	                _la = this._input.LA(1);
	            }
	        }

	        this.state = 223;
	        this.match(UVLJavaScriptParser.CLOSE_BRACK);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	constraintAttribute() {
	    let localctx = new ConstraintAttributeContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 34, UVLJavaScriptParser.RULE_constraintAttribute);
	    try {
	        this.state = 229;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 7:
	            localctx = new SingleConstraintAttributeContext(this, localctx);
	            this.enterOuterAlt(localctx, 1);
	            this.state = 225;
	            this.match(UVLJavaScriptParser.T__6);
	            this.state = 226;
	            this.constraint(0);
	            break;
	        case 8:
	            localctx = new ListConstraintAttributeContext(this, localctx);
	            this.enterOuterAlt(localctx, 2);
	            this.state = 227;
	            this.match(UVLJavaScriptParser.T__7);
	            this.state = 228;
	            this.constraintList();
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	constraintList() {
	    let localctx = new ConstraintListContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 36, UVLJavaScriptParser.RULE_constraintList);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 231;
	        this.match(UVLJavaScriptParser.OPEN_BRACK);
	        this.state = 240;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if((((_la) & ~0x1f) === 0 && ((1 << _la) & 16793088) !== 0) || ((((_la - 40)) & ~0x1f) === 0 && ((1 << (_la - 40)) & 7438337) !== 0)) {
	            this.state = 232;
	            this.constraint(0);
	            this.state = 237;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	            while(_la===59) {
	                this.state = 233;
	                this.match(UVLJavaScriptParser.COMMA);
	                this.state = 234;
	                this.constraint(0);
	                this.state = 239;
	                this._errHandler.sync(this);
	                _la = this._input.LA(1);
	            }
	        }

	        this.state = 242;
	        this.match(UVLJavaScriptParser.CLOSE_BRACK);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	constraints() {
	    let localctx = new ConstraintsContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 38, UVLJavaScriptParser.RULE_constraints);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 244;
	        this.match(UVLJavaScriptParser.T__7);
	        this.state = 245;
	        this.match(UVLJavaScriptParser.NEWLINE);
	        this.state = 246;
	        this.match(UVLJavaScriptParser.INDENT);
	        this.state = 250;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        while((((_la) & ~0x1f) === 0 && ((1 << _la) & 16793088) !== 0) || ((((_la - 40)) & ~0x1f) === 0 && ((1 << (_la - 40)) & 7438337) !== 0)) {
	            this.state = 247;
	            this.constraintLine();
	            this.state = 252;
	            this._errHandler.sync(this);
	            _la = this._input.LA(1);
	        }
	        this.state = 253;
	        this.match(UVLJavaScriptParser.DEDENT);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	constraintLine() {
	    let localctx = new ConstraintLineContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 40, UVLJavaScriptParser.RULE_constraintLine);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 255;
	        this.constraint(0);
	        this.state = 256;
	        this.match(UVLJavaScriptParser.NEWLINE);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}


	constraint(_p) {
		if(_p===undefined) {
		    _p = 0;
		}
	    const _parentctx = this._ctx;
	    const _parentState = this.state;
	    let localctx = new ConstraintContext(this, this._ctx, _parentState);
	    let _prevctx = localctx;
	    const _startState = 42;
	    this.enterRecursionRule(localctx, 42, UVLJavaScriptParser.RULE_constraint, _p);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 267;
	        this._errHandler.sync(this);
	        var la_ = this._interp.adaptivePredict(this._input,30,this._ctx);
	        switch(la_) {
	        case 1:
	            localctx = new EquationConstraintContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;

	            this.state = 259;
	            this.equation();
	            break;

	        case 2:
	            localctx = new LiteralConstraintContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 260;
	            this.reference();
	            break;

	        case 3:
	            localctx = new ParenthesisConstraintContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 261;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 262;
	            this.constraint(0);
	            this.state = 263;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;

	        case 4:
	            localctx = new NotConstraintContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 265;
	            this.match(UVLJavaScriptParser.NOT);
	            this.state = 266;
	            this.constraint(5);
	            break;

	        }
	        this._ctx.stop = this._input.LT(-1);
	        this.state = 283;
	        this._errHandler.sync(this);
	        var _alt = this._interp.adaptivePredict(this._input,32,this._ctx)
	        while(_alt!=2 && _alt!=antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ATN.INVALID_ALT_NUMBER) {
	            if(_alt===1) {
	                if(this._parseListeners!==null) {
	                    this.triggerExitRuleEvent();
	                }
	                _prevctx = localctx;
	                this.state = 281;
	                this._errHandler.sync(this);
	                var la_ = this._interp.adaptivePredict(this._input,31,this._ctx);
	                switch(la_) {
	                case 1:
	                    localctx = new AndConstraintContext(this, new ConstraintContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_constraint);
	                    this.state = 269;
	                    if (!( this.precpred(this._ctx, 4))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 4)");
	                    }
	                    this.state = 270;
	                    this.match(UVLJavaScriptParser.AND);
	                    this.state = 271;
	                    this.constraint(5);
	                    break;

	                case 2:
	                    localctx = new OrConstraintContext(this, new ConstraintContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_constraint);
	                    this.state = 272;
	                    if (!( this.precpred(this._ctx, 3))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 3)");
	                    }
	                    this.state = 273;
	                    this.match(UVLJavaScriptParser.OR);
	                    this.state = 274;
	                    this.constraint(4);
	                    break;

	                case 3:
	                    localctx = new ImplicationConstraintContext(this, new ConstraintContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_constraint);
	                    this.state = 275;
	                    if (!( this.precpred(this._ctx, 2))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 2)");
	                    }
	                    this.state = 276;
	                    this.match(UVLJavaScriptParser.IMPLICATION);
	                    this.state = 277;
	                    this.constraint(3);
	                    break;

	                case 4:
	                    localctx = new EquivalenceConstraintContext(this, new ConstraintContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_constraint);
	                    this.state = 278;
	                    if (!( this.precpred(this._ctx, 1))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 1)");
	                    }
	                    this.state = 279;
	                    this.match(UVLJavaScriptParser.EQUIVALENCE);
	                    this.state = 280;
	                    this.constraint(2);
	                    break;

	                } 
	            }
	            this.state = 285;
	            this._errHandler.sync(this);
	            _alt = this._interp.adaptivePredict(this._input,32,this._ctx);
	        }

	    } catch( error) {
	        if(error instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = error;
		        this._errHandler.reportError(this, error);
		        this._errHandler.recover(this, error);
		    } else {
		    	throw error;
		    }
	    } finally {
	        this.unrollRecursionContexts(_parentctx)
	    }
	    return localctx;
	}



	equation() {
	    let localctx = new EquationContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 44, UVLJavaScriptParser.RULE_equation);
	    try {
	        this.state = 310;
	        this._errHandler.sync(this);
	        var la_ = this._interp.adaptivePredict(this._input,33,this._ctx);
	        switch(la_) {
	        case 1:
	            localctx = new EqualEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 1);
	            this.state = 286;
	            this.expression(0);
	            this.state = 287;
	            this.match(UVLJavaScriptParser.EQUAL);
	            this.state = 288;
	            this.expression(0);
	            break;

	        case 2:
	            localctx = new LowerEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 2);
	            this.state = 290;
	            this.expression(0);
	            this.state = 291;
	            this.match(UVLJavaScriptParser.LOWER);
	            this.state = 292;
	            this.expression(0);
	            break;

	        case 3:
	            localctx = new GreaterEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 3);
	            this.state = 294;
	            this.expression(0);
	            this.state = 295;
	            this.match(UVLJavaScriptParser.GREATER);
	            this.state = 296;
	            this.expression(0);
	            break;

	        case 4:
	            localctx = new LowerEqualsEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 4);
	            this.state = 298;
	            this.expression(0);
	            this.state = 299;
	            this.match(UVLJavaScriptParser.LOWER_EQUALS);
	            this.state = 300;
	            this.expression(0);
	            break;

	        case 5:
	            localctx = new GreaterEqualsEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 5);
	            this.state = 302;
	            this.expression(0);
	            this.state = 303;
	            this.match(UVLJavaScriptParser.GREATER_EQUALS);
	            this.state = 304;
	            this.expression(0);
	            break;

	        case 6:
	            localctx = new NotEqualsEquationContext(this, localctx);
	            this.enterOuterAlt(localctx, 6);
	            this.state = 306;
	            this.expression(0);
	            this.state = 307;
	            this.match(UVLJavaScriptParser.NOT_EQUALS);
	            this.state = 308;
	            this.expression(0);
	            break;

	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}


	expression(_p) {
		if(_p===undefined) {
		    _p = 0;
		}
	    const _parentctx = this._ctx;
	    const _parentState = this.state;
	    let localctx = new ExpressionContext(this, this._ctx, _parentState);
	    let _prevctx = localctx;
	    const _startState = 46;
	    this.enterRecursionRule(localctx, 46, UVLJavaScriptParser.RULE_expression, _p);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 322;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 55:
	            localctx = new FloatLiteralExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;

	            this.state = 313;
	            this.match(UVLJavaScriptParser.FLOAT);
	            break;
	        case 56:
	            localctx = new IntegerLiteralExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 314;
	            this.match(UVLJavaScriptParser.INTEGER);
	            break;
	        case 62:
	            localctx = new StringLiteralExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 315;
	            this.match(UVLJavaScriptParser.STRING);
	            break;
	        case 9:
	        case 10:
	        case 11:
	        case 12:
	        case 13:
	            localctx = new AggregateFunctionExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 316;
	            this.aggregateFunction();
	            break;
	        case 60:
	        case 61:
	            localctx = new LiteralExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 317;
	            this.reference();
	            break;
	        case 24:
	            localctx = new BracketExpressionContext(this, localctx);
	            this._ctx = localctx;
	            _prevctx = localctx;
	            this.state = 318;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 319;
	            this.expression(0);
	            this.state = 320;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	        this._ctx.stop = this._input.LT(-1);
	        this.state = 338;
	        this._errHandler.sync(this);
	        var _alt = this._interp.adaptivePredict(this._input,36,this._ctx)
	        while(_alt!=2 && _alt!=antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ATN.INVALID_ALT_NUMBER) {
	            if(_alt===1) {
	                if(this._parseListeners!==null) {
	                    this.triggerExitRuleEvent();
	                }
	                _prevctx = localctx;
	                this.state = 336;
	                this._errHandler.sync(this);
	                var la_ = this._interp.adaptivePredict(this._input,35,this._ctx);
	                switch(la_) {
	                case 1:
	                    localctx = new AddExpressionContext(this, new ExpressionContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_expression);
	                    this.state = 324;
	                    if (!( this.precpred(this._ctx, 4))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 4)");
	                    }
	                    this.state = 325;
	                    this.match(UVLJavaScriptParser.ADD);
	                    this.state = 326;
	                    this.expression(5);
	                    break;

	                case 2:
	                    localctx = new SubExpressionContext(this, new ExpressionContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_expression);
	                    this.state = 327;
	                    if (!( this.precpred(this._ctx, 3))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 3)");
	                    }
	                    this.state = 328;
	                    this.match(UVLJavaScriptParser.SUB);
	                    this.state = 329;
	                    this.expression(4);
	                    break;

	                case 3:
	                    localctx = new MulExpressionContext(this, new ExpressionContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_expression);
	                    this.state = 330;
	                    if (!( this.precpred(this._ctx, 2))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 2)");
	                    }
	                    this.state = 331;
	                    this.match(UVLJavaScriptParser.MUL);
	                    this.state = 332;
	                    this.expression(3);
	                    break;

	                case 4:
	                    localctx = new DivExpressionContext(this, new ExpressionContext(this, _parentctx, _parentState));
	                    this.pushNewRecursionContext(localctx, _startState, UVLJavaScriptParser.RULE_expression);
	                    this.state = 333;
	                    if (!( this.precpred(this._ctx, 1))) {
	                        throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.FailedPredicateException(this, "this.precpred(this._ctx, 1)");
	                    }
	                    this.state = 334;
	                    this.match(UVLJavaScriptParser.DIV);
	                    this.state = 335;
	                    this.expression(2);
	                    break;

	                } 
	            }
	            this.state = 340;
	            this._errHandler.sync(this);
	            _alt = this._interp.adaptivePredict(this._input,36,this._ctx);
	        }

	    } catch( error) {
	        if(error instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = error;
		        this._errHandler.reportError(this, error);
		        this._errHandler.recover(this, error);
		    } else {
		    	throw error;
		    }
	    } finally {
	        this.unrollRecursionContexts(_parentctx)
	    }
	    return localctx;
	}



	aggregateFunction() {
	    let localctx = new AggregateFunctionContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 48, UVLJavaScriptParser.RULE_aggregateFunction);
	    try {
	        this.state = 363;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 9:
	            localctx = new SumAggregateFunctionContext(this, localctx);
	            this.enterOuterAlt(localctx, 1);
	            this.state = 341;
	            this.match(UVLJavaScriptParser.T__8);
	            this.state = 342;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 346;
	            this._errHandler.sync(this);
	            var la_ = this._interp.adaptivePredict(this._input,37,this._ctx);
	            if(la_===1) {
	                this.state = 343;
	                this.reference();
	                this.state = 344;
	                this.match(UVLJavaScriptParser.COMMA);

	            }
	            this.state = 348;
	            this.reference();
	            this.state = 349;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;
	        case 10:
	            localctx = new AvgAggregateFunctionContext(this, localctx);
	            this.enterOuterAlt(localctx, 2);
	            this.state = 351;
	            this.match(UVLJavaScriptParser.T__9);
	            this.state = 352;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 356;
	            this._errHandler.sync(this);
	            var la_ = this._interp.adaptivePredict(this._input,38,this._ctx);
	            if(la_===1) {
	                this.state = 353;
	                this.reference();
	                this.state = 354;
	                this.match(UVLJavaScriptParser.COMMA);

	            }
	            this.state = 358;
	            this.reference();
	            this.state = 359;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;
	        case 11:
	            localctx = new StringAggregateFunctionExpressionContext(this, localctx);
	            this.enterOuterAlt(localctx, 3);
	            this.state = 361;
	            this.stringAggregateFunction();
	            break;
	        case 12:
	        case 13:
	            localctx = new NumericAggregateFunctionExpressionContext(this, localctx);
	            this.enterOuterAlt(localctx, 4);
	            this.state = 362;
	            this.numericAggregateFunction();
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	stringAggregateFunction() {
	    let localctx = new StringAggregateFunctionContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 50, UVLJavaScriptParser.RULE_stringAggregateFunction);
	    try {
	        localctx = new LengthAggregateFunctionContext(this, localctx);
	        this.enterOuterAlt(localctx, 1);
	        this.state = 365;
	        this.match(UVLJavaScriptParser.T__10);
	        this.state = 366;
	        this.match(UVLJavaScriptParser.OPEN_PAREN);
	        this.state = 367;
	        this.reference();
	        this.state = 368;
	        this.match(UVLJavaScriptParser.CLOSE_PAREN);
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	numericAggregateFunction() {
	    let localctx = new NumericAggregateFunctionContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 52, UVLJavaScriptParser.RULE_numericAggregateFunction);
	    try {
	        this.state = 380;
	        this._errHandler.sync(this);
	        switch(this._input.LA(1)) {
	        case 12:
	            localctx = new FloorAggregateFunctionContext(this, localctx);
	            this.enterOuterAlt(localctx, 1);
	            this.state = 370;
	            this.match(UVLJavaScriptParser.T__11);
	            this.state = 371;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 372;
	            this.reference();
	            this.state = 373;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;
	        case 13:
	            localctx = new CeilAggregateFunctionContext(this, localctx);
	            this.enterOuterAlt(localctx, 2);
	            this.state = 375;
	            this.match(UVLJavaScriptParser.T__12);
	            this.state = 376;
	            this.match(UVLJavaScriptParser.OPEN_PAREN);
	            this.state = 377;
	            this.reference();
	            this.state = 378;
	            this.match(UVLJavaScriptParser.CLOSE_PAREN);
	            break;
	        default:
	            throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	reference() {
	    let localctx = new ReferenceContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 54, UVLJavaScriptParser.RULE_reference);
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 387;
	        this._errHandler.sync(this);
	        var _alt = this._interp.adaptivePredict(this._input,41,this._ctx)
	        while(_alt!=2 && _alt!=antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].atn.ATN.INVALID_ALT_NUMBER) {
	            if(_alt===1) {
	                this.state = 382;
	                this.id();
	                this.state = 383;
	                this.match(UVLJavaScriptParser.T__13); 
	            }
	            this.state = 389;
	            this._errHandler.sync(this);
	            _alt = this._interp.adaptivePredict(this._input,41,this._ctx);
	        }

	        this.state = 390;
	        this.id();
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	id() {
	    let localctx = new IdContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 56, UVLJavaScriptParser.RULE_id);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 392;
	        _la = this._input.LA(1);
	        if(!(_la===60 || _la===61)) {
	        this._errHandler.recoverInline(this);
	        }
	        else {
	        	this._errHandler.reportMatch(this);
	            this.consume();
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	featureType() {
	    let localctx = new FeatureTypeContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 58, UVLJavaScriptParser.RULE_featureType);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 394;
	        _la = this._input.LA(1);
	        if(!((((_la) & ~0x1f) === 0 && ((1 << _la) & 229376) !== 0) || _la===58)) {
	        this._errHandler.recoverInline(this);
	        }
	        else {
	        	this._errHandler.reportMatch(this);
	            this.consume();
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	languageLevel() {
	    let localctx = new LanguageLevelContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 60, UVLJavaScriptParser.RULE_languageLevel);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 396;
	        this.majorLevel();
	        this.state = 402;
	        this._errHandler.sync(this);
	        _la = this._input.LA(1);
	        if(_la===14) {
	            this.state = 397;
	            this.match(UVLJavaScriptParser.T__13);
	            this.state = 400;
	            this._errHandler.sync(this);
	            switch(this._input.LA(1)) {
	            case 20:
	            case 21:
	            case 22:
	            case 23:
	                this.state = 398;
	                this.minorLevel();
	                break;
	            case 52:
	                this.state = 399;
	                this.match(UVLJavaScriptParser.MUL);
	                break;
	            default:
	                throw new antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.NoViableAltException(this);
	            }
	        }

	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	majorLevel() {
	    let localctx = new MajorLevelContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 62, UVLJavaScriptParser.RULE_majorLevel);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 404;
	        _la = this._input.LA(1);
	        if(!(_la===18 || _la===19 || _la===58)) {
	        this._errHandler.recoverInline(this);
	        }
	        else {
	        	this._errHandler.reportMatch(this);
	            this.consume();
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}



	minorLevel() {
	    let localctx = new MinorLevelContext(this, this._ctx, this.state);
	    this.enterRule(localctx, 64, UVLJavaScriptParser.RULE_minorLevel);
	    var _la = 0;
	    try {
	        this.enterOuterAlt(localctx, 1);
	        this.state = 406;
	        _la = this._input.LA(1);
	        if(!((((_la) & ~0x1f) === 0 && ((1 << _la) & 15728640) !== 0))) {
	        this._errHandler.recoverInline(this);
	        }
	        else {
	        	this._errHandler.reportMatch(this);
	            this.consume();
	        }
	    } catch (re) {
	    	if(re instanceof antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].error.RecognitionException) {
		        localctx.exception = re;
		        this._errHandler.reportError(this, re);
		        this._errHandler.recover(this, re);
		    } else {
		    	throw re;
		    }
	    } finally {
	        this.exitRule();
	    }
	    return localctx;
	}


}

UVLJavaScriptParser.EOF = antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].Token.EOF;
UVLJavaScriptParser.T__0 = 1;
UVLJavaScriptParser.T__1 = 2;
UVLJavaScriptParser.T__2 = 3;
UVLJavaScriptParser.T__3 = 4;
UVLJavaScriptParser.T__4 = 5;
UVLJavaScriptParser.T__5 = 6;
UVLJavaScriptParser.T__6 = 7;
UVLJavaScriptParser.T__7 = 8;
UVLJavaScriptParser.T__8 = 9;
UVLJavaScriptParser.T__9 = 10;
UVLJavaScriptParser.T__10 = 11;
UVLJavaScriptParser.T__11 = 12;
UVLJavaScriptParser.T__12 = 13;
UVLJavaScriptParser.T__13 = 14;
UVLJavaScriptParser.T__14 = 15;
UVLJavaScriptParser.T__15 = 16;
UVLJavaScriptParser.T__16 = 17;
UVLJavaScriptParser.T__17 = 18;
UVLJavaScriptParser.T__18 = 19;
UVLJavaScriptParser.T__19 = 20;
UVLJavaScriptParser.T__20 = 21;
UVLJavaScriptParser.T__21 = 22;
UVLJavaScriptParser.T__22 = 23;
UVLJavaScriptParser.OPEN_PAREN = 24;
UVLJavaScriptParser.CLOSE_PAREN = 25;
UVLJavaScriptParser.OPEN_BRACK = 26;
UVLJavaScriptParser.CLOSE_BRACK = 27;
UVLJavaScriptParser.OPEN_BRACE = 28;
UVLJavaScriptParser.CLOSE_BRACE = 29;
UVLJavaScriptParser.OPEN_COMMENT = 30;
UVLJavaScriptParser.CLOSE_COMMENT = 31;
UVLJavaScriptParser.NEWLINE = 32;
UVLJavaScriptParser.INDENT = 33;
UVLJavaScriptParser.DEDENT = 34;
UVLJavaScriptParser.ORGROUP = 35;
UVLJavaScriptParser.ALTERNATIVE = 36;
UVLJavaScriptParser.OPTIONAL = 37;
UVLJavaScriptParser.MANDATORY = 38;
UVLJavaScriptParser.CARDINALITY = 39;
UVLJavaScriptParser.NOT = 40;
UVLJavaScriptParser.AND = 41;
UVLJavaScriptParser.OR = 42;
UVLJavaScriptParser.EQUIVALENCE = 43;
UVLJavaScriptParser.IMPLICATION = 44;
UVLJavaScriptParser.EQUAL = 45;
UVLJavaScriptParser.LOWER = 46;
UVLJavaScriptParser.LOWER_EQUALS = 47;
UVLJavaScriptParser.GREATER = 48;
UVLJavaScriptParser.GREATER_EQUALS = 49;
UVLJavaScriptParser.NOT_EQUALS = 50;
UVLJavaScriptParser.DIV = 51;
UVLJavaScriptParser.MUL = 52;
UVLJavaScriptParser.ADD = 53;
UVLJavaScriptParser.SUB = 54;
UVLJavaScriptParser.FLOAT = 55;
UVLJavaScriptParser.INTEGER = 56;
UVLJavaScriptParser.BOOLEAN = 57;
UVLJavaScriptParser.BOOLEAN_KEY = 58;
UVLJavaScriptParser.COMMA = 59;
UVLJavaScriptParser.ID_NOT_STRICT = 60;
UVLJavaScriptParser.ID_STRICT = 61;
UVLJavaScriptParser.STRING = 62;
UVLJavaScriptParser.SKIP_ = 63;

UVLJavaScriptParser.RULE_featureModel = 0;
UVLJavaScriptParser.RULE_includes = 1;
UVLJavaScriptParser.RULE_includeLine = 2;
UVLJavaScriptParser.RULE_namespace = 3;
UVLJavaScriptParser.RULE_imports = 4;
UVLJavaScriptParser.RULE_importLine = 5;
UVLJavaScriptParser.RULE_features = 6;
UVLJavaScriptParser.RULE_group = 7;
UVLJavaScriptParser.RULE_groupSpec = 8;
UVLJavaScriptParser.RULE_feature = 9;
UVLJavaScriptParser.RULE_featureCardinality = 10;
UVLJavaScriptParser.RULE_attributes = 11;
UVLJavaScriptParser.RULE_attribute = 12;
UVLJavaScriptParser.RULE_valueAttribute = 13;
UVLJavaScriptParser.RULE_key = 14;
UVLJavaScriptParser.RULE_value = 15;
UVLJavaScriptParser.RULE_vector = 16;
UVLJavaScriptParser.RULE_constraintAttribute = 17;
UVLJavaScriptParser.RULE_constraintList = 18;
UVLJavaScriptParser.RULE_constraints = 19;
UVLJavaScriptParser.RULE_constraintLine = 20;
UVLJavaScriptParser.RULE_constraint = 21;
UVLJavaScriptParser.RULE_equation = 22;
UVLJavaScriptParser.RULE_expression = 23;
UVLJavaScriptParser.RULE_aggregateFunction = 24;
UVLJavaScriptParser.RULE_stringAggregateFunction = 25;
UVLJavaScriptParser.RULE_numericAggregateFunction = 26;
UVLJavaScriptParser.RULE_reference = 27;
UVLJavaScriptParser.RULE_id = 28;
UVLJavaScriptParser.RULE_featureType = 29;
UVLJavaScriptParser.RULE_languageLevel = 30;
UVLJavaScriptParser.RULE_majorLevel = 31;
UVLJavaScriptParser.RULE_minorLevel = 32;

class FeatureModelContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_featureModel;
    }

	EOF() {
	    return this.getToken(UVLJavaScriptParser.EOF, 0);
	};

	namespace() {
	    return this.getTypedRuleContext(NamespaceContext,0);
	};

	NEWLINE = function(i) {
		if(i===undefined) {
			i = null;
		}
	    if(i===null) {
	        return this.getTokens(UVLJavaScriptParser.NEWLINE);
	    } else {
	        return this.getToken(UVLJavaScriptParser.NEWLINE, i);
	    }
	};


	includes() {
	    return this.getTypedRuleContext(IncludesContext,0);
	};

	imports() {
	    return this.getTypedRuleContext(ImportsContext,0);
	};

	features() {
	    return this.getTypedRuleContext(FeaturesContext,0);
	};

	constraints() {
	    return this.getTypedRuleContext(ConstraintsContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFeatureModel(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFeatureModel(this);
		}
	}


}



class IncludesContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_includes;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	includeLine = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(IncludeLineContext);
	    } else {
	        return this.getTypedRuleContext(IncludeLineContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterIncludes(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitIncludes(this);
		}
	}


}



class IncludeLineContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_includeLine;
    }

	languageLevel() {
	    return this.getTypedRuleContext(LanguageLevelContext,0);
	};

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterIncludeLine(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitIncludeLine(this);
		}
	}


}



class NamespaceContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_namespace;
    }

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterNamespace(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitNamespace(this);
		}
	}


}



class ImportsContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_imports;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	importLine = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ImportLineContext);
	    } else {
	        return this.getTypedRuleContext(ImportLineContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterImports(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitImports(this);
		}
	}


}



class ImportLineContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_importLine;
        this.ns = null;
        this.alias = null;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	reference = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ReferenceContext);
	    } else {
	        return this.getTypedRuleContext(ReferenceContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterImportLine(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitImportLine(this);
		}
	}


}



class FeaturesContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_features;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	feature() {
	    return this.getTypedRuleContext(FeatureContext,0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFeatures(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFeatures(this);
		}
	}


}



class GroupContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_group;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class AlternativeGroupContext extends GroupContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	ALTERNATIVE() {
	    return this.getToken(UVLJavaScriptParser.ALTERNATIVE, 0);
	};

	groupSpec() {
	    return this.getTypedRuleContext(GroupSpecContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAlternativeGroup(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAlternativeGroup(this);
		}
	}


}

UVLJavaScriptParser.AlternativeGroupContext = AlternativeGroupContext;

class OptionalGroupContext extends GroupContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPTIONAL() {
	    return this.getToken(UVLJavaScriptParser.OPTIONAL, 0);
	};

	groupSpec() {
	    return this.getTypedRuleContext(GroupSpecContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterOptionalGroup(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitOptionalGroup(this);
		}
	}


}

UVLJavaScriptParser.OptionalGroupContext = OptionalGroupContext;

class MandatoryGroupContext extends GroupContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	MANDATORY() {
	    return this.getToken(UVLJavaScriptParser.MANDATORY, 0);
	};

	groupSpec() {
	    return this.getTypedRuleContext(GroupSpecContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterMandatoryGroup(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitMandatoryGroup(this);
		}
	}


}

UVLJavaScriptParser.MandatoryGroupContext = MandatoryGroupContext;

class CardinalityGroupContext extends GroupContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	CARDINALITY() {
	    return this.getToken(UVLJavaScriptParser.CARDINALITY, 0);
	};

	groupSpec() {
	    return this.getTypedRuleContext(GroupSpecContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterCardinalityGroup(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitCardinalityGroup(this);
		}
	}


}

UVLJavaScriptParser.CardinalityGroupContext = CardinalityGroupContext;

class OrGroupContext extends GroupContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	ORGROUP() {
	    return this.getToken(UVLJavaScriptParser.ORGROUP, 0);
	};

	groupSpec() {
	    return this.getTypedRuleContext(GroupSpecContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterOrGroup(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitOrGroup(this);
		}
	}


}

UVLJavaScriptParser.OrGroupContext = OrGroupContext;

class GroupSpecContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_groupSpec;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	feature = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(FeatureContext);
	    } else {
	        return this.getTypedRuleContext(FeatureContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterGroupSpec(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitGroupSpec(this);
		}
	}


}



class FeatureContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_feature;
    }

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	featureType() {
	    return this.getTypedRuleContext(FeatureTypeContext,0);
	};

	featureCardinality() {
	    return this.getTypedRuleContext(FeatureCardinalityContext,0);
	};

	attributes() {
	    return this.getTypedRuleContext(AttributesContext,0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	group = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(GroupContext);
	    } else {
	        return this.getTypedRuleContext(GroupContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFeature(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFeature(this);
		}
	}


}



class FeatureCardinalityContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_featureCardinality;
    }

	CARDINALITY() {
	    return this.getToken(UVLJavaScriptParser.CARDINALITY, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFeatureCardinality(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFeatureCardinality(this);
		}
	}


}



class AttributesContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_attributes;
    }

	OPEN_BRACE() {
	    return this.getToken(UVLJavaScriptParser.OPEN_BRACE, 0);
	};

	CLOSE_BRACE() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_BRACE, 0);
	};

	attribute = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(AttributeContext);
	    } else {
	        return this.getTypedRuleContext(AttributeContext,i);
	    }
	};

	COMMA = function(i) {
		if(i===undefined) {
			i = null;
		}
	    if(i===null) {
	        return this.getTokens(UVLJavaScriptParser.COMMA);
	    } else {
	        return this.getToken(UVLJavaScriptParser.COMMA, i);
	    }
	};


	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAttributes(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAttributes(this);
		}
	}


}



class AttributeContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_attribute;
    }

	valueAttribute() {
	    return this.getTypedRuleContext(ValueAttributeContext,0);
	};

	constraintAttribute() {
	    return this.getTypedRuleContext(ConstraintAttributeContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAttribute(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAttribute(this);
		}
	}


}



class ValueAttributeContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_valueAttribute;
    }

	key() {
	    return this.getTypedRuleContext(KeyContext,0);
	};

	value() {
	    return this.getTypedRuleContext(ValueContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterValueAttribute(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitValueAttribute(this);
		}
	}


}



class KeyContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_key;
    }

	id() {
	    return this.getTypedRuleContext(IdContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterKey(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitKey(this);
		}
	}


}



class ValueContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_value;
    }

	BOOLEAN() {
	    return this.getToken(UVLJavaScriptParser.BOOLEAN, 0);
	};

	FLOAT() {
	    return this.getToken(UVLJavaScriptParser.FLOAT, 0);
	};

	INTEGER() {
	    return this.getToken(UVLJavaScriptParser.INTEGER, 0);
	};

	STRING() {
	    return this.getToken(UVLJavaScriptParser.STRING, 0);
	};

	attributes() {
	    return this.getTypedRuleContext(AttributesContext,0);
	};

	vector() {
	    return this.getTypedRuleContext(VectorContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterValue(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitValue(this);
		}
	}


}



class VectorContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_vector;
    }

	OPEN_BRACK() {
	    return this.getToken(UVLJavaScriptParser.OPEN_BRACK, 0);
	};

	CLOSE_BRACK() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_BRACK, 0);
	};

	value = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ValueContext);
	    } else {
	        return this.getTypedRuleContext(ValueContext,i);
	    }
	};

	COMMA = function(i) {
		if(i===undefined) {
			i = null;
		}
	    if(i===null) {
	        return this.getTokens(UVLJavaScriptParser.COMMA);
	    } else {
	        return this.getToken(UVLJavaScriptParser.COMMA, i);
	    }
	};


	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterVector(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitVector(this);
		}
	}


}



class ConstraintAttributeContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_constraintAttribute;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class ListConstraintAttributeContext extends ConstraintAttributeContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraintList() {
	    return this.getTypedRuleContext(ConstraintListContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterListConstraintAttribute(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitListConstraintAttribute(this);
		}
	}


}

UVLJavaScriptParser.ListConstraintAttributeContext = ListConstraintAttributeContext;

class SingleConstraintAttributeContext extends ConstraintAttributeContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraint() {
	    return this.getTypedRuleContext(ConstraintContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterSingleConstraintAttribute(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitSingleConstraintAttribute(this);
		}
	}


}

UVLJavaScriptParser.SingleConstraintAttributeContext = SingleConstraintAttributeContext;

class ConstraintListContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_constraintList;
    }

	OPEN_BRACK() {
	    return this.getToken(UVLJavaScriptParser.OPEN_BRACK, 0);
	};

	CLOSE_BRACK() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_BRACK, 0);
	};

	constraint = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintContext,i);
	    }
	};

	COMMA = function(i) {
		if(i===undefined) {
			i = null;
		}
	    if(i===null) {
	        return this.getTokens(UVLJavaScriptParser.COMMA);
	    } else {
	        return this.getToken(UVLJavaScriptParser.COMMA, i);
	    }
	};


	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterConstraintList(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitConstraintList(this);
		}
	}


}



class ConstraintsContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_constraints;
    }

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	INDENT() {
	    return this.getToken(UVLJavaScriptParser.INDENT, 0);
	};

	DEDENT() {
	    return this.getToken(UVLJavaScriptParser.DEDENT, 0);
	};

	constraintLine = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintLineContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintLineContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterConstraints(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitConstraints(this);
		}
	}


}



class ConstraintLineContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_constraintLine;
    }

	constraint() {
	    return this.getTypedRuleContext(ConstraintContext,0);
	};

	NEWLINE() {
	    return this.getToken(UVLJavaScriptParser.NEWLINE, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterConstraintLine(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitConstraintLine(this);
		}
	}


}



class ConstraintContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_constraint;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class OrConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraint = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintContext,i);
	    }
	};

	OR() {
	    return this.getToken(UVLJavaScriptParser.OR, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterOrConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitOrConstraint(this);
		}
	}


}

UVLJavaScriptParser.OrConstraintContext = OrConstraintContext;

class EquationConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	equation() {
	    return this.getTypedRuleContext(EquationContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterEquationConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitEquationConstraint(this);
		}
	}


}

UVLJavaScriptParser.EquationConstraintContext = EquationConstraintContext;

class LiteralConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLiteralConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLiteralConstraint(this);
		}
	}


}

UVLJavaScriptParser.LiteralConstraintContext = LiteralConstraintContext;

class ParenthesisConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	constraint() {
	    return this.getTypedRuleContext(ConstraintContext,0);
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterParenthesisConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitParenthesisConstraint(this);
		}
	}


}

UVLJavaScriptParser.ParenthesisConstraintContext = ParenthesisConstraintContext;

class NotConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	NOT() {
	    return this.getToken(UVLJavaScriptParser.NOT, 0);
	};

	constraint() {
	    return this.getTypedRuleContext(ConstraintContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterNotConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitNotConstraint(this);
		}
	}


}

UVLJavaScriptParser.NotConstraintContext = NotConstraintContext;

class AndConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraint = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintContext,i);
	    }
	};

	AND() {
	    return this.getToken(UVLJavaScriptParser.AND, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAndConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAndConstraint(this);
		}
	}


}

UVLJavaScriptParser.AndConstraintContext = AndConstraintContext;

class EquivalenceConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraint = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintContext,i);
	    }
	};

	EQUIVALENCE() {
	    return this.getToken(UVLJavaScriptParser.EQUIVALENCE, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterEquivalenceConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitEquivalenceConstraint(this);
		}
	}


}

UVLJavaScriptParser.EquivalenceConstraintContext = EquivalenceConstraintContext;

class ImplicationConstraintContext extends ConstraintContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	constraint = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ConstraintContext);
	    } else {
	        return this.getTypedRuleContext(ConstraintContext,i);
	    }
	};

	IMPLICATION() {
	    return this.getToken(UVLJavaScriptParser.IMPLICATION, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterImplicationConstraint(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitImplicationConstraint(this);
		}
	}


}

UVLJavaScriptParser.ImplicationConstraintContext = ImplicationConstraintContext;

class EquationContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_equation;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class EqualEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	EQUAL() {
	    return this.getToken(UVLJavaScriptParser.EQUAL, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterEqualEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitEqualEquation(this);
		}
	}


}

UVLJavaScriptParser.EqualEquationContext = EqualEquationContext;

class LowerEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	LOWER() {
	    return this.getToken(UVLJavaScriptParser.LOWER, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLowerEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLowerEquation(this);
		}
	}


}

UVLJavaScriptParser.LowerEquationContext = LowerEquationContext;

class LowerEqualsEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	LOWER_EQUALS() {
	    return this.getToken(UVLJavaScriptParser.LOWER_EQUALS, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLowerEqualsEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLowerEqualsEquation(this);
		}
	}


}

UVLJavaScriptParser.LowerEqualsEquationContext = LowerEqualsEquationContext;

class GreaterEqualsEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	GREATER_EQUALS() {
	    return this.getToken(UVLJavaScriptParser.GREATER_EQUALS, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterGreaterEqualsEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitGreaterEqualsEquation(this);
		}
	}


}

UVLJavaScriptParser.GreaterEqualsEquationContext = GreaterEqualsEquationContext;

class GreaterEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	GREATER() {
	    return this.getToken(UVLJavaScriptParser.GREATER, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterGreaterEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitGreaterEquation(this);
		}
	}


}

UVLJavaScriptParser.GreaterEquationContext = GreaterEquationContext;

class NotEqualsEquationContext extends EquationContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	NOT_EQUALS() {
	    return this.getToken(UVLJavaScriptParser.NOT_EQUALS, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterNotEqualsEquation(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitNotEqualsEquation(this);
		}
	}


}

UVLJavaScriptParser.NotEqualsEquationContext = NotEqualsEquationContext;

class ExpressionContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_expression;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class BracketExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	expression() {
	    return this.getTypedRuleContext(ExpressionContext,0);
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterBracketExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitBracketExpression(this);
		}
	}


}

UVLJavaScriptParser.BracketExpressionContext = BracketExpressionContext;

class AggregateFunctionExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	aggregateFunction() {
	    return this.getTypedRuleContext(AggregateFunctionContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAggregateFunctionExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAggregateFunctionExpression(this);
		}
	}


}

UVLJavaScriptParser.AggregateFunctionExpressionContext = AggregateFunctionExpressionContext;

class FloatLiteralExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	FLOAT() {
	    return this.getToken(UVLJavaScriptParser.FLOAT, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFloatLiteralExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFloatLiteralExpression(this);
		}
	}


}

UVLJavaScriptParser.FloatLiteralExpressionContext = FloatLiteralExpressionContext;

class StringLiteralExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	STRING() {
	    return this.getToken(UVLJavaScriptParser.STRING, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterStringLiteralExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitStringLiteralExpression(this);
		}
	}


}

UVLJavaScriptParser.StringLiteralExpressionContext = StringLiteralExpressionContext;

class AddExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	ADD() {
	    return this.getToken(UVLJavaScriptParser.ADD, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAddExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAddExpression(this);
		}
	}


}

UVLJavaScriptParser.AddExpressionContext = AddExpressionContext;

class IntegerLiteralExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	INTEGER() {
	    return this.getToken(UVLJavaScriptParser.INTEGER, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterIntegerLiteralExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitIntegerLiteralExpression(this);
		}
	}


}

UVLJavaScriptParser.IntegerLiteralExpressionContext = IntegerLiteralExpressionContext;

class LiteralExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLiteralExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLiteralExpression(this);
		}
	}


}

UVLJavaScriptParser.LiteralExpressionContext = LiteralExpressionContext;

class DivExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	DIV() {
	    return this.getToken(UVLJavaScriptParser.DIV, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterDivExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitDivExpression(this);
		}
	}


}

UVLJavaScriptParser.DivExpressionContext = DivExpressionContext;

class SubExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	SUB() {
	    return this.getToken(UVLJavaScriptParser.SUB, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterSubExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitSubExpression(this);
		}
	}


}

UVLJavaScriptParser.SubExpressionContext = SubExpressionContext;

class MulExpressionContext extends ExpressionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	expression = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ExpressionContext);
	    } else {
	        return this.getTypedRuleContext(ExpressionContext,i);
	    }
	};

	MUL() {
	    return this.getToken(UVLJavaScriptParser.MUL, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterMulExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitMulExpression(this);
		}
	}


}

UVLJavaScriptParser.MulExpressionContext = MulExpressionContext;

class AggregateFunctionContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_aggregateFunction;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class AvgAggregateFunctionContext extends AggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	reference = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ReferenceContext);
	    } else {
	        return this.getTypedRuleContext(ReferenceContext,i);
	    }
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	COMMA() {
	    return this.getToken(UVLJavaScriptParser.COMMA, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterAvgAggregateFunction(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitAvgAggregateFunction(this);
		}
	}


}

UVLJavaScriptParser.AvgAggregateFunctionContext = AvgAggregateFunctionContext;

class NumericAggregateFunctionExpressionContext extends AggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	numericAggregateFunction() {
	    return this.getTypedRuleContext(NumericAggregateFunctionContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterNumericAggregateFunctionExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitNumericAggregateFunctionExpression(this);
		}
	}


}

UVLJavaScriptParser.NumericAggregateFunctionExpressionContext = NumericAggregateFunctionExpressionContext;

class SumAggregateFunctionContext extends AggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	reference = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(ReferenceContext);
	    } else {
	        return this.getTypedRuleContext(ReferenceContext,i);
	    }
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	COMMA() {
	    return this.getToken(UVLJavaScriptParser.COMMA, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterSumAggregateFunction(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitSumAggregateFunction(this);
		}
	}


}

UVLJavaScriptParser.SumAggregateFunctionContext = SumAggregateFunctionContext;

class StringAggregateFunctionExpressionContext extends AggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	stringAggregateFunction() {
	    return this.getTypedRuleContext(StringAggregateFunctionContext,0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterStringAggregateFunctionExpression(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitStringAggregateFunctionExpression(this);
		}
	}


}

UVLJavaScriptParser.StringAggregateFunctionExpressionContext = StringAggregateFunctionExpressionContext;

class StringAggregateFunctionContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_stringAggregateFunction;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class LengthAggregateFunctionContext extends StringAggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLengthAggregateFunction(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLengthAggregateFunction(this);
		}
	}


}

UVLJavaScriptParser.LengthAggregateFunctionContext = LengthAggregateFunctionContext;

class NumericAggregateFunctionContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_numericAggregateFunction;
    }


	 
		copyFrom(ctx) {
			super.copyFrom(ctx);
		}

}


class CeilAggregateFunctionContext extends NumericAggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterCeilAggregateFunction(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitCeilAggregateFunction(this);
		}
	}


}

UVLJavaScriptParser.CeilAggregateFunctionContext = CeilAggregateFunctionContext;

class FloorAggregateFunctionContext extends NumericAggregateFunctionContext {

    constructor(parser, ctx) {
        super(parser);
        super.copyFrom(ctx);
    }

	OPEN_PAREN() {
	    return this.getToken(UVLJavaScriptParser.OPEN_PAREN, 0);
	};

	reference() {
	    return this.getTypedRuleContext(ReferenceContext,0);
	};

	CLOSE_PAREN() {
	    return this.getToken(UVLJavaScriptParser.CLOSE_PAREN, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFloorAggregateFunction(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFloorAggregateFunction(this);
		}
	}


}

UVLJavaScriptParser.FloorAggregateFunctionContext = FloorAggregateFunctionContext;

class ReferenceContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_reference;
    }

	id = function(i) {
	    if(i===undefined) {
	        i = null;
	    }
	    if(i===null) {
	        return this.getTypedRuleContexts(IdContext);
	    } else {
	        return this.getTypedRuleContext(IdContext,i);
	    }
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterReference(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitReference(this);
		}
	}


}



class IdContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_id;
    }

	ID_STRICT() {
	    return this.getToken(UVLJavaScriptParser.ID_STRICT, 0);
	};

	ID_NOT_STRICT() {
	    return this.getToken(UVLJavaScriptParser.ID_NOT_STRICT, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterId(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitId(this);
		}
	}


}



class FeatureTypeContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_featureType;
    }

	BOOLEAN_KEY() {
	    return this.getToken(UVLJavaScriptParser.BOOLEAN_KEY, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterFeatureType(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitFeatureType(this);
		}
	}


}



class LanguageLevelContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_languageLevel;
    }

	majorLevel() {
	    return this.getTypedRuleContext(MajorLevelContext,0);
	};

	minorLevel() {
	    return this.getTypedRuleContext(MinorLevelContext,0);
	};

	MUL() {
	    return this.getToken(UVLJavaScriptParser.MUL, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterLanguageLevel(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitLanguageLevel(this);
		}
	}


}



class MajorLevelContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_majorLevel;
    }

	BOOLEAN_KEY() {
	    return this.getToken(UVLJavaScriptParser.BOOLEAN_KEY, 0);
	};

	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterMajorLevel(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitMajorLevel(this);
		}
	}


}



class MinorLevelContext extends antlr4__WEBPACK_IMPORTED_MODULE_0__["default"].ParserRuleContext {

    constructor(parser, parent, invokingState) {
        if(parent===undefined) {
            parent = null;
        }
        if(invokingState===undefined || invokingState===null) {
            invokingState = -1;
        }
        super(parent, invokingState);
        this.parser = parser;
        this.ruleIndex = UVLJavaScriptParser.RULE_minorLevel;
    }


	enterRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.enterMinorLevel(this);
		}
	}

	exitRule(listener) {
	    if(listener instanceof _UVLJavaScriptListener_js__WEBPACK_IMPORTED_MODULE_1__["default"] ) {
	        listener.exitMinorLevel(this);
		}
	}


}




UVLJavaScriptParser.FeatureModelContext = FeatureModelContext; 
UVLJavaScriptParser.IncludesContext = IncludesContext; 
UVLJavaScriptParser.IncludeLineContext = IncludeLineContext; 
UVLJavaScriptParser.NamespaceContext = NamespaceContext; 
UVLJavaScriptParser.ImportsContext = ImportsContext; 
UVLJavaScriptParser.ImportLineContext = ImportLineContext; 
UVLJavaScriptParser.FeaturesContext = FeaturesContext; 
UVLJavaScriptParser.GroupContext = GroupContext; 
UVLJavaScriptParser.GroupSpecContext = GroupSpecContext; 
UVLJavaScriptParser.FeatureContext = FeatureContext; 
UVLJavaScriptParser.FeatureCardinalityContext = FeatureCardinalityContext; 
UVLJavaScriptParser.AttributesContext = AttributesContext; 
UVLJavaScriptParser.AttributeContext = AttributeContext; 
UVLJavaScriptParser.ValueAttributeContext = ValueAttributeContext; 
UVLJavaScriptParser.KeyContext = KeyContext; 
UVLJavaScriptParser.ValueContext = ValueContext; 
UVLJavaScriptParser.VectorContext = VectorContext; 
UVLJavaScriptParser.ConstraintAttributeContext = ConstraintAttributeContext; 
UVLJavaScriptParser.ConstraintListContext = ConstraintListContext; 
UVLJavaScriptParser.ConstraintsContext = ConstraintsContext; 
UVLJavaScriptParser.ConstraintLineContext = ConstraintLineContext; 
UVLJavaScriptParser.ConstraintContext = ConstraintContext; 
UVLJavaScriptParser.EquationContext = EquationContext; 
UVLJavaScriptParser.ExpressionContext = ExpressionContext; 
UVLJavaScriptParser.AggregateFunctionContext = AggregateFunctionContext; 
UVLJavaScriptParser.StringAggregateFunctionContext = StringAggregateFunctionContext; 
UVLJavaScriptParser.NumericAggregateFunctionContext = NumericAggregateFunctionContext; 
UVLJavaScriptParser.ReferenceContext = ReferenceContext; 
UVLJavaScriptParser.IdContext = IdContext; 
UVLJavaScriptParser.FeatureTypeContext = FeatureTypeContext; 
UVLJavaScriptParser.LanguageLevelContext = LanguageLevelContext; 
UVLJavaScriptParser.MajorLevelContext = MajorLevelContext; 
UVLJavaScriptParser.MinorLevelContext = MinorLevelContext; 


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry need to be wrapped in an IIFE because it need to be in strict mode.
(() => {
"use strict";
/*!**************************************************!*\
  !*** ./app/modules/hubfile/assets/js/scripts.js ***!
  \**************************************************/
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var uvl_parser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! uvl-parser */ "./node_modules/uvl-parser/index.js");


// 

let valid = true;
let invalid_uvl_message = '';

let dropzone = Dropzone.options.myDropzone = {
    url: "/hubfile/upload",
    paramName: 'file',
    maxFilesize: 10,
    acceptedFiles: '.uvl',
    init: function () {

        let fileList = document.getElementById('file-list');
        let dropzoneText = document.getElementById('dropzone-text');
        let alerts = document.getElementById('alerts');

        
        if (hubfiles) {
            for (let i = 0; i < hubfiles.length; i++) {
                let hubfile = hubfiles[i];
                fetch(hubfile.url)
                .then(response => response.blob())
                .then(blob => {
                    let file = new File([blob], hubfile.name, {type: 'uvl'});
                    this.addFile(file);
                })
            }
        }
            

        this.on('addedfile', function (file) {

            let ext = file.name.split('.').pop();
            if (ext !== 'uvl') {
                this.removeFile(file);

                let alert = document.createElement('p');
                alert.textContent = 'Invalid file extension: ' + file.name;
                alerts.appendChild(alert);
                alerts.style.display = 'block';
            }  else {
                // Read the file as text to pass it to the UVL parser
                let reader = new FileReader();
                reader.onload = function(event) {
                    const fileContent = event.target.result;  // This contains the UVL file content

                    // Now, use uvl-parser to parse the content
                    try {
                        const featureModel = new uvl_parser__WEBPACK_IMPORTED_MODULE_0__.FeatureModel(fileContent);
                        const tree = featureModel.getFeatureModel();  // This is your parsed UVL tree

                        console.log("Parsed UVL Feature Model:", tree);
                        valid = true;

                        // You can now manipulate `tree` or display it in the UI as needed
                    } catch (error) {
                        if (error instanceof TypeError) {
                            console.error("Caught a TypeError:", error.message);
                        } else {
                            valid = false;
                            console.error("Error parsing UVL file:", error.message);
                            invalid_uvl_message = error.message
                            let alert = document.createElement('p');
                            alert.innerHTML = 'Syntax error in <b>' + file.name + '</b><br>&nbsp;>&nbsp;>&nbsp;>&nbsp;' + error.message;
                            alerts.appendChild(alert);
                            alerts.style.display = 'block';
                        }

                    }
                };
                reader.readAsText(file);  // Read the file as text
            }

        });

        this.on('error', function (file, response) {
            console.error("Error uploading file: ", response);
            let alert = document.createElement('p');
            alert.textContent = 'Error uploading file: ' + file.name;
            alerts.appendChild(alert);
            alerts.style.display = 'block';
        });


        this.on('success', function (file, response) {

            if(valid){
                let dropzone = this;

                showUploadDataset();

                console.log("File uploaded: ", response);
                // actions when UVL model is uploaded
                let listItem = document.createElement('li');
                let h4Element = document.createElement('h4');
                h4Element.textContent = response.filename;
                listItem.appendChild(h4Element);

                // generate incremental id for form
                let formUniqueId = generateIncrementalId();

                /*
                    ##########################################
                    FORM BUTTON
                    ##########################################
                */
                let formButton = document.createElement('button');
                formButton.innerHTML = 'Show info';
                formButton.classList.add('info-button', 'btn', 'btn-outline-secondary', "btn-sm");
                formButton.style.borderRadius = '5px';
                formButton.id = formUniqueId + "_button";

                formButton.addEventListener('click', function () {
                    if (formContainer.style.display === "none") {
                        formContainer.style.display = "block";
                        formButton.innerHTML = 'Hide info';
                    } else {
                        formContainer.style.display = "none";
                        formButton.innerHTML = 'Add info';
                    }
                });

                // append space
                let space = document.createTextNode(" ");
                listItem.appendChild(space);

                /*
                    ##########################################
                    REMOVE BUTTON
                    ##########################################
                */

                // remove button
                let removeButton = document.createElement('button');
                removeButton.innerHTML = 'Delete model';
                removeButton.classList.add("remove-button", "btn", "btn-outline-danger", "btn-sm", "remove-button");
                removeButton.style.borderRadius = '5px';

                // append space
                space = document.createTextNode(" ");
                listItem.appendChild(space);

                removeButton.addEventListener('click', function () {
                    fileList.removeChild(listItem);
                    this.removeFile(file);

                    // Ajax request
                    let xhr = new XMLHttpRequest();
                    xhr.open('POST', '/hubfile/delete', true);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.onload = function () {
                        if (xhr.status === 200) {
                            console.log('Deleted file from server');

                            if (dropzone.files.length === 0) {
                                document.getElementById("submit_dataset").style.display = "none";
                                cleanUploadErrors();
                            }

                        }
                    };
                    xhr.send(JSON.stringify({file: file.name}));
                }.bind(this));

                /*
                    ##########################################
                    APPEND BUTTONS
                    ##########################################
                */
                listItem.appendChild(formButton);
                listItem.appendChild(removeButton);

                /*
                    ##########################################
                    UVL FORM
                    ##########################################
                */

                // create specific form for UVL
                let formContainer = document.createElement('div');
                formContainer.id = formUniqueId + "_form";
                formContainer.classList.add('uvl_form', "mt-3");
                formContainer.style.display = "none";

                formContainer.innerHTML = `
                    <div class="row">
                        <input type="hidden" value="${response.filename}" name="feature_models-${formUniqueId}-uvl_filename">
                        <div class="col-12">
                            <div class="row">
                                <div class="col-12">
                                    <div class="mb-3">
                                        <label class="form-label">Title</label>
                                        <input type="text" class="form-control" name="feature_models-${formUniqueId}-title">
                                    </div>
                                </div>
                                <div class="col-12">
                                    <div class="mb-3">
                                        <label class="form-label">Description</label>
                                        <textarea rows="4" class="form-control" name="feature_models-${formUniqueId}-desc"></textarea>
                                    </div>
                                </div>
                                <div class="col-lg-6 col-12">
                                    <div class="mb-3">
                                        <label class="form-label" for="publication_type">Publication type</label>
                                        <select class="form-control" name="feature_models-${formUniqueId}-publication_type">
                                            <option value="none">None</option>
                                            <option value="annotationcollection">Annotation Collection</option>
                                            <option value="book">Book</option>
                                            <option value="section">Book Section</option>
                                            <option value="conferencepaper">Conference Paper</option>
                                            <option value="datamanagementplan">Data Management Plan</option>
                                            <option value="article">Journal Article</option>
                                            <option value="patent">Patent</option>
                                            <option value="preprint">Preprint</option>
                                            <option value="deliverable">Project Deliverable</option>
                                            <option value="milestone">Project Milestone</option>
                                            <option value="proposal">Proposal</option>
                                            <option value="report">Report</option>
                                            <option value="softwaredocumentation">Software Documentation</option>
                                            <option value="taxonomictreatment">Taxonomic Treatment</option>
                                            <option value="technicalnote">Technical Note</option>
                                            <option value="thesis">Thesis</option>
                                            <option value="workingpaper">Working Paper</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-lg-6 col-6">
                                    <div class="mb-3">
                                        <label class="form-label" for="publication_doi">Publication DOI</label>
                                        <input class="form-control" name="feature_models-${formUniqueId}-publication_doi" type="text" value="">
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="mb-3">
                                        <label class="form-label">Tags (separated by commas)</label>
                                        <input type="text" class="form-control" name="feature_models-${formUniqueId}-tags">
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="mb-3">
                                        <label class="form-label">UVL version</label>
                                        <input type="text" class="form-control" name="feature_models-${formUniqueId}-uvl_version">
                                    </div>
                                </div>
                                <div class="col-12">
                                    <div class="mb-3">
                                        <label class="form-label">Authors</label>
                                        <div id="` + formContainer.id + `_authors">
                                        </div>
                                        <button type="button" class="add_author_to_uvl btn btn-secondary" id="` + formContainer.id + `_authors_button">Add author</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;

                listItem.appendChild(formContainer);
                fileList.appendChild(listItem);
            }

            

        });

        
    }
};
})();

/******/ })()
;
//# sourceMappingURL=hubfile.bundle.js.map