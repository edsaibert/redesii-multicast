# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 04/11/26
# ======================

import argparse
import json
import threading
from collections.abc import Callable

import src.state as state
from src.helpers import configure_debug, debug_print, read_config
from src import tcp_server, udp_server
from src.state import get_leader

failure_t = 0
routes: dict[tuple[str, str], Callable[[dict], dict]] = {}


def _response(status: str, **data: object) -> dict:
    """
    Cria uma resposta padronizada para requisições.
    """
    return {
        "response": {
            "status": status,
            "server_id": state.get_server_id(),
            "server_address": state.get_server_ip(),
            "server_port": state.get_server_tcp_port(),
            **data,
        }
    }


def route(method: str, resource: str):
    """
    Decorador para registrar handlers de requisições.
    """
    def decorator(handler: Callable[[dict], dict]) -> Callable[[dict], dict]:
        routes[(method.upper(), resource)] = handler
        return handler

    return decorator


def get(resource: str):
    """
    Decorador para registrar handlers de requisições GET.
    """
    return route("GET", resource)


def post(resource: str):
    """
    Decorador para registrar handlers de requisições POST.
    """
    return route("POST", resource)


@get("films")
def get_films(request: dict) -> dict:
    resource_id = request.get("resource_id")
    if resource_id is None:
        return _response("OK", films=state.get_films())

    film = state.get_film(resource_id)
    if not film:
        return _response(
            "ERROR",
            message=f"Filme com ID {resource_id} não encontrado",
        )
    return _response("OK", film=film)


@post("films")
def add_review(request: dict) -> dict:
    resource_id = request.get("resource_id")
    body = request.get("body", {})
    review = body.get("content")

    if not state.get_film(resource_id):
        return _response(
            "ERROR",
            message=f"Filme com ID {resource_id} não encontrado",
        )

    replication_body = {"resource_id": resource_id, "content": review}
    if not tcp_server.replicate_post_to_peers(replication_body):
        return _response(
            "ERROR",
            message="Falha ao replicar alteração nos servidores ativos",
        )

    if not state.add_review(resource_id, review):
        return _response(
            "ERROR",
            message=f"Erro ao adicionar review ao filme {resource_id}",
        )
    return _response("OK", message=f"Review adicionada ao filme {resource_id}")


@post("replicate-post")
def replicate_post(request: dict) -> dict:
    if str(request.get("server_id")) != str(get_leader()):
        return _response("ERROR", message="Apenas o líder pode replicar alterações")

    resource_id = request.get("resource_id")
    review = request.get("body", {}).get("content")
    if not state.add_review(resource_id, review):
        return _response(
            "ERROR",
            message=f"Erro ao adicionar review ao filme {resource_id}",
        )
    return _response("OK", message=f"Review adicionada ao filme {resource_id}")


@post("heartbeat")
def heartbeat(request: dict) -> dict:
    tcp_server.process_heartbeat(request.get("server_id"), failure_t)
    return _response("OK")


def process_server_message(message: dict) -> dict:
    """Processa mensagens recebidas de outros servidores."""
    method = message.get("method")
    resource = message.get("resource")
    handler = routes.get((method, resource))
    if handler is None:
        return _response(
            "ERROR",
            message=f"Recurso não encontrado: {method} {resource}",
        )

    try:
        return handler(message)
    except Exception as error:
        debug_print(f"Erro ao processar {method} {resource}: {error}")
        return _response("ERROR", message="Erro interno ao processar requisição")
        

def process_client_message(message: str, address: tuple) -> dict:
    """Despacha uma requisição para o handler do método e recurso."""
    request = json.loads(message)

    if not state.is_leader():
        debug_print(f"Servidor não é líder. Requisição recebida de {address}")
        return {}

    method = request.get("method")
    resource = request.get("resource")
    handler = routes.get((method, resource))
    if handler is None:
        return _response(
            "ERROR",
            message=f"Recurso não encontrado: {method} {resource}",
        )

    try:
        return handler(request)
    except Exception as error:
        debug_print(f"Erro ao processar {method} {resource}: {error}")
        return _response("ERROR", message="Erro interno ao processar requisição")


def main() -> None:
    """Função principal do servidor."""
    global failure_t

    parser = argparse.ArgumentParser(description="Servidor multicast")
    parser.add_argument("-d", "--debug", action="store_true", help="ativa as mensagens de debug")
    parser.add_argument("server_id", help="identificador do servidor")
    parser.add_argument("config_path", help="caminho para o arquivo config.toml")
    args = parser.parse_args()

    config = read_config(args.config_path)
    multicast_config = config["multicast"]
    configure_debug(args.debug, args.server_id)

    servers_config = {
        str(server_id): {
            "ip": server_config["ip"],
            "tcp_port": server_config["tcp_port"],
            "heartbeats_to_die": config["failure_t"],
        }
        for server_id, server_config in config["servers"].items()
    }
    failure_t = config["failure_t"]

    state.init_state(
        server_id=args.server_id,
        server_ip=servers_config[str(args.server_id)]["ip"],
        server_tcp_port=servers_config[str(args.server_id)]["tcp_port"],
        debug=args.debug,
        initial_leader_id=str(multicast_config["leader_id"]),
        initial_peer_servers={
            key: value for key, value in servers_config.items() if key != args.server_id
        },
    )

    threading.Thread(
        target=udp_server.start_udp_multicast,
        args=(multicast_config, process_client_message),
        daemon=True,
    ).start()
    threading.Thread(
        target=tcp_server.start_tcp,
        args=(servers_config[state.get_server_id()], process_server_message),
        daemon=True,
    ).start()
    threading.Thread(
        target=tcp_server.heartbeat,
        args=(servers_config, config["heartbeat_t"]),
        daemon=True,
    ).start()
    threading.Thread(
        target=tcp_server.discount_heartbeat,
        args=(config["heartbeat_t"],),
        daemon=True,
    ).start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down server...")


if __name__ == "__main__":
    main()
