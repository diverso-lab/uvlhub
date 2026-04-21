import JSZip from "jszip";
import { saveAs } from "file-saver";

console.log("Hi, I am a script loaded from the step5 of generator module");

class NavigatorExecutor {
  constructor() {
    this.pyodide = null;
    this.isValid = false;
    this.totalModels = 0;
    this.generatedModels = 0;
    this.lastPercent = 0;
  }

  setProgress(percent, phase = "", status = "") {
    const safePercent = Math.max(0, Math.min(100, Math.round(percent)));
    this.lastPercent = safePercent;

    const bar = document.getElementById("generate-progress-bar");
    const percentEl = document.getElementById("generate-percent");
    const phaseEl = document.getElementById("generate-phase");
    const statusEl = document.getElementById("generate-status");

    if (bar) {
      bar.style.width = `${safePercent}%`;
      bar.setAttribute("aria-valuenow", String(safePercent));
      bar.textContent = `${safePercent}%`;

      if (safePercent >= 100) {
        bar.classList.remove("progress-bar-animated");
      }
    }

    if (percentEl) {
      percentEl.textContent = `${safePercent}%`;
    }

    if (phaseEl && phase) {
      phaseEl.textContent = phase;
    }

    if (statusEl && status) {
      statusEl.textContent = status;
    }
  }

  appendLog(message, level = "info") {
    const logViewer = document.getElementById("generate-log-viewer");
    if (!logViewer) return;

    const prefixMap = {
      info: "[INFO]",
      success: "[OK]",
      error: "[ERROR]",
      warn: "[WARN]",
    };

    const prefix = prefixMap[level] || "[INFO]";
    const line = document.createElement("div");
    line.textContent = `${prefix} ${message}`;

    if (level === "error") {
      line.style.color = "#fca5a5";
    } else if (level === "success") {
      line.style.color = "#86efac";
    } else if (level === "warn") {
      line.style.color = "#fde68a";
    } else {
      line.style.color = "#e5e7eb";
    }

    logViewer.appendChild(line);
    logViewer.scrollTop = logViewer.scrollHeight;
  }

  updateGenerationProgressFromPythonLog(text) {
    if (!this.totalModels || this.totalModels <= 0) return;

    const lower = String(text).toLowerCase();

    // Captura mensajes tipo:
    // "Modelo 0: satisfacible encontrado..."
    // "Modelo 3: ..."
    const match = text.match(/Modelo\s+(\d+)/i);
    if (match) {
      const modelIndex = parseInt(match[1], 10);
      if (!Number.isNaN(modelIndex)) {
        const current = Math.min(this.totalModels, modelIndex + 1);
        this.generatedModels = Math.max(this.generatedModels, current);

        const percent = 30 + (this.generatedModels / this.totalModels) * 55;
        this.setProgress(
          percent,
          "Generating models",
          `Generating model ${this.generatedModels} of ${this.totalModels}...`
        );
        return;
      }
    }

    // Respaldo: si aparece "modelo generado" sumamos uno
    if (lower.includes("modelo generado")) {
      this.generatedModels = Math.min(this.totalModels, this.generatedModels + 1);
      const percent = 30 + (this.generatedModels / this.totalModels) * 55;
      this.setProgress(
        percent,
        "Generating models",
        `Generating model ${this.generatedModels} of ${this.totalModels}...`
      );
    }
  }

