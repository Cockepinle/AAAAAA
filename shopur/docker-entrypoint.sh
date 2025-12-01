#!/usr/bin/env sh
set -e

echo "➜ Applying migrations..."
python manage.py migrate --noinput

LOAD_FIXTURE=${LOAD_FIXTURE:-false}
FIXTURE_PATH="${FIXTURE_PATH:-/app/backups/backup_20251122_184946.json}"

if [ "$LOAD_FIXTURE" = "true" ] && [ -f "$FIXTURE_PATH" ]; then
  echo "➜ Checking for existing products before loading fixture..."
  export DJANGO_SETTINGS_MODULE=shopur.settings
  python - <<'PYCODE'
import os
from pathlib import Path
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopur.settings")
django.setup()

from django.core import management
from catalog.models import Product

fixture = Path(os.environ.get("FIXTURE_PATH", ""))
if Product.objects.exists():
    print("✔ Products already exist, skipping fixture load.")
else:
    if fixture.is_file():
        print(f"➜ Loading fixture {fixture} ...")
        management.call_command("loaddata", str(fixture))
        print("✔ Fixture loaded.")
    else:
        print(f"⚠ Fixture file not found: {fixture}, skipping load.")
PYCODE
else
  echo "➜ Skipping fixture load (LOAD_FIXTURE=${LOAD_FIXTURE}, file: ${FIXTURE_PATH})."
fi

echo "➜ Starting Django dev server..."
exec python manage.py runserver 0.0.0.0:8000
