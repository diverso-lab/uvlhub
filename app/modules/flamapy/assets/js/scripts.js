function checkUVL(file_id) {
    const outputDiv = document.getElementById('check_' + file_id);
    outputDiv.innerHTML = ''; // Clear previous output

    fetch(`/flamapy/check_uvl/${file_id}`)
        .then(response => {
            return response.json().then(data => ({
                status: response.status,
                data
            }));
        })
        .then(({ status, data }) => {
            if (status === 400) {
                // Display errors
                if (data.errors) {
                    outputDiv.innerHTML = '<span class="badge badge-danger">Errors:</span>';
                    data.errors.forEach(error => {
                        const errorElement = document.createElement('span');
                        errorElement.className = 'badge badge-danger';
                        errorElement.textContent = error;
                        outputDiv.appendChild(errorElement);
                        outputDiv.appendChild(document.createElement('br')); // Line break for better readability
                    });
                } else {
                    outputDiv.innerHTML = `<span class="badge badge-danger">Error: ${data.error}</span>`;
                }
            } else if (status === 200) {
                // Display success message
                outputDiv.innerHTML = '<span class="badge badge-success">Valid Model</span>';
            } else {
                // Handle unexpected status
                outputDiv.innerHTML = `<span class="badge badge-warning">Unexpected response status: ${status}</span>`;
            }
        })
        .catch(error => {
            // Handle fetch errors
            outputDiv.innerHTML = `<span class="badge badge-danger">An unexpected error occurred: ${error.message}</span>`;
        });
}

function checkSAT(file_id) {
    const outputDiv = document.getElementById('check_' + file_id);
    outputDiv.innerHTML = ''; // Clear previous output

    fetch(`/flamapy/valid/${file_id}`)
        .then(response => {
            return response.json().then(data => ({
                status: response.status,
                data
            }));
        })
        .then(({ status, data }) => {
            if (status === 400) {
                // Display errors
                if (data.errors) {
                    outputDiv.innerHTML = '<span class="badge badge-danger">Errors:</span>';
                    data.errors.forEach(error => {
                        const errorElement = document.createElement('span');
                        errorElement.className = 'badge badge-danger';
                        errorElement.textContent = error;
                        outputDiv.appendChild(errorElement);
                        outputDiv.appendChild(document.createElement('br')); // Line break for better readability
                    });
                } else {
                    outputDiv.innerHTML = `<span class="badge badge-danger">Error: ${data.error}</span>`;
                }
            } else if (status === 200) {
                // Display success message
                outputDiv.innerHTML = '<span class="badge badge-success">Valid SAT Model</span>';
            } else {
                // Handle unexpected status
                outputDiv.innerHTML = `<span class="badge badge-warning">Unexpected response status: ${status}</span>`;
            }
        })
        .catch(error => {
            // Handle fetch errors
            outputDiv.innerHTML = `<span class="badge badge-danger">An unexpected error occurred: ${error.message}</span>`;
        });
}

/*
async function valid() {
    showLoading()
    let pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    //await micropip.install("/assets/web_assembly/antlr4_python3_runtime-4.7.2-py3-none-any.whl");
    await micropip.install("antlr4-python3-runtime==4.13.1");
    await micropip.install("uvlparser==2.0.1");
    //await micropip.install("afmparser==1.0.0");

    await pyodide.runPythonAsync(
    `
        import micropip
        #await micropip.install("flamapy-fm-dist", deps=False)#this is to avoid problems with deps later on
        await micropip.install("flamapy==2.0.1.dev1", deps=False);
        await micropip.install("flamapy-fm==2.0.1.dev1", deps=False);
        await micropip.install("flamapy-sat");
    `
    )
    hideLoading()

    try {
        let output = pyodide.runPython(
        `
        import js

        file_content = js.document.getElementById('fileContent').textContent
        div = js.document.createElement("result")

        with open("uvlfile.uvl", "w") as text_file:
            print(file_content, file=text_file)

        from flamapy.interfaces.python.FLAMAFeatureModel import FLAMAFeatureModel

        fm = FLAMAFeatureModel("uvlfile.uvl")
        result=fm.valid()

        div.innerHTML = "<div id='deleteme'>"+str(result)+"</div>"
        exists=js.document.getElementById('deleteme')
        if(exists):
            exists.remove()

        js.document.getElementById('result').append(div)
        `
    );
    } catch (err) {
        console.log(err);
    }
}
*/