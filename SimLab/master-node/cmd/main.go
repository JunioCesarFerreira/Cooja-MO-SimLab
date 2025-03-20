package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Número máximo de simulações concorrentes
const MaxWorkers = 5

var mongoURI = "mongodb://localhost:27017/?replicaSet=rs0" //os.Getenv("MONGO_URI")

func main() {
	clientOptions := options.Client().ApplyURI(mongoURI)
	client, err := mongo.Connect(context.TODO(), clientOptions)
	if err != nil {
		log.Fatal(err)
	}
	defer client.Disconnect(context.TODO())

	db := client.Database("simulation_db")
	tasksCollection := db.Collection("simulations_tasks")
	resultsCollection := db.Collection("simulations_results")

	fmt.Println("[MasterNode] Aguardando novas tarefas...")

	// Canal para processamento concorrente das tarefas
	taskChannel := make(chan bson.M, MaxWorkers)

	// Inicia os workers
	for i := 0; i < MaxWorkers; i++ {
		go worker(taskChannel, resultsCollection)
	}

	// Escuta novas tarefas via Change Streams
	stream, err := tasksCollection.Watch(context.TODO(), mongo.Pipeline{})
	if err != nil {
		log.Fatal(err)
	}
	defer stream.Close(context.TODO())

	for stream.Next(context.TODO()) {
		var change map[string]interface{}
		if err := stream.Decode(&change); err != nil {
			log.Println("Erro ao processar evento:", err)
			continue
		}

		// Extrai a nova tarefa e envia para o canal
		newTask := change["fullDocument"].(map[string]interface{})
		taskChannel <- newTask
	}
}

// Worker que processa as tarefas concorrentes
func worker(taskChannel <-chan bson.M, resultsCollection *mongo.Collection) {
	for task := range taskChannel {
		taskID := task["_id"]
		fmt.Printf("[Worker] Processando tarefa %v\n", task)

		// Simula o processamento da tarefa
		time.Sleep(2 * time.Second)

		// Salva o resultado no MongoDB
		result := bson.M{
			"task_id":   taskID,
			"result":    "Simulação concluída com sucesso",
			"timestamp": time.Now(),
		}
		_, err := resultsCollection.InsertOne(context.TODO(), result)
		if err != nil {
			log.Println("Erro ao salvar resultado:", err)
		}

		fmt.Printf("[Worker] Tarefa %v concluída\n", taskID)
	}
}
