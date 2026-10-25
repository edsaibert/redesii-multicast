# ======================
# Eduarda Saibert - 20232368
# Modificado em 25/10/26
# ======================

from datetime import datetime
import tomllib

# ======================

# Globais
DEBUG = None

# ======================
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
    global DEBUG, SERVER_ID
    if DEBUG:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[SERVER: {SERVER_ID}] [{timestamp}] {message}")