import { loadPyodide } from './pyodide/pyodide.mjs';
// import('/generator/js/pyodide/pyodide.js')

console.log("Hi, I am a script loaded from generator module");

class NavigatorExecutor {
    constructor() {
        this.pyodide = null;
    }

    async load_WASM(){
        
        const pythonFile = await fetch("/generator/js/flamapy_ide.py");
        const pyodideInstance = await loadPyodide({
            indexURL: "./pyodide",
        });
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
    
        await pyodide.runPythonAsync(`
            import micropip
            
            await micropip.install("afmparser-1.0.3-py3-none-any.whl", deps=False)
            await micropip.install("antlr4_python3_runtime-4.13.1-py3-none-any.whl", deps=False)
            await micropip.install("astutils-0.0.6-py3-none-any.whl", deps=False)
            await micropip.install("dd-0.5.7-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_bdd-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_configurator-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_fm-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_fm-2.0.2.dev0-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_fw-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_fw-2.0.2.dev0-py3-none-any.whl", deps=False)
            await micropip.install("flamapy_sat-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("flamapy-2.0.1-py3-none-any.whl", deps=False)
            await micropip.install("fm_generator-0.0.1-py3-none-any.whl", deps=False)
            await micropip.install("graphviz-0.20-py3-none-any.whl", deps=False)
            await micropip.install("networkx-3.4.2-py3-none-any.whl", deps=False)
            await micropip.install("ply-3.11-py2.py3-none-any.whl", deps=False)
            await micropip.install("psutil-7.0.0-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", deps=False)
            await micropip.install("pydot-4.0.0-py3-none-any.whl", deps=False)
            await micropip.install("python_sat-0.1.8.dev17-pp310-pypy310_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl", deps=False)
            await micropip.install("setuptools-80.9.0-py3-none-any.whl", deps=False)
            await micropip.install("six-1.17.0-py2.py3-none-any.whl", deps=False)
            await micropip.install("uvlparser-2.0.1-py3-none-any.whl", deps=False)
            print("AAAAAAAAAAA")
        `)

        await pyodideInstance.runPythonAsync(await pythonFile.text());
        pyodideInstance.FS.mkdir("export");

        this.pyodide = pyodideInstance;
    }

    async generate_models() {
        // this.pyodide.globals.set("code", code);
        // const jsonResult = await this.pyodide.runPythonAsync(
        // `
        //     with open("uvlfile.uvl", "w") as text_file:
        //         text_file.write(code)
            
        //     process_uvl_file('uvlfile.uvl')
        // `
        // );
        // const result = JSON.parse(jsonResult);
        // this.isValid = result.valid;
        console.log('Executing from scripts.js')
        return result;
    }
}

const navigatorExecutor = new NavigatorExecutor()

navigatorExecutor.load_WASM()
    .then(() => {
        self.postMessage({ status: "loaded" })
        navigatorExecutor.generate_models()
        console.log('AAAAAAAAAAAAA')
    })
    .catch((exception) => self.postMessage({ status: "error", exception }));

// const pyodideInstance = await loadPyodide({
//     indexURL: "js/pyodide",
// });
// await pyodide.loadPackage("micropip");
// const micropip = pyodide.pyimport("micropip");
// console.log()