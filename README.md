# Sistema distribuído de mensagens

Aplicação Flask executada em três containers Docker. As mensagens são gravadas em um volume compartilhado e replicadas entre as instâncias pela rede bridge do Docker Compose.

## Fluxo da aplicação

```mermaid
flowchart TD
    Cliente["Cliente HTTP"] --> App1["app1 - localhost:5001"]
    Cliente --> App2["app2 - localhost:5002"]
    Cliente --> App3["app3 - localhost:5003"]

    App1 --> Armazenamento[("Volume compartilhado - /data/messages.jsonl")]
    App2 --> Armazenamento
    App3 --> Armazenamento

    App1 -->|"POST /internal/replicate"| App2
    App1 -->|"POST /internal/replicate"| App3
    App2 -->|"POST /internal/replicate"| App1
    App2 -->|"POST /internal/replicate"| App3
    App3 -->|"POST /internal/replicate"| App1
    App3 -->|"POST /internal/replicate"| App2

    App1 --> Log1["/data/logs/app1.log"]
    App2 --> Log2["/data/logs/app2.log"]
    App3 --> Log3["/data/logs/app3.log"]
```

Ao receber um `POST /send`, a instância de origem grava a mensagem no volume compartilhado e envia uma cópia para as outras duas instâncias. Cada container registra seus próprios eventos no arquivo de log correspondente.

## Estrutura

```text
/avaliacao/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── test.sh
└── README.md
```

## Como executar

Pré-requisitos: Docker com Docker Compose e, para executar `test.sh`, `curl` e Python 3.

```bash
docker compose up -d --build
```

Verifique o funcionamento:

```bash
curl http://localhost:5001/health
curl -X POST http://localhost:5001/send \
  -H "Content-Type: application/json" \
  -d '{"mensagem":"hello"}'
curl http://localhost:5002/messages
```

Execute o teste completo:

```bash
bash test.sh
```

Para acompanhar os logs:

```bash
docker compose logs -f
```

Para parar os containers sem remover os dados:

```bash
docker compose down
```

Para parar os containers e remover o volume persistente:

```bash
docker compose down -v
```

## Endpoints

- `GET /health`: verifica se a instância está disponível.
- `POST /send`: recebe `{"mensagem":"texto"}` e replica a mensagem.
- `GET /messages`: lista as mensagens persistidas.
- `POST /internal/replicate`: endpoint interno usado entre containers.

As portas externas são `5001`, `5002` e `5003`. Internamente, os serviços se comunicam usando os nomes `app1`, `app2` e `app3`.

O endpoint aceita tanto o campo descritivo `mensagem` quanto `message`, usado no exemplo do enunciado.
