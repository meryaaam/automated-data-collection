FROM python:3.12 AS builder
SHELL ["/bin/bash", "-c"]

ENV APP_ROOT="/var/www/app" \
    PATH="/var/www/app/.venv/bin:$PATH" \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

RUN <<-EOF
set -euo pipefail

install -o www-data -g www-data -d "${APP_ROOT}" "/var/www/.local"

# apt-get clean
EOF

WORKDIR /var/www/app
USER www-data

COPY requirements.txt .

RUN <<-EOR
ls -hal
pip install -r requirements.txt
EOR

COPY --chown=www-data:www-data . .

FROM builder AS runtime

ARG BUILDTIME=""
ARG VERSION=""
ARG REVISION=""
ARG SENTRY_RELEASE=""

ENV BUILDTIME=$BUILDTIME \
    VERSION=$VERSION \
    REVISION=$REVISION \
    SENTRY_RELEASE=$SENTRY_RELEASE

RUN <<EOF
set -euo pipefail
printf '{"VERSION":"%s","REVISION":"%s","BUILDTIME":"%s"}' "$VERSION" "$REVISION" "$BUILDTIME" > BUILDINFO
cat BUILDINFO
EOF
