# Runbook: meal-planner → recipes.mauriecloud.com

Moves meal-planner from LAN-only (mDNS, gunicorn serving everything with
`DEBUG = True`) to a production setup behind Cloudflare:

```
iPhone / Mac ─HTTPS─▶ Cloudflare (Access login) ─▶ cloudflared ─▶ nginx 127.0.0.1:8090 ─▶ gunicorn 127.0.0.1:8001
                                                                     ├─ /static/ → staticfiles/
                                                                     └─ /media/  → media/
```

> ⚠️ **The app has no login on its own pages** — anyone who reaches it can
> add, edit or delete recipes. Cloudflare Access on the *whole* hostname is
> what keeps it private. Set up Access (step 4) **before** the DNS route
> (step 7), so there's never a moment the site is open.

All commands run on **OXFORD** unless noted. Paths assume the checkout is at
`~/Projects/meal-planner` — adjust everywhere if step 0 says otherwise.

---

## 0. Discover the current setup

```bash
# Current service: name, ExecStart (bind/port), EnvironmentFile, WorkingDirectory
systemctl list-units --type=service | grep -i -E 'meal|gunicorn|recipe'
systemctl cat <unit-name>

# Ports we're about to use must be free (nothing printed = free)
sudo ss -tlnp | grep -E ':(8001|8090)\b'

# Tunnel: locally managed if config.yml has an `ingress:` section
ls /etc/cloudflared/ && sudo cat /etc/cloudflared/config.yml

# nginx installed already?
nginx -v
```

If 8001 or 8090 is taken, pick other ports and change them in
`deploy/meal-planner.service`, `deploy/nginx-meal-planner.conf` and the
tunnel ingress.

Write the answers into `OXFORD.md` in the Homelab project while you're here.

## 1. Back up

```bash
cd ~/Projects/meal-planner
mkdir -p ~/Backup/meal-planner
sqlite3 db.sqlite3 ".backup '$HOME/Backup/meal-planner/db-$(date +%F).sqlite3'"
tar czf ~/Backup/meal-planner/media-$(date +%F).tgz media/
sudo cp /etc/systemd/system/<unit-name>.service ~/Backup/meal-planner/   # old unit, for rollback
```

## 2. Get the code

On the dev machine (WOLFMAN/ICEMAN): apply the patch, push the branch, open a
PR, merge. Then on OXFORD:

```bash
cd ~/Projects/meal-planner
git pull
venv/bin/pip install -r requirements.txt     # adds gunicorn (pure Python, armhf-safe)
```

## 3. Environment file

```bash
cd ~/Projects/meal-planner
# If the old unit already had an EnvironmentFile with a secret key, reuse that key.
cp deploy/meal-planner.env.example .env
chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
nano .env      # paste the key into DJANGO_SECRET_KEY, check the hostnames
```

Sanity check — should print `System check identified no issues` (or only
warnings about HSTS/SSL redirect, which Cloudflare handles):

```bash
set -a; . ./.env; set +a
venv/bin/python manage.py check --deploy
```

## 4. Cloudflare Access (dashboard) — do this before step 7

Zero Trust dashboard → **Access → Applications → Add an application → Self-hosted**:

| Setting | Value |
|---|---|
| Application name | Recipes |
| Domain | `recipes.mauriecloud.com` (path empty = whole site) |
| Session duration | 1 month |
| Identity provider | One-time PIN |
| Policy | Allow → Include → Emails → Michael + Laurie |

## 5. New gunicorn service

```bash
sudo systemctl disable --now <old-unit-name>          # frees the old port
sudo cp deploy/meal-planner.service /etc/systemd/system/meal-planner.service
sudo systemctl daemon-reload
sudo systemctl enable --now meal-planner
systemctl status meal-planner --no-pager
journalctl -u meal-planner -n 30 --no-pager

# Expect HTTP/1.1 200
curl -sI -H 'Host: recipes.mauriecloud.com' -H 'X-Forwarded-Proto: https' \
  http://127.0.0.1:8001/recipes/ | head -1
```

(If the old unit was already named `meal-planner`, skip the disable — the
`cp` replaces it; just `daemon-reload` and `restart`.)

## 6. nginx

