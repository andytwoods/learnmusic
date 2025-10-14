FROM python:3.13-slim-bookworm

SHELL ["/bin/bash", "-c"]

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=0

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      nano gettext \
 && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install gunicorn

WORKDIR /code

# Create unprivileged user and writable dirs
RUN useradd -ms /bin/bash code \
 && mkdir -p /code/staticfiles \
 && chown -R code:code /code

# deps first (cache-friendly)
COPY ./code/requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt

# app code + env
COPY ./env/ /env/
COPY ./code/ /code/
RUN chown -R code:code /code /env

# Optional build hook
USER code
RUN source /env/envs_export.sh \
 && if [[ -n "$BUILD_COMMAND" ]]; then eval "$BUILD_COMMAND"; fi

# collectstatic as unprivileged user
RUN source /env/envs_export.sh \
 && if [[ -f "manage.py" ]]; then \
        if [[ "$DISABLE_COLLECTSTATIC" == "1" ]]; then \
            echo "collectstatic disabled"; \
        else \
            echo "Running collectstatic (as code)"; \
            python manage.py collectstatic --noinput; \
        fi; \
    else \
        echo "No manage.py found. Skipping collectstatic."; \
    fi

# Drop privileges for the final image (already code, but explicit is fine)
USER code
