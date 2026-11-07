"""
versao2.py

Questão A4, versão 2: buffer circular com três semáforos.

vazio (começa em N) conta posições livres, cheio (começa em 0) conta posições com dado e
mutex (começa em 1) garante que só uma thread mexe no buffer e nos índices por vez. O
mesmo time.sleep(0) da versão 1 continua dentro da região crítica, para mostrar que a
interrupção no pior momento deixa de causar dano quando a região está protegida.

Uso: python3 versao2.py   (opções: --n, --amostras, --execucoes)
"""

import threading
import time

from comum import Experimento, consumidor_espera, esperar_semaforo, rodar


def preparar(exp: Experimento) -> None:
    """Cria os três semáforos da versão no experimento.

    Parâmetros:
        exp: experimento que vai rodar; recebe os atributos vazio, cheio e mutex.

    Retorna:
        None.
    """
    exp.vazio = threading.Semaphore(exp.n)
    exp.cheio = threading.Semaphore(0)
    exp.mutex = threading.Semaphore(1)


def produtor(exp: Experimento) -> None:
    """Thread do sensor: wait(vazio), wait(mutex), grava, signal(mutex), signal(cheio).

    Parâmetros:
        exp: estado compartilhado, já com os semáforos criados por preparar().

    Retorna:
        None. Ao terminar todas as amostras, sinaliza exp.produtor_terminou.

    Funcionamento:
        Para cada amostra, espera uma posição livre (vazio), entra na região crítica
        (mutex), grava e avança o índice, sai da região crítica e avisa que há uma
        posição a mais com dado (cheio).
    """
    entrada = 0
    for amostra in range(exp.total):
        if not esperar_semaforo(exp, exp.vazio):
            return
        if not esperar_semaforo(exp, exp.mutex):
            return
        exp.buffer[entrada] = amostra
        time.sleep(0)
        entrada = (entrada + 1) % exp.n
        exp.mutex.release()
        exp.cheio.release()
    exp.produtor_terminou.set()


def consumidor(exp: Experimento) -> None:
    """Thread do motor: wait(cheio), wait(mutex), lê, signal(mutex), signal(vazio).

    Parâmetros:
        exp: estado compartilhado, já com os semáforos criados por preparar().

    Retorna:
        None. As amostras entregues ficam em exp.recebidas e o travamento em exp.travou.

    Funcionamento:
        Termina normalmente quando o produtor acabou e não sobrou nada no buffer; se uma
        espera passar de 1 s com o produtor ainda ativo, registra travamento.
    """
    saida = 0
    while True:
        estado = consumidor_espera(exp, exp.cheio)
        if estado == "fim":
            return
        if estado == "travou" or consumidor_espera(exp, exp.mutex) != "ok":
            exp.travou = True
            return
        amostra = exp.buffer[saida]
        time.sleep(0)
        saida = (saida + 1) % exp.n
        exp.mutex.release()
        exp.vazio.release()
        exp.recebidas.append(amostra)


if __name__ == "__main__":
    rodar("Versão 2: semáforos vazio, cheio e mutex", produtor, consumidor, preparar)
