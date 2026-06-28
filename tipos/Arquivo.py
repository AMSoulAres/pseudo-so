from dataclasses import dataclass
from typing import Optional

@dataclass
class Arquivo:
    nome: str
    bloco_inicial: int
    tamanho: int
    criador_pid: Optional[int] = None
