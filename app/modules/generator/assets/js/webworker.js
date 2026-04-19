// webworker.js
/* global loadPyodide */
importScripts('/generator/assets/js/pyodide/pyodide.mjs');

let pyodideReady = (async () => {
  self.pyodide = await loadPyodide({ indexURL: '/generator/assets/js/pyodide' });
  await self.pyodide.loadPackage('micropip');
  // Monta la carpeta de tu wrapper en /pywrap
  self.pyodide.FS.mount(self.pyodide.FS.filesystems.NODEFS,
    { root: '/generator/assets/js/pyodide' }, '/pywrap');
  await self.pyodide.runPythonAsync(`
import sys
sys.path.append('/pywrap')
import pyodide_wrapper
`);
  self.postMessage({ status: 'loaded' });
})();

self.onmessage = async (e) => {
  await pyodideReady;
  const { action, paramsJson } = e.data;
  try {
    let resultJson;
    if (action === 'generateModels') {
      // Llamada al wrapper
      resultJson = await self.pyodide.runPythonAsync(
        `pyodide_wrapper.generate_models(${JSON.stringify(paramsJson)})`
      );
    }
    self.postMessage({ action, resultJson });
  } catch (err) {
    self.postMessage({ action, error: err.toString() });
  }
};
