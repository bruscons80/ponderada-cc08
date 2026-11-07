"""
versao3.py

Questão A4, versão 3: os mesmos três semáforos da versão 2, mas o produtor faz
wait(mutex) ANTES de wait(vazio).

Quando o buffer enche, o produtor fica parado em wait(vazio) segurando o mutex. O
consumidor, que é o único que poderia liberar uma posição, precisa do mutex para ler e
fica parado em wait(mutex). Cada um espera pelo outro: deadlock.

Uso: python3 versao3.py   (opções: --n, --amostras, --execucoes)
"""

import time

from comum import Experimento, esperar_semaforo, rodar
from versao2 import consumidor, preparar


def produtor(exp: Experimento) -> None:
    """Thread do sensor com a ordem trocada: wait(mutex), wait(vazio), grava, signal.

    Parâmetros:
        exp: estado compartilhado, com os semáforos criados por versao2.preparar().

    Funcionamento:
        Igual ao produtor da versão 2, exceto pela ordem das duas esperas. O consumidor
        é o mesmo da versão 2, para que a única diferença entre as versões seja essa.
    """
    entrada = 0
    for amostra in range(exp.total):
        if not esperar_semaforo(exp, exp.mutex):
            return
        if not esperar_semaforo(exp, exp.vazio):
            return
        exp.buffer[entrada] = amostra
        time.sleep(0)
        entrada = (entrada + 1) % exp.n
        exp.mutex.release()
        exp.cheio.release()
    exp.produtor_terminou.set()


if __name__ == "__main__":
    rodar("Versão 3: ordem trocada no produtor", produtor, consumidor, preparar)
