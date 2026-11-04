# ======================
# Eduarda Saibert - 20232368
# Modificado em 31/10/26
# ======================

import json
import socket
import argparse
from typing import Optional
from helpers import configure_debug, read_config, debug_print

# =====================

TIMEOUT_MESSAGE = 5 // Tempo limite de espera para resposta do servidor em segundos

# Header = {
#    "operation": str,  # Tipo de operação (GET, POST, etc.)
#    "message_id": int,  # ID da mensagem
#    "body": Optional[str]  # Corpo da mensagem (opcional)
#}

# body = {
#    "id": Optional[int],  # ID do item (opcional)
#    "response_code": Optional[int],  # Código de resposta (opcional)
#    "content": Optional[str]  # Conteúdo do item (opcional)
#}

# ======================

def get(sock: socket.socket, resource_id: Optional[int], ip_dest: str, port: int) -> int:
    """
    Solicita informações sobre um item específico ao servidor.
    """ 
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header("GET", resource_id=resource_id)
        sock.sendto(json.dumps(header).encode(), (ip_dest, port))
    except socket.timeout:
        return -1   # Retorna -1 em caso de timeout

    try:
        response_data, _ = sock.recvfrom(4096)
    




def post(sock: socket.socket, resource_id: int, review: str, ip_dest: str, port: int) -> int:
    """
    Envia um novo item à um recurso específico ao servidor.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header("POST", resource_id=resource_id, review=review)
        sock.sendto(json.dumps(header).encode(), (ip_dest, port))
    except socket.timeout:
        return -1   # Retorna -1 em caso de timeout
    return 0

def respond(sock: socket.socket, ip_dest: str, port: int, response_code: int, response: dict) -> int:
    """
    Resposta a uma solicitação do tipo GET ou POST.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header(
            "RESPONSE", response_code=response_code, content=response
        )
        sock.sendto(json.dumps(header).encode(), (ip_dest, port))
    except socket.timeout:
        return -1   # Retorna -1 em caso de timeout
    return 0


def build_header(
    operation: str,
    resource_id: Optional[int] = None,
    response_code: Optional[int] = None,
    content: Optional[str] = None,
    review: Optional[str] = None,
) -> dict:
    """
    Constrói o cabeçalho da mensagem a ser enviada ao servidor.
    """
    body = {}
    if resource_id is not None:
        body["id"] = resource_id
    if response_code is not None:
        body["response_code"] = response_code
    if content is not None:
        body["content"] = content
    if review is not None:
        body["review"] = review

    return {"operation": operation, "body": body}


def interpret_header(header: dict) -> None:
    """
    Interpreta o cabeçalho da mensagem.
    """
    return header.get("operation"), header.get("message_id"), header.get("body")

