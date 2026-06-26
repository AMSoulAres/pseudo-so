from tipos.EstadoProcesso import EstadoProcesso
from MemoriaService import MemoriaService
from FilaService import FilaService
from RecursoService import RecursoService
from typing import Optional
from dataclasses import dataclass
from tipos.Processo import Processo

@dataclass
class ProcessosService:
    def __init__(
        self,
        fila_service,
        memoria_service,
        recurso_service
    ) -> None:
        self.fila_service: FilaService = fila_service
        self.memoria_service: MemoriaService = memoria_service
        self.recurso_service: RecursoService = recurso_service

        self.processos_ativos: dict[int, Processo] = {}
        self.processo_executando: Optional[Processo] = None
        self.ticks_no_quantum: int = 0
        self.processos_finalizados: list[Processo] = []
        self.processos_aguardando_recursos: list[Processo] = []

    def criar_processo(self, processo: Processo):
        # Checa se há memória disponível
        is_memoria_alocada: bool = self.memoria_service.alocar(
            processo.pid,
            processo.blocos_memoria,
            processo.is_tempo_real,
        )
        if not is_memoria_alocada:
            self._bloquear_processo(processo, "memória insuficiente")
            return False

        # Se não for processo de tempo real, tenta alocar recursos pedidos
        if not processo.is_tempo_real and processo.is_requesting_recursos:
            #TODO: implementar função de recursos (checar impressora, discos, modem e scanner)
            is_recursos_alocados: bool = self.recurso_service.alocar_recursos(
                processo.pid,
                impressora=processo.requisicao_impressora,
                scanner=processo.requisicao_scanner,
                modem=processo.requisicao_modem,
                disco=processo.requisicao_disco,
            )
            if not is_recursos_alocados:
                # Libera memória já alocada antes de enfileirar
                self.memoria_service.liberar(processo.pid)
                self._bloquear_processo(processo, "recursos de E/S indisponíveis")
                return False
        
        # Insere na fila
        #TODO: Implementar fila
        is_inserido: bool = self.fila_service.insere_processo(processo)
        if not is_inserido:
            self.memoria_service.liberar(processo.pid)
            if not processo.is_tempo_real and processo.is_requesting_recursos:
                # TODO implementar
                self.recurso_service.liberar()
            self._bloquear_processo(processo, "fila de escalonamento cheia")

        # TODO: Avaliar reprocessamento
        
            
        return True

    def finalizar_processo(self, processo: Processo):
        #liberar memoria
        #liberar recursos
        #remover da fila
        return True

    def _bloquear_processo(self, processo: Processo, motivo: str):
        processo.estado = EstadoProcesso.BLOQUEADO
        if processo not in self.processos_aguardando_recursos:
            self.processos_aguardando_recursos.append(processo)
            self._log(
                f"PID {processo.pid}: aguardando recursos ({motivo}). "
                f"Enfileirado para reavaliação."
            )

    def desbloquear_processo(self, processo: Processo):
        #desbloquear na fila
        #remover da fila
        return True