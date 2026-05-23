document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const loader = document.getElementById('loader');

    // Подгружаем конфигурацию виджета динамически
    loadTelegramWidget();

    const cachedUser = sessionStorage.getItem('user_name');
    if (cachedUser) {
        showUserProfile(cachedUser);
    }

    window.onTelegramAuth = function(user) {
        const fullName = `${user.first_name} ${user.last_name || ''}`;
        sessionStorage.setItem('user_name', fullName);
        showUserProfile(fullName);
        sendWidgetAuthToBackend(user);
    };

    async function loadTelegramWidget() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();

            const container = document.getElementById('tg-widget-container');
            if (!container || !config.tg_bot_username) return;

            const script = document.createElement('script');
            script.async = true;
            script.src = "https://telegram.org/js/telegram-widget.js?22";

            script.setAttribute('data-telegram-login', config.tg_bot_username);
            script.setAttribute('data-size', 'medium');
            script.setAttribute('data-onauth', 'onTelegramAuth(user)');
            script.setAttribute('data-request-access', 'write');

            container.appendChild(script);
        } catch (err) {
            console.error("Сбой инициализации параметров конфигурации бота:", err);
        }
    }

    function showUserProfile(name) {
        const widgetContainer = document.getElementById('tg-widget-container');
        const userProfile = document.getElementById('user-profile');

        if (widgetContainer) widgetContainer.classList.add('id-hidden');
        if (userProfile) {
            userProfile.classList.remove('id-hidden');
            userProfile.textContent = `Студент: ${name}`;
        }
    }

    async function sendWidgetAuthToBackend(telegramUser) {
        try {
            const response = await fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(telegramUser)
            });
            const data = await response.json();
            if (response.ok) {
                sessionStorage.setItem('token', data.token);
            } else {
                alert("Ошибка валидации HMAC подписи на стороне бэкенда.");
            }
        } catch (err) {
            console.error("Сбой сети при отправке пакета авторизации:", err);
        }
    }

    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('zone-active');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('zone-active');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('zone-active');
            const droppedFiles = e.dataTransfer.files;
            if (droppedFiles.length > 0) processFileValidation(droppedFiles[0]);
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) processFileValidation(e.target.files[0]);
        });
    }

    function processFileValidation(file) {
        const maxSizeLimit = 10 * 1024 * 1024;
        if (file.size > maxSizeLimit) {
            alert('Размер файла превышает лимит 10 МБ.');
            return;
        }

        const validExtensions = /(\.docx|\.pdf)$/i;
        if (!validExtensions.exec(file.name)) {
            alert('Допускаются только документы .docx и .pdf.');
            return;
        }

        sendDocumentToBackend(file);
    }

    async function sendDocumentToBackend(file) {
        loader.classList.remove('id-hidden');
        const formData = new FormData();
        formData.append('file', file);
        const authToken = sessionStorage.getItem('token');

        try {
            await new Promise(resolve => setTimeout(resolve, 1500));

            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData
            });

            if (response.ok) {
                const verificationResult = await response.json();
                sessionStorage.setItem('gost_results', JSON.stringify(verificationResult));
                window.location.href = '/results';
            } else {
                const errorPayload = await response.json();
                alert('Ошибка: ' + (errorPayload.detail || 'Неизвестный сбой'));
            }
        } catch (serverError) {
            console.error(serverError);
            alert('Не удалось связаться с сервером проверки.');
        } finally {
            loader.classList.add('id-hidden');
        }
    }
});