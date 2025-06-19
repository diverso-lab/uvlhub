// app/modules/generator/assets/js/scripts.js

// Importamos Pyodide desde tu carpeta estática
// import { loadPyodide } from '/static/pyodide/pyodide.mjs';
// const JSZip  = globalThis.JSZip;
// const saveAs = globalThis.saveAs;

import JSZip from "jszip";
import { saveAs } from "file-saver";

console.log("Hi, I am a script loaded from the step5 of generator module")

class NavigatorExecutor {
  constructor() {
    this.pyodide = null;
    this.isValid = false;
  }

  /**
   * Carga Pyodide, micropip y todos los wheels desde /static/js
   */
  async loadFlamapy() {
    // 1) Carga Pyodide
    const pythonFile = await fetch("/static/js/fmgen_wrapper.py");
    console.log("🚀 Loading Pyodide…");
    const pyodide = await window.loadPyodide({
      indexURL: '/static/pyodide'
    });
    await pyodide.loadPackage('micropip');
    await pyodide.loadPackage('packaging');
    console.log("📦 micropip + packaging ready");

    // 2) Instala todos los wheels en bloque
    const wheels = [
      'afmparser-1.0.3-py3-none-any.whl',
      'antlr4_python3_runtime-4.13.1-py3-none-any.whl',
      'astutils-0.0.6-py3-none-any.whl',
      'blinker-1.9.0-py3-none-any.whl',
      'dd-0.5.7-py3-none-any.whl',
      'flamapy_bdd-2.0.1-py3-none-any.whl',
      'flamapy_configurator-2.0.1-py3-none-any.whl',
      'flamapy_fm-2.0.1-py3-none-any.whl',
      'flamapy_fm-2.0.2.dev0-py3-none-any.whl',
      'flamapy_fw-2.0.1-py3-none-any.whl',
      'flamapy_fw-2.0.2.dev0-py3-none-any.whl',
      'flamapy_sat-2.0.1-py3-none-any.whl',
      'flamapy-2.0.1-py3-none-any.whl',
      'flask-3.1.0-py3-none-any.whl',
      'fm_generator-0.0.1-py3-none-any.whl',
      'graphviz-0.20-py3-none-any.whl',
      'itsdangerous-2.2.0-py3-none-any.whl',
      'networkx-3.4.2-py3-none-any.whl',
      'ply-3.11-py2.py3-none-any.whl',
      'pydot-4.0.0-py3-none-any.whl',
      'setuptools-80.9.0-py3-none-any.whl',
      'six-1.17.0-py2.py3-none-any.whl',
      'uvlparser-2.0.1-py3-none-any.whl',
      'werkzeug-3.1.3-py3-none-any.whl'
    ];

    console.log("📦 Installing wheels…");
    for (let wheel of wheels) {
      const url = `/static/js/${wheel}`;
      await pyodide.runPythonAsync(`
        import micropip
        await micropip.install("${url}", deps=False)
        print("✅ Installed ${wheel}")
      `);
    }

    console.log("✅ All wheels installed");
    this.pyodide = pyodide;

    await pyodide.runPythonAsync(await pythonFile.text())
      .then(() => console.log("El wrapper lo coge piola"))
      .catch((e) => console.error("Las cagao con el wrapper", e))
  }


  async generateModels() {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized — call loadFlamapy() first");
    }

    console.log("🔄 Fetching params-json…");
    const resp = await fetch('/generator/params-json');
    if (!resp.ok) {
      throw new Error("Failed to fetch params-json: " + resp.status);
    }

    const paramsObj = await resp.json();
    console.log(paramsObj)

    // Inyectamos el JSON en una variable Python
    const pj = JSON.stringify(paramsObj);
    this.pyodide.globals.set('params_json', pj);

    console.log("⚙️ Running generate_models wrapper…");

    const uvlsJson = await this.pyodide.runPythonAsync(`
      generate_models(params_json)
    `);



    return JSON.parse(uvlsJson);
  }
}

// Al cargar el módulo, instanciamos y arrancamos la carga
const executor = new NavigatorExecutor();

executor.loadFlamapy()
  .then(async () => {
    console.log("🚀 Pyodide y wheels listos");

    // Aquí llamamos a generateModels, obtenemos el array de UVLs…
    const uvls = await executor.generateModels();

    // …y lo metemos en un ZIP:
    const zip = new JSZip();
    uvls.forEach((u, i) => {
      zip.file(`fm${i}.uvl`, u);
    });

    // Generamos el blob y lo descargamos:
    const blob = await zip.generateAsync({ type: "blob" });
    saveAs(blob, "feature_models.zip");
    console.log("💾 ZIP descargado");
  })
  .catch(err => console.error("❌ Error cargando Pyodide:", err));


// Exportamos la clase por si la necesitas en otros scripts
export { NavigatorExecutor };
