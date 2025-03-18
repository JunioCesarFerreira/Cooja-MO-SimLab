package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type SimulationStatus string

const (
	StatusQueued     SimulationStatus = "QUEUED"
	StatusProcessing SimulationStatus = "PROCESSING"
	StatusCompleted  SimulationStatus = "COMPLETED"
	StatusFailed     SimulationStatus = "FAILED"
)

type Simulation struct {
	ID          primitive.ObjectID     `bson:"_id,omitempty"`
	InputData   map[string]interface{} `bson:"inputData"`
	Status      SimulationStatus       `bson:"status"`
	ContainerID string                 `bson:"containerId,omitempty"`
	CreatedAt   time.Time              `bson:"createdAt"`
	StartedAt   time.Time              `bson:"startedAt,omitempty"`
	CompletedAt time.Time              `bson:"completedAt,omitempty"`
	Error       string                 `bson:"error,omitempty"`
	ResultID    primitive.ObjectID     `bson:"resultId,omitempty"`
}
