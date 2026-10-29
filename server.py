# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

import json
import state
import threading
import socket
import argparse
from helpers import configure_debug, read_config, debug_print

# ======================


def start_udp_multicast(multicast_config: dict) -> None:
    """
    Inicia o servidor UDP de multicast.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", multicast_config["port"]))

    multicast_group = socket.inet_aton(multicast_config["group"]) + socket.inet_aton(multicast_config["interface"])

    sock.setsockopt(
        socket.IPPROTO_IP, 
        socket.IP_ADD_MEMBERSHIP, 
        multicast_group)

    # Loop para receber mensagens de multicast
    while True:
        data, address = sock.recvfrom(4096)
        state.debug_print(f"Mensagem recebida de {address}: {data.decode()}")
        response = process_client_message(data.decode("utf-8"), address)

        request = json.loads(data.decode("utf-8"))
        state.debug_print(f"Processando mensagem do cliente {address}: {request}, resposta: {response}")
        if response:
            sock.sendto(json.dumps(response).encode("utf-8"), address)

def handle_tcp_message(client: socket.socket) -> None:
    """
    Trata uma conexao TCP
    """

    data, address = client.recvfrom(4096)

    # implementar: logica de tratar uma mensagem TCP recebida
    # exemplo: atualizar dado

    shutdown(client)

def start_tcp(server_config: dict) -> None:
    """
    Inicia o servidor TCP.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((server_config["ip"], server_config["tcp_port"]))

    sock.listen(5)

    while True:
        client, addr = sock.accept()

        client_handler = threading.Thread(target = handle_tcp_message, args = (client,))
        client_handler.start();

    pass


def connect_to_servers():
    """
    Conecta-se aos servidores vizinhos.
    """

    pass


def heartbeat(multicast_config: dict):
    """
    Envia um heartbeat para os outros servidores.
    """
    
    pass


def elect_leader():
    """
    Inicia o processo de eleição do líder.
    """

    pass


def process_server_message():
    """
    Processa mensagens recebidas de outros servidores.
    """

    pass


def process_client_message(message: str, address: tuple):
    """
    Processa mensagens recebidas de clientes.
    """
    request = json.loads(message)

    if not state.is_leader():
        debug_print(f"Servidor não é líder. Ignorando mensagem do cliente {address}")
        return

    operation = request.get("operation")
    response = {}

    if operation == "LIST":
        films = state.get_films()
        response = {"status": "OK", "films": films}
        return response

    if operation == "ADD_REVIEW":
        film_id = request.get("film_id")
        review = request.get("review")
        success = state.add_review(film_id, review)
        if not success:
            response = {"status": "ERROR", "message": f"Erro ao adicionar review ao filme {film_id}"}
            return response
        
        response = {"status": "OK", "message": f"Review adicionada ao filme {film_id}"}
        return response
    
    response = {"status": "ERROR", "message": "Operação desconhecida"}
    return response


def shutdown(sock: socket.socket, warn: bool = False) -> None:
    """
    Encerra o servidor.
    """
    
    try:
        if (warn):
            sock.shutdown(socket.SHUT_RDWR)
    finally:
        sock.close()

    pass


def main() -> None:
    """
    Função principal do servidor.
    """
    parser = argparse.ArgumentParser(description="Servidor multicast")
    parser.add_argument("-d", "--debug", action="store_true", help="ativa as mensagens de debug")
    parser.add_argument("server_id", help="identificador do servidor")
    parser.add_argument("config_path", help="caminho para o arquivo config.toml")
    args = parser.parse_args()

    debug_enabled = args.debug
    server_id = args.server_id
    config = read_config(args.config_path)
    multicast_config = config["multicast"]
    configure_debug(debug_enabled, server_id)

    # Coleta os servidores
    servers_config = {
        str(server_id): {
            "ip": server_config["ip"],
            "tcp_port": server_config["tcp_port"],
        }
        for server_id, server_config in config["servers"].items()
    }
    
    state.init_state(
        server_id=server_id,
        server_ip=servers_config[str(server_id)]["ip"],
        server_tcp_port=servers_config[str(server_id)]["tcp_port"],
        debug=debug_enabled,
        initial_leader_id=str(multicast_config["leader_id"]),
        initial_peer_servers={k: v for k, v in servers_config.items() if k != server_id}
    )

    # Inicia os threads para UDP, TCP e heartbeat
    threading.Thread(target=start_udp_multicast, args=(multicast_config,), daemon=True).start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        shutdown()

if __name__ == "__main__":
    main()



# def main():
#     threading.Thread(target=udp_receiver, daemon=True).start()
#     threading.Thread(target=tcp_listener, daemon=True).start()

#     print("Server is running")

#     try:
#         threading.Event().wait()
#     except KeyboardInterrupt:
#         print("Shutting down")