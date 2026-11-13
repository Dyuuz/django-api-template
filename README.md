# Django API Template

A production-minded starter for building a JSON API with **Django 6** and **Django REST Framework**. It ships with JWT auth, a 2FA-protected admin, brute-force lockout, structured logging, Celery, Docker, and CI already wired up, so you can start on your own endpoints instead of re-doing the plumbing.

> Click **Use this template** on GitHub (or clone it) to start a new project.

## What's included

**API**
- DRF with versioned routes under `/api/v1/` (namespace versioning) and `IsAuthenticated` by default
- JWT auth via SimpleJWT: 15-minute access tokens, 7-day refresh tokens, rotation and blacklisting
- Consistent error envelope for every failure: `{"status": "error", "code": "...", "errors": ...}` (`Main/core/exceptions.py`)
- Throw `AppError` subclasses (`Main/core/errors.py`) from anywhere to return a clean API error
- Scoped throttle classes ready to use: `LoginThrottle`, `RegistrationThrottle`, `PasswordResetThrottle`, `PaymentThrottle` (`Main/throttle.py`)
- Pagination (20 per page) and `django-filter` enabled globally
- OpenAPI schema with Swagger UI and ReDoc through `drf-spectacular`
- `X-Client-Type` header check on `/api/` routes (only `web` is accepted, easy to extend)
- Health check endpoint, plus `sitemap.xml` and `robots.txt` routes

**Security**
- Admin protected by two-factor auth (`django-two-factor-auth`, TOTP and backup codes)
- Login lockout after 5 failures per username and IP (`django-axes`), proxy-aware IP detection
- Content Security Policy with nonces (`django-csp`), HSTS, secure cookies, SSL redirect, `X-Frame-Options: DENY`
- CORS and CSRF origins configured from environment variables
- 11-character minimum password length
- All secrets come from environment variables, and the app refuses to start without `SECRET_KEY`

**Infrastructure**
- PostgreSQL through `dj-database-url`, with SSL required when `DEBUG=False`
- Redis for cache, sessions and as the Celery broker
- Celery worker and beat (`ProjectTemplate/celery.py`), with `django-celery-beat` installed
- Dockerfile and `start.sh` that runs the container as `web`, `worker` or `beat` through a `ROLE` variable
- WhiteNoise for static files, Gunicorn for serving
- Optional Cloudinary credentials, Resend email helper (`Main/smtp/email_service.py`) and a Resend webhook secret setting

**Observability**
- JSON logs to stdout and stderr, with a `request_id` and `user_id` on every record
- In DEBUG mode, logs are also written to rotating files in `logs/`
- IP geolocation with a local MaxMind GeoLite2 database, cached in the `IPLocation` model (`Main/geo_location/geo.py`)

**Developer experience**
- Ruff for lint and format (`pyproject.toml`)
- pytest and pytest-django configured
- GitHub Actions CI (`.github/workflows/ci.yml`): Ruff, `manage.py check`, `check --deploy`, `pip-audit`, and a missing-migrations check
- Dependabot for pip and GitHub Actions
- Jazzmin admin theme
- `compress_images.py`, a helper that resizes and compresses images and writes `.webp` copies

## Project layout

```
ProjectTemplate/     Django project: settings, urls, celery, wsgi/asgi
Main/                Main app
  core/              AppError + custom DRF exception handler
  log_configs/       request-aware logging filters and context
  geo_location/      GeoIP lookup + caching
  smtp/              Resend email helper and templates
  middleware.py      request-id logging, X-Client-Type enforcement
  signals.py         login alerts / geo resolution (see Known gaps)
  throttle.py        scoped throttles
  views.py           health check
tests/               pytest tests (empty, add yours here)
templates/ static/   two-factor auth template/CSS overrides
Dockerfile, start.sh container build and entrypoint
```

## Quick start (local)

You need Python 3.13, PostgreSQL and Redis.

```bash
git clone https://github.com/Dyuuz/django-api-template.git my-api
cd my-api

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set SECRET_KEY and check POSTGRES_URL / REDIS_URL
```

Don't have Postgres or Redis? Start both with Docker:

