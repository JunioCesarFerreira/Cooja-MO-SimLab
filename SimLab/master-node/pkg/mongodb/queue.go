package mongodb

import (
	"context"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"m/pkg/models"
)

type QueueManager struct {
	client *mongo.Client
}

func NewQueueManager(client *mongo.Client) *QueueManager {
	return &QueueManager{
		client: client,
	}
}

func (q *QueueManager) WatchQueue(ctx context.Context) (<-chan models.Simulation, error) {
	pipeline := mongo.Pipeline{
		bson.D{{"$match", bson.D{{"operationType", "insert"}}}},
	}

	opts := options.ChangeStream().SetFullDocument(options.UpdateLookup)

	stream, err := q.client.Database("your_database_name").Collection("your_collection_name").Watch(ctx, pipeline, opts)
	if err != nil {
		return nil, err
	}

	simulationCh := make(chan models.Simulation)

	go func() {
		defer func() {
			if err := stream.Close(ctx); err != nil {
				log.Printf("Error closing stream: %v", err)
			}
			close(simulationCh)
		}()

		for stream.Next(ctx) {
			var changeDoc struct {
				FullDocument models.Simulation `bson:"fullDocument"`
			}

			if err := stream.Decode(&changeDoc); err != nil {
				log.Printf("Error decoding queue document: %v", err)
				continue
			}

			simulationCh <- changeDoc.FullDocument
		}

		if err := stream.Err(); err != nil {
			log.Printf("Error in stream: %v", err)
		}
	}()

	return simulationCh, nil
}

func (q *QueueManager) UpdateSimulationStatus(ctx context.Context, simID string, status models.SimulationStatus) error {
	objID, err := primitive.ObjectIDFromHex(simID)
	if err != nil {
		return err
	}

	update := bson.M{
		"$set": bson.M{
			"status": status,
		},
	}

	if status == models.StatusProcessing {
		update["$set"].(bson.M)["startedAt"] = time.Now()
	} else if status == models.StatusCompleted || status == models.StatusFailed {
		update["$set"].(bson.M)["completedAt"] = time.Now()
	}

	_, err = q.client.Database("your_database_name").Collection("your_collection_name").UpdateOne(
		ctx,
		bson.M{"_id": objID},
		update,
	)

	return err
}
