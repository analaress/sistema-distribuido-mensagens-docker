# Relatório de Testes

Este relatório registra os testes executados manualmente no sistema distribuído de mensagens.

## 1. Verificação de saúde do serviço

### Comando

```bash
curl http://localhost:5001/health
```

### Propósito

Verificar se o container `app1` está ativo e aceitando requisições HTTP.

### Resultado

```json
{"servico":"app1","status":"ok"}
```

### Conclusão

O serviço `app1` iniciou corretamente e está disponível na porta `5001`.

## 2. Envio de mensagem

### Comando

```bash
curl -X POST http://localhost:5001/send \
  -H "Content-Type: application/json" \
  -d '{"message":"hello ana"}'
```

### Propósito

Enviar uma mensagem para o endpoint `POST /send` do container `app1`.

### Resultado

```json
{
  "mensagem": {
    "data_hora": "2026-10-03T12:44:10.006643+00:00",
    "id": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384",
    "mensagem": "hello ana",
    "origem": "app1"
  },
  "replicacoes": {
    "app2": "sucesso",
    "app3": "sucesso"
  }
}
```

### Conclusão

A mensagem foi aceita pelo `app1`, recebeu um identificador único e foi replicada com sucesso para `app2` e `app3`.

## 3. Verificação da mensagem no app2

### Comando

```bash
curl http://localhost:5002/messages
```

### Propósito

Confirmar que o `app2` recebeu e armazenou a mensagem replicada.

### Resultado

```json
[
  {
    "data_hora": "2026-10-03T12:44:10.006643+00:00",
    "id": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384",
    "mensagem": "hello ana",
    "origem": "app1"
  }
]
```

### Conclusão

A mensagem foi replicada corretamente para o `app2`.

## 4. Verificação da mensagem no app3

### Comando

```bash
curl http://localhost:5003/messages
```

### Propósito

Confirmar que o `app3` recebeu e armazenou a mensagem replicada.

### Resultado

```json
[
  {
    "data_hora": "2026-10-03T12:44:10.006643+00:00",
    "id": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384",
    "mensagem": "hello ana",
    "origem": "app1"
  }
]
```

### Conclusão

A mensagem foi replicada corretamente para o `app3`.

## 5. Execução do teste automatizado

### Comando

```bash
bash test.sh
```

### Propósito

Validar automaticamente a disponibilidade dos três serviços, o envio de uma mensagem, a replicação e a leitura da mensagem em cada container.

### Resultado

```text
Verificando servicos...
Enviando mensagem para a porta 5001...
{"mensagem":{"data_hora":"2026-10-03T12:44:47.905129+00:00","id":"f3d94972-4360-4ba6-8c9a-d718c059a7ab","mensagem":"teste de replicacao 1791031487","origem":"app1"},"replicacoes":{"app2":"sucesso","app3":"sucesso"}}
Teste concluido: mensagem encontrada nas tres instancias.
```

### Conclusão

O teste automatizado foi executado com sucesso. A mensagem foi encontrada nas três instâncias.

## 6. Verificação dos arquivos de log

### Comando

```bash
docker compose exec app1 sh -c 'ls -l /data/logs'
```

### Propósito

Verificar se cada container criou seu próprio arquivo de log dentro do volume compartilhado.

### Resultado

```text
total 12
-rw-r--r-- 1 root root 310 Oct  3 12:44 app1.log
-rw-r--r-- 1 root root 366 Oct  3 12:44 app2.log
-rw-r--r-- 1 root root 366 Oct  3 12:44 app3.log
```

### Conclusão

Os três arquivos de log foram criados corretamente no volume compartilhado:

```text
/data/logs/app1.log
/data/logs/app2.log
/data/logs/app3.log
```

## 7. Verificação do conteúdo dos logs

### Comando

```bash
docker compose exec app1 sh -c 'for arquivo in /data/logs/*.log; do echo "--- $arquivo"; cat "$arquivo"; done'
```

### Resultado

