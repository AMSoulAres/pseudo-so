from services.Dispatcher import Dispatcher
from tipos.Processo import Processo
from helpers.parsers import carregar_processos, carregar_refs_paginas, carregar_ops_arquivos
import sys

def main() -> None:
    caminho_processos: str = sys.argv[1]
    caminho_arquivos: str = sys.argv[2]
    caminho_string: str = sys.argv[3]

    try:
        processos: list[Processo] = carregar_processos(caminho_processos)
    except FileNotFoundError as e:
        print(f"Erro ao carregar processos: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Erro ao carregar processos: {e}", file=sys.stderr)
        sys.exit(1)

    if not processos:
        print("[WARN] Sem processos para serem executados")
        sys.exit(0)

    referencias_paginas: dict[int, list[int]] = carregar_refs_paginas(caminho_string)
    dados_sistema_arquivos: list[dict[str, object]] = carregar_ops_arquivos(caminho_arquivos)

    dispatcher: Dispatcher = Dispatcher(processos, referencias_paginas, dados_sistema_arquivos)
    dispatcher.main_loop()

if __name__ == "__main__":
    main()