FROM python:3.11-slim

# Racine du dépôt montée dans le conteneur → import big_data.duckdb_analytics fonctionne
WORKDIR /workspace

# Copier tout le dépôt (le docker-compose mount le contexte depuis la racine)
COPY . /workspace/

# Dépendances Django uniquement
RUN pip install --no-cache-dir -r django_app/requirements.txt

# SECRET_KEY factice pour permettre à collectstatic de charger settings.py au
# moment du build (les variables `environment:` de docker-compose ne sont
# disponibles qu'à l'exécution du conteneur, pas pendant le build de l'image).
# La vraie clé est injectée normalement à l'exécution, via docker-compose.yml.
ARG DJANGO_SECRET_KEY=build-time-placeholder-non-utilise-en-production
ENV DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY

# Collecter les fichiers statiques
RUN cd django_app && python manage.py collectstatic --noinput

EXPOSE 8001

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "2", "--chdir", "django_app"]
