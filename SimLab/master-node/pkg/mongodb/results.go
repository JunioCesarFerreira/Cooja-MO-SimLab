package mongodb

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"m/pkg/models"
)

type ResultsManager struct {
	client *Client
}

func NewResultsManager(client *Client) *ResultsManager {
	return &ResultsManager{
		client: client,
	}
}

func (r *ResultsManager) StoreResult(ctx context.Context, simID primitive.ObjectID, outputData map[string]interface{}, metrics map[string]float64) (primitive.ObjectID, error) {
	result := models.Result{
		ID:           primitive.NewObjectID(),
		SimulationID: simID,
		OutputData:   outputData,
		Metrics:      metrics,
		CreatedAt:    time.Now(),
	}

	_, err := r.client.GetResultsCollection().InsertOne(ctx, result)
	if err != nil {
		return primitive.NilObjectID, err
	}

	// Atualiza a simulação com a referência ao resultado
	_, err = r.client.GetQueueCollection().UpdateOne(
		ctx,
		bson.M{"_id": simID},
		bson.M{
			"$set": bson.M{
				"status":   models.StatusCompleted,
				"resultId": result.ID,
			},
		},
	)

	return result.ID, err
}
