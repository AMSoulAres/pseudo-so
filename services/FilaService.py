from typing import Optional
from tipos.EstadoProcesso import EstadoProcesso
from tipos.Processo import Processo
from collections import deque
from dataclasses import dataclass

# Constantes de escalonamento
QUANTUM: int = 1
LIMIAR_AGING: int = 5  # Tempo para aplicar aging e aumentar prioridade
LIMITE_TAMANHO_FILA: int = 1000


@dataclass
class FilaService:
    def __init__(self) -> None:
        self.filas: dict[int, deque[Processo]] = {
            0: deque(), # Tempo real
            1: deque(), # Usuário - Alto
            2: deque(), # Usuário - Médio
            3: deque()  # Usuário - Baixo
        }
        # Fila global só para controle
        self.fila_global: deque[Processo] = deque()
        self.quantum: int = QUANTUM
        

    def inserir_processo_fila_pronto(self, processo: Processo) -> bool:
        """Insere processo na fila global e na fila de prioridade correspondente"""
        if len(self.fila_global) >= LIMITE_TAMANHO_FILA:
            return False

        self.fila_global.append(processo)

        if processo.prioridade_atual > 3:
            print(f"WARN: prioridade inválida, pid: {processo.pid}")
            return False
        self.filas[processo.prioridade_atual].append(processo)

        return True

    def deve_preemptar(self, processo_executando: Processo):
        """Verifica se o processo passado é preemptável"""
        if processo_executando.is_tempo_real:
            return False

        # Verifica se existe processo pronto em fila de maior prioridade do que o atual
        for nivel in range(0, processo_executando.prioridade_atual):
            if self.filas[nivel]:
                return True

        return False

    def reinserir_processo_preemptado(self, processo: Processo) -> None:
        """Reinsere processo preemptado (ao menos um quantum executado) na fila, rebaixando a prioridade"""
        processo.prioridade_atual: int = min(processo.prioridade_atual + 1, 3)
        processo.tempo_espera = 0 # Aging no 5
        self.fila_global.append(processo)
        self.filas[processo.prioridade_atual].append(processo)    

    def aplicar_aging(self) -> None:
        """Percorre as listas atualizando a prioridade de cada processo e movendo-os"""
        for nivel_prioridade in range(2, 4):
            processos_promovidos: list[Processo] = []
            processos_mantidos: deque[Processo] = deque()

            for processo in self.filas[nivel_prioridade]:
                processo.tempo_espera += 1

                if processo.tempo_espera >= LIMIAR_AGING:
                    processo.prioridade_atual = nivel_prioridade - 1
                    processo.tempo_espera = 0
                    processos_promovidos.append(processo)
                else:
                    processos_mantidos.append(processo)

            self.filas[nivel_prioridade] = processos_mantidos
            self.filas[nivel_prioridade - 1].extend(processos_promovidos)

    def selecionar_pronto(self) -> Optional[Processo]:
        """Seleciona próximo processo nas filas na ordem 0 -> 1 -> 2 -> 3"""
        for nivel_prioridade in range(0, 4):
            if self.filas[nivel_prioridade]:
                processo = self.filas[nivel_prioridade].popleft()
                self.fila_global.remove(processo)
                return processo
        
        return None
                
                    
    
            