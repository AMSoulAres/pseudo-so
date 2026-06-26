from dataclasses import dataclass
from modules import gerenciador_filas
from modules import gerenciador_filas
import sys
from pathlib import Path
from typing import Optional
from tipos.Processo import Processo

_CAMPOS_POR_LINHA: int = 8
_PRIORIDADE_MIN: int = 0
_PRIORIDADE_MAX: int = 3

def carregar_processos(caminho_arquivo: str) -> list[Processo]:
    path = Path(caminho_arquivo)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path.resolve()}")
    
    processos: list[Processo] = []
    pid_sequencial: int = 0

    with path.open(mode="r", encoding="utf-8") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            processo = _parse_linha_processo(linha, pid_sequencial, numero_linha)
            if processo is not None:
                processos.append(processo)
                pid_sequencial += 1

    if not processos:
        print(
            f"[WARN] Nenhum processo válido encontrado em '{path}'.",
            file=sys.stderr,
        )

   #Teste TODO: APAGAR
    for processo in processos:
        print(processo)

    return processos

def carregar_refs_paginas(caminho_arquivo: str) -> list[int]:
    # TODO: REVISAR (DEVE TA ERRADO)
    path = Path(caminho_arquivo)
    if not path.is_file():
        return {}

    referencias_por_pid: dict[int, list[int]] = {}
    pid: int = 0

    with path.open(mode="r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            clean_line: str = linha.strip()
            if not clean_line or clean_line.startswith("#"):
                continue
    try:
        paginas: list[int] = [
                    int(ref.strip())
                    for ref in clean_line.split(",")
                    if ref.strip()
                ]
        referencias_por_pid[pid] = paginas
        pid += 1
    except ValueError:
        print(
            f"[WARN] Formato inválido na linha {pid + 1} "
                    f"do arquivo de referências: '{path}'.",
            file=sys.stderr,
        )
        referencias_por_pid[pid] = []
        pid += 1

    return referencias_por_pid

def carregar_ops_arquivos(caminho_arquivo: str) -> list[dict[str, object]]:

    # TODO: REVISAR (DEVE TA ERRADO)
    caminho: Path = Path(caminho_arquivo)

    if not caminho.is_file():
        return None

    linhas: list[str] = []
    with caminho.open(mode="r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha_limpa: str = linha.strip()
            if linha_limpa and not linha_limpa.startswith("#"):
                linhas.append(linha_limpa)

    if len(linhas) < 2:
        print(
            f"[AVISO] Arquivo de operações incompleto: '{caminho}'.",
            file=sys.stderr,
        )
        return None

    try:
        tamanho_disco: int = int(linhas[0])
        num_segmentos: int = int(linhas[1])
    except ValueError:
        print(
            f"[AVISO] Formato inválido nas linhas 1-2 de '{caminho}'.",
            file=sys.stderr,
        )
        return None

    # Parseia arquivos iniciais (segmentos ocupados)
    arquivos_iniciais: list[tuple[str, int, int]] = []
    idx: int = 2
    for i in range(num_segmentos):
        if idx + i >= len(linhas):
            break
        campos = [c.strip() for c in linhas[idx + i].split(",")]
        if len(campos) >= 3:
            nome: str = campos[0]
            bloco_inicio: int = int(campos[1])
            tamanho: int = int(campos[2])
            arquivos_iniciais.append((nome, bloco_inicio, tamanho))

    # Parseia operações de arquivo
    operacoes: list[tuple[int, int, str, int]] = []
    idx_ops: int = 2 + num_segmentos
    for i in range(idx_ops, len(linhas)):
        campos = [c.strip() for c in linhas[i].split(",")]
        if len(campos) >= 3:
            pid_op: int = int(campos[0])
            codigo_op: int = int(campos[1])
            nome_arq: str = campos[2]
            num_blocos_op: int = int(campos[3]) if len(campos) >= 4 else 0
            operacoes.append((pid_op, codigo_op, nome_arq, num_blocos_op))

    return DadosSistemaArquivos(
        tamanho_disco=tamanho_disco,
        arquivos_iniciais=arquivos_iniciais,
        operacoes=operacoes,
    )

def _parse_linha_processo(linha: str, pid: int, num_linha: int) -> Optional[Processo]:
    clean_line = linha.strip()
    if not clean_line or clean_line.startswith("#"):
        return None

    campos: list[str] = [campo.strip() for campo in clean_line.split(",")]

    if len(campos) != _CAMPOS_POR_LINHA:
        raise ValueError(
            f"Linha {num_linha}: Esperados {_CAMPOS_POR_LINHA} campos, "
            f"encontrados {len(campos)}"
        )
    
    try:
        valores: list[int] = [int(campo) for campo in campos]
    except ValueError as erro:
        raise ValueError(
            f"Linha {num_linha}: Campo não-numérico encontrado. "
            f"Conteúdo: '{clean_line}'"
        ) from erro

    tempo_init, prioridade, tempo_cpu, working_set_len, imp, scan, modem, disco = valores
    
    if not (_PRIORIDADE_MIN <= prioridade <= _PRIORIDADE_MAX):
        raise ValueError(
            f"Linha {num_linha}: Prioridade inválida. Deve estar entre "
            f"{_PRIORIDADE_MIN} e {_PRIORIDADE_MAX}, mas foi "
            f"encontrada {prioridade}."
        )

    if tempo_cpu <= 0:
        raise ValueError(
            f"Linha {num_linha}: tempo de processador deve ser > 0, "
            f"recebido {tempo_cpu}."
        )
    
    return Processo(
        pid, 
        prioridade, 
        tempo_init, 
        tempo_cpu, 
        working_set_len, 
        imp, 
        scan, 
        modem, 
        disco
    )
       
@dataclass
class DadosSistemaArquivos:
    tamanho_disco: int
    arquivos_iniciais: list[tuple[str, int, int]]
    operacoes: list[tuple[int, int, str, int]]