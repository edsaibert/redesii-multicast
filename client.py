
# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 04/11/26
# ======================

import os
import time
import socket
import argparse
import src.application as application
from src.helpers import configure_debug, read_config, debug_print

MULTICAST_GROUP = None
MULTICAST_PORT = None

# ======================

def request_films(sock: socket.socket) -> None:
    """
    Solicita a lista de filmes ao servidor.
    """
    res = application.get(sock, None, MULTICAST_GROUP, MULTICAST_PORT)
    if (not res):
        debug_print("Não foi possível obter resposta a requisição.")
        return 0

    print(res["response"], end="\n\n")
    return 1


def request_film(sock: socket.socket, film_id: int) -> None:
    """
    Solicita detalhes de um filme específico ao servidor.
    """
    res = application.get(sock, film_id, MULTICAST_GROUP, MULTICAST_PORT)
    if (not res):
        debug_print("Não foi possível obter resposta a requisição.")
        return 0

    response = res["response"]
    if "film" not in response:
        print(response, end="\n\n")
        return 0

    print(response["film"], end="\n\n")
    return 1


def add_review(sock: socket.socket, film_id: int, review: str) -> None:
    """
    Adiciona uma avaliação a um filme específico.
    """
    flag = application.post(sock, film_id, review, MULTICAST_GROUP, MULTICAST_PORT)
    if flag.get("response", {}).get("status") != "OK":
        debug_print("Não foi possível adicionar a avaliação.")
        return 0

    print("Avaliação adicionada com sucesso.")
    return 1


def main() -> None:
    """Função que realiza testes de requisições ao servidor multicast."""

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
    sock.bind(("", 0))
    if (not sock): debug_print("Não foi possível se conectar ao socket.")

    # Solicita a lista de filmes, detalhes de um filme específico e adiciona uma avaliação
    try:
        request_films(sock)
        time.sleep(5)
        request_film(sock, 1)
        time.sleep(5)
        request_film(sock, -1)
        time.sleep(5)
        add_review(sock, 1, "Ótimo filme!")
    except KeyboardInterrupt:
        debug_print("Encerrando cliente...")
        sock.close()

if __name__ == "__main__":
    main()