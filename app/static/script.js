let API_BASE_URL = '';

document.addEventListener('DOMContentLoaded', async function() {
    await loadConfig();
    
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        document.getElementById('apiKey').value = savedApiKey;
    }

    document.getElementById('apiKey').addEventListener('change', function() {
        localStorage.setItem('apiKey', this.value);
    });

    setupMainTabs();
    setupFormHandlers();
});

async function loadConfig() {
    try {
        const response = await fetch('/config');
        const config = await response.json();
        API_BASE_URL = config.api_url;
    } catch {
        API_BASE_URL = window.location.origin;
    }
    
    document.getElementById('baseUrlDisplay').textContent = API_BASE_URL;
    document.querySelectorAll('.base-url').forEach(el => {
        el.textContent = API_BASE_URL;
    });
}

function setupMainTabs() {
    const mainTabs = document.querySelectorAll('.main-tab');
    const sections = document.querySelectorAll('.section-content');

    mainTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            mainTabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`section-${tab.dataset.section}`).classList.add('active');
        });
    });
}

function toggleEndpoint(header) {
    const card = header.parentElement;
    card.classList.toggle('open');
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKey');
    input.type = input.type === 'password' ? 'text' : 'password';
}

function getApiKey() {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        showToast('Please enter the API Key', 'error');
        return null;
    }
    return apiKey;
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function getFilenameFromResponse(response, fallback) {
    const disposition = response.headers.get('Content-Disposition');
    if (disposition) {
        let match = disposition.match(/filename\*?=(?:UTF-8'')?([^;\s]+)/i);
        if (match) {
            let filename = match[1].replace(/['"]/g, '');
            try {
                filename = decodeURIComponent(filename);
            } catch (e) {}
            return filename;
        }
    }
    return fallback;
}

async function makeRequest(endpoint, formData) {
    const apiKey = getApiKey();
    if (!apiKey) return null;

    showLoading();
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-API-Key': apiKey
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request error');
        }

        return response;
    } catch (error) {
        showToast(error.message, 'error');
        hideLoading();
        return null;
    }
}

function setupFormHandlers() {
    // PDF Split Form
    document.getElementById('splitForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('splitFile').files[0]);
        formData.append('pages', document.getElementById('splitPages').value);

        const response = await makeRequest('/pdf/split', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'result.pdf');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('PDF split successfully!');
        }
    });

    // Video Cut Form
    document.getElementById('cutMovieForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('cutMovieFile').files[0]);
        formData.append('start', document.getElementById('cutMovieStart').value);
        formData.append('end', document.getElementById('cutMovieEnd').value);

        const response = await makeRequest('/movie/cut', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'recorte.mp4');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('Vídeo recortado com sucesso!');
        }
    });

    document.getElementById('extractForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('extractFile').files[0]);

        const response = await makeRequest('/pdf/extract-pages', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'pages.zip');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('Pages extracted successfully!');
        }
    });

    document.getElementById('mergeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const files = document.getElementById('mergeFiles').files;
        
        if (files.length < 2) {
            showToast('Select at least 2 files', 'error');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        const response = await makeRequest('/pdf/merge', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'merged.pdf');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('PDFs merged successfully!');
        }
    });

    document.getElementById('addPasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('addPwdFile').files[0]);
        formData.append('user_password', document.getElementById('userPassword').value);
        
        const ownerPwd = document.getElementById('ownerPassword').value;
        if (ownerPwd) {
            formData.append('owner_password', ownerPwd);
        }

        const response = await makeRequest('/pdf/add-password', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'protected.pdf');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('Password added successfully!');
        }
    });

    document.getElementById('removePasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('removePwdFile').files[0]);
        formData.append('password', document.getElementById('currentPassword').value);

        const response = await makeRequest('/pdf/remove-password', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'unlocked.pdf');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('Password removed successfully!');
        }
    });

    document.getElementById('infoForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('infoFile').files[0]);

        const response = await makeRequest('/pdf/info', formData);
        if (response) {
            const data = await response.json();
            hideLoading();
            const resultBox = document.getElementById('infoResult');
            resultBox.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            resultBox.classList.remove('hidden');
            showToast('Information retrieved successfully!');
        }
    });

    document.getElementById('convertImageForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('convertImageFile').files[0]);
        formData.append('format', document.getElementById('convertImageFormat').value);
        formData.append('dpi', document.getElementById('convertImageDpi').value);
        
        const pages = document.getElementById('convertImagePages').value;
        if (pages) {
            formData.append('pages', pages);
        }

        const response = await makeRequest('/pdf/convert-to-image', formData);
        if (response) {
            const contentType = response.headers.get('Content-Type');
            const blob = await response.blob();
            hideLoading();
            
            let filename;
            if (contentType.includes('zip')) {
                filename = getFilenameFromResponse(response, 'images.zip');
            } else {
                const format = document.getElementById('convertImageFormat').value;
                const ext = format === 'jpeg' ? 'jpg' : format;
                filename = getFilenameFromResponse(response, `image.${ext}`);
            }
            
            downloadBlob(blob, filename);
            showToast('PDF converted to image successfully!');
        }
    });

    document.getElementById('convertOfxForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('convertOfxFile').files[0]);
        formData.append('bank_id', document.getElementById('convertOfxBankId').value);
        formData.append('account_id', document.getElementById('convertOfxAccountId').value);
        formData.append('account_type', document.getElementById('convertOfxAccountType').value);

        const response = await makeRequest('/pdf/convert-to-ofx', formData);
        if (response) {
            const filename = getFilenameFromResponse(response, 'statement.ofx');
            const blob = await response.blob();
            hideLoading();
            downloadBlob(blob, filename);
            showToast('PDF converted to OFX successfully!');
        }
    });
}
