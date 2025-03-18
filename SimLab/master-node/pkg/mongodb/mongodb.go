package mongodb

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"m/pkg/config"
)

type Client struct {
	client   *mongo.Client
	database *mongo.Database
	config   *config.Config
}

func NewClient(cfg *config.Config) (*Client, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(cfg.MongoURI))
	if err != nil {
		return nil, err
	}

	// Verificar conexão
	err = client.Ping(ctx, nil)
	if err != nil {
		return nil, err
	}

	return &Client{
		client:   client,
		database: client.Database(cfg.MongoDatabase),
		config:   cfg,
	}, nil
}

func (c *Client) Close(ctx context.Context) error {
	return c.client.Disconnect(ctx)
}

func (c *Client) GetQueueCollection() *mongo.Collection {
	return c.database.Collection(c.config.QueueCollection)
}

func (c *Client) GetResultsCollection() *mongo.Collection {
	return c.database.Collection(c.config.ResultsCollection)
}
