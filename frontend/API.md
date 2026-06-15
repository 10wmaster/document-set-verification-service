# API Documentation — OHS Expert Compliance

## Обзор

Сервис экспресс-аудита ЛНА по охране труда с учетом требований:
- **Приказ 772н** — Инструкции по охране труда
- **Постановление 2464** — Журналы инструктажей

**Базовый URL:** `http://127.0.0.1:9001`

---

## Структура проекта (фронтенд + тестовый бэкенд)

```
frontend/
├── main.py              # FastAPI сервер (для тестов)
├── requirements.txt     # Зависимости
├── index.html           # Главная страница (авторизация)
├── index.css            # Стили
├── index.js             # Логика главной страницы
├── upload.html          # Страница загрузки
├── upload_page.css      # Стили загрузки
├── upload_page.js       # Логика загрузки
├── document.html        # Страница результатов
└── *.png                # Изображения

# Полная версия бэкенда:
backend/
├── main.py              # FastAPI приложение (продакшн)
├── requirements.txt     # Зависимости
└── services/            # Бизнес-логика
    ├── analyzer.py      # Анализ документов
    ├── validator_772n.py # Валидация инструкций
    └── validator_2464.py # Валидация журналов
```

---

## Типы документов

| Значение | Описание | Нормативный акт |
|----------|----------|-----------------|
| `instruction` | Инструкция по охране труда | Приказ 772н |
| `journal` | Журнал инструктажей | Постановление 2464 |

---

## Эндпоинты

### 1. Проверка документа

**POST** `/api/v1/verify/expert`

Проверка документа на соответствие нормативным требованиям.

**Запрос:**

```json
{
    "doc_type": "instruction",
    "document_data": [
        {
            "text": "Текст документа",
            "font": "Times New Roman",
            "size": 14,
            "page": 1
        }
    ]
}
```

**Поля запроса:**

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `doc_type` | string | Да | `instruction` или `journal` |
| `document_data` | array | Да | Массив элементов документа |

**Элемент document_data:**

| Поле | Тип | Описание |
|------|-----|----------|
| `text` | string | Текст элемента |
| `font` | string | Название шрифта |
| `size` | int | Размер шрифта |
| `page` | int | Номер страницы |

**Ответ (успех):**

```json
{
    "status": "FAILED",
    "analyzed_at": "2026-05-23T12:00:00",
    "total_errors": 5,
    "compliance_percent": 75,
    "critical_errors": 2,
    "warnings": 2,
    "recommendations": 1,
    "passed_checks": 15,
    "violations": [
        {
            "category": "Структура (Приказ 772н)",
            "severity": "CRITICAL",
            "message": "Отсутствует обязательный нормативный раздел: 'Общие требования охраны труда'",
            "location": "Structures",
            "legal_tip": "Добавьте в документ главу с точным заголовком."
        }
    ]
}
```

**Поля ответа:**

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | `"PASSED"` или `"FAILED"` |
| `analyzed_at` | string | ISO-формат даты |
| `total_errors` | int | Всего ошибок |
| `compliance_percent` | int | Процент соответствия (0-100) |
| `critical_errors` | int | Критических ошибок |
| `warnings` | int | Предупреждений |
| `recommendations` | int | Рекомендаций |
| `passed_checks` | int | Пройдено проверок |
| `violations` | array | Массив нарушений |

**Уровни критичности (severity):**

| Значение | Описание | Цвет в UI |
|----------|----------|-----------|
| `CRITICAL` | Криатическая ошибка | Красный |
| `WARNING` | Нарушение стандартов оформления | Желтый |
| `RECOMMEND` | Рекомендация по улучшению | Зеленый |

---

### 2. Экспорт отчета в Excel

**GET** `/api/v1/verify/export/{doc_type}`

Генерация и скачивание отчета в формате Excel.

**Параметры:**
- `doc_type` — тип документа (`instruction` или `journal`)

**Ответ:**
- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition`: `attachment; filename="OHS_Expert_Report_instruction_2026-05-23.xlsx"`

**Столбцы Excel:**

| № | Колонка |
|---|---------|
| 1 | Категория |
| 2 | Уровень риска |
| 3 | Описание нарушения |
| 4 | Локация |
| 5 | Рекомендация |

**Раскраска ячеек:**
- `CRITICAL` → красный фон
- `WARNING` → желтый фон
- `RECOMMEND` → зеленый фон

---

### 4. Проверка работы API

**GET** `/api/health`

Проверка работоспособности сервиса.

**Ответ:**

```json
{
    "service": "OHS Expert Compliance API",
    "version": "1.0.0",
    "status": "running",
    "timestamp": "2026-05-23T12:00:00"
}
```

### 5. Статистика

**GET** `/api/v1/dashboard/stats`

Получение статистики проверок (демо-данные).

**Ответ:**

```json
{
    "total_documents": 47,
    "passed_documents": 32,
    "failed_documents": 15,
    "compliance_rate": 68,
    "last_check": "2026-05-23T12:00:00"
}
```

---

## Интеграция с фронтендом

### Фронтенд-структура

```
frontend/
├── index.html          # Главная страница (авторизация)
├── index.css           # Стили главной страницы
├── index.js            # JS главной страницы
├── upload.html         # Страница загрузки документа
├── upload_page.css     # Стили страницы загрузки
├── upload_page.js      # JS страницы загрузки
└── document.html       # Страница результатов
```

### Вызов API из upload_page.js

```javascript
const API_URL = 'http://127.0.0.1:9001';

