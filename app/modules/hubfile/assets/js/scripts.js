import { FeatureModel } from "uvl-parser";

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
            } else {
                // Read the file as text to pass it to the UVL parser
                let reader = new FileReader();
                reader.onload = function(event) {
                    const fileContent = event.target.result;  // This contains the UVL file content
        
                    // Now, use uvl-parser to parse the content
                    try {
                        const featureModel = new FeatureModel(fileContent);
                        const tree = featureModel.getFeatureModel();  // This is your parsed UVL tree
        
                        console.log("Parsed UVL Feature Model:", tree);
                        valid = true;
        
                        
                        // You can now manipulate `tree` or display it in the UI as needed
                    } catch (error) {
                        // Verificar si el error es debido a `Error.captureStackTrace`
                        if (error.message.includes("Error.captureStackTrace is not a function")) {
                            console.warn("Error.captureStackTrace is not supported in this environment.");
                            valid = false;
                            let alert = document.createElement('p');
                            alert.innerHTML = 'Syntax error in <b>' + file.name + '</b>';
                            alerts.appendChild(alert);
                            alerts.style.display = 'block';
                        } else {
                            // Si es un error de sintaxis en el UVL, mostrar mensaje personalizado
                            valid = false;
                            console.error("Error parsing UVL file:", error.message);
                            invalid_uvl_message = error.message;
                            
                            // Muestra el mensaje de error de sintaxis en el UI
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