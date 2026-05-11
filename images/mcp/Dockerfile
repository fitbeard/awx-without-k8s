###
### aap-mcp-server
###

FROM docker.io/rockylinux/rockylinux:9-minimal AS dumb_init_build
USER root
RUN microdnf install --setopt=install_weak_deps=0 --nodocs -y gcc \
    && microdnf clean all
COPY deps/dumb-init /deps/dumb-init
WORKDIR /deps/dumb-init
RUN gcc -std=gnu99 -O2 -g -o dumb-init dumb-init.c

FROM docker.io/rockylinux/rockylinux:9-minimal AS builder
USER root
RUN microdnf module enable -y nodejs:22 \
    && microdnf install --setopt=install_weak_deps=0 --nodocs -y nodejs npm \
    && microdnf clean all
WORKDIR /app
COPY src/package*.json src/tsconfig.json ./
RUN npm ci
COPY src/src/ ./src/
RUN npm install && npm run build

FROM docker.io/rockylinux/rockylinux:9-minimal
USER root
RUN microdnf module reset -y php nginx \
    && microdnf module enable -y nodejs:22 nginx:1.26 \
    && microdnf install --setopt=install_weak_deps=0 --nodocs -y \
    nodejs \
    npm \
    ca-certificates \
    glibc-langpack-en \
    nginx \
    tzdata \
    && microdnf clean all

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

COPY nginx.conf /etc/nginx/nginx.conf
RUN chown -R 1000:0 /var/lib/nginx /var/log/nginx

WORKDIR /app
COPY src/aap-mcp.sample.yaml /app/aap-mcp.yaml
COPY src/package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY --from=builder /app/dist ./dist
COPY src/data/ ./data/
COPY --from=dumb_init_build /deps/dumb-init/dumb-init /usr/local/bin

USER 1000
EXPOSE 8086

ENV BASE_URL="" \
    NODE_ENV=production \
    MCP_PORT=3000 \
    IGNORE_CERTIFICATE_ERRORS="" \
    SESSION_TIMEOUT="1200" \
    ENABLE_METRICS=""

ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]
CMD ["/entrypoint.sh"]
