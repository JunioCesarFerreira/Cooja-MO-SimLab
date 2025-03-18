package simulator

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"m/pkg/config"
	dockerclient "m/pkg/docker"
	"m/pkg/models"
	"m/pkg/mongodb"
	"m/pkg/remote"
)

type Worker struct {
	simulation     models.Simulation
	config         *config.Config
	queueManager   *mongodb.QueueManager
	resultsManager *mongodb.ResultsManager
	dockerClient   *dockerclient.DockerClient
}

func NewWorker(cfg *config.Config, qm *mongodb.QueueManager, rm *mongodb.ResultsManager, sim models.Simulation) (*Worker, error) {
	cli, err := dockerclient.NewDockerClient()
	if err != nil {
		return nil, err
	}

	return &Worker{
		simulation:     sim,
		config:         cfg,
		queueManager:   qm,
		resultsManager: rm,
		dockerClient:   cli,
	}, nil
}

func (w *Worker) Run(ctx context.Context) error {
	simID := w.simulation.ID.Hex()

	// Atualizar status para PROCESSING
	if err := w.queueManager.UpdateSimulationStatus(ctx, simID, models.StatusProcessing); err != nil {
		return fmt.Errorf("failed to update simulation status: %v", err)
	}

	containerName := "sim_" + simID
	hostPort := strconv.Itoa(2222)

	log.Printf("Starting container %s in port %s\n", containerName, hostPort)

	// Criar container Docker
	containerID, err := w.dockerClient.CreateContainer(ctx, containerName, hostPort)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to create container: %v", err))
		return err
	}

	// Preparar diretório temporário para dados de entrada
	tmpDir, err := ioutil.TempDir("", fmt.Sprintf("sim-%s-", simID))
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to create temp directory: %v", err))
		return err
	}
	defer os.RemoveAll(tmpDir)

	// Salvar os dados de entrada em um arquivo JSON
	inputFile := filepath.Join(tmpDir, "input.json")
	inputData, err := json.Marshal(w.simulation.InputData)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to marshal input data: %v", err))
		return err
	}

	if err := ioutil.WriteFile(inputFile, inputData, 0644); err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to write input file: %v", err))
		return err
	}

	// Conectar via SSH ao container (assumindo que ele expõe SSH)
	// Em um cenário real, você pode precisar esperar que o container esteja pronto para aceitar conexões SSH
	sshClient, err := w.connectToContainer(containerID)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to connect to container: %v", err))
		return err
	}
	defer sshClient.Close()

	// Copiar dados de entrada para o container
	remoteInputPath := "/app/data/input.json"
	if err := sshClient.CopyFileToRemote(inputFile, remoteInputPath); err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to copy input file: %v", err))
		return err
	}

	// Iniciar a simulação
	if err := w.dockerClient.StartContainer(ctx, containerID); err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to start container: %v", err))
		return err
	}

	// Criar contexto com timeout para a simulação
	simCtx, cancel := context.WithTimeout(ctx, time.Duration(w.config.SimulationTimeout)*time.Second)
	defer cancel()

	// Aguardar a conclusão da simulação
	isRunning, err := w.dockerClient.IsContainerRunning(simCtx, containerID)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("simulation failed: %v", err))
		return err
	}

	if !isRunning {
		logs, _ := w.dockerClient.GetContainerLogs(ctx, containerID)
		w.failSimulation(ctx, fmt.Sprintf("simulation exited\nLog:\n%s\n", logs))
		return fmt.Errorf("simulation exited with error")
	}

	// Copiar resultados do container
	remoteOutputPath := "/app/data/output.json"
	localOutputPath := filepath.Join(tmpDir, "output.json")

	if err := sshClient.CopyFileFromRemote(remoteOutputPath, localOutputPath); err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to copy output file: %v", err))
		return err
	}

	// Ler e processar resultados
	outputBytes, err := os.ReadFile(localOutputPath)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to read output file: %v", err))
		return err
	}

	var outputData map[string]interface{}
	if err := json.Unmarshal(outputBytes, &outputData); err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to parse output data: %v", err))
		return err
	}

	// Calcular métricas (exemplo)
	metrics := map[string]float64{
		"executionTime": time.Since(w.simulation.StartedAt).Seconds(),
	}

	// Armazenar resultados no MongoDB
	_, err = w.resultsManager.StoreResult(ctx, w.simulation.ID, outputData, metrics)
	if err != nil {
		w.failSimulation(ctx, fmt.Sprintf("failed to store results: %v", err))
		return err
	}

	// Remover o container
	if err := w.dockerClient.RemoveContainer(ctx, containerID); err != nil {
		// Apenas logar o erro, não falhar a simulação
		fmt.Printf("Warning: failed to remove container %s: %v\n", containerID, err)
	}

	return nil
}

func (w *Worker) connectToContainer(containerID string) (*remote.SSHClient, error) {
	// Em um cenário real, você precisaria obter o IP do container
	// Aqui estamos usando um exemplo simplificado
	containerIP := "172.17.0.2" // Precisará ser obtido dinamicamente

	sshConfig := remote.SSHConfig{
		Host:     containerIP,
		Port:     22,
		User:     "root",
		Password: "password", // Em produção, use chaves SSH ou outro método seguro
	}

	return remote.NewSSHClient(sshConfig)
}

func (w *Worker) failSimulation(ctx context.Context, errMsg string) {
	simID := w.simulation.ID.Hex()

	// Atualizar status para FAILED
	err := w.queueManager.UpdateSimulationStatus(ctx, simID, models.StatusFailed)
	if err != nil {
		fmt.Printf("Error updating simulation status: %v\n", err)
	}
}
