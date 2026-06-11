// Переключаем константу на порт 9001, где запущен FastAPI
const API_URL = 'http://127.0.0.1:9001';

document.addEventListener('DOMContentLoaded', () => {
    const data = JSON.parse(sessionStorage.getItem('check_result'));
    if (!data) return;

    // Заполняем счетчики
    document.getElementById('criticalCount').textContent = data.critical_errors;
    document.getElementById('passedCount').textContent = data.passed_count;
    document.getElementById('percentCount').textContent = data.compliance_percent + '%';

    const container = document.getElementById('checkColumns');

    if (data.errors_list && data.errors_list.length > 0) {
        // Динамически выводим список ошибок, если они есть
        container.innerHTML = data.errors_list.map(err => `
            <div class="check-row" style="border-left: 4px solid ${err.severity === 'CRITICAL' ? 'var(--color-error)' : 'var(--color-warning)'}; display: block; margin-bottom: 12px;">
                <div style="font-weight: 600; font-size: 15px;">[${err.category}] — Локация: ${err.location}</div>
                <div style="margin-top: 4px; color: var(--color-text);">${err.message}</div>
                <div style="margin-top: 6px; font-size: 13px; color: var(--color-error); font-weight: 500;">Возможный риск штрафа ГИТ: ${err.fine_equivalent}</div>
                <div style="margin-top: 4px; font-size: 13px; color: var(--color-success);">💡 Совет: ${err.legal_tip}</div>
            </div>
        `).join('');
    } else {
        // Если нарушений не найдено
        container.innerHTML = `
            <div class="check-row" style="border-left: 4px solid var(--color-success);">
                <div>Проверка структуры ЛНА по ГОСТ Р 7.0.97 / Приказ 772н</div>
                <div style="font-weight:600; color:var(--color-success)">Соответствует нормам (100%)</div>
            </div>
        `;
    }
});

// Кнопка скачивания Excel-отчета
document.getElementById('downloadBtn').addEventListener('click', async () => {
    const docType = sessionStorage.getItem('selected_doc_type') || 'instruction';
    // Направляем скачивание на правильный порт бэкенда
    window.location.href = `${API_URL}/api/v1/verify/export/${docType}`;
});