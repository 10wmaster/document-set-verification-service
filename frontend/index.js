/**
 * Index page JavaScript
 * Главная страница с авторизацией через Telegram
 */

document.addEventListener('DOMContentLoaded', function() {
    initTelegramAuth();
});

/**
 * Инициализация авторизации через Telegram
 */
function initTelegramAuth() {
    const telegramBtn = document.querySelector('.button_telegram svg');

    if (telegramBtn) {
        telegramBtn.addEventListener('click', function() {
            console.log('Инициирована авторизация через Telegram');

            // Имитация успешной авторизации - переход на страницу загрузки
            alert('Авторизация успешна! Переход на страницу загрузки...');

            // Переход на страницу загрузки
            window.location.href = 'upload.html';
        });
    }
}