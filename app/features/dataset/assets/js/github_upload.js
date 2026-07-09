export function initializeGithubUpload() {
    const uploadBtn = document.getElementById('github_upload_btn');
    if (!uploadBtn) return;

    uploadBtn.addEventListener('click', handleGithubUpload);

    // Clear file list when user changes any input
    const repoInput = document.getElementById('github_repo_url');
    const branchInput = document.getElementById('github_branch');
    const pathInput = document.getElementById('github_path');

    const clearFileList = () => {
        const fileListContainer = document.getElementById('github_file_list_container');
        const fileListDiv = document.getElementById('github_file_list');
        const statusDiv = document.getElementById('github_upload_status');
        const btn = document.getElementById('github_upload_btn');

        if (fileListContainer) fileListContainer.style.display = 'none';
        if (fileListDiv) fileListDiv.innerHTML = '';
        if (statusDiv) {
            statusDiv.innerHTML = '';
            statusDiv.className = 'mt-3 fs-7';
        }

        // Reset button completely - clone to remove all old listeners
        if (btn) {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);

            // Attach fresh listener
            const freshBtn = document.getElementById('github_upload_btn');
            if (freshBtn) {
                freshBtn.addEventListener('click', handleGithubUpload);
            }
        }
    };

    if (repoInput) repoInput.addEventListener('input', clearFileList);
    if (branchInput) branchInput.addEventListener('input', clearFileList);
    if (pathInput) pathInput.addEventListener('input', clearFileList);
}

async function handleGithubUpload(e) {
    e.preventDefault();
    e.stopImmediatePropagation();

    // Get input values
    const repoUrl = document.getElementById('github_repo_url')?.value.trim();
    const branch = document.getElementById('github_branch')?.value.trim() || 'main';
    const path = document.getElementById('github_path')?.value.trim();
    const statusDiv = document.getElementById('github_upload_status');
    const uploadBtn = document.getElementById('github_upload_btn');
    const fileListContainer = document.getElementById('github_file_list_container');

    // Reset status
    if (statusDiv) {
        statusDiv.innerHTML = '';
        statusDiv.className = 'mt-3 fs-7';
    }

    // Validation
    if (!repoUrl) {
        showStatus(statusDiv, 'Repository URL is required', 'error');
        return;
    }

    if (!path) {
        showStatus(statusDiv, 'Path is required', 'error');
        return;
    }

    // Check if it's a file or folder
    const isFile = path.toLowerCase().endsWith('.uvl');

    if (isFile) {
        // Handle single file download
        await handleSingleFile(repoUrl, branch, path, statusDiv, uploadBtn);
    } else {
        // Handle folder - list files and show checkboxes
        await handleFolderSelection(repoUrl, branch, path, statusDiv, uploadBtn, fileListContainer);
    }
}

