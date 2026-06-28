from enum import Enum

class EstadoProcesso(Enum):
    BLOQUEADO = 1
    PRONTO = 2
    EXECUTANDO = 3
    FINALIZADO = 4