import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

# Для работы с токенами обычно используется PyJWT (import jwt)
try:
    import jwt
except ImportError:
    jwt = None

def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    """Проверка криптографической подписи данных от Telegram"""
    if 'hash' not in data:
        print("❌ Ошибка валидации: В данных от фронтенда нет поля 'hash'")
        return False

    received_hash = data['hash']

    # Собираем строку для проверки (сортируем ключи, исключая сам hash)
    data_check_list = []
    for key, value in sorted(data.items()):
        if key != 'hash' and value is not None and value != '':
            data_check_list.append(f"{key}={value}")

    data_check_string = "\n".join(data_check_list)

    # Вычисляем секретный ключ
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()

    # Считаем HMAC-SHA256
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # ОТЛАДКА В КОНСОЛЬ PYCHARM:
    print("\n" + "-"*40)
    print("ВХОДЯЩИЕ ДАННЫЕ ДЛЯ ПРОВЕРКИ:")
    print(f"Строка проверки:\n{data_check_string}")
    print(f"Полученный хэш:  {received_hash}")
    print(f"Вычисленный хэш: {computed_hash}")
    print("-"*40 + "\n")

    return hmac.compare_digest(computed_hash, received_hash)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Генерация безопасного JWT-токена для сессии пользователя"""
    to_encode = data.copy()

    # Устанавливаем время жизни токена (по умолчанию 1 день)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=1)

    to_encode.update({"exp": expire})

    # Берем SECRET_KEY, который прописан у тебя в .env
    secret_key = os.getenv("SECRET_KEY", "super-secret-fallback-key")
    algorithm = "HS256"

    if jwt:
        return jwt.encode(to_encode, secret_key, algorithm=algorithm)

    # Запасной вариант, если библиотека PyJWT ещё не установлена в окружении
    print("⚠️ Предупреждение: пакет PyJWT не найден. Используется временный токен.")
    return f"mock-session-token-{data.get('sub')}"