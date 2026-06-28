from services.RecursoService import RecursoService
from services.MemoriaService import MemoriaService
from helpers.parsers import DadosSistemaArquivos
from typing import Optional
from services.FilaService import FilaService
from services.ProcessosService import ProcessosService
from tipos.Processo import Processo

MAX_TICKS: int = 1_000_000


class Dispatcher:
    """Loop principal que irá simular um clock e a CPU consumindo processos"""
    def __init__(
        self,
        processos: list[Processo],
        referencias_paginas: dict[int, list[int]],
        dados_sistema_arquivos: Optional[DadosSistemaArquivos]
        ) -> None:
        # Ordena processos por ordem de "chegada" (parametrizada no arquivo lido)
        self.processos_pendentes: list[Processo] = sorted(processos, key=lambda p: p.tempo_inicializacao)

        # Injeta services
        self.fila_service: FilaService = FilaService()
        self.memoria_service: MemoriaService = MemoriaService()
        self.arquivos_service = None # TODO: Implementar
        self.recursos_service: RecursoService = RecursoService()
        self.processos_service: ProcessosService = ProcessosService(
            self.fila_service,
            self.memoria_service,
            self.recursos_service)
        self.processos_service.referencias_paginas = referencias_paginas

        self.operacoes_por_pid: dict[int, list[tuple[int, int, str, int]]] = {}
        if dados_sistema_arquivos:
            for op in dados_sistema_arquivos.operacoes:
                pid_op = op[0]
                if pid_op not in self.operacoes_por_pid:
                    self.operacoes_por_pid[pid_op] = []
                self.operacoes_por_pid[pid_op].append(op)

        self.tick: int = 0
        # Qquais processos já tiveram o "dispatcher =>" impresso
        self._processos_despachados: set[int] = set()

    def main_loop(self):
        print(f"  Processos carregados: {len(self.processos_pendentes)}")
        print("=" * 60)

        while self.tick < MAX_TICKS:
            # Processos com tempo de inicialização igual ao tick
            # 1. Recebe processos
            while (
                self.processos_pendentes
                and self.processos_pendentes[0].tempo_inicializacao <= self.tick
            ):
                processo: Processo = self.processos_pendentes.pop(0)
                is_processo_criado: bool = self.processos_service.criar_processo(processo)

                if is_processo_criado:
                    self._log_dispatcher(processo)
                else:
                    print(f"[TICK {self.tick}] Processo PID {processo.pid} não criado.")

            # 2. Aging
            self.fila_service.aplicar_aging()

            # 3. Passa o tick da CPU
            processo_executando: Optional[Processo] = self.processos_service.tick()

            if processo_executando is not None:
                self._log_execucao(processo_executando)

            if self._interromper_execucao():
                break

            self.tick += 1

        self._log_resumo_final()

    def _log_dispatcher(self, processo: Processo) -> None:
        """Impresso na criação — quando o SO admite o processo."""
        print(f"dispatcher =>")
        print(f" PID: {processo.pid}")
        print(f" frames: {processo.working_set_len}")
        print(f" priority: {processo.prioridade}")
        print(f" time: {processo.tempo_processador}")
        print(f" printers: {processo.requisicao_impressora}")
        print(f" scanners: {processo.requisicao_scanner}")
        print(f" modems: {processo.requisicao_modem}")
        print(f" drives: {processo.requisicao_disco}")

    def _log_execucao(self, processo: Processo) -> None:
        """Impresso a cada tick que o processo roda na CPU."""
        if processo.pid not in self._processos_despachados:
            print(f"process {processo.pid} =>")
            print(f"P{processo.pid} STARTED")
            self._processos_despachados.add(processo.pid)

        print(f"P{processo.pid} instruction {processo.tempo_executado}")

        if processo.tempo_executado >= processo.tempo_processador:
            print(f"P{processo.pid} return SIGINT")

    def _interromper_execucao(self) -> bool:
        return (
            not self.processos_pendentes
            and not self.processos_service.processos_ativos
            and not self.fila_service.fila_global
            and self.processos_service.processo_executando is None
            and not self.processos_service.processos_aguardando_recursos
        )

    def _log_resumo_final(self) -> None:
        """Exibe o resumo da simulação após a conclusão."""
        finalizados: list[Processo] = self.processos_service.processos_finalizados

        # TODO: Sistema de arquivos
        # print("Sistema de arquivos =>")

        print()
        print("=" * 60)
        print("  SIMULAÇÃO CONCLUÍDA")
        print("=" * 60)
        print(f"  Total de ticks: {self.tick}")
        print(f"  Processos finalizados: {len(finalizados)}")
        print()

        # Mapa de disco (TODO: implementar com ArquivoService)
        # print("Mapa de ocupação do disco:")

        # Page faults por processo
        print("Número de Faltas de Páginas por processo:")
        for p in finalizados:
            print(f"  P{p.pid} = {p.page_faults} faltas de páginas")

        print("=" * 60)