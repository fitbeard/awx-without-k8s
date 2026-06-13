# `haproxy`

Runs HAProxy in Docker Compose with a CA-signed HTTPS frontend and HTTPS
backend pools. The frontend certificate is generated from the shared `tls`
role CA unless `haproxy_frontend_tls_crt` and `haproxy_frontend_tls_key` are
provided.

## Example

```yaml
haproxy_routes:
  - fqdn: awx.demo.io
    backend_pool: awx
  - fqdn: eda.demo.io
    backend_pool: eda
  - fqdn: ap.demo.io
    backend_pool: gateway

haproxy_backend_pools:
  awx:
    port: 8443
    servers:
      - name: awx-1
        host: awx-1.demo.io
      - name: awx-2
        host: awx-2.demo.io
  eda:
    port: 8445
    servers:
      - name: eda-1
        host: eda-1.demo.io
      - name: eda-2
        host: eda-2.demo.io
  gateway:
    port: 9080
    servers:
      - name: gateway-1
        host: gateway-1.demo.io
      - name: gateway-2
        host: gateway-2.demo.io
```

If the backend address differs from the backend certificate name, set `sni` on
that server.

For backends that need exact HAProxy syntax, such as Gateway/Envoy health
checks, provide a complete backend stanza with `raw_backend`. The backend name
must match the generated pool name, `be_<pool name>`.

```yaml
haproxy_backend_pools:
  gateway:
    raw_backend: |
      backend be_gateway
          balance roundrobin

          option httpchk
          http-check send meth GET uri / ver HTTP/1.1 hdr Host %[srv_name].demo.io:9080
          http-check expect status 200-399

          server ap-gw-1 ap-gw-1.demo.io:9080 ssl verify none sni str(ap-gw-1.demo.io) check-sni ap-gw-1.demo.io check
          server ap-gw-2 ap-gw-2.demo.io:9080 ssl verify none sni str(ap-gw-2.demo.io) check-sni ap-gw-2.demo.io check
```

Use `backend_extra_config` when you only need to add custom lines while keeping
generated `server` entries. Set `httpchk: false` if those lines replace the
default generated health check.

By default the role:

- listens on ports `80` and `443` using Docker host networking;
- redirects HTTP to HTTPS;
- generates `/opt/haproxy/certs/frontend.pem` from a certificate signed by the
  AP CA, with SANs from `haproxy_routes`;
- sends backend traffic to HTTPS port `443`;
- uses `ssl verify none` for backend servers because they are self-signed;
- requires at least one server in every backend pool.

Your inventory needs a `[haproxy]` group containing the endpoint host.

Provide both `haproxy_frontend_tls_crt` and `haproxy_frontend_tls_key` to use
your own frontend certificate. Those values are rendered into `frontend.pem`
with `frontend.pem.j2`.
