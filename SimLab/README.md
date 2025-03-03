# GoMongoQueue

🌍 *[Português](README_pt.md)*

GoMongoQueue is a prototype system for managing distributed simulations based on **Docker**, using **MongoDB Change Streams** for communication between components.

**Attention!** This version is a prototype and is still incomplete.

## 📌 Architecture
The system consists of three main services:

1. **MongoDB**: NoSQL database that stores simulation tasks and their results.
2. **WorkGenerator (Python)**: Generates simulation tasks and monitors results using MongoDB Change Streams.
3. **MasterNode (Go)**: Consumes tasks from MongoDB and executes simulations concurrently using goroutines.

📜 **Workflow:**
1. The **WorkGenerator** inserts 15 tasks into MongoDB.
2. The **MasterNode** listens for these tasks, executes the simulations, and inserts the results into the database.
3. The **WorkGenerator** listens for the results and, once all 15 tasks are completed, generates a new batch.

## 🚀 Setup and Execution
### **1. Clone the Repository**
```sh
git clone https://github.com/JunioCesarFerreira/ScalableSimulationSystem
cd examples/GoMongoQueue
```

### **2. Build and Start Containers**
```sh
docker-compose up --build -d
```

### **3. Initialize MongoDB Replica Set**
MongoDB Change Streams require an active **Replica Set**:
```sh
docker exec -it mongodb mongosh
rs.initiate()
exit
```

### **4. View Service Logs**
- **WorkGenerator:**
```sh
docker-compose logs -f work-generator
```
- **MasterNode:**
```sh
docker-compose logs -f master-node
```

## 📂 Project Structure
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

## 🔍 Querying Data in MongoDB
### **Access MongoDB via Terminal**
```sh
docker exec -it mongodb mongosh
```
**List databases:**
```sh
show dbs
use simulation_db
show collections
```
**Query tasks and results:**
```sh
db.simulations_tasks.find().pretty()
db.simulations_results.find().pretty()
```

## 📜 License
This project is licensed under the [MIT License](../../LICENSE).

