# Meal Planner

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Django](https://img.shields.io/badge/django-5.2-0C4B33)
![License: MIT](https://img.shields.io/badge/license-MIT-yellow)
![Self-hosted](https://img.shields.io/badge/self--hosted-Raspberry%20Pi-c51a4a)

A small Django app that turns a recipe into a page that schema.org-aware
recipe managers (Paprika, etc.) can import directly — no manual re-entry, no
missing fields.

Built as a hands-on Django learning project, and self-hosted on a Raspberry Pi
for actual daily use in one kitchen.

## What it does

- **Paste a recipe, get a page.** Drop in a plain-text recipe (the labeled
  `Name: / Ingredients: / Instructions:` format most recipe-writing AI tools
  already produce) and it's parsed into a proper `Recipe` — including
  converting human durations ("6 hours") to the ISO 8601 durations
  schema.org expects.
- **Schema.org out of the box.** Every recipe page renders both JSON-LD and
  microdata (`itemscope`/`itemprop`), so recipe managers that scrape
  schema.org/Recipe markup can import it with no extra work.
- **Images from an upload or a URL.** Attach a photo directly, or point at a
  recipe/blog page and it'll follow that page's `og:image` to fetch the photo
  itself.
- **Favorites.** Star a recipe to pin it to the top of the list.
- **Edit and delete**, obviously.

## Running it locally

```bash
git clone https://github.com/mbulkeley/meal-planner.git
cd meal-planner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # to add recipes via /admin/
python manage.py runserver
```

Visit `http://127.0.0.1:8000/recipes/`.

A `DJANGO_SECRET_KEY` environment variable is picked up if set; otherwise a
placeholder dev key is used, which is fine for local use.

## Deploying

Runs anywhere Python 3.10+ and Django 5.2 do. Production settings come from
environment variables (see `deploy/meal-planner.env.example`); with none set,
it runs in development mode.

The reference deployment is a Raspberry Pi:

```
Cloudflare (HTTPS + Access) → cloudflared tunnel → nginx (static/media) → gunicorn → Django
```

Everything needed is in [`deploy/`](deploy/):

| File | What it is |
|---|---|
| `RUNBOOK.md` | Step-by-step migration and deploy guide |
| `meal-planner.service` | systemd unit for gunicorn (localhost only; runs migrate + collectstatic on start) |
| `nginx-meal-planner.conf` | nginx site: serves `/static/` and `/media/`, proxies the rest |
| `meal-planner.env.example` | Environment file template |
| `cloudflared-ingress.example.yml` | Tunnel ingress entry |

The app has no login on its own pages — put it behind an authenticating
proxy (e.g. Cloudflare Access) or keep it on a trusted LAN.

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev placeholder | Required when `DJANGO_DEBUG=false` |
| `DJANGO_DEBUG` | `true` | Set `false` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | e.g. `https://recipes.example.com` |
| `DJANGO_BEHIND_PROXY` | `false` | Trust `X-Forwarded-Proto` from the proxy |
| `DJANGO_SECURE_COOKIES` | `not DEBUG` | HTTPS-only cookies |
| `DJANGO_TIME_ZONE` | `Europe/Amsterdam` | Display time zone |
| `DJANGO_LOG_LEVEL` | `WARNING` | Django log level (to stderr / journald) |

## License

MIT — see [LICENSE](LICENSE).
