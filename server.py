# ======================
# Eduarda Saibert - 20232368
# Eduardo Munaretto Majczak - 20242288
# Modificado em 31/10/26
# ======================

import argparse
import json
import threading

import src.state as state
from src.helpers import configure_debug, debug_print, read_config
from src import tcp_server, udp_server
from src.state import get_leader

failure_t = 0


def process_server_message(message: dict) -> dict:
    """Processa mensagens recebidas de outros servidores."""
    operation = message.get("operation")

    if operation == "REPLICATE_POST":
        if str(message.get("server_id")) != str(get_leader()):
            return {
                "status": "ERROR",
                "message": "Apenas o líder pode replicar alterações",
            }

        body = message.get("body", {})
        film_id = body.get("resource_id")
        if not state.add_review(film_id, body.get("content")):
            return {
                "status": "ERROR",
                "message": f"Erro ao adicionar review ao filme {film_id}",
            }
        return {"status": "OK", "message": f"Review adicionada ao filme {film_id}"}

    if operation == "HEARTBEAT":
        tcp_server.process_heartbeat(message.get("server_id"), failure_t)

    return {"status": "ERROR", "message": "Operação desconhecida"}


def process_client_message(message: str, address: tuple) -> dict | None:
    """Processa mensagens recebidas de clientes."""
    request = json.loads(message)

    if not state.is_leader():
        debug_print(f"Servidor não é líder. Ignorando mensagem do cliente {address}")
        return None

    operation = request.get("operation")
    body = request.get("body", {})

    if operation == "GET":
        try:
            resource_id = body.get("resource_id")
            if resource_id is None:
                return {"status": "OK", "films": state.get_films()}

            film = state.get_film(resource_id)
            if not film:
                return {
                    "status": "ERROR",
                    "message": f"Filme com ID {resource_id} não encontrado",
                }
            return {"status": "OK", "film": film}
        except Exception as error:
            debug_print(f"Erro ao processar GET: {error}")
            return {"status": "ERROR", "message": "Erro ao processar GET"}

    if operation == "POST":
        film_id = body.get("resource_id")
        if not state.get_film(film_id):
            return {
                "status": "ERROR",
                "message": f"Filme com ID {film_id} não encontrado",
            }

        if not tcp_server.replicate_post_to_peers(body):
            return {
                "status": "ERROR",
                "message": "Falha ao replicar alteração nos servidores ativos",
            }

        if not state.add_review(film_id, body.get("content")):
            return {
                "status": "ERROR",
                "message": f"Erro ao adicionar review ao filme {film_id}",
            }
        return {"status": "OK", "message": f"Review adicionada ao filme {film_id}"}

    return {"status": "ERROR", "message": "Operação desconhecida"}


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
