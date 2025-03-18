package config

import (
	"os"
	"strconv"
)

type Config struct {
	MongoURI          string
	MongoDatabase     string
	QueueCollection   string
	ResultsCollection string
	MaxParallelSims   int
	DockerBaseImage   string
	SimulationTimeout int
	LogLevel          string
}

func NewConfig() *Config {
	maxParallelSims, _ := strconv.Atoi(getEnvOrDefault("MAX_PARALLEL_SIMS", "5"))
	simTimeout, _ := strconv.Atoi(getEnvOrDefault("SIMULATION_TIMEOUT", "3600"))

	return &Config{
		MongoURI:          getEnvOrDefault("MONGO_URI", "mongodb://localhost:27017"),
		MongoDatabase:     getEnvOrDefault("MONGO_DATABASE", "simulations"),
		QueueCollection:   getEnvOrDefault("QUEUE_COLLECTION", "queue"),
		ResultsCollection: getEnvOrDefault("RESULTS_COLLECTION", "results"),
		MaxParallelSims:   maxParallelSims,
		DockerBaseImage:   getEnvOrDefault("DOCKER_BASE_IMAGE", "simulation-base:latest"),
		SimulationTimeout: simTimeout,
		LogLevel:          getEnvOrDefault("LOG_LEVEL", "info"),
	}
}

func getEnvOrDefault(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
