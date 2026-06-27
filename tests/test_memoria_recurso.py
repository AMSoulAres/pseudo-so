import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.MemoriaService import MemoriaService
from services.RecursoService import RecursoService


# ── MemoriaService ────────────────────────────────────────────────────────────

def test_memoria_aloca_e_libera():
    m = MemoriaService()
    assert m.alocar(pid=0, working_set=2, is_tempo_real=False, pagina_inicial=0)
    assert m.frames_alocados(0) == 1  # pré-carga de 1 página
    m.liberar(0)


def test_memoria_pools_nao_se_cruzam():
    m = MemoriaService()
    # Esgota pool de tempo real (8 frames, 1 por processo)
    for pid in range(8):
        assert m.alocar(pid=pid, working_set=1, is_tempo_real=True, pagina_inicial=pid)
    # Nono processo tempo real falha
    assert not m.alocar(pid=8, working_set=1, is_tempo_real=True, pagina_inicial=0)
    # Mas processo de usuário ainda consegue
    assert m.alocar(pid=9, working_set=1, is_tempo_real=False, pagina_inicial=0)


def test_memoria_sem_fault_em_hit():
    m = MemoriaService()
    m.alocar(pid=0, working_set=3, is_tempo_real=False, pagina_inicial=1)
    # página 1 já está carregada (pré-carga)
    assert not m.referenciar_pagina(0, 1)
    assert m.page_faults(0) == 0


def test_memoria_fault_em_miss():
    m = MemoriaService()
    m.alocar(pid=0, working_set=3, is_tempo_real=False, pagina_inicial=1)
    # página 2 não está carregada
    assert m.referenciar_pagina(0, 2)
    assert m.page_faults(0) == 1


def test_memoria_lru_evicta_menos_recente():
    m = MemoriaService()
    # working_set=2: pode ter no máximo 2 páginas simultaneamente
    m.alocar(pid=0, working_set=2, is_tempo_real=False, pagina_inicial=1)
    m.referenciar_pagina(0, 2)   # carrega página 2 → frames: [1, 2]
    m.referenciar_pagina(0, 1)   # acessa 1 → move para fim: [2, 1]
    m.referenciar_pagina(0, 3)   # falta → evicta LRU (2) → frames: [1, 3]

    faults_antes = m.page_faults(0)
    # página 1 ainda deve estar em memória (não foi evictada)
    assert not m.referenciar_pagina(0, 1)
    assert m.page_faults(0) == faults_antes  # sem novo fault

    # página 2 foi evictada, deve gerar fault
    assert m.referenciar_pagina(0, 2)


def test_memoria_liberar_devolve_frames():
    m = MemoriaService()
    for pid in range(12):  # esgota pool de usuário (12 frames)
        assert m.alocar(pid=pid, working_set=1, is_tempo_real=False, pagina_inicial=0)
    assert not m.alocar(pid=12, working_set=1, is_tempo_real=False, pagina_inicial=0)

    m.liberar(0)  # devolve 1 frame
    assert m.alocar(pid=12, working_set=1, is_tempo_real=False, pagina_inicial=0)


# ── RecursoService ────────────────────────────────────────────────────────────

def test_recurso_aloca_basico():
    r = RecursoService()
    assert r.alocar(pid=0, impressora=1, scanner=0, modem=0, sata=0)


def test_recurso_indisponivel_retorna_false():
    r = RecursoService()
    r.alocar(pid=0, impressora=0, scanner=1, modem=0, sata=0)  # único scanner alocado
    assert not r.alocar(pid=1, impressora=0, scanner=1, modem=0, sata=0)


def test_recurso_all_or_nothing():
    r = RecursoService()
    r.alocar(pid=0, impressora=0, scanner=1, modem=0, sata=0)  # toma o scanner
    # pid=1 pede impressora (disponível) + scanner (indisponível) → deve falhar tudo
    assert not r.alocar(pid=1, impressora=1, scanner=1, modem=0, sata=0)
    # impressora deve ainda estar disponível (não foi alocada parcialmente)
    assert r.alocar(pid=2, impressora=1, scanner=0, modem=0, sata=0)


def test_recurso_liberar_devolve():
    r = RecursoService()
    r.alocar(pid=0, impressora=0, scanner=1, modem=0, sata=0)
    assert not r.alocar(pid=1, impressora=0, scanner=1, modem=0, sata=0)
    r.liberar(0)
    assert r.alocar(pid=1, impressora=0, scanner=1, modem=0, sata=0)


def test_recurso_dois_processos_mesma_impressora():
    r = RecursoService()
    # 2 impressoras disponíveis: dois processos podem ter uma cada
    assert r.alocar(pid=0, impressora=1, scanner=0, modem=0, sata=0)
    assert r.alocar(pid=1, impressora=1, scanner=0, modem=0, sata=0)
    # terceiro falha
    assert not r.alocar(pid=2, impressora=1, scanner=0, modem=0, sata=0)


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    testes = [v for k, v in list(globals().items()) if k.startswith("test_")]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print(f"  ok  {teste.__name__}")
        except AssertionError as e:
            print(f"FAIL  {teste.__name__}: {e}")
            falhas += 1
    print(f"\n{len(testes) - falhas}/{len(testes)} passou")
