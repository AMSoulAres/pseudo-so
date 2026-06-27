# Recursos disponíveis no pseudo-SO (exclusivos por processo, sem preempção)
_TOTAL = {
    "scanner":   1,
    "impressora": 2,
    "modem":     1,
    "sata":      2,
}


class RecursoService:
    def __init__(self):
        self._disponiveis: dict[str, int] = dict(_TOTAL)
        # Guarda o que cada processo alocou para poder liberar depois
        self._alocados: dict[int, dict[str, int]] = {}

    def alocar(self, pid: int, impressora: int, scanner: int, modem: int, sata: int) -> bool:
        """Tenta alocar todos os recursos pedidos de uma vez. Retorna False se qualquer um estiver indisponível."""
        pedido = {"scanner": scanner, "impressora": impressora, "modem": modem, "sata": sata}

        if any(self._disponiveis[r] < qtd for r, qtd in pedido.items()):
            return False

        for recurso, qtd in pedido.items():
            self._disponiveis[recurso] -= qtd

        self._alocados[pid] = pedido
        return True

    def liberar(self, pid: int) -> None:
        """Devolve todos os recursos alocados pelo processo."""
        recursos = self._alocados.pop(pid, None)
        if recursos is None:
            return
        for recurso, qtd in recursos.items():
            self._disponiveis[recurso] += qtd