  /**
   * Carga Pyodide, micropip y todos los wheels desde /static/js
   */
  async loadFlamapy() {
    const pythonFile = await fetch("/static/js/fmgen_wrapper.py");

    this.appendLog("Loading Pyodide...");
    this.setProgress(5, "Loading Pyodide", "Loading Python runtime...");

    const pyodide = await window.loadPyodide({
      indexURL: "/static/pyodide/"
    });

    // Redirigir stdout/stderr de Python al visor de logs
    pyodide.setStdout({
      batched: (msg) => {
        if (msg && msg.trim()) {
          this.appendLog(msg.trim(), "info");
          this.updateGenerationProgressFromPythonLog(msg.trim());
        }
      }
    });

    pyodide.setStderr({
      batched: (msg) => {
        if (msg && msg.trim()) {
          this.appendLog(msg.trim(), "error");
        }
      }
    });

    this.appendLog("Pyodide loaded", "success");
    this.setProgress(10, "Loading packages", "Loading Pyodide packages...");

    this.appendLog("Loading micropip and packaging...");
    await pyodide.loadPackage("micropip");
    await pyodide.loadPackage("packaging");

    this.appendLog("Loading six and python-sat...");
    await pyodide.loadPackage("six");
    await pyodide.loadPackage("python-sat");

    this.appendLog("micropip + packaging + python-sat ready", "success");
    this.setProgress(18, "Installing dependencies", "Installing generator dependencies...");

    const wheels = [
      "afmparser-1.0.3-py3-none-any.whl",
      "antlr4_python3_runtime-4.13.1-py3-none-any.whl",
      "astutils-0.0.6-py3-none-any.whl",
      "blinker-1.9.0-py3-none-any.whl",
      "dd-0.5.7-py3-none-any.whl",
      "flamapy_bdd-2.5.0-py3-none-any.whl",
      "flamapy_configurator-2.0.1-py3-none-any.whl",
      "flamapy_fm-2.5.0-py3-none-any.whl",
      "flamapy_fw-2.5.0-py3-none-any.whl",
      "flamapy_sat-2.5.0-py3-none-any.whl",
      "flamapy-2.5.0-py3-none-any.whl",
      "flask-3.1.0-py3-none-any.whl",
      "fm_generator-0.0.1-py3-none-any.whl",
      "graphviz-0.20-py3-none-any.whl",
      "itsdangerous-2.2.0-py3-none-any.whl",
      "networkx-3.4.2-py3-none-any.whl",
      "ply-3.11-py2.py3-none-any.whl",
      "pydot-4.0.0-py3-none-any.whl",
      "setuptools-80.9.0-py3-none-any.whl",
      "six-1.17.0-py2.py3-none-any.whl",
      "uvlparser-2.0.1-py3-none-any.whl",
      "werkzeug-3.1.3-py3-none-any.whl"
    ];

    this.appendLog(`Installing ${wheels.length} wheels...`);

    for (let i = 0; i < wheels.length; i++) {
      const wheel = wheels[i];
      const url = `/static/js/${wheel}`;

      this.appendLog(`Installing ${wheel}...`);
      await pyodide.runPythonAsync(`
import micropip
await micropip.install("${url}", deps=False)
print("Installed ${wheel}")
      `);

      const percent = 18 + ((i + 1) / wheels.length) * 10;
      this.setProgress(
        percent,
        "Installing dependencies",
        `Installing dependency ${i + 1} of ${wheels.length}...`
      );
    }

    this.appendLog("All wheels installed", "success");
    this.setProgress(28, "Preparing wrapper", "Loading generation wrapper...");

    this.pyodide = pyodide;

    await pyodide.runPythonAsync(await pythonFile.text())
      .then(() => {
        this.appendLog("Python wrapper loaded", "success");
      })
      .catch((e) => {
        this.appendLog(`Wrapper loading error: ${e}`, "error");
        throw e;
      });

    this.setProgress(30, "Ready to generate", "Starting model generation...");
  }

  async generateModels() {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized — call loadFlamapy() first");
    }

    this.appendLog("Fetching generation params...");
    const resp = await fetch("/generator/params-json");
    if (!resp.ok) {
      throw new Error("Failed to fetch params-json: " + resp.status);
    }

    const paramsObj = await resp.json();
    this.totalModels = parseInt(paramsObj.NUM_MODELS || 0, 10);
    this.generatedModels = 0;

    this.appendLog(`Received params for ${this.totalModels} model(s)`);
    console.log(paramsObj);

    const pj = JSON.stringify(paramsObj);
    this.pyodide.globals.set("params_json", pj);

    this.appendLog("Running generate_models wrapper...");
    this.setProgress(
      30,
      "Generating models",
      this.totalModels > 0
        ? `Generating model 0 of ${this.totalModels}...`
        : "Generating models..."
    );

    const uvlsJson = await this.pyodide.runPythonAsync(`
generate_models(params_json)
    `);

    this.generatedModels = this.totalModels;
    this.setProgress(90, "Creating ZIP", "Creating ZIP file...");

    return JSON.parse(uvlsJson);
  }
}

const executor = new NavigatorExecutor();

executor.loadFlamapy()
  .then(async () => {
    executor.appendLog("Pyodide and dependencies ready", "success");

    const uvls = await executor.generateModels();

    executor.appendLog(`Generated ${uvls.length} UVL model(s)`, "success");
    executor.setProgress(92, "Creating ZIP", "Packing files into ZIP...");

    const zip = new JSZip();
    uvls.forEach((u, i) => {
      zip.file(`fm${i}.uvl`, u);
    });

    const blob = await zip.generateAsync(
      { type: "blob" },
      (metadata) => {
        const percent = 92 + (metadata.percent / 100) * 7;
        executor.setProgress(
          percent,
          "Creating ZIP",
          `Packing ZIP... ${Math.round(metadata.percent)}%`
        );
      }
    );

    executor.setProgress(100, "Completed", "Download ready");
    executor.appendLog("ZIP generated successfully", "success");

    saveAs(blob, "feature_models.zip");
    executor.appendLog("ZIP download started", "success");
    console.log("ZIP downloaded");
  })
  .catch((err) => {
    console.error("Error loading Pyodide:", err);
    executor.setProgress(100, "Failed", "Generation failed");
    executor.appendLog(String(err), "error");

    const bar = document.getElementById("generate-progress-bar");
    if (bar) {
      bar.classList.remove("progress-bar-animated");
      bar.classList.remove("progress-bar-striped");
      bar.classList.add("bg-danger");
    }
  });