```text
--- /data/logs/app1.log
{"data_hora": "2026-10-03T12:44:10.006832+00:00", "servico": "app1", "evento": "mensagem_recebida", "id_mensagem": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384"}
{"data_hora": "2026-10-03T12:44:47.905326+00:00", "servico": "app1", "evento": "mensagem_recebida", "id_mensagem": "f3d94972-4360-4ba6-8c9a-d718c059a7ab"}
--- /data/logs/app2.log
{"data_hora": "2026-10-03T12:44:10.021635+00:00", "servico": "app2", "evento": "mensagem_duplicada_ignorada", "id_mensagem": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384", "origem": "app1"}
{"data_hora": "2026-10-03T12:44:47.907033+00:00", "servico": "app2", "evento": "mensagem_duplicada_ignorada", "id_mensagem": "f3d94972-4360-4ba6-8c9a-d718c059a7ab", "origem": "app1"}
--- /data/logs/app3.log
{"data_hora": "2026-10-03T12:44:10.029534+00:00", "servico": "app3", "evento": "mensagem_duplicada_ignorada", "id_mensagem": "d445fe1b-c8d8-444b-a551-dc1a5eaf2384", "origem": "app1"}
{"data_hora": "2026-10-03T12:44:47.909105+00:00", "servico": "app3", "evento": "mensagem_duplicada_ignorada", "id_mensagem": "f3d94972-4360-4ba6-8c9a-d718c059a7ab", "origem": "app1"}
```

### Conclusão

O `app1` registrou o recebimento das mensagens. Os `app2` e `app3` registraram as cópias recebidas como duplicadas porque a mensagem já estava gravada no volume compartilhado pelo `app1`. Isso confirma que a replicação ocorreu e que o identificador único impediu gravações duplicadas.

## Conclusão geral

Os testes confirmaram:

1. Funcionamento da API.
2. Comunicação entre os containers.
3. Envio e recebimento de mensagens.
4. Replicação para `app2` e `app3`.
5. Funcionamento do script automatizado de testes.

## Atendimento aos requisitos do PDF

### Aplicação Python

- `app/app.py` foi criado.
- `POST /send` foi testado com sucesso.
- `GET /messages` foi testado com sucesso.
- As mensagens são recebidas em formato JSON.

**Situação:** atendido e testado.

### Dockerfile

- `app/Dockerfile` foi criado.
- A imagem utiliza Python.
- As dependências são instaladas a partir de `requirements.txt`.
- A porta interna `5000` é exposta.

**Situação:** atendido pela configuração do projeto.

### Docker Compose

- Os serviços `app1`, `app2` e `app3` foram configurados.
- As portas externas são `5001`, `5002` e `5003`.
- O volume `mensagens_compartilhadas` é montado em `/data` nos três containers.
- A rede bridge personalizada `rede_mensagens` foi configurada.

**Situação:** atendido e executado.

### Comunicação e replicação

- O `POST /send` armazena a mensagem na origem.
- A mensagem é enviada para os outros dois containers.
- A resposta confirmou `app2: sucesso` e `app3: sucesso`.
- A mensagem foi consultada com sucesso nas três instâncias.
- A deduplicação foi confirmada pelos logs.

**Situação:** testado com sucesso.

### Persistência e logs

- As mensagens são persistidas no volume compartilhado.
- Foram encontrados `/data/logs/app1.log`, `/data/logs/app2.log` e `/data/logs/app3.log`.
- Cada instância registrou seus próprios eventos no respectivo arquivo de log.

**Situação:** testado com sucesso.

### Entrega e documentação

- `app/app.py`
- `app/requirements.txt`
- `app/Dockerfile`
- `docker-compose.yml`
- `test.sh`
- `README.md`
- `RELATORIO_TESTES.md`
- `.dockerignore`
- `.gitignore`

**Situação:** estrutura de entrega atendida.

### Resultado final

Todos os requisitos funcionais e estruturais descritos no PDF estão contemplados. Os requisitos de execução foram demonstrados pelos comandos registrados neste relatório, e os requisitos de configuração foram confirmados nos arquivos entregues.
