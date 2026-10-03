import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, request


aplicacao = Flask(__name__)

nome_servico = os.getenv("NOME_SERVICO", "app")
porta_aplicacao = int(os.getenv("PORTA_APLICACAO", "5000"))
diretorio_dados = Path(os.getenv("DIRETORIO_DADOS", "/data"))
arquivo_mensagens = diretorio_dados / "messages.jsonl"
diretorio_logs = diretorio_dados / "logs"
arquivo_log = diretorio_logs / f"{nome_servico}.log"
tempo_limite_replicacao = float(os.getenv("TEMPO_LIMITE_REPLICACAO", "3"))
servicos_replicacao = [
    servico.strip()
    for servico in os.getenv("SERVICOS_REPLICACAO", "").split(",")
    if servico.strip() and servico.strip() != nome_servico
]

trava_arquivo = threading.Lock()


def preparar_armazenamento():
    diretorio_dados.mkdir(parents=True, exist_ok=True)
    diretorio_logs.mkdir(parents=True, exist_ok=True)
    arquivo_mensagens.touch(exist_ok=True)
    arquivo_log.touch(exist_ok=True)


def registrar_log(evento, **detalhes):
    registro = {
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "servico": nome_servico,
        "evento": evento,
        **detalhes,
    }
    with trava_arquivo, arquivo_log.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def ler_mensagens():
    mensagens = []
    linhas_invalidas = []
    with trava_arquivo, arquivo_mensagens.open("r", encoding="utf-8") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue
            try:
                mensagens.append(json.loads(linha))
            except json.JSONDecodeError:
                linhas_invalidas.append(numero_linha)
    for numero_linha in linhas_invalidas:
        registrar_log("linha_invalida_ignorada", numero_linha=numero_linha)
    return mensagens


def armazenar_mensagem(mensagem):
    with trava_arquivo:
        mensagens_existentes = []
        with arquivo_mensagens.open("r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                if linha.strip():
                    try:
                        mensagens_existentes.append(json.loads(linha))
                    except json.JSONDecodeError:
                        continue

        if any(item.get("id") == mensagem["id"] for item in mensagens_existentes):
            return False

        with arquivo_mensagens.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(mensagem, ensure_ascii=False) + "\n")
        return True


def criar_mensagem(texto):
    return {
        "id": str(uuid.uuid4()),
        "mensagem": texto,
        "origem": nome_servico,
        "data_hora": datetime.now(timezone.utc).isoformat(),
    }


def replicar_mensagem(mensagem):
    resultados = {}
    for servico in servicos_replicacao:
        endereco = f"http://{servico}:{porta_aplicacao}/internal/replicate"
        try:
            resposta = requests.post(
                endereco,
                json=mensagem,
                timeout=tempo_limite_replicacao,
            )
            resposta.raise_for_status()
            resultados[servico] = "sucesso"
        except requests.RequestException as erro:
            resultados[servico] = f"erro: {erro}"
            registrar_log("falha_replicacao", destino=servico, erro=str(erro))
    return resultados


@aplicacao.get("/health")
def verificar_saude():
    return jsonify({"status": "ok", "servico": nome_servico})


@aplicacao.post("/send")
def enviar_mensagem():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "O corpo deve ser um objeto JSON."}), 400

    texto_recebido = dados.get("mensagem", dados.get("message"))
    if not isinstance(texto_recebido, str):
        return jsonify({"erro": "O campo 'mensagem' ou 'message' deve ser um texto."}), 400

    texto = texto_recebido.strip()
    if not texto:
        return jsonify({"erro": "O campo 'mensagem' não pode ser vazio."}), 400

    mensagem = criar_mensagem(texto)
    armazenar_mensagem(mensagem)
    registrar_log("mensagem_recebida", id_mensagem=mensagem["id"])
    resultados = replicar_mensagem(mensagem)

    codigo_http = 200 if all(valor == "sucesso" for valor in resultados.values()) else 207
    return jsonify({"mensagem": mensagem, "replicacoes": resultados}), codigo_http


@aplicacao.post("/internal/replicate")
def receber_replicacao():
    mensagem = request.get_json(silent=True)
    campos_obrigatorios = {"id", "mensagem", "origem", "data_hora"}
    if not isinstance(mensagem, dict) or not campos_obrigatorios.issubset(mensagem):
        return jsonify({"erro": "Mensagem de replicação inválida."}), 400

    foi_nova = armazenar_mensagem(mensagem)
    registrar_log(
        "mensagem_replicada" if foi_nova else "mensagem_duplicada_ignorada",
        id_mensagem=mensagem["id"],
        origem=mensagem["origem"],
    )
    return jsonify({"armazenada": foi_nova}), 200


@aplicacao.get("/messages")
def listar_mensagens():
    return jsonify(ler_mensagens())


if __name__ == "__main__":
    preparar_armazenamento()
    aplicacao.run(host="0.0.0.0", port=porta_aplicacao)
