package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type Result struct {
	ID           primitive.ObjectID     `bson:"_id,omitempty"`
	SimulationID primitive.ObjectID     `bson:"simulationId"`
	OutputData   map[string]interface{} `bson:"outputData"`
	Metrics      map[string]float64     `bson:"metrics,omitempty"`
	CreatedAt    time.Time              `bson:"createdAt"`
}
