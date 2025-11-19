# AstroBot

AstroBot — Telegram-бот для создания и управления событиями с помощью текста и голосовых сообщений.
Бот умеет распознавать естественный язык, создавать события в Google Calendar, формировать удобные карточки встреч и анализировать благоприятность времени на основе астрологического контекста.

## Основные возможности

### Голосовое создание событий
Пользователь может отправить голосовое сообщение. Бот распознает речь и автоматически извлекает время, дату и название события.

### Команда ++event
AstroBot поддерживает ручное создание события в формате:

    ++event пятница 14:00-16:00 презентация клиенту --remind 1h,15m

Бот корректно обрабатывает относительные и абсолютные формулировки:
"завтра в 11", "через 2 часа", "следующий понедельник", "15:00-16:00" и другие.

### Понимание естественного языка
Бот анализирует текст запроса, извлекает структуру события, даты, диапазоны времени и длительности.

### Астрологическая оценка времени
AstroBot использует локальный векторный индекс (FAISS) для поиска релевантных астрологических текстов.
Затем, на основе найденного контекста, бот запрашивает LLM для формирования краткого астрологического совета о благоприятности выбранного времени.

### Напоминания
Пользователь может указать напоминания вручную:

    --remind 15m,1h,2h

Или использовать настройки по умолчанию.

### Интеграция с Google Calendar
Каждое созданное событие автоматически добавляется в Google Calendar пользователя.

### Карточки событий
После создания события бот формирует информативную карточку события и закрепляет её в чате.

## Структура проекта

```
project/
├── src/                          # Основной код приложения
│   ├── main.py                   # Точка входа приложения
│   │
│   ├── bot/                      # Telegram бот
│   │   ├── service.py            # Основной сервис бота
│   │   ├── keyboards.py          # Клавиатуры для бота
│   │   └── handlers/             # Обработчики событий бота
│   │       ├── callbacks.py      # Обработчики callback-запросов
│   │       ├── events.py         # Обработчики событий
│   │       └── settings.py       # Обработчики настроек
│   │
│   ├── userbot/                  # Telegram userbot (для работы с сообщениями)
│   │   ├── service.py            # Сервис userbot
│   │   ├── message_manager.py    # Менеджер сообщений
│   │   └── handlers/             # Обработчики userbot
│   │       └── commands.py       # Обработчики команд
│   │
│   ├── services/                 # Бизнес-логика приложения
│   │   ├── service.py            # Базовый класс сервиса
│   │   ├── ai_service.py        # Сервис для работы с LLM
│   │   ├── asr_service.py        # Сервис распознавания речи (Deepgram)
│   │   ├── calendar_service.py   # Интеграция с Google Calendar
│   │   ├── event_service.py      # Управление событиями
│   │   ├── scheduler_service.py  # Планировщик задач
│   │   ├── search_service.py     # Поиск в векторном индексе (FAISS)
│   │   └── user_settings_service.py  # Управление настройками пользователей
│   │
│   ├── models/                   # Модели данных (TortoiseORM)
│   │   ├── document.py           # Модель документа для поиска
│   │   ├── event.py              # Модель события
│   │   └── user.py               # Модель пользователя
│   │
│   ├── config/                   # Конфигурация
│   │   ├── settings.py           # Настройки приложения (Pydantic)
│   │   └── database.py           # Настройка базы данных
│   │
│   └── utils/                    # Вспомогательные утилиты
│       ├── logger.py             # Настройка логирования
│       ├── exceptions.py         # Кастомные исключения
│       └── helpers.py            # Вспомогательные функции
│
├── scripts/                      # Скрипты для настройки
│   ├── auth/                     # Авторизация Telegram
│   │   ├── auth_telegram.py      # Скрипт авторизации
│   │   ├── setup_auth.sh        # Скрипт установки
│   │   └── requirements.txt      # Зависимости для авторизации
│   └── calendar/                 # Авторизация Google Calendar
│       ├── auth_calendar.py      # Скрипт авторизации
│       └── setup_auth.sh        # Скрипт установки
│
├── credentials/                  # Учетные данные
│   └── token.json                # Токен Google Calendar (генерируется)
│
├── sessions/                     # Сессии Telegram
│   └── project_userbot.session   # Сессия userbot (генерируется)
│
├── faiss_index/                  # Векторный индекс для поиска
│   ├── index.faiss               # FAISS индекс
│   └── index.pkl                 # Метаданные индекса
│
├── benchmark/                    # Бенчмарки и тесты
│   ├── benchmark.py              # Скрипт бенчмарка
│   ├── dataset.json              # Тестовый датасет
│   ├── metrics.md                # Метрики производительности
│   └── requirements.txt          # Зависимости для бенчмарков
│
├── docker-compose.yml            # Конфигурация Docker Compose
├── Dockerfile                    # Образ Docker для приложения
├── requirements.txt              # Python зависимости
├── example.env                   # Пример файла с переменными окружения
└── README.md                     # Документация проекта
```

### Описание основных компонентов

#### `src/main.py`
Точка входа приложения. Содержит класс `Application`, который инициализирует и управляет всеми сервисами:
- Инициализация базы данных
- Создание и запуск всех сервисов
- Обработка сигналов завершения работы

