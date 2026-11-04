
# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 02/11/26
# ======================

import os
import socket
import argparse
import application
from helpers import configure_debug, read_config, debug_print

MULTICAST_GROUP = None
MULTICAST_PORT = None

# ======================

# def request_films(sock: socket.socket) -> None:
#     """
#     Solicita a lista de filmes ao servidor.
#     """
#     request = {
#         "operation": "LIST"
#     }
#     request_msg = json.dumps(request).encode("utf-8")
#     sock.sendto(request_msg, (MULTICAST_GROUP, MULTICAST_PORT))

# def add_review(sock: socket.socket, film_id: int, review: str) -> None:
#     """
#     Adiciona uma avaliação a um filme específico.
#     """
#     request = {
#         "operation": "ADD_REVIEW",
#         "film_id": film_id,
#         "review": review
#     }
#     request_msg = json.dumps(request).encode("utf-8")
#     sock.sendto(request_msg, (MULTICAST_GROUP, MULTICAST_PORT))

# def wait_for_response(sock: socket.socket) -> None:
#     """
#     Aguarda a resposta do servidor.
#     """
#     try:
#         response_data, _ = sock.recvfrom(4096)
#         response = json.loads(response_data.decode("utf-8"))
#         debug_print(f"Resposta recebida: {response}")
#     except socket.timeout:
#         debug_print("Tempo limite de espera pela resposta do servidor.")
#     # finally:
#     #     sock.close()

def client_interface(sock: socket.socket) -> None:
    """
    Monta uma interface CLI para teste do cliente.
    """

    while True:
        os.system('clear')  
        print("=== Cliente Multicast ===")
        print("1. Solicitar lista de filmes")
        print("2. Solicitar detalhes de um filme específico")
        print("3. Adicionar avaliação a um filme")
        print("0. Sair")

        choice = input("Escolha uma opção: ")

        if choice == "1":
            # Solicita a lista de filmes
            res = application.get(sock, None, MULTICAST_GROUP, MULTICAST_PORT)
            if (not res):
                debug_print("Não foi possível obter resposta a requisição.")
                break
            print(f"{res}")
        elif choice == "2":
            os.system('clear')
            print("Digite o ID do filme:")
            film_id = int(input())
            debug_print(f"{MULTICAST_GROUP}, {MULTICAST_PORT}")
            res = application.get(sock, film_id, MULTICAST_GROUP, MULTICAST_PORT)
            if (res == -1):
                debug_print("Não foi possível obter resposta a requisição.")
                break
            # Solicita detalhes de um filme específico
        elif choice == "3":
            os.system('clear')
            # Adiciona uma avaliação a um filme específico
            print("Digite o ID do filme:")
            film_id = int(input())

            os.system('clear')
            print("Digite a avaliação:")
            review = input()
            res = application.post(sock, film_id, review, MULTICAST_GROUP, MULTICAST_PORT)
            if (res == -1):
                debug_print("Não foi possível obter resposta a requisição.")
                break
        elif choice == "0":
            # Sai do cliente
            os.system('clear')
            break

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
    sock.bind(("", 0))

    if (not sock): debug_print("Não foi possível se conectar ao socket.")
    client_interface(sock)

if __name__ == "__main__":
    main()