package simulator

import (
	"context"
	"log"
	"sync"

	"m/pkg/config"
	"m/pkg/models"
	"m/pkg/mongodb"
)

type SimulationManager struct {
	config         *config.Config
	queueManager   *mongodb.QueueManager
	resultsManager *mongodb.ResultsManager
	workerPool     chan struct{}
	workers        map[string]*Worker
	mu             sync.Mutex
}

func NewSimulationManager(cfg *config.Config, qm *mongodb.QueueManager, rm *mongodb.ResultsManager) *SimulationManager {
	return &SimulationManager{
		config:         cfg,
		queueManager:   qm,
		resultsManager: rm,
		workerPool:     make(chan struct{}, cfg.MaxParallelSims),
		workers:        make(map[string]*Worker),
		mu:             sync.Mutex{},
	}
}

func (sm *SimulationManager) StartWorker(ctx context.Context, simulation models.Simulation) error {
	// Adquirir um slot no pool de workers
	select {
	case sm.workerPool <- struct{}{}:
		// Slot adquirido, continuar
	case <-ctx.Done():
		return ctx.Err()
	}

	worker, err := NewWorker(sm.config, sm.queueManager, sm.resultsManager, simulation)
	if err != nil {
		<-sm.workerPool // Liberar slot
		return err
	}

	sm.mu.Lock()
	sm.workers[simulation.ID.Hex()] = worker
	sm.mu.Unlock()

	// Iniciar worker em uma goroutine
	go func() {
		defer func() {
			<-sm.workerPool // Liberar slot quando terminar
			sm.mu.Lock()
			delete(sm.workers, simulation.ID.Hex())
			sm.mu.Unlock()
		}()

		err := worker.Run(ctx)
		if err != nil {
			log.Printf("Simulation %s failed: %v", simulation.ID.Hex(), err)
		}
	}()

	return nil
}

func (sm *SimulationManager) GetActiveWorkers() int {
	sm.mu.Lock()
	defer sm.mu.Unlock()
	return len(sm.workers)
}
