
# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

import json
import socket
import argparse
from helpers import configure_debug, read_config, debug_print

TIMEOUT_SEGUNDOS = 5
MULTICAST_GROUP = None
MULTICAST_PORT = None

# ======================

def request_films(sock: socket.socket) -> None:
    """
    Solicita a lista de filmes ao servidor.
    """
    request = {
        "operation": "LIST"
    }
    request_msg = json.dumps(request).encode("utf-8")
    sock.sendto(request_msg, (MULTICAST_GROUP, MULTICAST_PORT))

def add_review(sock: socket.socket, film_id: int, review: str) -> None:
    """
    Adiciona uma avaliação a um filme específico.
    """
    request = {
        "operation": "ADD_REVIEW",
        "film_id": film_id,
        "review": review
    }
    request_msg = json.dumps(request).encode("utf-8")
    sock.sendto(request_msg, (MULTICAST_GROUP, MULTICAST_PORT))

def wait_for_response(sock: socket.socket) -> None:
    """
    Aguarda a resposta do servidor.
    """
    try:
        response_data, _ = sock.recvfrom(4096)
        response = json.loads(response_data.decode("utf-8"))
        debug_print(f"Resposta recebida: {response}")
    except socket.timeout:
        debug_print("Tempo limite de espera pela resposta do servidor.")
    # finally:
    #     sock.close()


def main() -> None:
    global MULTICAST_GROUP, MULTICAST_PORT

    parser = argparse.ArgumentParser(description="Cliente multicast")
    parser.add_argument("-d", "--debug", action="store_true", help="ativa as mensagens de debug")
    parser.add_argument("config_path", help="caminho para o arquivo config.toml")
    args = parser.parse_args()

    configure_debug(args.debug)
    config_path = args.config_path
    config = read_config(config_path)

    MULTICAST_GROUP = config["multicast"]["group"]
    MULTICAST_PORT = config["multicast"]["port"]

    # Conecta-se ao servidor e realiza operações (LIST, ADD_REVIEW)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = 1
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.settimeout(TIMEOUT_SEGUNDOS)
    sock.bind(("", 0))

    # Solicita a lista de filmes
    request_films(sock)
    wait_for_response(sock)

    # Adiciona uma avaliação a um filme específico
    film_id = 1  
    review = "Ótimo filme!"  
    add_review(sock, film_id, review)
    wait_for_response(sock)

if __name__ == "__main__":
    main()