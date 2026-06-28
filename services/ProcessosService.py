from tipos.EstadoProcesso import EstadoProcesso
from services.MemoriaService import MemoriaService
from services.FilaService import FilaService
from services.RecursoService import RecursoService
from typing import Optional
from dataclasses import dataclass
from tipos.Processo import Processo

import sys


@dataclass
class ProcessosService:
    """Gerencia processos e executa "processamento" da CPU"""
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
        self.referencias_paginas: dict[int, list[int]] = {}
        self.processos_finalizados: list[Processo] = []
        self.processos_aguardando_recursos: list[Processo] = []

    def criar_processo(self, processo: Processo) -> bool:
        """
        Cria processo e checa se todos os recursos estão disponíveis. Se estiverem,
        insere na fila de prontos, caso contrário, insere na fila de bloqueados.
        """

        # Pré-carga de 1 página
        refs = self.referencias_paginas.get(processo.pid, [])
        pagina_inicial = refs[0] if refs else 0

        # Checa se há memória disponível
        is_memoria_alocada: bool = self.memoria_service.alocar(
            processo.pid,
            processo.working_set_len,
            processo.is_tempo_real,
            pagina_inicial
        )
        if not is_memoria_alocada:
            self._bloquear_processo(processo, "memória insuficiente")
            return False

        # Se não for processo de tempo real, tenta alocar recursos pedidos
        if not processo.is_tempo_real and processo.is_requesting_recursos:
            is_recursos_alocados: bool = self.recurso_service.alocar(
                processo.pid,
                processo.requisicao_impressora,
                processo.requisicao_scanner,
                processo.requisicao_modem,
                processo.requisicao_disco
            )
            if not is_recursos_alocados:
                # Libera memória já alocada antes de bloquear
                self.memoria_service.liberar(processo.pid)
                self._bloquear_processo(processo, "recursos de E/S indisponíveis")
                return False

        # Verificou acesso aos recursos
        processo.estado = EstadoProcesso.PRONTO

        is_inserido: bool = self.fila_service.inserir_processo_fila_pronto(processo)
        if not is_inserido:
            self.memoria_service.liberar(processo.pid)
            if not processo.is_tempo_real and processo.is_requesting_recursos:
                self.recurso_service.liberar(processo.pid)
            self._bloquear_processo(processo, "fila de escalonamento cheia")
            return False

        if processo in self.processos_aguardando_recursos:
            self.processos_aguardando_recursos.remove(processo)

        self.processos_ativos[processo.pid] = processo

        # Como as filas foram alteradas, força verificação de prioridades
        # Processo é reinserido com menor prioridade seguindo o diagrama da especificação
        if self.processo_executando is not None:
            if self.fila_service.deve_preemptar(self.processo_executando):
                self.fila_service.reinserir_processo_preemptado(self.processo_executando)
                self.processo_executando = None

        return True

    def tick(self) -> Optional[Processo]:
        """Simula tick e processamento da CPU"""
        if self.processo_executando is None:
            self.processo_executando = self.fila_service.selecionar_pronto()

            if self.processo_executando is None:
                return None

            self.processo_executando.estado = EstadoProcesso.EXECUTANDO

        processo: Processo = self.processo_executando
        processo.tempo_executado += 1

        self._processar_ref_pag(processo)

        if processo.tempo_executado >= processo.tempo_processador:
            self._finalizar_processo(processo)
            return processo

        # Preempção em processos de usuario
        if not processo.is_tempo_real:
            processo.estado = EstadoProcesso.PRONTO
            self.fila_service.reinserir_processo_preemptado(processo)
            self.processo_executando = None

        return processo

    def _finalizar_processo(self, processo: Processo) -> None:
        """Remove o processo da CPU e libera todos os seus recursos."""
        processo.estado = EstadoProcesso.FINALIZADO

        # Libera memória e recursos
        self.memoria_service.liberar(processo.pid)
        if not processo.is_tempo_real and processo.is_requesting_recursos:
            self.recurso_service.liberar(processo.pid)

        self.processos_finalizados.append(processo)
        self.processos_ativos.pop(processo.pid, None)
        self.processo_executando = None

        self._reavaliar_bloqueados()

    def _reavaliar_bloqueados(self) -> None:
        """Avalia os processos bloqueados"""
        if not self.processos_aguardando_recursos:
            return

        for processo in list(self.processos_aguardando_recursos):
            self.criar_processo(processo)

    def _bloquear_processo(self, processo: Processo, motivo: str) -> None:
        """Bloqueia processo, inserindo na lista de bloqueados"""
        processo.estado = EstadoProcesso.BLOQUEADO
        if processo not in self.processos_aguardando_recursos:
            self.processos_aguardando_recursos.append(processo)

    def _processar_ref_pag(self, processo: Processo) -> None:
        """Processa referência de página para o tick"""
        refs: list[int] = self.referencias_paginas.get(processo.pid, [])
        if not refs:
            return

        # Índice na string de referência = ticks executados - 1 (base 0)
        index: int = processo.tempo_executado - 1

        if index >= len(refs):
            return

        pagina: int = refs[index]

        is_page_fault: bool = self.memoria_service.referenciar_pagina(processo.pid, pagina)

        if is_page_fault:
            processo.page_faults += 1
