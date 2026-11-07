"""
comum.py

Infraestrutura compartilhada pelas três versões da questão A4 (buffer circular entre a
thread do sensor, produtora, e a thread do motor, consumidora).

Este módulo cuida de tudo que precisa ser igual nas três versões para que a comparação
seja justa: os parâmetros do experimento, o estado compartilhado entre as threads, a
regra de travamento (1 s sem receber nada), a contagem de amostras consumidas, perdidas e
duplicadas e a tabela final. Cada versão só implementa o produtor e o consumidor.
"""

import argparse
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

N_PADRAO = 6
AMOSTRAS_PADRAO = 20_000
EXECUCOES_PADRAO = 3
TIMEOUT_TRAVAMENTO_S = 1.0
PASSO_ESPERA_S = 0.05


@dataclass
class Experimento:
    """Estado compartilhado por produtor e consumidor durante uma execução.

    Atributos:
        n: número de posições do buffer circular.
        total: quantas amostras o produtor gera (numeradas de 0 a total - 1).
        buffer: as N posições do buffer circular.
        recebidas: amostras na ordem em que o consumidor as entregou ao motor.
        ocupadas: contador de posições ocupadas (usado só pela versão 1).
        produtor_terminou: sinaliza que o produtor gerou todas as amostras.
        parar: pede para as threads encerrarem (usado depois de um travamento).
        travou: o consumidor ficou 1 s sem receber nada antes do fim.
    """

    n: int
    total: int
    buffer: list = field(init=False)
    recebidas: list = field(default_factory=list)
    ocupadas: int = 0
    produtor_terminou: threading.Event = field(default_factory=threading.Event)
    parar: threading.Event = field(default_factory=threading.Event)
    travou: bool = False

    def __post_init__(self) -> None:
        """Cria o buffer circular vazio com N posições logo depois da construção.

        Retorna:
            None.
        """
        self.buffer = [None] * self.n


@dataclass
class Resultado:
    """Resumo de uma execução, uma linha da tabela pedida no enunciado."""

    consumidas: int
    perdidas: int
    duplicadas: int
    travou: bool
    duracao_s: float


def analisar(exp: Experimento, duracao_s: float) -> Resultado:
    """Compara o que o motor recebeu com o que o sensor gerou.

    Parâmetros:
        exp: o experimento já encerrado.
        duracao_s: tempo de parede da execução, em segundos.

    Retorna:
        Resultado com consumidas (entregas ao motor, contando repetições), perdidas
        (amostras geradas que nunca chegaram), duplicadas (entregas repetidas da mesma
        amostra) e se houve travamento.
    """
    vistas: set[int] = set()
    duplicadas = 0
    for amostra in exp.recebidas:
        if amostra in vistas:
            duplicadas += 1
        else:
            vistas.add(amostra)
    perdidas = exp.total - len(vistas & set(range(exp.total)))
    return Resultado(len(exp.recebidas), perdidas, duplicadas, exp.travou, duracao_s)


def esperar_semaforo(exp: Experimento, semaforo: threading.Semaphore) -> bool:
    """Faz wait() num semáforo sem bloquear para sempre.

    Tenta adquirir em passos curtos para poder desistir quando o experimento pede para
    parar (depois de um travamento detectado pelo consumidor). Enquanto tenta, a thread
    continua segurando tudo que já tinha adquirido, exatamente como num wait() comum.

    Parâmetros:
        exp: experimento em andamento.
        semaforo: semáforo a adquirir.

    Retorna:
        True se adquiriu; False se o experimento mandou parar antes disso.
    """
    while not exp.parar.is_set():
        if semaforo.acquire(timeout=PASSO_ESPERA_S):
            return True
    return False


def consumidor_espera(exp: Experimento, semaforo: threading.Semaphore) -> str:
    """wait() do consumidor com a regra de travamento do enunciado.

    Parâmetros:
        exp: experimento em andamento.
        semaforo: semáforo que o consumidor quer adquirir.

    Retorna:
        "ok" se adquiriu; "fim" se o produtor já terminou e não há mais nada a consumir;
        "travou" se passou 1 s sem conseguir adquirir com o produtor ainda ativo.
    """
    prazo = time.monotonic() + TIMEOUT_TRAVAMENTO_S
    while True:
        if semaforo.acquire(timeout=PASSO_ESPERA_S):
            return "ok"
        if exp.produtor_terminou.is_set() and not semaforo.acquire(blocking=False):
            return "fim"
        if time.monotonic() > prazo:
            return "travou"


def rodar(
    titulo: str,
    produtor: Callable[[Experimento], None],
    consumidor: Callable[[Experimento], None],
    preparar: Callable[[Experimento], None] | None = None,
) -> list[Resultado]:
    """Executa o experimento várias vezes e imprime a tabela de resultados.

    Parâmetros:
        titulo: nome da versão, usado no cabeçalho.
        produtor: função da thread do sensor; recebe o Experimento.
        consumidor: função da thread do motor; recebe o Experimento.
        preparar: chamada antes de cada execução para criar os semáforos da versão.

    Retorna:
        A lista de resultados, uma por execução.

    Funcionamento:
        Lê --n, --amostras e --execucoes da linha de comando, cria as duas threads,
        espera o consumidor acabar (fim normal ou travamento), manda o produtor parar
        e registra a execução.
    """
    parser = argparse.ArgumentParser(description=titulo)
    parser.add_argument("--n", type=int, default=N_PADRAO, help="posições do buffer")
    parser.add_argument("--amostras", type=int, default=AMOSTRAS_PADRAO)
    parser.add_argument("--execucoes", type=int, default=EXECUCOES_PADRAO)
    args = parser.parse_args()

    print(f"{titulo}  |  N = {args.n}  |  {args.amostras} amostras  |  {args.execucoes} execuções")
    resultados = []
    for i in range(1, args.execucoes + 1):
        exp = Experimento(args.n, args.amostras)
        if preparar:
            preparar(exp)
        t_produtor = threading.Thread(target=produtor, args=(exp,), name="sensor", daemon=True)
        t_consumidor = threading.Thread(target=consumidor, args=(exp,), name="motor", daemon=True)
        inicio = time.monotonic()
        t_produtor.start()
        t_consumidor.start()
        t_consumidor.join()
        exp.parar.set()
        t_produtor.join(timeout=2)
        r = analisar(exp, time.monotonic() - inicio)
        resultados.append(r)
        print(
            f"  execução {i}: consumidas={r.consumidas:>6}  perdidas={r.perdidas:>6}  "
            f"duplicadas={r.duplicadas:>6}  travou={'sim' if r.travou else 'não':<3}  "
            f"({r.duracao_s:.2f} s)"
        )

    print("\n| Execução | Consumidas | Perdidas | Duplicadas | Travou |")
    print("|---|---|---|---|---|")
    for i, r in enumerate(resultados, 1):
        travou = "sim" if r.travou else "não"
        print(f"| {i} | {r.consumidas} | {r.perdidas} | {r.duplicadas} | {travou} |")
    return resultados
