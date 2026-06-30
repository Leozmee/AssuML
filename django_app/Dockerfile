FROM python:3.12-slim

# Racine du dépôt montée dans le conteneur → import big_data.duckdb_analytics fonctionne
WORKDIR /workspace

# Copier tout le dépôt (le docker-compose mount le contexte depuis la racine)
COPY . /workspace/

# Dépendances Django uniquement
RUN pip install --no-cache-dir -r django_app/requirements.txt

# Collecter les fichiers statiques
RUN cd django_app && python manage.py collectstatic --noinput

EXPOSE 8001

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "2", "--chdir", "django_app"]