```bash
docker run -d --name pg -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=projecttemplate postgres:17
docker run -d --name redis -p 6379:6379 redis:7
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Check it works:

```bash
curl http://127.0.0.1:8000/api/v1/health-check/
# {"status":"healthy"}
```

## URLs

| URL | What |
| --- | --- |
| `/api/v1/health-check/` | Public health check |
| `/api/docs/` | Swagger UI (admin session required) |
| `/api/redoc/` | ReDoc (admin session required) |
| `/api/schema/` | OpenAPI schema (admin session required) |
| `/account/login/` | Two-factor login (also the admin login) |
| `/account/two_factor/setup/` | Enrol an authenticator app |
| `/admin/` | Admin, requires a verified 2FA device |
| `/api/v1/sitemap.xml`, `/api/v1/robots.txt` | SEO helpers |

**Admin first login:** sign in at `/account/login/`, then enrol an authenticator app at `/account/two_factor/setup/`. The admin is only available to users with a verified device.

## Configuration

Everything is configured through environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | yes | Django secret key |
| `DEBUG` | no (default `False`) | `True` for local development |
| `POSTGRES_URL` | yes | Database URL |
| `REDIS_URL` | yes | Cache, sessions and Celery broker |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` | production | Comma-separated lists. In DEBUG the `LOCAL_*` variants are used instead |
| `DOMAIN` | production | Public base URL |
| `RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET`, `RESEND_FROM_EMAIL` | for email | Resend credentials and sender address |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | optional | Cloudinary credentials |
| `OTP_THROTTLE_FACTOR` | no (default `0`) | Wrong-code throttling for 2FA |
| `ROLE`, `PORT` | container only | Process type and port used by `start.sh` |

Never commit `.env`. It is already in `.gitignore`.

## Using it for your own project

1. **Rename the project.** Replace `ProjectTemplate` with your project name: rename the `ProjectTemplate/` folder, then update `manage.py`, `ProjectTemplate/{wsgi,asgi,celery}.py`, `ROOT_URLCONF` and `WSGI_APPLICATION` in `settings.py`, `start.sh`, `pytest.ini`, and the `DJANGO_SETTINGS_MODULE` line in `.github/workflows/ci.yml`. Also change the Jazzmin and drf-spectacular titles in `settings.py`.
2. **Add your apps.** Create an app with `python manage.py startapp <name>`, add it to `INSTALLED_APPS`, and include its URLs in `Main/urls.py` (or a new `urls.py`) under `api/v1/`.
3. **Add an endpoint.** Subclass `APIView` or a DRF viewset, decorate it with `extend_schema` so it shows up in the docs, and set `throttle_scope = "login"` (and so on) where you want rate limiting, since the default is `ScopedRateThrottle`.
4. **Return errors consistently.** Subclass `AppError`, set `code`, `message` and `status`, and raise it. The exception handler turns it into the standard error envelope.
5. **Background jobs.** Put Celery tasks in `<app>/tasks.py` (they are auto-discovered) and schedule periodic ones in `beat_schedule` in `ProjectTemplate/celery.py`.
6. **Clean up placeholders.** Set the real sender in `RESEND_FROM_EMAIL`, the real domain in `Main/templates/robots.txt`, and your own URL names in `Main/sitemaps.py`.

## Running tests and checks

```bash
pytest
ruff check . && ruff format --check .
python manage.py check --deploy
```

The same checks run in CI on every push to `main` and on pull requests.

## Deploying with Docker

```bash
docker build -t my-api .

# web
docker run --env-file .env -e ROLE=web -e PORT=8000 -p 8000:8000 my-api
# worker
docker run --env-file .env -e ROLE=worker my-api
# beat
docker run --env-file .env -e ROLE=beat my-api
```

The `web` role runs migrations and `collectstatic`, then starts Gunicorn. On platforms like Railway or Render, run one service per role from the same image and set `ROLE` on each. With `DEBUG=False` the app expects HTTPS, so run it behind a proxy that sets `X-Forwarded-Proto`. The login-lockout IP detection assumes exactly one proxy in front (`AXES_IPWARE_PROXY_COUNT = 1`), so change that if your setup differs.

### GeoIP database

IP geolocation needs a MaxMind GeoLite2 City database at `geoip/GeoLite2-City.mmdb` (git-ignored). Get a free licence key from MaxMind and download it yourself or with `geoipupdate`, which is installed in the Docker image but not called by `start.sh`. Without the file, lookups fail quietly and no location is stored.

## Known gaps (good first things to finish)

This is a template, so a few pieces are scaffolding that you will want to complete:

- **Login-alert emails are not wired up.** `Main/signals.py` imports `send_login_alert` from `Main/tasks.py`, which is empty, and `MainConfig.ready()` doesn't import the signals. Write the task (the HTML helpers live in `Main/smtp/`) and register the signals in `apps.py` to enable login alerts and geolocation on login.
- **`sitemap.xml` is a placeholder.** `Main/sitemaps.py` lists URL names (`homepage`, `about`, ...) that don't exist in this project, so the sitemap fails until you replace them with your own.
- **No tests yet.** `tests/` contains empty files. Start with a test for the health-check endpoint.
- **Cloudinary is configured but not active.** `STORAGES["default"]` uses the local filesystem. Point it at `cloudinary_storage.storage.MediaCloudinaryStorage` to use Cloudinary for uploads.
- **`pgjson.py`** (a simple Postgres JSON export/restore script) is listed in `.gitignore` on purpose and isn't part of the published template.

## License

[MIT](LICENSE)
