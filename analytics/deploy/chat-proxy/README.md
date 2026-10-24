# chat-proxy

nginx in front of LibreChat (service `chat-proxy` in `/mnt/ssd/apps/librechat/docker-compose.yml`). It publishes
port 3080 (the cloudflared ingress for chat.vogelring.com) and proxies to `librechat:3080`, replacing LibreChat's
`X-Frame-Options: SAMEORIGIN` with `Content-Security-Policy: frame-ancestors 'self' https://analytics.vogelring.com …`
so the Analyse-App can embed the chat in its drawer. LibreChat itself is no longer published on the host
(reachable as 127.0.0.1:3079 for debugging).

```yaml
  chat-proxy:
    image: nginx:1.27-alpine
    container_name: librechat-chat-proxy
    restart: unless-stopped
    ports:
      - "3080:80"
    volumes:
      - ./chat-proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - librechat
    networks:
      - librechat
```
