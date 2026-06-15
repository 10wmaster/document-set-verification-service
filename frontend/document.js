document.addEventListener('DOMContentLoaded', () => {
    try {
        // 1. Достаем результаты из памяти браузера
        const rawData = sessionStorage.getItem('check_result');
        const docType = sessionStorage.getItem('selected_doc_type');

        if (!rawData) {
            const container = document.getElementById('checkColumns');
            if (container) {
                container.innerHTML = `
                    <div style="background: #FEF2F2; padding: 20px; border-radius: 12px; border-left: 4px solid #EF4444; text-align: center;">
                        <h3 style="color: #B91C1C; margin-top: 0; margin-bottom: 8px;">Нет данных для отображения</h3>
                        <div style="color: #7F1D1D; font-size: 15px;">Система не нашла результатов проверки в памяти браузера.<br>Пожалуйста, вернитесь на страницу загрузки и выберите файл.</div>
                    </div>
                `;
            }
            return;
        }

        const data = JSON.parse(rawData);

        // Вспомогательная функция для безопасного заполнения текста
        const safeSetText = (id, text) => {
            const element = document.getElementById(id);
            if (element) element.textContent = text;
        };

        // 2. Заполняем карточку: Метаданные проверки
        safeSetText('docName', data.filename || 'Неизвестный файл');
        safeSetText('docType', docType === 'instruction' ? 'Инструкция по ОТ' : 'Журнал инструктажей');

        const now = new Date();
        safeSetText('checkDate', now.toLocaleDateString('ru-RU') + ' ' + now.toLocaleTimeString('ru-RU'));

        // 3. Заполняем карточку: Статус проверки (Счетчики)
        safeSetText('criticalCount', data.critical_errors || 0);
        safeSetText('warningCount', data.warnings || 0);
        safeSetText('passedCount', data.passed_count || 0);

        // 4. Заполняем НОВУЮ карточку: Итог в процентах
        const compliancePercent = data.compliance_percent || 0;
        const failPercent = 100 - compliancePercent; // Вычисляем "Ошибки"

        safeSetText('successPercent', compliancePercent + '%');
        safeSetText('failPercent', failPercent + '%');

        // 5. Отрисовываем параметры проверки (список ошибок)
        const container = document.getElementById('checkColumns');
        if (container) {
            if (data.errors_list && data.errors_list.length > 0) {
                container.innerHTML = data.errors_list.map(err => `
                    <div style="background: #fff; padding: 16px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid ${err.severity === 'CRITICAL' ? '#EF4444' : '#F59E0B'}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-weight: 600; color: #1E2937; margin-bottom: 8px;">[${err.category}] Локация: ${err.location}</div>
                        <div style="color: #475569; font-size: 14.5px; margin-bottom: 8px;">${err.message}</div>
                        <div style="color: #EF4444; font-size: 13.5px; font-weight: 500; margin-bottom: 4px;">Риск: ${err.fine_equivalent}</div>
                        <div style="color: #10B981; font-size: 13.5px;">💡 Совет эксперта: ${err.legal_tip}</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div style="background: #fff; padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-weight: 600; color: #10B981;">Нарушений ГОСТ не обнаружено. Документ полностью соответствует требованиям.</div>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error("Ошибка при обработке данных на странице результатов:", e);
    }
});

// Кнопки управления
document.getElementById('newCheckBtn')?.addEventListener('click', () => {
    window.location.href = 'upload.html';
});

document.getElementById('downloadBtn')?.addEventListener('click', () => {
    const docType = sessionStorage.getItem('selected_doc_type') || 'instruction';
    window.location.href = `https://precook-earwig-anyway.ngrok-free.dev/api/v1/verify/export/${docType}`;
});