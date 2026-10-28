# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

import threading
from helpers import configure_debug, debug_print

# ======================
# Constantes
SERVER_ID = None
SERVER_IP = None
SERVER_TCP_PORT = None

# Variáveis
leader_id = None
peer_servers = {}

# Variáveis do domínio do servidor (simulam um banco de dados)
films = [
    {
        "id": 1,
        "title": "Devoradores de Estrelas",
        "year": None,
        "genre": None,
        "reviews": []
    },
    {
        "id": 2,
        "title": "Resident Evil",
        "year": None,
        "genre": None,
        "reviews": []
    },
    {
        "id": 3,
        "title": "Blade Runner",
        "year": None,
        "genre": None,
        "reviews": []
    },
    {
        "id": 4,
        "title": "Interestelar",
        "year": None,
        "genre": None,
        "reviews": []
    }
]

# Lock
lock = threading.Lock()
# ======================

def init_state(server_id: str, server_ip: str, server_tcp_port: int,
               debug: bool, initial_leader_id: str, initial_peer_servers: dict) -> None:
    global SERVER_ID, SERVER_IP, SERVER_TCP_PORT
    global leader_id, peer_servers

    with lock:
        SERVER_ID = server_id
        SERVER_IP = server_ip
        SERVER_TCP_PORT = server_tcp_port
        configure_debug(debug, server_id)
        leader_id = str(initial_leader_id)
        peer_servers = initial_peer_servers.copy()
    
    debug_print(f"Estado inicializado")


def set_leader(new_leader_id: str) -> None:
    global leader_id

    with lock:
        leader_id = str(new_leader_id)

    debug_print(f"Líder atualizado para: {new_leader_id}")


def get_leader() -> str:
    with lock:
        return leader_id


def is_leader() -> bool:
    with lock:
        return SERVER_ID == leader_id


def get_peer_servers() -> dict:
    with lock:
        return peer_servers.copy()


def set_peer_servers(new_peer_servers: dict) -> None:
    global peer_servers

    with lock:
        peer_servers = new_peer_servers.copy()

def get_films() -> list:
    with lock:
        return films.copy()

def add_review(film_id: int, review: dict) -> bool:
    with lock:
        for film in films:
            if film["id"] == film_id:
                film["reviews"].append(review)
                debug_print(f"Review adicionada ao filme {film_id}: {review}")
                return True
    debug_print(f"Filme com ID {film_id} não encontrado. Review não adicionada.")
    return False