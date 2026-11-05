# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 31/10/26
# ======================

import time
import threading
import json
import state
import threading
import socket
import application
import argparse
from state import set_leader, get_peer_servers, peer_servers, remove_peer_server, get_server_id, get_leader
from helpers import configure_debug, read_config, debug_print

lock = threading.Lock()

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

# Tratamento de TCP
def handle_tcp_message(client: socket.socket) -> None:
    """
    Trata uma conexao TCP
    """

    data = client.recv(4096)

    if data:
        state.debug_print(f"Mensagem recebida de: {data}")
        request = json.loads(data.decode("utf-8"))

        state.debug_print(f"Processando mensagem do servidor: {request}, resposta: {request}")
        process_server_message(request)

    shutdown(client)

def start_tcp(server_config: dict) -> None:
    """
    Inicia o servidor TCP.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((server_config["ip"], server_config["tcp_port"]))

    sock.listen(5)

    state.debug_print(f"Servidor {get_server_id()}: servidor TCP iniciado")
    while True:
        client, addr = sock.accept()

        client_handler = threading.Thread(target = handle_tcp_message, args = (client,))
        client_handler.start()

def connect_to_servers(target_host: str, target_port: int):
    """
    Conecta-se aos servidores vizinhos.
    """

    state.debug_print(f"Iniciando conexão com servidor {target_host}: porta {target_port}")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.settimeout(2)
    try:
        client.connect((target_host, target_port))
        return client
    except:
        return None

# Heartbeat

def heartbeat(servers_config: dict, time_sec: int):
    """
    Envia um heartbeat para os outros servidores.
    """
    
    request = {
        "operation": "HEARTBEAT",
        "server_id": str(get_server_id()),
    }

    request_msg = json.dumps(request).encode("utf-8")

    while True:
        time.sleep(time_sec)

        try: 
            server_id = get_server_id()
            servers = get_peer_servers()
            if servers:
                for v in servers:
                    if (v != server_id):
                        k = servers[v]
                        state.debug_print(f"Iniciando envio de Heartbeat para servidor {k["ip"]}, id {v} e porta {k["tcp_port"]}")
                        sock = connect_to_servers(k["ip"], k["tcp_port"])

                        if sock:
                            sock.send(request_msg)  
                            state.debug_print(f"Encerrando envio de Heartbeat para servidor {k["ip"]}, id {v} e porta {k["tcp_port"]}")
                            shutdown(sock)
                        else:
                            state.debug_print(f"Não foi possível enviar Heartbeat para o servidor em {k["ip"]}, id{v} e porta {k["tcp_port"]}")
            else:
                state.debug_print(f"Não há mais outros servidores vivos, desligando Heartbeat")
                return
        except:
            state.debug_print(f"Ocorreu um erro não identificado na comunicação.")
            continue

def process_heartbeat(heartbeat_server_id: int, failure_t: int) -> bool:
    """
    Processa o recebimento de um heartbeat
    """

    with lock:
        state.debug_print(f"Processando Heartbeat do servidor de id {heartbeat_server_id}")
        if (heartbeat_server_id == get_server_id()):
            return True

        peer = get_peer_servers()
        server = peer[str(heartbeat_server_id)]
        if (server["heartbeats_to_die"] <= 0):
            return False

        server["heartbeats_to_die"] = failure_t
        return True

def discount_heartbeat(time_sec: int) -> None:
    """
    Reduz a quantidade de heartbeats necessarios para os servidores serem considerados mortos e remove os mortos
    """

    while True:
        time.sleep(time_sec)
        peers_to_remove = []

        with lock:
            peers = get_peer_servers()
            for k in peers:
                v = peers[k]
                v["heartbeats_to_die"] = v["heartbeats_to_die"] - 1
                if v["heartbeats_to_die"] <= 0:
                    peers_to_remove.append(k)

            leader_removed = False
            for k in peers_to_remove:
                if (k == get_leader()):
                    leader_removed = True

                state.debug_print(f"Servidor de id {k} irresponsivo, removendo ele da lista de peers")
                remove_peer_server(k)
            
            if leader_removed:
                elect_leader()

# Eleicao de lider

def elect_leader():
    """
    Inicia o processo de eleição do líder.
    """

    peer = get_peer_servers()
    leader = get_server_id()

    for v in peer:
        if (int(v) < int(leader)):
            leader = v

    state.debug_print(f"Elegendo como líder o servidor de id {leader}")
    set_leader(leader)

# Processamento de mensagens

def process_server_message(message: str):
    """
    Processa mensagens recebidas de outros servidores.
    """

    operation = message.get("operation")
    response = {}

    if operation == "REPLICATE_POST":
        if str(message.get("server_id")) != str(get_leader()):
            return {
                "status": "ERROR",
                "message": "Apenas o líder pode replicar alterações",
            }

        body = message.get("body", {})
        film_id = body.get("resource_id")
        review = body.get("content")
        success = state.add_review(film_id, review)

        if not success:
            response = {"status": "ERROR", "message": f"Erro ao adicionar review ao filme {film_id}"}
            return response
        
        response = {"status": "OK", "message": f"Review adicionada ao filme {film_id}"}
        return response

    if operation == "HEARTBEAT":
        heartbeat_server_id = message.get("server_id")
        process_heartbeat(heartbeat_server_id, failure_t)

    response = {"status": "ERROR", "message": "Operação desconhecida"}
    return response


def replicate_post_to_peers(body: dict) -> bool:
    """
    Replica uma alteração em todos os servidores ativos.
    """
    for peer_id, peer in get_peer_servers().items():
        try:
            sock = connect_to_servers(peer["ip"], peer["tcp_port"])
            if sock is None:
                return False

            request = {
                "operation": "REPLICATE_POST",
                "server_id": str(get_server_id()),
                "body": body,
            }
            sock.sendall(json.dumps(request).encode("utf-8"))
            shutdown(sock)
        except (KeyError, OSError):
            return False

        state.debug_print(f"Alteração enviada ao servidor {peer_id}")

    return True


# Encerramento de socket

def process_client_message(message: str, address: tuple):
    """
    Processa mensagens recebidas de clientes.
    """
    request = json.loads(message)

    if not state.is_leader():
        debug_print(f"Servidor não é líder. Ignorando mensagem do cliente {address}")
        return

    operation = request.get("operation")
    body = request.get("body", {})
    response = {}

    if operation == "GET":
        try:
            resource_id = body.get("resource_id")
            if resource_id is None:
                films = state.get_films()
                response = {"status": "OK", "films": films}
                return response

            film = state.get_film(resource_id)
            if not film:
                response = {"status": "ERROR", "message": f"Filme com ID {resource_id} não encontrado"}
                return response

            response = {"status": "OK", "film": film}
            return response
        except Exception as e:
            debug_print(f"Erro ao processar GET: {e}")
            response = {"status": "ERROR", "message": "Erro ao processar GET"}
            return response

    elif operation == "POST":
        film_id = body.get("resource_id")
        review = body.get("content")
        success = state.add_review(film_id, review)
        if not success:
            response = {"status": "ERROR", "message": f"Erro ao adicionar review ao filme {film_id}"}
            return response

        if not replicate_post_to_peers(body):
            return {
                "status": "ERROR",
                "message": "Falha ao replicar alteração nos servidores ativos",
            }

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
            "heartbeats_to_die": config["failure_t"],
        }
        for server_id, server_config in config["servers"].items()
    }

    global failure_t 
    failure_t = config["failure_t"]
    
    state.init_state(
        server_id=server_id,
        server_ip=servers_config[str(server_id)]["ip"],
        server_tcp_port=servers_config[str(server_id)]["tcp_port"],
        debug=debug_enabled,
        initial_leader_id=str(multicast_config["leader_id"]),
        initial_peer_servers={k: v for k, v in servers_config.items() if k != server_id}
    )

    # Inicia os threads para UDP, TCP e heartbeat
    # threading.Thread(target=start_udp_multicast, args=(multicast_config,), daemon=True).start()
    threading.Thread(target=start_tcp, args=(servers_config[get_server_id()] ,), daemon=True).start()
    threading.Thread(target=heartbeat, args=(servers_config, config["heartbeat_t"], ), daemon=True).start()
    threading.Thread(target=discount_heartbeat, args=(config["heartbeat_t"], ), daemon=True).start()

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
