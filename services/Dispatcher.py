from utils.parsers import DadosSistemaArquivos
from typing import Optional
from FilaService import FilaService
from ProcessosService import ProcessosService
from tipos.Processo import Processo

MAX_TICKS: int = 1_000_000


class Dispatcher:
    # Loop principal que irá simular um clock e a CPU consumindo processos
    def __init__(
        self,
        processos: list[Processo],
        referencias_paginas: dict[int, list[int]],
        dados_fs: Optional[DadosSistemaArquivos]
        ) -> None:
        # Ordena processos por ordem de "chegada" (parametrizada no arquivo lido)
        self.processos_pendentes: list[Processo] = sorted(processos, key=lambda p: p.tempo_inicializacao)

        # Injeta services
        self.fila_service = FilaService()
        self.memoria_service = None # TODO: Implementar
        self.arquivos_service = None # TODO: Implementar
        self.recursos_service = None # TODO: Implementar
        self.processos_service = ProcessosService(
            self.fila_service,
            self.memoria_service,
            self.recursos_service)

        self.gerenciador_processos.referencias_paginas = referencias_paginas

        self.tick: int = 0
        
    def main_loop(self):
        print("=" * 60)
        print(f"{self.processos_pendentes} processos carregados")

        while self.tick < MAX_TICKS: # Evitar loop infinito
            processos_criados: int = 0
            # Processos com tempo de inicialização igual ao tick
            for p in self.processos_pendentes:
                if p.tempo_inicializacao <= self.tick:
                    processo: Processo = self.processos_pendentes.pop(0)
                    is_processo_criado: bool = self.processos_service.criar_processo(processo)

                    if is_processo_criado:
                        processos_criados += 1
                    else:
                        # Falha ao criar processo
                        print(f"TICK {self.tick} Processo PID {processo.pid} não criado.")
            
            
            
        
                
            
                    
            
            