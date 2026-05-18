# Thai Boxing DRF

> DRF-версия проекта судейства по тайскому боксу.

- Проект: [devarena.ru](http://devarena.ru:3000/)
- Swagger: [devarena.ru Swagger](http://devarena.ru:8000/api/swagger/)

---

**Thai Boxing DRF** — это backend API для системы судейства, авторизации и управления сущностями турнира.  
Проект стал логическим продолжением шаблонной Django Templates-версии и переводит основную бизнес-логику в формат REST API.

---

## Функциональность проекта

### Пользователи и авторизация
- регистрация и авторизация пользователей
- JWT-аутентификация
- кастомная модель пользователя

### Судейский модуль
- создание и управление комнатами
- работа с боями
- логика для боксеров, тренеров и судей
- ролевой доступ

### Документация и админка
- Swagger UI
- ReDoc
- Django Admin

---

## Stack

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose
- Nginx
- Gunicorn
- drf-spectacular

---

## Особенности проекта

- backend отделен от frontend
- конфигурация через `.env`
- PostgreSQL и локально, и на VPS
- продовый запуск через `gunicorn`
- статика Django admin раздается через `nginx`
- проект готов к деплою на VPS через GitHub Actions

---

## Локальный запуск

| Шаг | Команда / Действие |
|-----|--------------------|
| 1 | Установи [Git](https://git-scm.com), [Docker](https://www.docker.com/products/docker-desktop) |
| 2 | `git clone https://github.com/Skuba4/thai_boxing_drf.git` |
| 3 | `cd thai_boxing_drf` |
| 4 | Создай `.env` на основе `.env.example` |
| 5 | `docker compose up --build` |
| 6 | Открывай `http://localhost:8000/admin/` или `http://localhost:8000/api/swagger/` |

---

## Продовый запуск

Для prod используются:
- `DEBUG=False`
- PostgreSQL
- `gunicorn`
- `nginx` внутри backend-контейнера

Базовый запуск:

```bash
docker compose up -d --build
```

---

## Файл `.env.example`

В проекте лежит [.env.example](/E:/Projects/drf/.env.example).  
Создай на его основе `.env` и укажи свои значения.

Главные группы переменных:
- Django settings
- CORS / CSRF
- PostgreSQL
- Docker env

---

## Docker-шпаргалка

```bash
docker compose build --no-cache
docker compose up -d
docker compose down
docker compose down -v
docker logs -f thai_boxing_drf_backend
```

---

## Примечание

Сейчас проект ориентирован именно на backend-часть.  
Frontend поднимается отдельно и подключается к API по настроенным `CORS_ALLOWED_ORIGINS` и `CSRF_TRUSTED_ORIGINS`.
