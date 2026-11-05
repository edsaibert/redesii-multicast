# ======================
# Eduarda Saibert - 20232368
# Modificado em 04/11/26
# ======================

import json
import socket
import argparse
from typing import Optional
from helpers import configure_debug, debug_print

# =====================

TIMEOUT_MESSAGE = 5 # Tempo limite de espera para resposta do servidor em segundos

# Header = {
#    "operation": str,  # Tipo de operação (GET, POST, etc.)
#    "body": Optional[str]  # Corpo da mensagem (opcional)
#}

# body = {
#    "id": Optional[int],  # ID do item (opcional)
#    "response_code": Optional[int],  # Código de resposta (opcional)
#    "content": Optional[str]  # Conteúdo do item (opcional)
#}

# ======================

def get(sock: socket.socket, resource_id: Optional[int], ip_dest: str, port: int) -> dict:
    """
    Solicita informações sobre um item específico ao servidor.
    """ 
    sock.settimeout(TIMEOUT_MESSAGE)
    # Envia requisição pedindo recurso ao processo
    try:
        header = build_header("GET", resource_id=resource_id)
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendto(request_msg, (ip_dest, port))
    except socket.timeout:
        return {}  

    # Espera uma resposta do servidor contendo os dados do recurso
    try:
        response_data, _ = sock.recvfrom(4096)
        response = json.loads(response_data.decode("utf-8"))
        return response 
    except socket.timeout:
        return {}   
    
def post(sock: socket.socket, resource_id: int, resource_body: str, ip_dest: str, port: int) -> int:
    """
    Envia um novo item à um recurso específico ao servidor.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header("POST", resource_id=resource_id, resource_body=resource_body)
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendto(request_msg, (ip_dest, port))
    except socket.timeout:
        return 0   # timeout
    return 1

def respond(sock: socket.socket, ip_dest: str, port: int, response_code: int, response: dict) -> int:
    """
    Resposta a uma solicitação do tipo GET ou POST.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header(
            "RESPONSE", response_code=response_code, content=response
        )
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendto(request_msg, (ip_dest, port))
    except socket.timeout:
        return 0   # timeout
    return 1

def build_header(
    operation: str,
    resource_id: Optional[int] = None,
    response_code: Optional[int] = None,
    resource_body: Optional[str] = None,
    content: Optional[str] = None,
) -> dict:
    """
    Constrói o cabeçalho da mensagem a ser enviada ao servidor.
    """
    body = {}
    if resource_id is not None:
        body["resource_id"] = resource_id
    if response_code is not None:
        body["response_code"] = response_code
    if content is not None:
        body["content"] = content
    if resource_body is not None:
        body["content"] = resource_body

    return {"operation": operation, "body": body}