async function handleSingleFile(repoUrl, branch, filePath, statusDiv, uploadBtn) {
    // Disable button and show loading
    uploadBtn.disabled = true;
    const originalText = uploadBtn.innerHTML;
    uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Downloading...';
    showStatus(statusDiv, 'Downloading from GitHub...', 'info');

    try {
        const response = await fetch('/hubfile/upload-github', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                github_url: repoUrl,
                branch: branch,
                file_path: filePath,
            }),
        });

        let data;
        try {
            data = await response.json();
        } catch (e) {
            console.error('Failed to parse JSON response:', e);
            showStatus(statusDiv, `❌ Server error: Invalid response (Status ${response.status})`, 'error');
            return;
        }

        console.log('Server response:', data, 'Status:', response.status);

        if (!response.ok) {
            showStatus(statusDiv, `❌ ${data.message || 'Failed to download file'}`, 'error');
            return;
        }

        if (!data.filename) {
            showStatus(statusDiv, `❌ Server error: No filename in response`, 'error');
            console.error('Response has no filename:', data);
            return;
        }

        const tempFilename = data.filename;
        addFileToDropzone(tempFilename, filePath);

        // Clear inputs
        document.getElementById('github_repo_url').value = '';
        document.getElementById('github_branch').value = 'main';
        document.getElementById('github_path').value = '';

        showStatus(
            statusDiv,
            `✓ ${filePath.split('/').pop()} downloaded successfully from GitHub`,
            'success'
        );

    } catch (error) {
        console.error('GitHub upload error:', error);
        showStatus(statusDiv, `❌ Network error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = originalText;
    }
}

async function handleFolderSelection(repoUrl, branch, folderPath, statusDiv, uploadBtn, fileListContainer) {
    uploadBtn.disabled = true;
    const originalText = uploadBtn.innerHTML;
    uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Listing files...';
    showStatus(statusDiv, 'Fetching files from GitHub...', 'info');

    try {
        const response = await fetch('/hubfile/list-github-files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                github_url: repoUrl,
                branch: branch,
                folder_path: folderPath,
            }),
        });

        let data;
        try {
            data = await response.json();
        } catch (e) {
            console.error('Failed to parse JSON response:', e);
            showStatus(statusDiv, `❌ Server error: Invalid response (Status ${response.status})`, 'error');
            return;
        }

        if (!response.ok) {
            showStatus(statusDiv, `❌ ${data.message || 'Failed to list files'}`, 'error');
            return;
        }

        if (!data.files || data.files.length === 0) {
            showStatus(statusDiv, '❌ No .uvl files found in this folder', 'error');
            return;
        }

        // Show file list with checkboxes
        showFileList(data.files, repoUrl, branch, folderPath, statusDiv, uploadBtn, fileListContainer);

    } catch (error) {
        console.error('Error listing files:', error);
        showStatus(statusDiv, `❌ Network error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = originalText;
    }
}

function showFileList(files, repoUrl, branch, folderPath, statusDiv, uploadBtn, fileListContainer) {
    const fileListDiv = document.getElementById('github_file_list');
    fileListDiv.innerHTML = '';

    files.forEach((file, index) => {
        const checkbox = document.createElement('div');
        checkbox.className = 'form-check mb-2';
        checkbox.innerHTML = `
            <input class="form-check-input github-file-checkbox" type="checkbox"
                   id="github_file_${index}" value="${file}" checked>
            <label class="form-check-label" for="github_file_${index}">
                ${file}
            </label>
        `;
        fileListDiv.appendChild(checkbox);
    });

    // Show container
    fileListContainer.style.display = 'block';

    // Change button behavior to download selected files
    uploadBtn.onclick = null;
    uploadBtn.innerHTML = 'Download selected files';
    uploadBtn.removeEventListener('click', handleGithubUpload);

    uploadBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopImmediatePropagation();

        const selectedFiles = Array.from(document.querySelectorAll('.github-file-checkbox:checked'))
            .map(cb => cb.value);

        if (selectedFiles.length === 0) {
            showStatus(statusDiv, '❌ Please select at least one file', 'error');
            return;
        }

        await downloadSelectedFiles(selectedFiles, repoUrl, branch, folderPath, statusDiv, uploadBtn, fileListContainer);
    });

    showStatus(statusDiv, `Found ${files.length} .uvl file(s). Select which ones to download.`, 'info');
}

