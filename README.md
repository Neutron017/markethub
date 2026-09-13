# MarketHub

Микросервисная платформа маркетплейса на Python и FastAPI.

Проект демонстрирует построение распределённой системы с отдельными базами данных для микросервисов, асинхронным взаимодействием через RabbitMQ, кешированием через Redis, балансировкой нагрузки Nginx, мониторингом Prometheus/Grafana и CI/CD через GitHub Actions.

---

## Архитектура

```text
                         Internet
                            |
                            v
                       +---------+
                       |  Nginx  |
                       |   :80   |
                       +----+----+
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
   User Service      Product Service     Order Service
      :8001             :8002                 :8003
                           |
                           v
                         Redis
                           |
                           v
                  Product Service 2


   Order Service
        |
        v
    RabbitMQ
        |
        v
 Notification Service
       :8004


   All services
        |
        v
    Prometheus
       :9090
        |
        v
     Grafana
       :3000
```

---

## Микросервисы

### User Service

Отвечает за:

- регистрацию пользователей;
- авторизацию;
- JWT-аутентификацию;
- роли пользователей;
- получение текущего пользователя.

Порт:

```text
8001
```

База данных:

```text
users_db
```

---

### Product Service

Отвечает за:

- категории товаров;
- создание и управление товарами;
- остатки товаров;
- отзывы;
- поиск и фильтрацию;
- Redis-кеширование.

Запущен в двух экземплярах для демонстрации балансировки нагрузки:

```text
product-service
product-service-2
```

Порт:

```text
8002
```

---

### Order Service

Отвечает за:

- корзину;
- добавление товаров в корзину;
- создание заказов;
- историю заказов;
- изменение статуса заказа;
- получение информации о товарах через Product Service;
- публикацию событий в RabbitMQ.

Порт:

```text
8003
```

---

### Notification Service

Получает события из RabbitMQ и создаёт уведомления пользователей.

Поддерживаются события:

```text
ORDER_CREATED
ORDER_STATUS_CHANGED
```

Порт:

```text
8004
```

---

# Технологии

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL 16
- Alembic
- Redis 7
- RabbitMQ
- aio-pika
- Nginx
- Docker
- Docker Compose
- Prometheus
- Grafana
- GitHub Actions
- GitHub Container Registry
- JWT
- Ruff

---

# Структура проекта

```text
markethub/
│
├── user-service/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── product-service/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── order-service/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── notification-service/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── nginx/
│   └── nginx.conf
│
├── prometheus/
│   └── prometheus.yml
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# Запуск проекта

## Требования

Для запуска необходимы:

- Docker
- Docker Compose
- Git

Клонировать репозиторий:

```bash
git clone <repository-url>
cd markethub
```

Запустить все сервисы:

```bash
docker compose up -d --build
```

Проверить состояние контейнеров:

```bash
docker compose ps
```

---

# Миграции базы данных

После первого запуска необходимо применить Alembic-миграции:

```bash
docker compose exec user-service alembic upgrade head
docker compose exec product-service alembic upgrade head
docker compose exec order-service alembic upgrade head
docker compose exec notification-service alembic upgrade head
```

После применения миграций сервисы готовы к работе.

---

# API

Основной вход в API осуществляется через Nginx:

```text
http://localhost
```

Swagger отдельных сервисов:

```text
User Service:
http://localhost:8001/docs

Product Service:
http://localhost:8002/docs

Order Service:
http://localhost:8003/docs

Notification Service:
http://localhost:8004/docs
```

---

# Основные API endpoints

## Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

## Users

```text
GET /api/v1/users/me
```

## Categories

```text
POST   /api/v1/categories
GET    /api/v1/categories
GET    /api/v1/categories/{category_id}
DELETE /api/v1/categories/{category_id}
```

## Products

```text
POST   /api/v1/products
GET    /api/v1/products
GET    /api/v1/products/{product_id}
PATCH  /api/v1/products/{product_id}
DELETE /api/v1/products/{product_id}
```

## Reviews

```text
POST /api/v1/products/{product_id}/reviews
GET  /api/v1/products/{product_id}/reviews
```

## Cart

```text
GET    /api/v1/cart
POST   /api/v1/cart/items
PATCH  /api/v1/cart/items/{item_id}
DELETE /api/v1/cart/items/{item_id}
DELETE /api/v1/cart
```

## Orders

```text
POST  /api/v1/orders
GET   /api/v1/orders
GET   /api/v1/orders/{order_id}
PATCH /api/v1/orders/{order_id}/status
```

## Notifications

```text
GET /api/v1/notifications
```

---

# PostgreSQL

Каждый микросервис использует собственную базу данных.

| Сервис | База данных | Порт |
|---|---|---:|
| User Service | users_db | 5433 |
| Product Service | products_db | 5434 |
| Order Service | orders_db | 5435 |
| Notification Service | notifications_db | 5436 |

Между базами данных отсутствуют общие таблицы и внешние ключи.

Связь между сервисами осуществляется через REST API и UUID идентификаторы.

---

# Redis

Redis используется в Product Service для кеширования списка товаров.

Основные параметры:

```text
TTL: 60 секунд
```

Кеш инвалидируется при изменении данных о товарах.

Если Redis временно недоступен, Product Service продолжает работать с PostgreSQL.

---

# RabbitMQ

RabbitMQ используется для асинхронного взаимодействия между микросервисами.

Exchange:

```text
markethub.events
```

Тип:

```text
topic
```

Основные события:

```text
ORDER_CREATED
ORDER_STATUS_CHANGED
```

Notification Service подписан на события, связанные с заказами.

---

# Nginx

Nginx используется как:

- reverse proxy;
- единая точка входа в API;
- балансировщик нагрузки.

Product Service запущен в двух экземплярах:

```text
product-service
product-service-2
```

Nginx распределяет запросы между экземплярами.

---

# Мониторинг

Для мониторинга используются:

- Prometheus;
- Grafana;
- prometheus-fastapi-instrumentator.

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

Метрики FastAPI доступны через:

```text
/metrics
```

Также реализованы бизнес-метрики:

```text
orders_created_total
orders_cancelled_total
rabbitmq_events_total
notifications_created_total
```

---

# CI/CD

Проект использует GitHub Actions.

При каждом `push` и `pull request` выполняются:

1. Проверка кода с помощью Ruff.
2. Проверка конфигурации Docker Compose.
3. Сборка Docker-образов.

При `push` в репозиторий Docker-образы автоматически публикуются в GitHub Container Registry (GHCR).

Публикуются следующие образы:

```text
markethub-user-service
markethub-product-service
markethub-order-service
markethub-notification-service
```

Для каждого образа создаются два тега:

```text
latest
<commit SHA>
```

Процесс CI/CD:

```text
Git Push
   |
   v
