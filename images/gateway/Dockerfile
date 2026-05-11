ARG PYTHON=python3.12

# =============================================================================
# UI Builder stage: build Platform UI (Vite SPA) from SRPM source
# =============================================================================
FROM docker.io/rockylinux/rockylinux:9 AS ui-builder

# Use the distro-provided npm to bootstrap Node 20 LTS (required for Vite build)
RUN dnf install -y nodejs && npm install -g n && n 20

# Copy platform UI source (placed in build context by build.sh)
COPY aap-ui/ /tmp/aap-ui/
RUN cd /tmp/aap-ui && npm ci
RUN cd /tmp/aap-ui/platform && NODE_OPTIONS=--max-old-space-size=8192 npx vite build

# =============================================================================
# Python Builder stage: install Python deps into a venv
# =============================================================================
FROM docker.io/rockylinux/rockylinux:9 AS builder
ARG PYTHON=python3.12

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en

RUN dnf install -y epel-release && \
    dnf config-manager --set-enabled crb && \
    dnf install -y \
    git \
    gcc \
    ${PYTHON}-devel \
    ${PYTHON} \
    ${PYTHON}-pip \
    libpq \
    libpq-devel \
    libtool-ltdl-devel \
    openldap-devel \
    xmlsec1-devel && \
    dnf clean all

RUN mkdir -p /opt/aap_gateway && chgrp -R 0 /opt/aap_gateway && chmod -R g=u /opt/aap_gateway

RUN /usr/bin/${PYTHON} -m venv /opt/aap_gateway/venv
RUN echo "/opt/aap_gateway/aap_gateway" > /opt/aap_gateway/venv/lib/${PYTHON}/site-packages/project.pth

# Upper bound <81 keeps pkg_resources
# (removed in 81; gateway transitive deps still rely on it).
RUN /opt/aap_gateway/venv/bin/pip install --upgrade 'setuptools>=78.1.1,<81'

COPY requirements/requirements.txt /tmp/requirements.txt
COPY requirements/requirements_git.txt /tmp/requirements_git.txt
RUN /opt/aap_gateway/venv/bin/pip --no-cache-dir install -r /tmp/requirements.txt
RUN /opt/aap_gateway/venv/bin/pip --no-cache-dir install -r /tmp/requirements_git.txt
RUN /opt/aap_gateway/venv/bin/pip --no-cache-dir install colorama logutils

# CVE bumps : force-upgrade past gateway
# requirements.in resolved versions where transitive constraints left
# vulnerable lower-bound versions in place. Tight upper bounds avoid major
# jumps. Skipped: lxml 5.3->6.1 (major, SAML/XML risk), protobuf 5.29->6.33
# (major, gRPC risk), wheel-vendored-inside-setuptools (false-positive).
#   django   5.2.9  -> 5.2.13   CVE-2026-3902, -33034, -25673, -1287, -1207, -1312, -33033
#   requests 2.32.3 -> 2.33.0   CVE-2024-47081, CVE-2026-25645
#   sqlparse 0.5.3  -> 0.5.4    GHSA-27jp-wm6q-gp25
#   cryptography 46.0.5 -> 46.0.7  CVE-2026-39892
#   pip 23.2.1 -> 26.1+  CVE-2023-5752, -2025-8869, -2026-6357
# social-auth-app-django CVE-2025-61783 (5.6.0 fix) is BLOCKED upstream:
# DAB at our pin (5f6343b) hard-pins `social-auth-app-django==5.4.1` in
# its [authentication]/[all] extras. Adding ">=5.6.0" here was silently
# resolved to 5.4.1 by pip to satisfy DAB's `==` constraint. To clear
# this CVE upstream, DAB needs to loosen the pin (or we'd need to fork).
RUN /opt/aap_gateway/venv/bin/pip install --no-cache-dir --upgrade \
    "django>=5.2.13,<6.0" \
    "requests>=2.33.0,<3.0" \
    "sqlparse>=0.5.4,<0.6" \
    "cryptography>=46.0.7,<47" \
    "pip>=26.1,<27.0"

# Install the gateway package itself
ARG VERSION
ARG SETUPTOOLS_SCM_PRETEND_VERSION
COPY . /tmp/gateway-src
RUN cd /tmp/gateway-src && /opt/aap_gateway/venv/bin/pip --no-cache-dir install .

# =============================================================================
# Runtime stage
# =============================================================================
FROM docker.io/rockylinux/rockylinux:9
ARG PYTHON=python3.12

RUN dnf -y update --security --bugfix && \
    dnf install -y epel-release && \
    dnf module install -y nginx:1.26/common && \
    dnf install -y \
    glibc-langpack-en \
    less \
    libpq \
    ${PYTHON} \
    ${PYTHON}-pip \
    supervisor \
    xmlsec1-openssl && \
    dnf clean all

COPY --from=builder /opt/aap_gateway /opt/aap_gateway
COPY tools/scripts/launch-gateway /usr/bin/launch-gateway
COPY tools/scripts/aap-gateway-manage /usr/bin/aap-gateway-manage
COPY tools/configs/nginx.conf /etc/ansible-automation-platform/gateway/nginx.conf
COPY tools/configs/nginx-gateway.conf /etc/ansible-automation-platform/gateway/nginx-gateway.conf
COPY tools/configs/uwsgi.ini /etc/ansible-automation-platform/gateway/uwsgi.ini
COPY tools/configs/supervisord.conf /etc/supervisord.conf
COPY tools/scripts/envoy-path-rewrite.lua /etc/ansible-automation-platform/gateway/envoy-path-rewrite.lua

RUN for dir in \
      /etc/nginx \
      /opt/aap_gateway \
      /opt/aap_gateway/src \
      /opt/aap_gateway/static \
      /var/log/supervisor \
      /var/run/supervisor \
      /var/run/uwsgi \
      /var/run/nginx \
      /var/log/nginx \
      /var/log/ansible-automation-platform/gateway \
      /var/cache/ansible-automation-platform/gateway \
      /var/run/django_metrics ; \
    do mkdir -m 0775 -p "$dir" ; chmod g+rwx "$dir" ; chgrp root "$dir" ; done && \
    for file in \
      /etc/nginx/gateway.crt \
      /etc/nginx/gateway.key ; \
    do touch "$file" ; chmod g+rw "$file" ; chgrp root "$file" ; done && \
    ln -s /usr/bin/aap-gateway-manage /usr/bin/gateway-manage && \
    chmod +x /usr/bin/launch-gateway /usr/bin/aap-gateway-manage

RUN chown -R 1000 /opt/aap_gateway/static
RUN chown -R 1000 /var/cache/ansible-automation-platform/gateway

# Required for xds protobuf definitions compatibility with protobuf 3.21+
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

COPY aap_gateway_api /opt/aap_gateway/src/aap_gateway_api/

# VERSION file: read by aap_gateway_api.version at runtime
COPY VERSION /opt/aap_gateway/src/VERSION

ENV PATH=/opt/aap_gateway/venv/bin:$PATH
ENV PYTHONPATH=/opt/aap_gateway/src
ENV DJANGO_SETTINGS_MODULE=aap_gateway_api.settings

# Pull in the platform-ui built from SRPM source (Apache-2.0)
COPY --from=ui-builder /tmp/aap-ui/platform/dist /opt/aap_gateway/platform_ui

USER 1000
EXPOSE 8000
EXPOSE 50051

WORKDIR /opt
CMD ["/usr/bin/launch-gateway"]
