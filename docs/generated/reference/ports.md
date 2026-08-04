<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/ports — 全量正典表

來源＝docker-compose.yml＋docker-compose.dev.yml＋docker-compose.example.yml 的 ports: 段（generate 重算；配號紀律歸 ADR 0004）。

| 服務 | host port | 容器內 port | 綁定 IP | 來源檔 |
|---|---|---|---|---|
| base-web | 22081 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 22080 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 22443 | 443 | 127.0.0.1 | docker-compose.dev.yml |
| grafana | 23000 | 3000 | 127.0.0.1 | docker-compose.dev.yml |
| loki | 23100 | 3100 | 127.0.0.1 | docker-compose.dev.yml |
| mailpit | 28025 | 8025 | 127.0.0.1 | docker-compose.dev.yml |
| postgres | 25432 | 5432 | 127.0.0.1 | docker-compose.dev.yml |
| prometheus | 29090 | 9090 | 127.0.0.1 | docker-compose.dev.yml |
| pushgateway | 29091 | 9091 | 127.0.0.1 | docker-compose.dev.yml |
| redis | 26379 | 6379 | 127.0.0.1 | docker-compose.dev.yml |
| rust-api | 22079 | 8080 | 127.0.0.1 | docker-compose.dev.yml |
| example-dev | 22089 | 80 | 127.0.0.1 | docker-compose.example.yml |
