package remote

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func (s *SSHClient) CopyFileToRemote(localPath, remotePath string) error {
	file, err := os.Open(localPath)
	if err != nil {
		return fmt.Errorf("failed to open local file: %v", err)
	}
	defer file.Close()

	fileInfo, err := file.Stat()
	if err != nil {
		return fmt.Errorf("failed to stat local file: %v", err)
	}

	session, err := s.client.NewSession()
	if err != nil {
		return fmt.Errorf("failed to create SSH session: %v", err)
	}
	defer session.Close()

	go func() {
		w, _ := session.StdinPipe()
		defer w.Close()

		fmt.Fprintf(w, "C%#o %d %s\n", fileInfo.Mode().Perm(), fileInfo.Size(), filepath.Base(remotePath))
		io.Copy(w, file)
		fmt.Fprint(w, "\x00")
	}()

	cmd := fmt.Sprintf("mkdir -p %s && cd %s && /usr/bin/scp -t .", filepath.Dir(remotePath), filepath.Dir(remotePath))
	if err := session.Run(cmd); err != nil {
		return fmt.Errorf("failed to run SCP command: %v", err)
	}

	return nil
}

func (s *SSHClient) CopyFileFromRemote(remotePath, localPath string) error {
	session, err := s.client.NewSession()
	if err != nil {
		return fmt.Errorf("failed to create SSH session: %v", err)
	}
	defer session.Close()

	// Criar diretório local se não existir
	if err := os.MkdirAll(filepath.Dir(localPath), 0755); err != nil {
		return fmt.Errorf("failed to create local directory: %v", err)
	}

	file, err := os.Create(localPath)
	if err != nil {
		return fmt.Errorf("failed to create local file: %v", err)
	}
	defer file.Close()

	stdout, err := session.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to get stdout pipe: %v", err)
	}

	cmd := fmt.Sprintf("/usr/bin/scp -f %s", remotePath)
	if err := session.Start(cmd); err != nil {
		return fmt.Errorf("failed to start SCP command: %v", err)
	}

	// Protocolo SCP básico
	var buffer [1]byte
	stdout.Read(buffer[:])

	w, _ := session.StdinPipe()
	defer w.Close()

	fmt.Fprint(w, "\x00")

	// Ignorar a linha com metadados
	var header string
	fmt.Fscanf(stdout, "%s\n", &header)

	fmt.Fprint(w, "\x00")

	// Copiar conteúdo do arquivo
	if _, err := io.Copy(file, stdout); err != nil {
		return fmt.Errorf("failed to copy file data: %v", err)
	}

	fmt.Fprint(w, "\x00")

	return nil
}
