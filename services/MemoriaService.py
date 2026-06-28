from collections import OrderedDict

# Memória principal: 20 frames (0-7 reservados para tempo real, 8-19 para usuário)
_FRAMES_TEMPO_REAL = range(0, 8)
_FRAMES_USUARIO = range(8, 20)


class MemoriaService:
    def __init__(self):
        self._livres_tempo_real: set[int] = set(_FRAMES_TEMPO_REAL)
        self._livres_usuario: set[int] = set(_FRAMES_USUARIO)
        # pid -> {paginas: OrderedDict(pagina->frame), max: int, rt: bool, faults: int}
        self._procs: dict[int, dict] = {}

    def alocar(self, pid: int, working_set: int, is_tempo_real: bool, pagina_inicial: int) -> bool:
        """Aloca memória para um processo com pré-carga de uma página. Retorna False se sem frames livres."""
        pool = self._livres_tempo_real if is_tempo_real else self._livres_usuario
        if not pool:
            return False

        frame = min(pool)  # determinístico: sempre pega o menor frame disponível
        pool.remove(frame)

        paginas: OrderedDict[int, int] = OrderedDict()
        paginas[pagina_inicial] = frame  # pré-carga: 1 página sem contar page fault

        self._procs[pid] = {
            "paginas": paginas,
            "max": working_set,
            "rt": is_tempo_real,
            "faults": 0,
        }
        return True

    def referenciar_pagina(self, pid: int, pagina: int) -> bool:
        """Processa uma referência de página com LRU local. Retorna True se houve page fault."""
        proc = self._procs[pid]
        paginas: OrderedDict = proc["paginas"]

        if pagina in paginas:
            paginas.move_to_end(pagina)  # marca como mais recentemente usado
            return False

        # Page fault: encontra ou libera um frame
        proc["faults"] += 1
        pool = self._livres_tempo_real if proc["rt"] else self._livres_usuario

        if len(paginas) < proc["max"] and pool:
            frame = min(pool)
            pool.remove(frame)
        else:
            # LRU: despeja a página menos recentemente usada (primeira do OrderedDict)
            _, frame = paginas.popitem(last=False)

        paginas[pagina] = frame
        return True

    def liberar(self, pid: int) -> None:
        """Devolve todos os frames do processo para o pool correspondente."""
        proc = self._procs.pop(pid, None)
        if proc is None:
            return
        pool = self._livres_tempo_real if proc["rt"] else self._livres_usuario
        pool.update(proc["paginas"].values())

    def page_faults(self, pid: int) -> int:
        return self._procs[pid]["faults"]

    def frames_alocados(self, pid: int) -> int:
        return len(self._procs[pid]["paginas"])
