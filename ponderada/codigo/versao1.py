"""
versao1.py

Questão A4, versão 1: buffer circular SEM sincronização.

Produtor e consumidor dividem um contador de posições ocupadas e usam espera ocupada
para saber se podem escrever ou ler. Entre ler e escrever o contador existe um
time.sleep(0), que entrega a CPU para a outra thread no pior momento possível, como se
o sistema operacional interrompesse a tarefa ali. É isso que expõe a condição de corrida.

Uso: python3 versao1.py   (opções: --n, --amostras, --execucoes)
"""

import time

from comum import TIMEOUT_TRAVAMENTO_S, Experimento, rodar


def produtor(exp: Experimento) -> None:
    """Thread do sensor: gera as amostras 0, 1, 2, ... e põe cada uma no buffer.

    Parâmetros:
        exp: estado compartilhado do experimento.

    Funcionamento:
        Espera (girando) até o contador indicar uma posição livre, grava a amostra e
        incrementa o contador em dois passos separados (ler, ser interrompido, escrever).
        Esse incremento não atômico é a região crítica desprotegida.
    """
    entrada = 0
    for amostra in range(exp.total):
        while exp.ocupadas >= exp.n:
            if exp.parar.is_set():
                return
            time.sleep(0)
        exp.buffer[entrada] = amostra
        entrada = (entrada + 1) % exp.n
        valor = exp.ocupadas
        time.sleep(0)
        exp.ocupadas = valor + 1
    exp.produtor_terminou.set()


def consumidor(exp: Experimento) -> None:
    """Thread do motor: tira amostras do buffer e as entrega para a vibração.

    Parâmetros:
        exp: estado compartilhado do experimento.

    Funcionamento:
        Espera (girando) até o contador indicar algo para ler, lê a posição e decrementa
        o contador em dois passos separados. Termina normalmente quando o produtor acabou
        e o contador chegou a zero; se ficar 1 s sem receber nada antes disso, registra
        travamento.
    """
    saida = 0
    ultima_entrega = time.monotonic()
    while True:
        while exp.ocupadas <= 0:
            if exp.produtor_terminou.is_set():
                return
            if time.monotonic() - ultima_entrega > TIMEOUT_TRAVAMENTO_S:
                exp.travou = True
                return
            time.sleep(0)
        exp.recebidas.append(exp.buffer[saida])
        saida = (saida + 1) % exp.n
        ultima_entrega = time.monotonic()
        valor = exp.ocupadas
        time.sleep(0)
        exp.ocupadas = valor - 1


if __name__ == "__main__":
    rodar("Versão 1: sem sincronização", produtor, consumidor)
