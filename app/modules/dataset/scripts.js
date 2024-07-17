document.addEventListener('DOMContentLoaded', () => {
    
    /*
        Selectable elements
    */
    const datasetAnonymousCheckbox = document.getElementById('dataset_anonymous');
    const uploadButton = document.getElementById('uploadButton');
    const upgradeButton = document.getElementById('upgradeButton');
    const authorsForm = document.getElementById('authors_form');
    const agreeCheckbox = document.getElementById('agreeCheckbox');

    const addField = (newAuthor, name, text, className = 'col-lg-6 col-12 mb-3') => {
        const fieldWrapper = document.createElement('div');
        fieldWrapper.className = className;

        const label = document.createElement('label');
        label.className = 'form-label';
        label.for = name;
        label.textContent = text;

        const field = document.createElement('input');
        field.name = name;
        field.className = 'form-control';

        fieldWrapper.appendChild(label);
        fieldWrapper.appendChild(field);
        newAuthor.appendChild(fieldWrapper);
    };

    const addRemoveButton = (newAuthor) => {
        const buttonWrapper = document.createElement('div');
        buttonWrapper.className = 'col-12 mb-2';

        const button = document.createElement('button');
        button.textContent = 'Remove author';
        button.className = 'btn btn-danger btn-sm';
        button.type = 'button';
        button.addEventListener('click', (event) => {
            event.preventDefault();
            newAuthor.remove();
        });

        buttonWrapper.appendChild(button);
        newAuthor.appendChild(buttonWrapper);
    };

    const createAuthorBlock = (idx, suffix) => {
        const newAuthor = document.createElement('div');
        newAuthor.className = 'author row';
        newAuthor.style.cssText = "border:2px dotted #ccc;border-radius:10px;padding:10px;margin:10px 0; background-color: white";

        addField(newAuthor, `${suffix}authors-${idx}-name`, 'Name *');
        addField(newAuthor, `${suffix}authors-${idx}-affiliation`, 'Affiliation');
        addField(newAuthor, `${suffix}authors-${idx}-orcid`, 'ORCID');
        addRemoveButton(newAuthor);

        return newAuthor;
    };

    const checkTitleAndDescription = () => {
        const titleInput = document.querySelector('input[name="title"]');
        const descriptionTextarea = document.querySelector('textarea[name="desc"]');

        titleInput.classList.remove("error");
        descriptionTextarea.classList.remove("error");
        cleanUploadErrors();

        const titleLength = titleInput.value.trim().length;
        const descriptionLength = descriptionTextarea.value.trim().length;

        if (titleLength < 3) {
            writeUploadError("Title must be of minimum length 3");
            titleInput.classList.add("error");
        }

        if (descriptionLength < 3) {
            writeUploadError("Description must be of minimum length 3");
            descriptionTextarea.classList.add("error");
        }

        return (titleLength >= 3 && descriptionLength >= 3);
    };

    const addAuthor = () => {
        const authors = document.getElementById('authors');
        const newAuthor = createAuthorBlock(amountAuthors++, "");
        authors.appendChild(newAuthor);
    };

    const showLoading = () => {
        document.querySelectorAll('.submitButton').forEach(button => {
            button.style.display = "none";
        });
        document.getElementById("loading").style.display = "block";
    };
    
    const hideLoading = () => {
        document.querySelectorAll('.submitButton').forEach(button => {
            button.style.display = "block";
        });
        document.getElementById("loading").style.display = "none";
    };
    

    const writeUploadError = (errorMessage) => {
        const uploadError = document.getElementById("upload_error");
        const alert = document.createElement('p');
        alert.style.margin = '0';
        alert.style.padding = '0';
        alert.textContent = 'Upload error: ' + errorMessage;
        uploadError.appendChild(alert);
        uploadError.style.display = 'block';
    };

    const sendDatasetToEndpoint = (endpoint) => {
        cleanUploadErrors();
        showLoading();

        if (checkTitleAndDescription()) {
            const formData = {};

            ["basic_info_form", "uploaded_models_form"].forEach((formId) => {
                const form = document.getElementById(formId);
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    if (input.name) {
                        formData[input.name] = formData[input.name] || [];
                        formData[input.name].push(input.value);
                    }
                });
            });

            const formDataJson = JSON.stringify(formData);
            console.log(formDataJson);

            const csrfToken = document.getElementById('csrf_token').value;
            const formUploadData = new FormData();
            formUploadData.append('csrf_token', csrfToken);

            for (const key in formData) {
                if (formData.hasOwnProperty(key)) {
                    formUploadData.set(key, formData[key]);
                }
            }

            let checkedOrcid = true;
            if (Array.isArray(formData.author_orcid)) {
                for (let orcid of formData.author_orcid) {
                    orcid = orcid.trim();
                    if (orcid !== '' && !isValidOrcid(orcid)) {
                        hideLoading();
                        writeUploadError("ORCID value does not conform to valid format: " + orcid);
                        checkedOrcid = false;
                        break;
                    }
                }
            }

            let checkedName = true;
            if (Array.isArray(formData.author_name)) {
                for (let name of formData.author_name) {
                    name = name.trim();
                    if (name === '') {
                        hideLoading();
                        writeUploadError("The author's name cannot be empty");
                        checkedName = false;
                        break;
                    }
                }
            }

            const datasetAnonymousCheckboxValue = datasetAnonymousCheckbox.checked;
            formUploadData.append('dataset_anonymous', datasetAnonymousCheckboxValue);

            const datasetIdInput = document.getElementById('datasetId');
            if (datasetIdInput) {
                const datasetId = datasetIdInput.value;
                formUploadData.append('datasetId', datasetId)
            }

            if (checkedOrcid && checkedName) {
                console.log("Sending this form data: ");

                formUploadData.forEach((value, key) => {
                    console.log(key, value);
                  });

                fetch(endpoint, {
                    method: 'POST',
                    body: formUploadData
                })
                .then(response => {
                    if (response.ok) {
                        console.log('Dataset sent successfully');
                        response.json().then(data => {
                            console.log(data.message);
                            //window.location.href = "/dataset/list";
                        });
                    } else {
                        response.json().then(data => {
                            console.error('Error: ' + data.message);
                            hideLoading();
                            writeUploadError(data.message);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error in POST request:', error);
                });
            }
        } else {
            hideLoading();
        }
    };

    const isValidOrcid = (orcid) => {
        const orcidRegex = /^\d{4}-\d{4}-\d{4}-\d{4}$/;
        return orcidRegex.test(orcid);
    };

    const toggleUploadButton = () => {
        if (agreeCheckbox && uploadButton) {
            uploadButton.disabled = !agreeCheckbox.checked;
        }
    };

    const toggleAuthorsForm = () => {
        if (datasetAnonymousCheckbox && authorsForm) {
            authorsForm.style.display = datasetAnonymousCheckbox.checked ? 'none' : 'block';
        }
    };

    /*
        Event listeners
    */
    document.getElementById('add_author').addEventListener('click', addAuthor);

    document.addEventListener('click', (event) => {
        if (event.target && event.target.classList.contains('add_author_to_uvl')) {
            const authorsButtonId = event.target.id;
            const authorsId = authorsButtonId.replace("_button", "");
            const authors = document.getElementById(authorsId);
            const id = authorsId.replace("_form_authors", "");
            const newAuthor = createAuthorBlock(amountAuthors, `feature_models-${id}-`);
            authors.appendChild(newAuthor);
        }
    });

    if (agreeCheckbox) {
        agreeCheckbox.addEventListener('change', toggleUploadButton);
        toggleUploadButton();
    }

    if (datasetAnonymousCheckbox) {
        datasetAnonymousCheckbox.addEventListener('change', toggleAuthorsForm);
        toggleAuthorsForm();
    }

    window.onload = () => {

        testZenodoConnection();

        if (uploadButton) {
            uploadButton.addEventListener('click', () => {
                console.log("Sending data...")
                sendDatasetToEndpoint('/dataset/upload');
            });
        }

        if (upgradeButton) {
            upgradeButton.addEventListener('click', () => {
                console.log("Sending data...")
                sendDatasetToEndpoint('/dataset/update');
            });
        }
    };
});

let currentId = 0;
let amountAuthors = 0;
const generateIncrementalId = () => currentId++;

const removeAuthor = (button) => {
    const authorDiv = button.closest('.author');
    if (authorDiv) {
        authorDiv.remove();
    }
};

const cleanUploadErrors = () => {
    const uploadError = document.getElementById("upload_error");
    uploadError.innerHTML = "";
    uploadError.style.display = 'none';
};

const showUploadDataset = () => {
    document.getElementById("submit_dataset").style.display = "block";
};