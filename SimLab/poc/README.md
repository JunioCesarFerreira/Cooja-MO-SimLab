# 🧪 POC: Integração de Simulações Cooja com Docker e MongoDB

## 🎯 Objetivo

Este diretório contém a implementação de uma **Prova de Conceito (POC)** para a orquestração de simulações de redes IoT no **Cooja (Contiki-NG)** utilizando **MongoDB** como sistema central de controle de fluxo e armazenamento de metadados. O sistema é projetado para execução em ambiente conteinerizado com **Docker**, permitindo escalabilidade e automação.

---

## ⚙️ Requisitos

- Python **3.12** ou superior  
- Biblioteca Python [`pymongo`](https://pymongo.readthedocs.io)
- Docker e Docker Compose
- Imagem Docker personalizada do Cooja: [`ssh-cooja-docker`](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup/tree/main/ssh-docker-cooja)
- Replica set do MongoDB ativado (`rs0`) – já incluído na composição Docker (`docker-compose`)
- Execução do Docker Compose localizada em: [`simlab/docker-compose.yaml`](./simlab/docker-compose.yaml)

---

## 🔄 Descrição do Fluxo de Execução

O fluxo de simulação ocorre conforme os seguintes passos:

1. **Inicialização do MongoDB com replica set (`rs0`)**  
   - Por meio do `docker-compose`, o MongoDB é iniciado com suporte a *change streams*, permitindo a escuta reativa de atualizações em coleções específicas.

2. **Criação de Experimentos**  
   - Os experimentos são definidos em arquivos JSON colocados no diretório `data/`.  
   - Cada experimento contém configurações de simulação, parâmetros evolutivos (ex: tamanho da população), e o modelo da rede.

3. **Execução do Notebook `flow.ipynb`**  
   - Este notebook realiza a leitura do próximo experimento pendente na coleção `experiments`.
   - Gera uma população inicial com configurações de topologia aleatória.
   - Cada indivíduo da população é transformado em uma simulação Cooja, com arquivos `.xml` e `.dat` gerados dinamicamente.
   - Os arquivos são armazenados temporariamente no diretório `tmp/`, e cada simulação é registrada na coleção `simqueue`.
   - Um *master node* via SSH é responsável por consumir as entradas da fila `simqueue`, realizar a simulação no Cooja (dentro de container ou VM) e capturar os resultados (logs de energia, tempo de envio, recepção, etc).
   - Após o término de cada simulação, o log de resultados é salvo no banco de dados e seu ID é atualizado na simulação correspondente no MongoDB (`simqueue`).
   - Os dados podem ser processados posteriormente para avaliação de desempenho, seleção e evolução de soluções.

4. **Reatividade via Change Stream**  
   - O script `change-stream-ex.py` permite monitorar a fila de simulações e disparar ações automatizadas sempre que uma nova entrada estiver pronta para execução.

5. **Limpeza e experimentos com Cooja em VM**
    - Utilize as ferramentas utilitárias para limpeza, visualização e transferência de dados para realizar simulações com GUI Cooja em VM.

---

## 📓 Notebooks

- [`flow.ipynb`](flow.ipynb)  
  Implementa o fluxo completo de execução: geração da população, montagem dos arquivos, inserção na fila e registro.

- [`random-points.ipynb`](random-points.ipynb)  
  Desenvolvimento de métodos para geração de topologias aleatórias válidas e conectadas.

---

## 📁 Estrutura dos Diretórios

```
.
├── data/          # Arquivos JSON com definições de experimentos
├── logs/          # Logs de execução das simulações no Cooja
├── simlab/        # Infraestrutura Docker Compose com MongoDB configurado
├── tmp/           # Arquivos temporários gerados dinamicamente (.xml, .dat)
├── flow.ipynb     # Notebook principal de execução do fluxo de simulações
├── random-points.ipynb
├── change-stream-ex.py
├── util-clear-tmp.py
├── util-plot-pos.py
├── util-send-vm.py
```

---

## 🛠️ Utilitários

- `util-clear-tmp.py`  
  Script para limpeza de arquivos temporários e logs antigos.

- `util-plot-pos.py`  
  Ferramenta para visualização gráfica dos pontos e trajetórias gerados em simulações.

- `util-send-vm.py`  
  Utilitário para envio automático dos arquivos `.xml` e `.dat` para execução remota em VMs ou containers do Cooja via SSH/SCP.

---

## 🔍 Observações Finais

Este projeto é voltado para experimentação de estratégias de simulação em larga escala com **controle distribuído**. Sua arquitetura permite a futura integração com algoritmos evolutivos, mecanismos de avaliação automática de desempenho, e clusters de execução remota.

Para mais informações sobre o ambiente Docker com Cooja, consulte o repositório:  
🔗 [https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup)