# Experimentos Unitários

Neste diretório você entrará material para execução de simulações isoladas com intuito de avaliar as métricas propóstas e funcionamento do Cooja.

## Fluxo de uso

1. O notebook [`fix-motes-pos.ipynb`](fix-motes-pos.ipynb) contém os exemplos de simulações estáticas. Neste notebook você pode visualizar a topologia do experimento e gerar o arquivo `data/inputExample.json`.

2. No diretório `single-experiment` execute `py main.py`. Note que, o diretório `data` contém os dados básicos para gerar simulações, incluindo o template de construção do xml e o json gerado no passo anterior.

3. 