<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/ports — 全量正典表

來源＝docker-compose.yml＋docker-compose.dev.yml＋docker-compose.example.yml 的 ports: 段（generate 重算；配號紀律歸 ADR 0019）。

| 服務 | host port | 容器內 port | 綁定 IP | 來源檔 |
|---|---|---|---|---|
| base-web | 52081 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 52080 | 80 | 127.0.0.1 | docker-compose.dev.yml |
| front-nginx | 52443 | 443 | 127.0.0.1 | docker-compose.dev.yml |
| grafana | 53000 | 3000 | 127.0.0.1 | docker-compose.dev.yml |
| loki | 53100 | 3100 | 127.0.0.1 | docker-compose.dev.yml |
| mailpit | 58025 | 8025 | 127.0.0.1 | docker-compose.dev.yml |
| postgres | 55432 | 5432 | 127.0.0.1 | docker-compose.dev.yml |
| prometheus | 59090 | 9090 | 127.0.0.1 | docker-compose.dev.yml |
| pushgateway | 59091 | 9091 | 127.0.0.1 | docker-compose.dev.yml |
| redis | 56379 | 6379 | 127.0.0.1 | docker-compose.dev.yml |
| rust-api | 52079 | 8080 | 127.0.0.1 | docker-compose.dev.yml |
| example-dev | 52089 | 80 | 127.0.0.1 | docker-compose.example.yml |
