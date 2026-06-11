let selectedDocType = null;

// Обработка выбора карточек типов ЛНА
document.querySelectorAll('.document-card').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.document-card').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        selectedDocType = this.dataset.type;
    });
});

// Drag-and-Drop визуальный эффект
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--color-primary-hover)';
    uploadZone.style.background = 'rgba(26, 115, 232, 0.08)';
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.style.borderColor = 'var(--color-primary)';
    uploadZone.style.background = '#fff';
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--color-primary)';
    uploadZone.style.background = '#fff';

    if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateUploadZoneText(e.dataTransfer.files[0].name);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        updateUploadZoneText(fileInput.files[0].name);
    }
});

function updateUploadZoneText(fileName) {
    uploadZone.querySelector('p').innerHTML = `Выбран файл: <strong>${fileName}</strong>`;
}

// Отправка файла через FormData
document.getElementById('submitBtn').addEventListener('click', async () => {
    if (!selectedDocType) {
        alert('Пожалуйста, укажите тип документа ЛНА.');
        return;
    }

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Пожалуйста, выберите или перетащите файл документа (.docx или .pdf).');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('doc_type', selectedDocType);
    formData.append('file', file);

    try {
        // Показываем индикатор загрузки на кнопке
        const submitBtn = document.getElementById('submitBtn');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Анализ документа парсером...';
        submitBtn.disabled = true;

        const response = await fetch('https://precook-earwig-anyway.ngrok-free.dev/api/v1/verify/expert', {
            method: 'POST',
            body: formData // Браузер сам выставит нужные multipart/form-data заголовки
        });

        submitBtn.textContent = originalText;
        submitBtn.disabled = false;

        if (response.ok) {
            const result = await response.json();
            // Сохраняем сессию для вывода на странице document.html
            sessionStorage.setItem('selected_doc_type', selectedDocType);
            sessionStorage.setItem('check_result', JSON.stringify(result));

            // Редирект на страницу отчета
            window.location.href = 'document.html';
        } else {
            const errData = await response.json();
            alert('Ошибка сервера при проверке: ' + (errData.detail || response.statusText));
        }
    } catch (error) {
        alert('Не удалось связаться с бэкенд-сервером.');
        console.error(error);
    }
});