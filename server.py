# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

import sys
import state
import threading
import socket
from helpers import read_config, debug_print, DEBUG

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

        if response:
            sock.sendto(json.dumps(response).encode("utf-8"), address)


def start_tcp():
    """
    Inicia o servidor TCP.
    """

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
        return

    operation = request.get("operation")
    response = {}

    if operation == "LIST":
        films = state.get_films()
        response = {"status": "OK", "films": films}
        send_to_client(response, address)
    elif operation == "ADD_REVIEW":
        film_id = request.get("film_id")
        review = request.get("review")
        success = state.add_review(film_id, review)
        if not success:
            response = {"status": "ERROR", "message": f"Erro ao adicionar review ao filme {film_id}"}
        else:
            response = {"status": "OK", "message": f"Review adicionada ao filme {film_id}"}
        send_to_client(response, address)
    else:
        response = {"status": "ERROR", "message": "Operação desconhecida"}

    return response


def shutdown():
    """
    Encerra o servidor.
    """

    pass


def main() -> None:
    """
    Função principal do servidor.
    """
    # Coleta os argumentos da linha de comando
    if (len(sys.argv) != 4):
        print("Uso: python server.py <debug> <id> <config>")
        sys.exit(1)

    server_id = sys.argv[2]
    config = read_config(sys.argv[3])
    multicast_config = config["multicast"]

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
        debug=DEBUG,
        initial_leader_id=multicast_config["leader_id"],
        initial_peer_servers={k: v for k, v in servers_config.items() if k != server_id}
    )

    # Inicia os threads para UDP, TCP e heartbeat
    threading.Thread(target=start_udp_multicast, args=(multicast_config,), daemon=True).start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down server...")

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