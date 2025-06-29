# MO-Cooja-Sim

## Visão Geral
Neste repositório apresento uma pesquisa sobre um sistema de simulação escalável para otimização multiobjetivo utilizando Cooja e Docker. Ele permite simulações distribuídas de algoritmos evolutivos em um ambiente conteinerizado, gerenciando eficientemente os fluxos de experimentos com Python, Go e MongoDB.

## Conteúdo
- **SimLab**: 

## Arquitetura do Sistema
O sistema é composto por três componentes principais:

1. **Módulo de Algoritmo Evolutivo em Python**
   - Executa um algoritmo evolutivo para gerar novas soluções candidatas.
   - Enfileira os elementos de cada nova geração no MongoDB para simulação.
   - Escuta os resultados das simulações via MongoDB Change Stream.

2. **Master-Node (Aplicação em Go)**
   - Consome a fila de simulações no MongoDB.
   - Cria dinamicamente containers Docker para execução das simulações.
   - Transfere os dados de entrada da simulação via SCP.
   - Monitora o processo de simulação via SSH.
   - Registra os resultados das simulações de volta no MongoDB.
   - Destroi o container de simulação após a execução.

3. **Containers de Simulação com Cooja**
   - Cada container executa uma instância do Cooja para processar uma única tarefa de simulação.
   - Recebe os dados de entrada do Master-Node.
   - Gera e retorna os resultados da simulação.

## Funcionalidades
- **Execução Escalável:** Provisão dinâmica de containers garante uso eficiente dos recursos.
- **Processamento Distribuído:** Execução paralela de múltiplas simulações.
- **Fluxo de Dados Integrado:** Integração com MongoDB para processamento em tempo real dos resultados.
- **Automação:** Execução totalmente automatizada, desde a evolução do algoritmo até a coleta dos resultados.

## Instalação
### Pré-requisitos
- Docker e Docker Compose
- Python (>= 3.12)
- Go (>= 1.23)
- MongoDB
- [Imagem Docker do Cooja (ambiente Contiki-NG)](https://github.com/JunioCesarFerreira/Cooja-Docker-VM-Setup)

### Instruções de Configuração

*Ainda não foram concluídas.*

## Uso

*Ainda não foram concluídas.*

## Melhorias Futuras
- Implementar mecanismos avançados de escalonamento para priorização de simulações.
- Otimizar o gerenciamento do ciclo de vida dos containers para reduzir custos.
- Estender o suporte a outras técnicas de otimização.

## Licença
Este projeto está licenciado sob a [Licença MIT](./LICENSE).

## Contribuições
Contribuições são bem-vindas! Envie issues ou pull requests com sugestões de melhorias.