GitHub Actions
   |
   +--> Ruff
   |
   +--> Docker Compose validation
   |
   +--> Docker build
   |
   v
GitHub Container Registry
```

---

# Конфигурация

Для локальной разработки используются `.env` файлы.

Примеры конфигурации находятся в:

```text
user-service/.env.example
product-service/.env.example
order-service/.env.example
notification-service/.env.example
```

Реальные `.env` файлы не должны попадать в Git.

Секреты и пароли в production-среде должны храниться в защищённом хранилище секретов.

---

# JWT-аутентификация

Для защищённых endpoints используется JWT.

После авторизации пользователь получает access token.

В Swagger необходимо нажать:

```text
Authorize
```

и передать JWT-токен.

Для HTTP-запросов используется заголовок:

```text
Authorization: Bearer <token>
```

Роли пользователей используются для ограничения доступа к административным операциям.

---

# Docker

Все компоненты системы запускаются через Docker Compose.

Основные контейнеры:

```text
markethub-user-service
markethub-product-service
markethub-product-service-2
markethub-order-service
markethub-notification-service

markethub-postgres-users
markethub-postgres-products
markethub-postgres-orders
markethub-postgres-notifications

markethub-redis
markethub-rabbitmq
markethub-nginx
markethub-prometheus
markethub-grafana
```

---

# Остановка проекта

Остановить контейнеры:

```bash
docker compose down
```

Остановить контейнеры и удалить volumes:

```bash
docker compose down -v
```

> Команда `docker compose down -v` удаляет данные PostgreSQL, Redis, RabbitMQ, Prometheus и Grafana.

---

# Проверка состояния

Для просмотра контейнеров:

```bash
docker compose ps
```

Для просмотра логов:

```bash
docker compose logs -f
```

Логи отдельного сервиса:

```bash
docker compose logs -f user-service
docker compose logs -f product-service
docker compose logs -f order-service
docker compose logs -f notification-service
```

---

# Статус проекта

| Компонент | Статус |
|---|---|
| User Service | Done |
| Product Service | Done |
| Order Service | Done |
| Notification Service | Done |
| PostgreSQL | Done |
| Alembic | Done |
| Redis | Done |
| RabbitMQ | Done |
| Nginx | Done |
| Load Balancing | Done |
| Prometheus | Done |
| Grafana | Done |
| Docker Compose | Done |
| CI/CD | Done |
| Automated Tests | Не реализованы |

---

# Архитектурные принципы

В проекте реализованы следующие принципы:

- независимые микросервисы;
- отдельная база данных для каждого сервиса;
- отсутствие общей БД;
- REST API для синхронного взаимодействия;
- RabbitMQ для асинхронного взаимодействия;
- Redis для кеширования;
- JWT-аутентификация;
- разграничение доступа по ролям;
- reverse proxy через Nginx;
- load balancing;
- контейнеризация через Docker;
- мониторинг через Prometheus и Grafana;
- автоматическая сборка Docker-образов;
- автоматическая публикация Docker-образов в GHCR.

---

# Ограничения

В текущей версии проекта автоматические интеграционные и unit-тесты не реализованы.

Для production-версии также рекомендуется:

- использовать отдельные секреты вместо демонстрационных значений;
- добавить более сложную обработку распределённых транзакций;
- использовать Outbox/Saga для гарантированной доставки событий;
- добавить полноценные health checks для всех сервисов;
- ограничить допустимые переходы статусов заказа.

---

# Цель проекта

MarketHub разработан для демонстрации практического применения микросервисной архитектуры и современных backend-технологий.

Проект объединяет:

- разработку REST API;
- работу с PostgreSQL;
- миграции Alembic;
- JWT-аутентификацию;
- микросервисную архитектуру;
- Redis-кеширование;
- RabbitMQ;
- Docker;
- Nginx;
- балансировку нагрузки;
- мониторинг;
- CI/CD.
