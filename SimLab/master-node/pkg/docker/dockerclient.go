package dockerclient

import (
	"context"
	"fmt"
	"io"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
)

type DockerClient struct {
	cli *client.Client
}

// NewDockerClient cria um novo cliente Docker
func NewDockerClient() (*DockerClient, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, fmt.Errorf("failed to create Docker client: %v", err)
	}
	return &DockerClient{cli: cli}, nil
}

// CreateAndStartContainer cria e inicia um container Docker com nome e porta customizados
func (dc *DockerClient) CreateContainer(ctx context.Context, containerName string, hostPort string) (string, error) {
	containerConfig := &container.Config{
		Image: "ubuntu-docker",
		ExposedPorts: nat.PortSet{
			"22/tcp": struct{}{},
		},
	}

	networkName := "simnet"

	hostConfig := &container.HostConfig{
		PortBindings: nat.PortMap{
			"22/tcp": []nat.PortBinding{
				{
					HostIP:   "0.0.0.0",
					HostPort: hostPort,
				},
			},
		},
		NetworkMode: container.NetworkMode(networkName),
	}

	// Cria o container com nome personalizado
	containerResp, err := dc.cli.ContainerCreate(ctx, containerConfig, hostConfig, nil, nil, containerName)
	if err != nil {
		return "", fmt.Errorf("failed to create container: %v", err)
	}

	return containerResp.ID, nil
}

func (dc *DockerClient) StartContainer(ctx context.Context, containerID string) error {
	// Inicia o container
	err := dc.cli.ContainerStart(ctx, containerID, container.StartOptions{})
	if err != nil {
		return fmt.Errorf("failed to start container: %v", err)
	}

	return nil
}

// RemoveContainer remove um container Docker
func (dc *DockerClient) RemoveContainer(ctx context.Context, containerID string) error {
	err := dc.cli.ContainerRemove(ctx, containerID, container.RemoveOptions{Force: true})
	if err != nil {
		return fmt.Errorf("failed to remove container: %v", err)
	}
	return nil
}

// IsContainerRunning verifica se um container está em execução
func (dc *DockerClient) IsContainerRunning(ctx context.Context, containerID string) (bool, error) {
	containerJSON, err := dc.cli.ContainerInspect(ctx, containerID)
	if err != nil {
		return false, fmt.Errorf("failed to inspect container: %v", err)
	}
	return containerJSON.State.Running, nil
}

// GetContainerLogs obtém os logs de um container
func (dc *DockerClient) GetContainerLogs(ctx context.Context, containerID string) (string, error) {
	out, err := dc.cli.ContainerLogs(ctx, containerID, container.LogsOptions{ShowStdout: true, ShowStderr: true})
	if err != nil {
		return "", fmt.Errorf("failed to get container logs: %v", err)
	}
	defer out.Close()

	logs, err := io.ReadAll(out)
	if err != nil {
		return "", fmt.Errorf("failed to read container logs: %v", err)
	}

	return string(logs), nil
}

// GetContainerIP obtém o IP do container na rede especificada
func (dc *DockerClient) GetContainerIP(ctx context.Context, containerID, networkName string) (string, error) {
	containerJSON, err := dc.cli.ContainerInspect(ctx, containerID)
	if err != nil {
		return "", fmt.Errorf("failed to inspect container: %v", err)
	}

	networkSettings := containerJSON.NetworkSettings.Networks[networkName]
	if networkSettings == nil {
		return "", fmt.Errorf("container is not connected to network %s", networkName)
	}

	return networkSettings.IPAddress, nil
}
