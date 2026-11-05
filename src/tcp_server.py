import json
import socket
import threading
import time
from collections.abc import Callable

import src.application as application
import src.state as state
from src.helpers import debug_print
from src.state import (
    get_leader,
    get_peer_servers,
    get_server_id,
    remove_peer_server,
    set_leader,
)

lock = threading.Lock()


def shutdown(sock: socket.socket, warn: bool = False) -> None:
    """Encerra o socket do servidor."""
    try:
        if warn:
            sock.shutdown(socket.SHUT_RDWR)
    finally:
        sock.close()


def connect_to_servers(target_host: str, target_port: int) -> socket.socket | None:
    """Conecta-se a um servidor vizinho."""
    state.debug_print(f"Iniciando conexão com servidor {target_host}: porta {target_port}")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    try:
        client.connect((target_host, target_port))
        return client
    except OSError:
        shutdown(client)
        return None


def handle_tcp_message(
    client: socket.socket,
    address: tuple,
    process_message: Callable[[dict], dict],
) -> None:
    """Recebe e processa mensagens de uma conexão TCP."""
    try:
        while True:
            data = client.recv(4096)
            if not data:
                return

            request = json.loads(data.decode("utf-8"))
            state.debug_print(f"Processando mensagem do servidor {address}: {request}")
            response = process_message(request)
            if response:
                client.sendall((json.dumps(response) + "\n").encode("utf-8"))
    except (ConnectionError, OSError, json.JSONDecodeError) as error:
        debug_print(f"Erro na conexão TCP com {address}: {error}")
    finally:
        shutdown(client)


def start_tcp(
    server_config: dict,
    process_message: Callable[[dict], dict],
) -> None:
    """Inicia o servidor TCP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((server_config["ip"], server_config["tcp_port"]))
    sock.listen(5)

    state.debug_print(f"Servidor {get_server_id()}: servidor TCP iniciado")
    while True:
        client, address = sock.accept()
        threading.Thread(
            target=handle_tcp_message,
            args=(client, address, process_message),
            daemon=True,
        ).start()


def heartbeat(servers_config: dict, time_sec: int) -> None:
    """Envia heartbeats para os outros servidores."""
    request = {
        "operation": "HEARTBEAT",
        "server_id": str(get_server_id()),
    }
    request_msg = json.dumps(request).encode("utf-8")
    connections = {}

    while True:
        time.sleep(time_sec)
        server_id = get_server_id()
        servers = get_peer_servers()
        if not servers:
            state.debug_print("Não há mais outros servidores vivos, desligando Heartbeat")
            return

        for peer_id, peer in servers.items():
            if peer_id == server_id:
                continue

            sock = connections.get(peer_id)
            if sock is None:
                sock = connect_to_servers(peer["ip"], peer["tcp_port"])
                if sock is None:
                    state.debug_print(f"Não foi possível conectar ao servidor {peer_id}")
                    continue
                connections[peer_id] = sock

            try:
                sock.sendall(request_msg)
            except ConnectionError:
                shutdown(sock)
                connections.pop(peer_id, None)


def process_heartbeat(heartbeat_server_id: int, failure_t: int) -> bool:
    """Processa o recebimento de um heartbeat."""
    with lock:
        state.debug_print(f"Processando Heartbeat do servidor de id {heartbeat_server_id}")
        if heartbeat_server_id == get_server_id():
            return True

        server = get_peer_servers()[str(heartbeat_server_id)]
        if server["heartbeats_to_die"] <= 0:
            return False

        server["heartbeats_to_die"] = failure_t
        return True


def discount_heartbeat(time_sec: int) -> None:
    """Remove os servidores que não enviaram heartbeats a tempo."""
    while True:
        time.sleep(time_sec)
        peers_to_remove = []

        with lock:
            peers = get_peer_servers()
            for peer_id, peer in peers.items():
                peer["heartbeats_to_die"] -= 1
                if peer["heartbeats_to_die"] <= 0:
                    peers_to_remove.append(peer_id)

            leader_removed = False
            for peer_id in peers_to_remove:
                if peer_id == get_leader():
                    leader_removed = True
                state.debug_print(
                    f"Servidor de id {peer_id} irresponsivo, removendo ele da lista de peers"
                )
                remove_peer_server(peer_id)

            if leader_removed:
                elect_leader()


def elect_leader() -> None:
    """Inicia o processo de eleição do líder."""
    leader = get_server_id()
    for peer_id in get_peer_servers():
        if int(peer_id) < int(leader):
            leader = peer_id

    state.debug_print(f"Elegendo como líder o servidor de id {leader}")
    set_leader(leader)


def replicate_post_to_peers(body: dict) -> bool:
    """Replica uma alteração em todos os servidores ativos."""
    for peer_id, peer in get_peer_servers().items():
        try:
            sock = connect_to_servers(peer["ip"], peer["tcp_port"])
            if sock is None:
                return False

            response = application.replicate_post(
                sock,
                str(get_server_id()),
                body["resource_id"],
                body["content"],
            )
            shutdown(sock)
            response_body = response.get("response", {})
            if response_body.get("status") != "OK":
                state.debug_print(
                    f"Falha ao replicar alteração no servidor {peer_id}: "
                    f"{response_body.get('message')}"
                )
                return False
        except Exception as error:
            state.debug_print(f"Erro ao replicar alteração no servidor {peer_id}: {error}")
            return False

        state.debug_print(f"Alteração confirmada pelo servidor {peer_id}")
    return True
