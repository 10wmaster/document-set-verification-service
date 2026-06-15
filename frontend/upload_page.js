let selectedDocType = 'instruction';
let selectedFiles = [];

document.addEventListener('DOMContentLoaded', function() {
    initDocumentSelection();
    initFileUpload();
    initSubmitButton();
});

function initDocumentSelection() {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedDocType = this.dataset.type;
        });
    });
}

function initFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectFilesBtn = document.getElementById('selectFilesBtn');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, function() {
            dropZone.style.borderColor = '#3B72E0';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function() {
            dropZone.style.borderColor = '#94A3B8';
        }, false);
    });

    dropZone.addEventListener('drop', function(e) {
        handleFiles(e.dataTransfer.files);
    });

    dropZone.addEventListener('click', function() {
        fileInput.click();
    });

    selectFilesBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    if (files.length > 0) {
        selectedFiles = Array.from(files);
        // Обновляем текст в UI
        const titleElement = document.querySelector('.upload-title');
        titleElement.innerHTML = `Выбран файл: <span style="color: #3B72E0;">${files[0].name}</span>`;
    }
}

function initSubmitButton() {
    const startCheckBtn = document.getElementById('startCheckBtn');
    startCheckBtn.addEventListener('click', function() {
        if (!selectedDocType) {
            alert('Пожалуйста, выберите тип документа');
            return;
        }
        if (selectedFiles.length === 0) {
            alert('Пожалуйста, загрузите файл');
            return;
        }
        startCheck();
    });
}

async function startCheck() {
    const startCheckBtn = document.getElementById('startCheckBtn');
    const originalText = startCheckBtn.innerHTML;

    startCheckBtn.innerHTML = 'Анализ документа...';
    startCheckBtn.disabled = true;

    const formData = new FormData();
    formData.append('doc_type', selectedDocType);
    formData.append('file', selectedFiles[0]);

    try {
        const response = await fetch('https://precook-earwig-anyway.ngrok-free.dev/api/v1/verify/expert', {
            method: 'POST',
            body: formData
        });

        startCheckBtn.innerHTML = originalText;
        startCheckBtn.disabled = false;

        if (response.ok) {
            const result = await response.json();
            sessionStorage.setItem('selected_doc_type', selectedDocType);
            sessionStorage.setItem('check_result', JSON.stringify(result));
            window.location.href = 'document.html';
        } else {
            const errData = await response.json();
            alert('Ошибка сервера: ' + (errData.detail || response.statusText));
        }
    } catch (error) {
        startCheckBtn.innerHTML = originalText;
        startCheckBtn.disabled = false;
        alert('Не удалось связаться с сервером ngrok.');
        console.error(error);
    }
}