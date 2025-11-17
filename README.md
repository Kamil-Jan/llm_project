
## Installation

Создаем python environment
```bash
python -m venv ~/venv/llm_project
source ~/venv/llm_project/bin/activate
```

Создаем .env файл
TODO: описать откуда брать ключи

Авторизовываемся в телеграмм
```bash
bash scripts/auth/setup_auth.sh
```

Авторизовываемся в google calendar
```bash
bash scripts/calendar/setup_auth.sh
```

Запускаем докер
```bash
docker-compose up -d
```
