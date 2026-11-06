
# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 04/11/26
# ======================

import json
import socket
from collections.abc import Callable
import struct

import src.state as state


def start_udp_multicast(
    multicast_config: dict,
    process_message: Callable[[str, tuple], dict | None],
) -> None:
    """Inicia o servidor UDP de multicast."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", multicast_config["port"]))
    
    mreq = struct.pack("=4sl", socket.inet_aton(multicast_config["group"]), socket.INADDR_ANY)
    sock.setsockopt(
        socket.IPPROTO_IP, 
        socket.IP_ADD_MEMBERSHIP, 
        mreq)

    while True:
        data, address = sock.recvfrom(4096)
        message = data.decode("utf-8")
        state.debug_print(f"Mensagem recebida de {address}: {message}")
        response = process_message(message, address)

        request = json.loads(message)
        state.debug_print(
            f"Processando mensagem do cliente {address}: {request}, resposta: {response}"
        )
        if response:
            sock.sendto(json.dumps(response).encode("utf-8"), address)
