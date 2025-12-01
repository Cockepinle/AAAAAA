# 🔐 Конфигурация и безопасность

## Переменные окружения (.env)

Все секреты и конфигурация хранятся в файле `.env` на сервере. Этот файл НЕ загружается в git (см. `.gitignore`).

### Локальная разработка

1. **Скопируйте `.env.example` в `.env`:**
   ```bash
   cp .env.example .env
   ```

2. **Отредактируйте `.env` со своими значениями:**
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   DB_PASSWORD=your-db-password
   ```

3. **Сервер автоматически загружает `.env` при запуске** (via `python-dotenv`)

### Продакшн-сервер

На продакшене создайте файл `.env` с реальными значениями:

```bash
# На сервере:
ssh user@server
cd /path/to/shopur
nano .env
```

Заполните:
```env
DEBUG=False
SECRET_KEY=<сгенерированный-ключ>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=shopurpro_prod
DB_USER=postgres
DB_PASSWORD=<strong-password>
DB_HOST=<db-server-ip>
DB_PORT=5432

DATA_ENCRYPTION_KEY=<new-encryption-key>

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>

TIME_ZONE=Europe/Moscow
LANGUAGE_CODE=ru
```

## Доступ к БД

### Локально (разработка)

```python
# settings.py автоматически читает:
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

Текущие значения из `.env`:
- **Хост:** localhost
- **БД:** shopurpro
- **Пользователь:** postgres
- **Пароль:** 1 (для разработки!)

### На продакшене

Используйте защищённые пароли и отдельный хост БД:

```
DB_HOST=db.production.internal
DB_USER=shopurpro_app
DB_PASSWORD=<very-strong-password>
```

## Генерация новых секретов

### 1. Новый SECRET_KEY для Django

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Скопируйте результат в `.env`:
```env
SECRET_KEY=your-new-key-here
```

### 2. Новый ключ шифрования

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Или используйте:
```bash
openssl rand -base64 32
```

Скопируйте в `.env`:
```env
DATA_ENCRYPTION_KEY=your-new-encryption-key
```

## Email конфигурация

Для отправки уведомлений (пароли, заказы и т.д.):

### Gmail (рекомендуется)

1. Включите двухфакторную аутентификацию в Google аккаунте
2. Создайте "App Password" на https://myaccount.google.com/apppasswords
3. Скопируйте пароль и добавьте в `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
```

### Свой SMTP сервер

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=admin@yourdomain.com
EMAIL_HOST_PASSWORD=your-password
```

## Порядок загрузки конфигурации

1. **`.env` файл** (локально или на сервере)
2. **Переменные окружения системы** (если переопределены)
3. **Значения по умолчанию в settings.py** (fallback)

## Чек-лист перед запуском на продакшене

- [ ] Создан новый SECRET_KEY
- [ ] Создан новый DATA_ENCRYPTION_KEY
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS установлены правильно
- [ ] DB_PASSWORD — сильный пароль
- [ ] EMAIL настроен и протестирован
- [ ] `.env` файл НЕ в git
- [ ] `.env` скопирован на продакшен-сервер
- [ ] Выполнены миграции: `python manage.py migrate`
- [ ] Собраны статические файлы: `python manage.py collectstatic --noinput`

## Безопасность

⚠️ **ВАЖНО:**
- Никогда не коммитьте `.env` файл в git
- Используйте разные секреты для разработки и продакшена
- Храните `.env` на сервере в защищённом месте (600 permissions)
- Регулярно ротируйте секреты
- Используйте VPN/firewall для доступа к БД

```bash
# Установите правильные permissions на .env
chmod 600 .env
```

## Примеры использования в коде

```python
# В settings.py переменные уже загружены
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'

# В коде можно использовать:
from django.conf import settings
db_name = settings.DATABASES['default']['NAME']
email_host = settings.EMAIL_HOST
```
