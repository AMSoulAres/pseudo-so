from tipos.Processo import Processo
from utils.parsers import carregar_processos
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

if __name__ == "__main__":
    main()