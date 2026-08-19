FROM python:3.11-slim

# Racine du dépôt montée dans le conteneur → import big_data.duckdb_analytics fonctionne
WORKDIR /workspace

# La liste des dépendances est copiée seule, avant le code : la couche pip qui suit
# reste ainsi en cache tant que ce fichier ne change pas. Copier tout le dépôt avant
# d'installer invaliderait cette couche à la moindre modification, et réinstallerait
# les treize paquets à chaque construction (même motif que le Dockerfile racine).
COPY django_app/requirements.txt django_app/
RUN pip install --no-cache-dir -r django_app/requirements.txt

# Le code ensuite (le docker-compose monte le contexte depuis la racine)
COPY . /workspace/

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
