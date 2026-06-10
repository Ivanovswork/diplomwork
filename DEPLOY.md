# Инструкция по развёртыванию на сервере reg.ru (Ubuntu 26.04 LTS)

## 📋 Характеристики сервера
- IP: 80.78.254.95
- ОС: Ubuntu 26.04 LTS
- CPU: 1 ядро
- RAM: 1 ГБ
- Disk: 10 ГБ

---

## 🔧 Шаг 1: Подключение к серверу

```powershell
# Windows PowerShell
ssh root@80.78.254.95
```

---

## 🔧 Шаг 2: Обновление системы

```bash
apt update && apt upgrade -y
```

---

## 🔧 Шаг 3: Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install -y docker-compose-plugin

# Проверка установки
docker --version
docker compose version

# Добавление пользователя в группу docker
usermod -aG docker $USER
```

**После этого выйди и зайди снова:**
```bash
exit
# Затем снова подключись
ssh root@80.78.254.95
```

---

## 🔧 Шаг 4: Загрузка проекта на сервер

### Вариант A: Через Git (рекомендуется)

```bash
# Установка Git
apt install -y git

# Клонирование репозитория
cd /root
git clone <твой-репозиторий> dymplom
cd dymplom
```

### Вариант B: Через SCP (если нет Git)

```powershell
# С локального компьютера (Windows PowerShell)
scp -r C:\Users\desti\PycharmProjects\dymplom root@80.78.254.95:/root/dymplom
```

---

## 🔧 Шаг 5: Настройка переменных окружения

```bash
cd /root/dymplom

# Копирование шаблона .env
cp .env.docker .env

# Редактирование .env (обязательно смени пароли!)
nano .env
```

**Обязательно измени:**
- `SECRET_KEY` — сгенерируй новый: `python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `DB_PASSWORD` — придумай сложный пароль
- `EMAIL_HOST_PASSWORD` — пароль приложения Mail.ru

**Сохранение в nano:** `Ctrl+O` → `Enter` → `Ctrl+X`

---

## 🔧 Шаг 6: Сборка и запуск контейнеров

```bash
# Сборка образов
docker compose build

# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f
```

---

## 🔧 Шаг 7: Проверка работы

Открой в браузере:
- **Фронтенд:** http://80.78.254.95
- **API:** http://80.78.254.95/api/users/login/

---

## 🔧 Шаг 8: Создание суперпользователя Django

```bash
docker compose exec backend python manage.py createsuperuser
```

Введи email, имя и пароль.

---

## 🔧 Шаг 9: Управление сервисами

```bash
# Перезапуск всех сервисов
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart backend

# Остановка всех сервисов
docker compose down

# Остановка с удалением данных (осторожно!)
docker compose down -v

# Просмотр логов
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Вход в контейнер
docker compose exec backend bash
docker compose exec db psql -U postgres -d diplom
```

---

## 🔧 Шаг 10: Обновление проекта

```bash
cd /root/dymplom

# Если через Git
git pull origin main

# Пересборка и перезапуск
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## ⚠️ Важные замечания

### 1. Экономия памяти (1 ГБ RAM — это мало!)

Если сервисы падают по памяти:

```bash
# Ограничить память для PostgreSQL
# В docker-compose.yml добавь в сервис db:
deploy:
  resources:
    limits:
      memory: 256M

# Ограничить память для Django
# В сервис backend:
deploy:
  resources:
    limits:
      memory: 384M

# Ограничить память для Node.js
# В сервис frontend:
deploy:
  resources:
    limits:
      memory: 256M
```

### 2. Swap файл (если не хватает памяти)

```bash
# Создание swap файла 2 ГБ
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Проверка
free -h

# Добавление в fstab для постоянного swap
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 3. Мониторинг ресурсов

```bash
# Использование памяти
docker stats

# Свободное место
df -h

# Процессы
htop
```

### 4. Резервное копирование базы данных

```bash
# Дамп базы
docker compose exec db pg_dump -U postgres diplom > backup_$(date +%Y%m%d).sql

# Восстановление из дампа
docker compose exec -T db psql -U postgres diplom < backup_20260110.sql
```

### 5. Логи

```bash
# Логи всех сервисов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend

# Последние 100 строк
docker compose logs --tail=100 backend
```

---

## 🚨 Возможные проблемы и решения

### 1. Контейнер не запускается

```bash
# Проверить логи
docker compose logs backend

# Проверить переменные окружения
docker compose exec backend env
```

### 2. Ошибка подключения к базе

Убедись, что `DB_HOST=db` в .env (имя сервиса, не localhost!)

### 3. Порт 80 занят

```bash
# Проверить занятые порты
netstat -tulpn | grep :80

# Остановить конфликтующий сервис
systemctl stop apache2  # если есть
```

### 4. Недостаточно памяти

```bash
# Добавить swap (см. выше)
# Или уменьшить workers в gunicorn до 1
```

---

## 📞 Контакты для поддержки

При проблемах смотри логи и проверяй:
1. `docker compose ps` — все ли сервисы up
2. `docker compose logs -f` — ошибки в логах
3. `df -h` — есть ли место на диске
4. `free -h` — есть ли свободная память