```bash
sudo apt install -y nginx acl

# Debian 12+/Trixie home dirs are 0700, so nginx (www-data) can't reach media/.
# Grant traverse-only (no listing) on the two parent dirs:
sudo setfacl -m u:www-data:x /home/pi /home/pi/Projects
namei -l /home/pi/Projects/meal-planner/media

# Older uploads may predate FILE_UPLOAD_PERMISSIONS — make sure they're readable
find media staticfiles -type d -exec chmod 755 {} + ; find media staticfiles -type f -exec chmod 644 {} +
sudo -u www-data test -r staticfiles/recipes/style.css && echo "nginx can read static"

# Distro default site listens on :80 — remove it unless something relies on it
ls -l /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

sudo cp deploy/nginx-meal-planner.conf /etc/nginx/sites-available/meal-planner
sudo ln -s /etc/nginx/sites-available/meal-planner /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl enable --now nginx && sudo systemctl reload nginx

# Expect 200 for each
for p in /recipes/ /static/recipes/style.css; do
  curl -s -o /dev/null -w "%{http_code} $p\n" -H 'Host: recipes.mauriecloud.com' http://127.0.0.1:8090$p
done
```

> Port 80 on OXFORD: check `sudo ss -tlnp | grep ':80\b'` before removing the
> default site — if Nextcloud's container already publishes :80, nginx's
> default site would have failed to start anyway.

## 7. Tunnel route

**Locally managed** (config.yml has `ingress:`): add the entry from
`deploy/cloudflared-ingress.example.yml` above the catch-all, then

```bash
sudo cp /etc/cloudflared/config.yml ~/Backup/meal-planner/cloudflared-config.yml.bak
sudo nano /etc/cloudflared/config.yml
sudo cloudflared tunnel ingress validate --config /etc/cloudflared/config.yml
sudo cloudflared tunnel route dns <tunnel-name> recipes.mauriecloud.com
sudo systemctl restart cloudflared
```

**Remotely managed**: dashboard → Networks → Tunnels → your tunnel → Public
Hostname → Add → `recipes` / `mauriecloud.com` → HTTP → `localhost:8090`.

## 8. Test

- [ ] Private window → `https://recipes.mauriecloud.com` → Cloudflare login page (not the app!)
- [ ] Log in with email PIN → recipe list loads, photos and favicon show
- [ ] Add a recipe by paste, with an image URL → saves, photo appears
- [ ] Log a cook, star a favorite → both persist (CSRF works)
- [ ] `/admin/` login works
- [ ] Laurie's iPhone: log in once, add to home screen
- [ ] **Paprika import**: open a recipe page in Paprika's in-app browser, log
      in through Access, import. If Paprika fetches server-side instead and
      gets the login page, options: a Cloudflare Access *service token* isn't
      usable from Paprika, so either a bypass policy on `/recipes/<id>/`
      (read-only pages) or keep importing from the LAN — decide then.
- [ ] `journalctl -u meal-planner` clean; `sudo tail /var/log/nginx/meal-planner.error.log` clean

## 9. Deploying future changes

```bash
cd ~/Projects/meal-planner && git pull && venv/bin/pip install -r requirements.txt && sudo systemctl restart meal-planner
```

Migrations and collectstatic run automatically on restart (`ExecStartPre`).

## Rollback

```bash
sudo systemctl disable --now meal-planner
sudo cp ~/Backup/meal-planner/<old-unit>.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now <old-unit-name>
# In .env, set DJANGO_DEBUG=true (old behaviour: Django serves static/media)
# and add the mDNS name to DJANGO_ALLOWED_HOSTS; set DJANGO_SECURE_COOKIES=false.
```

Remove the tunnel hostname (config.yml entry or dashboard) to take the site
off the internet; Access app can stay.

## Notes

- `_fetch_image` will download any URL it's given. Fine while the whole
  site is behind Access; restrict it (block private/loopback addresses)
  before any part of the site goes public.
- Backups: add `db.sqlite3` (via `sqlite3 .backup`) and `media/` to the Voodoo backup set.
- Ceramics will reuse this exact layout: its own gunicorn on 127.0.0.1:8002,
  a second `server` block on 127.0.0.1:8090 with `server_name
  ceramics.mauriecloud.com`, and one more tunnel hostname.