async function downloadSelectedFiles(selectedFiles, repoUrl, branch, folderPath, statusDiv, uploadBtn, fileListContainer) {
    uploadBtn.disabled = true;
    const originalText = uploadBtn.innerHTML;
    uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Downloading ${selectedFiles.length} file(s)...`;
    showStatus(statusDiv, `Downloading ${selectedFiles.length} file(s)...`, 'info');

    const results = { success: 0, failed: 0, errors: [] };

    try {
        for (const fileName of selectedFiles) {
            try {
                const filePath = folderPath.endsWith('/')
                    ? `${folderPath}${fileName}`
                    : `${folderPath}/${fileName}`;

                const response = await fetch('/hubfile/upload-github', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        github_url: repoUrl,
                        branch: branch,
                        file_path: filePath,
                    }),
                });

                let data;
                try {
                    data = await response.json();
                } catch (e) {
                    results.failed++;
                    results.errors.push(`${fileName}: Invalid server response`);
                    continue;
                }

                if (!response.ok) {
                    results.failed++;
                    results.errors.push(`${fileName}: ${data.message || 'Unknown error'}`);
                } else if (data.filename) {
                    addFileToDropzone(data.filename, filePath);
                    results.success++;
                } else {
                    results.failed++;
                    results.errors.push(`${fileName}: No filename in response`);
                }
            } catch (error) {
                console.error(`Error downloading ${fileName}:`, error);
                results.failed++;
                results.errors.push(`${fileName}: ${error.message}`);
            }
        }

        // Show results
        if (results.success > 0) {
            showStatus(
                statusDiv,
                `✓ Downloaded ${results.success} file(s) successfully${results.failed > 0 ? `. Failed: ${results.failed}` : ''}`,
                results.failed > 0 ? 'warning' : 'success'
            );

            // Reset form after a short delay
            setTimeout(() => {
                resetGithubForm(uploadBtn, originalText, fileListContainer, statusDiv);
            }, 2000);
        } else {
            showStatus(statusDiv, `❌ Failed to download files: ${results.errors.join('; ')}`, 'error');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Unexpected error in downloadSelectedFiles:', error);
        showStatus(statusDiv, `❌ Unexpected error: ${error.message}`, 'error');
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = originalText;
    }
}

function resetGithubForm(uploadBtn, originalText, fileListContainer, statusDiv) {
    try {
        // Clear input fields
        const repoInput = document.getElementById('github_repo_url');
        const branchInput = document.getElementById('github_branch');
        const pathInput = document.getElementById('github_path');

        if (repoInput) repoInput.value = '';
        if (branchInput) branchInput.value = 'main';
        if (pathInput) pathInput.value = '';

        // Clear file list container
        const fileListDiv = document.getElementById('github_file_list');
        if (fileListDiv) {
            fileListDiv.innerHTML = '';
        }
        if (fileListContainer) {
            fileListContainer.style.display = 'none';
        }

        // Clear status
        if (statusDiv) {
            statusDiv.innerHTML = '';
            statusDiv.className = 'mt-3 fs-7';
        }

        // Reset button to original state
        const btn = document.getElementById('github_upload_btn');
        if (btn) {
            btn.innerHTML = originalText || 'Upload from GitHub';
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Error resetting form:', error);
    }
}

function addFileToDropzone(tempFilename, originalPath) {
    if (typeof myDropzone === 'undefined' || !window.myDropzoneReady) {
        console.warn('Dropzone not ready yet. Retrying...');
        setTimeout(() => addFileToDropzone(tempFilename, originalPath), 200);
        return;
    }

    try {
        const displayName = originalPath.split('/').pop();

        const mockFile = {
            name: displayName,
            size: 0,
            type: 'text/plain',
            lastModified: Date.now(),
            lastModifiedDate: new Date(),
            tempFilename: tempFilename,
            status: Dropzone.SUCCESS,
            accepted: true,
        };

        myDropzone.files.push(mockFile);
        myDropzone.emit('addedfile', mockFile);
        myDropzone.emit('complete', mockFile);

        console.log('File added to dropzone:', tempFilename, 'Display name:', displayName);
    } catch (error) {
        console.error('Error adding file to dropzone:', error);
    }
}

function showStatus(element, message, type) {
    if (!element) return;

    const classMap = {
        info: 'text-muted',
        success: 'text-success',
        warning: 'text-warning',
        error: 'text-danger',
    };

    element.className = `mt-3 fs-7 ${classMap[type] || 'text-muted'}`;
    element.innerHTML = message;
}
