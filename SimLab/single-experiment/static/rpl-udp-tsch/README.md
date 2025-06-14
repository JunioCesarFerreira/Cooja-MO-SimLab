# Experimentos Unitários

Este diretório contém materiais para a execução de simulações isoladas, com o objetivo de avaliar as métricas propostas e verificar o funcionamento do simulador Cooja.

## Fluxo de Uso

1. **Configuração da topologia**

   Abra o notebook [`fix-motes-pos.ipynb`](fix-motes-pos.ipynb). Nele, é possível visualizar a topologia do experimento e gerar o arquivo `data/inputExample.json`. Para isso, modifique a linha `exp_index = n`, onde `n` é o índice do experimento desejado, e execute o último bloco de código.

2. **Inicialização do ambiente Cooja**

   Execute um container do Cooja utilizando o [guia disponível aqui](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja). Utilize por exemplo o [docker-compose disponível na poc](../poc/simlab/docker-compose.yaml).

3. **Geração do arquivo de simulação**

   No diretório `single-experiment`, execute o comando:
    ```bash
    python main.py
    ```

    Isso irá gerar o arquivo `output/simulation.xml`, com base nos dados presentes no diretório `data`, incluindo o template XML e o JSON criado no passo anterior.

4. **Envio do arquivo de simulação para o container**

   No diretório `~/Cooja-MO-SimLab/SimLab/single-experiment/output`, utilize o seguinte comando para enviar os arquivos ao container:

   ```bash
   scp -P 2231 * root@127.0.0.1:/opt/contiki-ng/tools/cooja
   ```

5. **Acesso ao container via SSH**

   Conecte-se ao container com o comando:

   ```bash
   ssh -p 2231 root@127.0.0.1
   ```

   Para mais detalhes, consulte novamente o [guia de configuração do container](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja).

6. **Preparação do arquivo de simulação no container**

   Dentro do container, acesse o diretório `/opt/contiki-ng/tools/cooja` e renomeie o arquivo:

   ```bash
   mv simulation.xml simulation.csc
   ```

7. **Execução da simulação**

   Execute o Cooja em modo não interativo com:

   ```bash
   java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
   ```

8. **Aguarde a finalização da simulação**

9. **Recuperação do log de simulação**

   Após a execução, recupere o arquivo de log com:

   ```bash
   scp -P 2231 root@127.0.0.1:/opt/contiki-ng/tools/cooja/COOJA.testlog cooja.log
   ```

10. **Organização dos resultados do experimento**

    * Crie um diretório `expN`, onde `N` é o número do experimento.
    * Copie para este diretório os seguintes arquivos:

      * `data/inputExample.json`
      * `cooja.log`
      * O notebook `expN-1.ipynb`, renomeando-o para `expN.ipynb`
    * Atualize o texto descritivo do notebook e execute todos os blocos.

---
