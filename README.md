# Sistema distribuído de mensagens

Aplicação Flask executada em três containers Docker. As mensagens são gravadas em um volume compartilhado e replicadas entre as instâncias pela rede bridge do Docker Compose.

## Fluxo da aplicação

```mermaid
flowchart LR
    Cliente["Cliente"] -->|"POST /send"| Origem["Container de origem\napp1, app2 ou app3"]
    Origem -->|"Grava mensagem"| Volume[("Volume compartilhado\n/data/messages.jsonl")]
    Origem -->|"Replica"| Outros["Outros dois containers"]
    Outros -->|"Gravam a mensagem"| Volume
    Origem --> LogOrigem["Log da origem"]
    Outros --> LogsOutros["Logs dos outros containers"]
```

Ao receber um `POST /send`, o container que recebe a requisição grava a mensagem no volume compartilhado, replica o conteúdo para os outros dois containers e registra o evento em seu próprio log. Os containers que recebem a réplica também gravam seus eventos nos respectivos logs.

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

Esse comando continua sendo o fluxo recomendado para Docker normal.

## Como executar no Docker Swarm

O Swarm não faz `build` a partir de `docker-stack.yml`. Para testar em um
único nó, acesse o projeto pelo WSL e execute na ordem:

```bash
cd /mnt/c/Users/User/Downloads/sistema-distribuido-mensagens-docker
```

Se o Swarm ainda não estiver inicializado:

```bash
docker swarm init
```

Marque o nó atual para receber os serviços:

```bash
docker node ls
docker node update --label-add mensagens_storage=true $(docker node ls -q | head -n 1)
```

Construa a imagem e implante a stack:

```bash
docker build -t mensagens-app:1.0 ./app
docker stack deploy -c docker-stack.yml mensagens
```

Verifique o resultado:

```bash
docker stack services mensagens
docker stack ps mensagens
```

Para um cluster com mais de um nó, publique a imagem em um registry acessível
por todos os nós e informe-a no deploy:

```bash
docker build -t SEU_USUARIO/mensagens-app:1.0 ./app
docker push SEU_USUARIO/mensagens-app:1.0
IMAGE_NAME=SEU_USUARIO/mensagens-app:1.0 \
  docker stack deploy -c docker-stack.yml mensagens
```

O arquivo `docker-stack.yml` fixa os três serviços no nó marcado porque o
volume nomeado usa o driver local. Para distribuir os serviços entre vários
nós, substitua esse volume por NFS ou por um volume plugin compartilhado.

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