// Пример вызова проверки документа
async function runDocumentCheck(docType) {
    const testDocumentData = docType === 'instruction'
        ? [
            { text: "Инструкция по охране труда", font: "Times New Roman", size: 14, page: 1 },
            { text: "1. Общие требования охраны труда", font: "Times New Roman", size: 14, page: 1 }
        ]
        : [
            { text: "Журнал инструктажей", font: "Times New Roman", size: 14, page: 1 }
        ];

    const response = await fetch(`${API_URL}/api/v1/verify/expert`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            doc_type: docType,
            document_data: testDocumentData
        })
    });

    if (!response.ok) {
        throw new Error('Ошибка при проверке документа');
    }

    return await response.json();
}
```

### Навигация между страницами

```javascript
// index.js — переход после авторизации
window.location.href = 'upload.html';

// upload_page.js — переход после проверки
sessionStorage.setItem('check_result', JSON.stringify(result));
window.location.href = 'document.html';
```

---

## Валидация данных

### Приказ 772н (Инструкции по охране труда)

**Обязательные разделы:**
1. Общие требования охраны труда
2. Требования охраны труда перед началом работы
3. Требования охраны труда во время работы
4. Требования охраны труда в аварийных ситуациях
5. Требования охраны труда по окончании работы

**Проверки формата:**
| Параметр | Требование |
|----------|-----------|
| Шрифт | Times New Roman или Arial |
| Размер | 14 пт |
| Выравнивание | По ширине |
| Межстрочный интервал | 1.5 |
| Красная строка | 1.25 см |
| Поля | Согласно ГОСТ |

**Проверки заполнения:**
- Наличие ФИО разработчика
- Дата утверждения
- Наличие подписей

---

### Постановление 2464 (Журналы инструктажей)

**Обязательные поля записи:**
| Поле | Описание |
|------|----------|
| ФИО | ФИО работника |
| Дата | Дата инструктажа |
| Подпись | Подпись работника |

**Проверки:**
- Заполнение всех граф
- Наличие подписей ответственных лиц
- Нумерация записей по порядку
- **Контроль просрочки** — если с последнего инструктажа прошло более 6 месяцев

---

## Коды ошибок HTTP

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 400 | Неверный тип документа или данные |
| 404 | Документ не найден |
| 422 | Ошибка валидации данных |
| 500 | Внутренняя ошибка сервера |

**Формат ошибки:**

```json
{
    "detail": "Текст ошибки"
}
```

---

## Запуск сервера (фронтенд + тестовый бэкенд)

Сервер в папке `frontend/` раздаёт статические файлы и предоставляет API для тестирования.

### 1. Установка зависимостей

```powershell
cd frontend
pip install -r requirements.txt
```

### 2. Запуск сервера

```powershell
cd frontend
python main.py
```

После запуска:
- **Главная страница:** http://127.0.0.1:9001/
- **API health:** http://127.0.0.1:9001/api/health
- **Проверка документа:** POST http://127.0.0.1:9001/api/v1/verify/expert

### 3. Доступные страницы

| URL | Описание |
|-----|----------|
| `/` | Главная страница (авторизация) |
| `/upload.html` | Страница загрузки документа |
| `/document.html` | Страница результатов |

### 4. API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/health` | Проверка работоспособности |
| POST | `/api/v1/verify/expert` | Проверка документа |
| GET | `/api/v1/dashboard/stats` | Статистика (демо) |
| GET | `/api/v1/verify/export/{doc_type}` | Экспорт (заглушка) |

### 5. Быстрый тест

```powershell
# Проверка здоровья API
curl http://127.0.0.1:9001/api/health

# Проверка документа
curl -X POST http://127.0.0.1:9001/api/v1/verify/expert -H "Content-Type: application/json" -d "{\"doc_type\":\"instruction\",\"document_data\":[{\"text\":\"ИНСТРУКЦИЯ\",\"font\":\"Times New Roman\",\"size\":14,\"page\":1}]}"
```

---

## Зависимости

```
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
openpyxl>=3.1.0
python-multipart>=0.0.6
```

---

## Тестовые данные

### Пример instruction (инструкция)

```json
{
    "doc_type": "instruction",
    "document_data": [
        { "text": "ИНСТРУКЦИЯ", "font": "Times New Roman", "size": 16, "page": 1 },
        { "text": "по охране труда", "font": "Times New Roman", "size": 14, "page": 1 },
        { "text": "1. ОБЩИЕ ТРЕБОВАНИЯ ОХРАНЫ ТРУДА", "font": "Times New Roman", "size": 14, "page": 1 },
        { "text": "1.1. К работе допускаются лица прошедшие обучение", "font": "Times New Roman", "size": 14, "page": 1 }
    ]
}
```

### Пример journal (журнал)

```json
{
    "doc_type": "journal",
    "document_data": [
        { "text": "№1 | Иванов И.И. | 15.01.2025 | Подпись", "font": "Times New Roman", "size": 12, "page": 1 },
        { "text": "№2 | Петров П.П. | 20.01.2025 | Подпись", "font": "Times New Roman", "size": 12, "page": 1 }
    ]
}
```