#### `src/bot/`
Модуль Telegram бота, который обрабатывает команды и сообщения от пользователей:
- `service.py` - основной сервис бота на базе aiogram
- `handlers/` - обработчики различных типов событий (команды, callback, настройки)

#### `src/userbot/`
Telegram userbot для работы с сообщениями пользователя:
- Перехватывает сообщения с командой `++event`
- Обрабатывает голосовые сообщения
- Взаимодействует с основным ботом

#### `src/services/`
Бизнес-логика приложения:
- **ai_service.py** - интеграция с LLM (OpenAI/OpenRouter) для обработки естественного языка
- **asr_service.py** - распознавание речи через Deepgram API
- **calendar_service.py** - создание и управление событиями в Google Calendar
- **event_service.py** - бизнес-логика работы с событиями
- **search_service.py** - поиск в векторном индексе FAISS для астрологического контекста
- **scheduler_service.py** - планирование напоминаний
- **user_settings_service.py** - управление настройками пользователей

#### `src/models/`
Модели данных для базы данных (TortoiseORM):
- `user.py` - пользователи и их настройки
- `event.py` - события
- `document.py` - документы для векторного поиска

## Установка и запуск

### Предварительные требования

- Python 3.11+
- Docker и Docker Compose
- Telegram API credentials (API ID и API Hash)
- Google Cloud Project с включенным Calendar API
- API ключи для:
  - Deepgram (распознавание речи)
  - OpenAI/OpenRouter (LLM)
  - Yandex (опционально)

### Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd project
```

### Шаг 2: Настройка окружения

1. Создайте файл `.env` на основе `example.env`:

```bash
cp example.env .env
```

2. Заполните все необходимые переменные в `.env`:

```env
# Telegram
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE_NUMBER=+1234567890
TELEGRAM_BOT_TOKEN=your_bot_token_here
OWNER_USER_ID=123456789

# База данных
POSTGRES_USER=project
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=project
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Настройки
TIMEZONE=Europe/Moscow
DEFAULT_REMINDER_TIMES=15m,1h
LOG_LEVEL=INFO

# Yandex (опционально)
YANDEX_FOLDER_ID=your_yandex_folder_id_here
YANDEX_API_KEY=your_yandex_api_key_here

# OpenAI/OpenRouter
OPENAI_API_KEY=your_openrouter_api_key_here

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials/credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=credentials/token.json
GOOGLE_CALENDAR_ID=primary

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_api_key
```

### Шаг 3: Получение API ключей

#### Deepgram API Key
1. Перейдите на [Deepgram Console](https://console.deepgram.com)
2. Зарегистрируйтесь или войдите в аккаунт
3. Откройте раздел **API Keys**
4. Нажмите **Create API Key**
5. Скопируйте ключ и вставьте в `DEEPGRAM_API_KEY` в файле `.env`

#### Telegram API Credentials
1. Перейдите на [my.telegram.org](https://my.telegram.org)
2. Войдите с вашим номером телефона
3. Перейдите в раздел **API development tools**
4. Создайте новое приложение и получите `API_ID` и `API_HASH`
5. Вставьте их в `.env`

#### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен в `TELEGRAM_BOT_TOKEN`

#### OpenAI/OpenRouter API Key
1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai) или используйте OpenAI
2. Получите API ключ
3. Вставьте в `OPENAI_API_KEY`

#### Google Calendar API
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com)
2. Включите Google Calendar API
3. Создайте OAuth 2.0 credentials (тип "Desktop app")
4. Скачайте файл credentials и сохраните как `credentials/credentials.json`

### Шаг 4: Авторизация Telegram

Запустите скрипт авторизации для userbot:

```bash
bash scripts/auth/setup_auth.sh
```

Это создаст файл сессии `sessions/project_userbot.session`.

### Шаг 5: Авторизация Google Calendar

Запустите скрипт авторизации для Google Calendar:

```bash
bash scripts/calendar/setup_auth.sh
```

Это создаст файл `credentials/token.json` после авторизации через браузер.

### Шаг 6: Запуск через Docker

Запустите все сервисы с помощью Docker Compose:

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL базу данных
- Приложение AstroBot

Для просмотра логов:

```bash
docker-compose logs -f app
```

Для остановки:

```bash
docker-compose down
```

### Шаг 7: Проверка работы

1. Найдите вашего бота в Telegram по имени, указанному при создании
2. Отправьте команду `/start`
3. Попробуйте создать событие:
   - Текстом: `++event завтра в 14:00 встреча с командой`
   - Голосовым сообщением: отправьте голосовое сообщение с описанием события

## Troubleshooting

### Проблемы с авторизацией Telegram
- Убедитесь, что `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` корректны
- Проверьте, что файл сессии создан в `sessions/`

### Проблемы с Google Calendar
- Убедитесь, что `credentials/credentials.json` существует
- Проверьте, что Google Calendar API включен в проекте
- Перезапустите авторизацию: `bash scripts/calendar/setup_auth.sh`

### Проблемы с базой данных
- Проверьте, что PostgreSQL контейнер запущен: `docker-compose ps`
- Проверьте логи: `docker-compose logs postgres`
- Убедитесь, что переменные окружения для БД корректны

### Проблемы с распознаванием речи
- Проверьте, что `DEEPGRAM_API_KEY` валиден
- Убедитесь, что на аккаунте Deepgram есть кредиты
