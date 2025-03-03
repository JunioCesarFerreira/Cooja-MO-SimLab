# GoMongoQueue

🌍 *[English](README.md)*

GoMongoQueue é um protótipo de sistema para gerenciamento de simulações distribuídas baseado em **Docker**, utilizando **MongoDB Change Streams** para comunicação entre os componentes.

**Atenção!** Esta versão é um protótipo e ainda está incompleta.

## 📌 Arquitetura
O sistema é composto por três serviços principais:

1. **MongoDB**: Banco de dados NoSQL que armazena as tarefas de simulação e seus resultados.
2. **WorkGenerator (Python)**: Gera tarefas de simulação e monitora os resultados usando MongoDB Change Streams.
3. **MasterNode (Go)**: Consome tarefas do MongoDB e executa as simulações concorrentes usando goroutines.

📜 **Fluxo de trabalho:**
1. O **WorkGenerator** insere 15 tarefas no MongoDB.
2. O **MasterNode** escuta essas tarefas, executa as simulações e insere os resultados no banco.
3. O **WorkGenerator** escuta os resultados e, quando todas as 15 tarefas forem concluídas, gera um novo lote.

## 🚀 Configuração e Execução
### **1. Clonar o Repositório**
```sh
 git clone https://github.com/JunioCesarFerreira/ScalableSimulationSystem
 cd examples/GoMongoQueue
```

### **2. Construir e Iniciar os Containers**
```sh
 docker-compose up --build -d
```

### **3. Inicializar o Replica Set do MongoDB**
O MongoDB Change Streams requer um **Replica Set** ativo:
```sh
docker exec -it mongodb mongosh
rs.initiate()
exit
```

### **4. Ver Logs dos Serviços**
- **WorkGenerator:**
```sh
 docker-compose logs -f work-generator
```
- **MasterNode:**
```sh
 docker-compose logs -f master-node
```

## 📂 Estrutura do Projeto
```
GoMongoQueue/
│── docker-compose.yaml
│── master-node/
│   │── Dockerfile
│   │── go.mod
│   │── go.sum
│   │── main.go
│── work-generator/
│   │── Dockerfile
│   │── requirements.txt
│   │── work_generator.py
```

## 🔍 Consultando os Dados no MongoDB
### **Acessar o MongoDB via Terminal**
```sh
docker exec -it mongodb mongosh
```
**Listar bancos de dados:**
```sh
show dbs
use simulation_db
show collections
```
**Consultar tarefas e resultados:**
```sh
db.simulations_tasks.find().pretty()
db.simulations_results.find().pretty()
```

## 📜 Licença
Este projeto está licenciado sob a [MIT License](../../LICENSE).

