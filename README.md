# Ponderada CC08: do pipeline ao deadlock

**Aluno:** Bruno Discacciati Vieiralves Martins

Análise de arquitetura, pipeline, processos, semáforos e deadlock aplicada à pulseira sensorial da Tato, com a decisão de CTO em [`ponderada/ponderada-tato.md`](ponderada/ponderada-tato.md).

## Estrutura

```
ponderada/
  ponderada-tato.md   Parte A (questões A1 a A5) e Parte B (memorando do CTO)
  codigo/             questão A4: buffer circular entre sensor e motor
  img/                prints usados no documento
```

## Como rodar a questão A4

&emsp;Precisa só de Python 3.10 ou mais novo, sem nenhuma biblioteca externa. A partir da pasta `ponderada/codigo`, cada versão roda com um único comando e já executa 3 vezes com 20.000 amostras e N = 6, imprimindo a tabela de resultados no fim:

```bash
cd ponderada/codigo
python3 versao1.py   # sem sincronização: contador compartilhado e espera ocupada
python3 versao2.py   # semáforos vazio (N), cheio (0) e mutex (1)
python3 versao3.py   # semáforos com a ordem trocada no produtor (deadlock)
```

&emsp;As três aceitam opções para mudar o experimento, por exemplo `python3 versao2.py --n 6 --amostras 20000 --execucoes 3`. Uma execução é registrada como travada quando o consumidor passa 1 s sem receber nenhuma amostra antes de o produtor terminar.
