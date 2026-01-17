document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });

    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        document.getElementById('apiKey').value = savedApiKey;
    }

    document.getElementById('apiKey').addEventListener('change', function() {
        localStorage.setItem('apiKey', this.value);
    });

    setupFormHandlers();
});

function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKey');
    input.type = input.type === 'password' ? 'text' : 'password';
}

function getApiKey() {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        showToast('Por favor, informe a API Key', 'error');
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
            throw new Error(error.detail || 'Erro na requisição');
        }

        return response;
    } catch (error) {
        showToast(error.message, 'error');
        return null;
    } finally {
        hideLoading();
    }
}

function setupFormHandlers() {
    document.getElementById('splitForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('splitFile').files[0]);
        formData.append('pages', document.getElementById('splitPages').value);

        const response = await makeRequest('/pdf/split', formData);
        if (response) {
            const blob = await response.blob();
            downloadBlob(blob, 'split_result.pdf');
            showToast('PDF dividido com sucesso!');
        }
    });

    document.getElementById('extractForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('extractFile').files[0]);

        const response = await makeRequest('/pdf/extract-pages', formData);
        if (response) {
            const blob = await response.blob();
            downloadBlob(blob, 'pages.zip');
            showToast('Páginas extraídas com sucesso!');
        }
    });

    document.getElementById('mergeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const files = document.getElementById('mergeFiles').files;
        
        if (files.length < 2) {
            showToast('Selecione pelo menos 2 arquivos', 'error');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        const response = await makeRequest('/pdf/merge', formData);
        if (response) {
            const blob = await response.blob();
            downloadBlob(blob, 'merged.pdf');
            showToast('PDFs mesclados com sucesso!');
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
            const blob = await response.blob();
            downloadBlob(blob, 'protected.pdf');
            showToast('Senha adicionada com sucesso!');
        }
    });

    document.getElementById('removePasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('removePwdFile').files[0]);
        formData.append('password', document.getElementById('currentPassword').value);

        const response = await makeRequest('/pdf/remove-password', formData);
        if (response) {
            const blob = await response.blob();
            downloadBlob(blob, 'unlocked.pdf');
            showToast('Senha removida com sucesso!');
        }
    });

    document.getElementById('infoForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', document.getElementById('infoFile').files[0]);

        const response = await makeRequest('/pdf/info', formData);
        if (response) {
            const data = await response.json();
            const resultBox = document.getElementById('infoResult');
            resultBox.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            resultBox.classList.remove('hidden');
            showToast('Informações obtidas com sucesso!');
        }
    });
}
