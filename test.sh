#!/usr/bin/env bash
set -euo pipefail

PORTA_ORIGEM="${1:-5001}"
MENSAGEM="teste de replicacao $(date +%s)"

echo "Verificando servicos..."
for porta in 5001 5002 5003; do
  curl --fail --silent "http://localhost:${porta}/health" > /dev/null
done

echo "Enviando mensagem para a porta ${PORTA_ORIGEM}..."
resposta=$(curl --fail --silent \
  -H "Content-Type: application/json" \
  -d "{\"mensagem\":\"${MENSAGEM}\"}" \
  "http://localhost:${PORTA_ORIGEM}/send")
echo "${resposta}"

for porta in 5001 5002 5003; do
  quantidade=$(curl --fail --silent "http://localhost:${porta}/messages" | \
    python3 -c 'import json, sys; print(sum(1 for item in json.load(sys.stdin) if item.get("mensagem") == sys.argv[1]))' "${MENSAGEM}")
  if [ "${quantidade}" -lt 1 ]; then
    echo "Falha: mensagem não encontrada na porta ${porta}." >&2
    exit 1
  fi
done

echo "Teste concluido: mensagem encontrada nas tres instancias."
