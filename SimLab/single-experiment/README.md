# Single Experiment

Neste diretório você encontrará diversos scripts e resultados de experimentos realizados com o Cooja. O objetivo é verificar o comportamento de diferentes topologias e configurações dos motes no simulador, além de avaliar as métricas a serem utilizadas para análises e processamentos futuros.

## Organização

Neste nível você encontrará a seguinte organização dos diretórios:
- `build`: Este diretório contém os scripts de geração de configurações para testes com Cooja.
- `result`: Neste estão os subdiretórios organizados de resultados e análises do experimentos executados.
- `setting`: Contém a coleção de configurações geradas com o processo do `build` para os experimentos.
- `source`: Contém os códigos fonte em C para compilação dos motes nas simulações.

O diretório `build` contém os códigos e dados necessários para gerar configurações do Cooja e executar simulações. O processo é descrito no [arquivo](./build/README.md).



## Fluxo de Uso

1. **Configuração da topologia**

   Abra o notebook um dos notebooks do diretório `build` ([`static-motes-pos`](./build/static-motes-pos.ipynb) ou [mobile-motes-pos](./build/mobile-motes-pos.ipynb)). Nestes notebooks é possível visualizar a topologia do experimento e gerar o arquivo `data/inputExample.json`. Sendo:
   - Caso Estático: Para isso, modifique a linha `exp_index = n`, onde `n` é o índice do experimento desejado, e execute o último bloco de código.
   - Caso Móvel: Modifique o arquivo **json** de entrada.

   Observe que em ambos os casos, temos a execução do script `build.py`, este realiza a construção das configurações, tendo como entrada os arquivos do diretório `build/data` e como saída os arquivos do diretório `build/output`.  

2. **Inicialização do ambiente Cooja**

   Execute um container do Cooja utilizando o [guia disponível aqui](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja). Utilize por exemplo o [docker-compose disponível na poc](../poc/simlab/docker-compose.yaml).

3. **Envio do código fonte para container de simulação**

   No diretório `~/Cooja-MO-SimLab/SimLab/single-experiment/source`, utilizando o subdiretório desejado, execute o seguinte comando para enviar os arquivos ao container:

   ```bash
   scp -P 2231 * root@127.0.0.1:/opt/contiki-ng/tools/cooja
   ```

4. **Acesso ao container via SSH**

   Conecte-se ao container com o comando:

   ```bash
   ssh -p 2231 root@127.0.0.1
   ```

   Para mais detalhes, consulte novamente o [guia de configuração do container](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja).

5. **Preparação do arquivo de simulação no container**

   Dentro do container, acesse o diretório `/opt/contiki-ng/tools/cooja` e renomeie o arquivo:

   ```bash
   mv simulation.xml simulation.csc
   ```

6. **Execução da simulação**

   Execute o Cooja em modo não interativo com:

   ```bash
   java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
   ```

7. **Aguarde a finalização da simulação**

8. **Recuperação do log de simulação**

   Após a execução, recupere o arquivo de log com:

   ```bash
   scp -P 2231 root@127.0.0.1:/opt/contiki-ng/tools/cooja/COOJA.testlog cooja.log
   ```

9. **Organização dos resultados do experimento**

    * Dentro do diretório `result` siga a organização, dividida por tipo de experimento, com mobilidade ou sem, e os protocolos utilizados.
    * Uma vez determinado o nível correto, crie um diretório para os resultados.
    * No diretório de resultados copie um nb `expN.ipynb` de algum outro resultado já existente.
    * Copie o arquivo de log do Cooja e o inputExample.json utilizado para geração das configurações.
    * Modifique o nome do arquivo `expN.ipynb`