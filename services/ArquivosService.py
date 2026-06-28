from typing import Optional
from helpers.parsers import DadosSistemaArquivos
from tipos.Arquivo import Arquivo
from tipos.Processo import Processo

class ArquivosService:
    def __init__(self, dados: DadosSistemaArquivos):
        self.tamanho_disco: int = dados.tamanho_disco
        self.mapa_disco: list[Optional[str]] = [None] * self.tamanho_disco
        self.arquivos: dict[str, Arquivo] = {}
        self.operacoes: list[tuple[int, int, str, int]] = dados.operacoes
        
        # Inicializar os arquivos já existentes
        for nome, bloco_inicial, tamanho in dados.arquivos_iniciais:
            novo_arquivo = Arquivo(nome, bloco_inicial, tamanho, criador_pid=None)
            self.arquivos[nome] = novo_arquivo
            for i in range(tamanho):
                if bloco_inicial + i < self.tamanho_disco:
                    self.mapa_disco[bloco_inicial + i] = nome

    def _encontrar_espaco(self, tamanho: int) -> int:
        """Encontra o primeiro espaço contíguo de blocos livres usando First-Fit."""
        livres_consecutivos = 0
        bloco_inicio = -1

        for i in range(self.tamanho_disco):
            if self.mapa_disco[i] is None:
                if livres_consecutivos == 0:
                    bloco_inicio = i
                livres_consecutivos += 1
                
                if livres_consecutivos == tamanho:
                    return bloco_inicio
            else:
                livres_consecutivos = 0
                bloco_inicio = -1
                
        return -1

    def executar_operacoes(self, processos_dict: dict[int, Processo]) -> None:
        """Executa a fila de operações ao fim da simulação de CPU."""
        for op_idx, operacao in enumerate(self.operacoes):
            pid, codigo, nome_arq, tamanho = operacao
            numero_operacao = op_idx + 1

            print(f"Operação {numero_operacao} => ", end="")

            processo = processos_dict.get(pid)
            if not processo:
                print(f"Falha\nO processo {pid} não existe.")
                continue
            
            is_tempo_real = processo.prioridade == 0

            # CRIAR (0)
            if codigo == 0:
                if nome_arq in self.arquivos:
                    print(f"Falha\nO processo {pid} não pode criar o arquivo {nome_arq} (já existe).")
                    continue
                
                bloco_inicial = self._encontrar_espaco(tamanho)
                if bloco_inicial != -1:
                    # Sucesso na alocação
                    novo_arquivo = Arquivo(nome_arq, bloco_inicial, tamanho, criador_pid=pid)
                    self.arquivos[nome_arq] = novo_arquivo
                    for i in range(tamanho):
                        self.mapa_disco[bloco_inicial + i] = nome_arq
                    
                    # Cria a string (blocos x, y e z) formatada
                    blocos_str = " e ".join([
                        ", ".join(map(str, range(bloco_inicial, bloco_inicial + tamanho - 1))),
                        str(bloco_inicial + tamanho - 1)
                    ]) if tamanho > 1 else str(bloco_inicial)

                    # Se tamanho == 2, o código acima gera 'x e y', e deixa um comma trailing no inicio se for vazio, 
                    # vamos fazer de um jeito mais limpo:
                    blocos = list(range(bloco_inicial, bloco_inicial + tamanho))
                    if len(blocos) == 1:
                        blocos_str = str(blocos[0])
                    elif len(blocos) == 2:
                        blocos_str = f"{blocos[0]} e {blocos[1]}"
                    else:
                        blocos_str = ", ".join(map(str, blocos[:-1])) + f" e {blocos[-1]}"

                    print(f"Sucesso\nO processo {pid} criou o arquivo {nome_arq} (blocos {blocos_str}).")
                else:
                    print(f"Falha\nO processo {pid} não pode criar o arquivo {nome_arq} (falta de espaço).")

            # DELETAR (1)
            elif codigo == 1:
                arquivo = self.arquivos.get(nome_arq)
                if not arquivo:
                    print(f"Falha\nO processo {pid} não pode deletar o arquivo {nome_arq} porque ele não existe.")
                    continue
                
                # Checagem de permissão
                if not is_tempo_real and arquivo.criador_pid != pid:
                    print(f"Falha\nO processo {pid} não pode deletar o arquivo {nome_arq} porque não tem permissão.")
                    continue
                
                # Sucesso
                del self.arquivos[nome_arq]
                for i in range(arquivo.bloco_inicial, arquivo.bloco_inicial + arquivo.tamanho):
                    self.mapa_disco[i] = None
                print(f"Sucesso\nO processo {pid} deletou o arquivo {nome_arq}.")

        # Imprimir o mapa de ocupação
        print("Mapa de ocupação do disco:")
        mapa_impressao = [bloco if bloco is not None else "0" for bloco in self.mapa_disco]
        print(" ".join(mapa_impressao))
