# ======================
# Eduarda Saibert - 20232368
# Modificado em 04/11/26
# ======================

import json
import socket
from typing import Optional

# =====================

TIMEOUT_MESSAGE = 5 # Tempo limite de espera para resposta do servidor em segundos

# Header = {
#    "operation": str,  # Tipo de operação (GET, POST, etc.)
#    "body": Optional[str]  # Corpo da mensagem (opcional)
# }

# body = {
#    "id": Optional[int],  # ID do item (opcional)
#    "response_code": Optional[int],  # Código de resposta (opcional)
#    "content": Optional[str]  # Conteúdo do item (opcional)
# }

# ======================

def _read_blocks(sock: socket.socket, buffer_size: int = 4096) -> bytes:
    """
    Lê uma mensagem TCP terminada por newline.
    """
    data = b""

    while b"\n" not in data:
        block = sock.recv(buffer_size)
        if not block:
            break
        data += block

    return data.split(b"\n", 1)[0]

def _read_udp_response(sock: socket.socket) -> dict:
    response_data, _ = sock.recvfrom(4096)
    return json.loads(response_data.decode("utf-8"))


def get(sock: socket.socket, resource_id: Optional[int], ip_dest: str, port: int) -> dict:
    """
    Solicita informações sobre um item específico ao servidor.
    """ 
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        # Envia requisição pedindo recurso ao processo
        header = build_header("GET", resource_id=resource_id)
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendto(request_msg, (ip_dest, port))

        # Aguarda resposta do servidor UDP
        return _read_udp_response(sock)
    except socket.timeout:
        return {"response": {"status": "ERROR", "message": "Tempo limite excedido"}}


def post(
    sock: socket.socket,
    resource_id: int,
    resource_body: str,
    ip_dest: str,
    port: int,
) -> dict:
    """
    Envia um novo item à um recurso específico ao servidor.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header("POST", resource_id=resource_id, resource_body=resource_body)
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendto(request_msg, (ip_dest, port))
        return _read_udp_response(sock)
    except socket.timeout:
        return {"response": {"status": "ERROR", "message": "Tempo limite excedido"}}

def replicate_post(
    sock: socket.socket,
    server_id: str,
    resource_id: int,
    resource_body: str,
) -> dict:
    """
    Solicita a replicação de uma avaliação em um servidor conectado.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header(
            "REPLICATE_POST",
            resource_id=resource_id,
            resource_body=resource_body,
        )
        header["server_id"] = server_id
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendall(request_msg)

        response_data = _read_blocks(sock)
        if not response_data:
            return {"response": {"status": "ERROR", "message": "Resposta vazia"}}

        response = json.loads(response_data.decode("utf-8"))    
        return response 

    except socket.timeout:
        return {"response": {"status": "ERROR", "message": "Tempo limite excedido"}}

def health(sock: socket.socket, server_id: str) -> dict:
    """
    Verifica a saúde de um servidor através de um socket TCP conectado.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header("HEALTH", resource_id=server_id)
        request_msg = json.dumps(header).encode("utf-8")
        sock.sendall(request_msg)

        # Aguarda resposta do servidor
        response_data = _read_blocks(sock)
        if not response_data:
            return {"response": {"status": "ERROR", "message": "Resposta vazia"}}

        response = json.loads(response_data.decode("utf-8"))    
        return response 
    except socket.timeout:
        return {"response": {"status": "ERROR", "message": "Tempo limite excedido"}}

def respond(
    sock: socket.socket,
    ip_dest: str,
    port: int,
    response_code: int,
    response: dict,
) -> int:
    """
    Resposta a uma solicitação do tipo GET ou POST.
    """
    sock.settimeout(TIMEOUT_MESSAGE)
    try:
        header = build_header(
            "RESPONSE",
            response_code=response_code,
            content={"response": response},
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
