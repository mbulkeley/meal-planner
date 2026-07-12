# Meal Planner

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Django](https://img.shields.io/badge/django-4.2-0C4B33)
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

Runs anywhere Python 3.9+ and Django 4.2 do. The reference deployment is a
Raspberry Pi: `gunicorn` behind a `systemd` service, `DJANGO_SECRET_KEY` set
via an `EnvironmentFile`, discovered on the LAN via mDNS/Bonjour (no router
configuration needed) — see `config/settings.py` for the relevant
`ALLOWED_HOSTS` entries to adjust for your own network.

## License

MIT — see [LICENSE](LICENSE).
