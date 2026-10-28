# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

from datetime import datetime
import tomllib

# ======================

# Globais
DEBUG = None
SERVER_ID = None

# ======================

def configure_debug(enabled: bool, server_id=None) -> None:
    """
    Configura a saída de debug e o identificador exibido nas mensagens.
    """
    global DEBUG, SERVER_ID
    DEBUG = enabled
    SERVER_ID = server_id


def read_config(path: str) -> dict:
    """
    Lê o arquivo de configuração TOML e retorna um dicionário com as configurações.
    """
    with open(path, "rb") as f:
        return tomllib.load(f)

def debug_print(message: str) -> None:
    """
    Imprime mensagens de debug se a flag DEBUG estiver ativada.
    """
    if DEBUG:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        source = f"SERVER: {SERVER_ID}" if SERVER_ID is not None else "CLIENT"
        print(f"[{source}] [{timestamp}] {message}")