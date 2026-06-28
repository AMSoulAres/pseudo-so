from dataclasses import dataclass, field
from .EstadoProcesso import EstadoProcesso

@dataclass
class Processo:
    # file : <tempo de inicialização>, <prioridade>, <tempo de processador>,
    # <tamanho máximo do conjunto de trabalho>, <requisição da impressora>,
    # <requisição do scanner>, <requisição do modem>,
    # <requisição do disco SATA>

    pid: int # entrada
    prioridade: int # entrada
    tempo_inicializacao: int # entrada
    tempo_processador: int # entrada
    working_set_len: int # entrada
    requisicao_impressora: int # entrada
    requisicao_scanner: int # entrada
    requisicao_modem: int # entrada
    requisicao_disco: int # entrada

    # dados em tempo de execução
    estado: EstadoProcesso = EstadoProcesso.BLOQUEADO # inicia bloqueado para pedir recursos
    tempo_executado: int = 0
    prioridade_atual: int = field(init=False)
    page_faults: int = 0
    tempo_espera: int = 0
    frames: int = 0


    def __post_init__(self) -> None:
        self.prioridade_atual = self.prioridade # atribui prioridade inicial

    @property
    def tempo_restante(self) -> int:
        return self.tempo_processador - self.tempo_executado

    @property
    def is_tempo_real(self) -> bool:
        return self.prioridade == 0

    @property
    def is_requesting_recursos(self) -> bool:
        return any([
            self.requisicao_disco,
            self.requisicao_scanner,
            self.requisicao_impressora,
            self.requisicao_modem
        ])

    def bloquear(self) -> None:
        self.estado = EstadoProcesso.BLOQUEADO

    def desbloquear(self) -> None:
        self.estado = EstadoProcesso.PRONTO

