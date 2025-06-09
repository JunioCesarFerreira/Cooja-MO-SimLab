# Experimentos Unitários

Neste diretório você entrará material para execução de simulações isoladas com intuito de avaliar as métricas propóstas e funcionamento do Cooja.

## Fluxo de uso

1. Abra o notebook [`fix-motes-pos.ipynb`](fix-motes-pos.ipynb). Neste notebook você pode visualizar a topologia do experimento e gerar o arquivo `data/inputExample.json` utilizando o ultimo bloco de código, modifique a linha `exp_index = n` onde `n` é o indice do experimento.

2. Execute um container do Cooja use o [seguinte guia](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja).

3. No diretório `single-experiment` execute `py main.py`. Note que, o diretório `data` contém os dados básicos para gerar simulações, incluindo o template de construção do xml e o json gerado no passo anterior. Após esta execução, o arquivo `output/simulation.xml` será atualizado.

4. No diretório `~/Cooja-MO-SimLab/SimLab/single-experiment/output` utilize:
```shell
scp -P 2231 * root@127.0.0.1:/opt/contiki-ng/tools/cooja
```
para enviar os arquivos para execução da simualação.

5. Conecte via SSH no container de simulação:
```shell
ssh -p 2231 root@127.0.0.1
```
para mais [detalhes veja](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja).

6. Dentro do container de escopo vá para o diretório `/opt/contiki-ng/tools/cooja` e modifique o nome do arquivo:
```shel
mv simulation.xml simulation.csc
```

7. Execute a simulação com o comando:
```shell
java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
```

8. Aguarde o final da execução da simulação.

9. Utilize o `scp` para pegar o log resultante:
```shell
scp -P 2231 root@127.0.0.1:/opt/contiki-ng/tools/cooja/COOJA.testlog cooja.log
```

10. Crie um diretório para os resultados:
- Diretórion `expN` onde `N` é o número do experimento.
- Copie o `data/inputExample.json` para o diretório `expN`.
- Copie o `cooja.log` obtido no passo anterior para o diretório `expN`.
- Copie o nb `expN-1.ipynb` e renomeie para `expN.ipynb`, ajuste o texto descritivo e execute todos os blocos.