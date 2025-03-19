using Microsoft.AspNetCore.Mvc;
using SimAPI.Models;
using SimAPI.Services;

namespace SimAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SimulationController : ControllerBase
    {
        private readonly SimulationService _simulationService;

        public SimulationController(SimulationService simulationService)
        {
            _simulationService = simulationService;
        }

        /// <summary>
        /// Inicia uma nova simulação com a configuração fornecida
        /// </summary>
        /// <param name="config">Configuração inicial da simulação</param>
        /// <returns>Status da simulação recém-criada</returns>
        /// <response code="201">Retorna a simulação recém-criada</response>
        /// <response code="400">Se o objeto de configuração for nulo</response>
        [HttpPost("start")]
        [ProducesResponseType(StatusCodes.Status201Created)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public async Task<ActionResult<Simulation>> StartSimulation(Simulation config)
        {
            if (config == null)
            {
                return BadRequest("Configuração de simulação é obrigatória");
            }

            var simulationStatus = await _simulationService.CreateAsync(config);

            return CreatedAtAction(nameof(GetSimulationStatus), new { id = simulationStatus.Id }, simulationStatus);
        }

        /// <summary>
        /// Para uma simulação em execução
        /// </summary>
        /// <param name="id">ID da simulação</param>
        /// <returns>Status atualizado da simulação</returns>
        /// <response code="200">Retorna o status atualizado</response>
        /// <response code="404">Se a simulação não for encontrada</response>
        [HttpPut("stop/{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<Simulation>> StopSimulation(string id)
        {
            var simulation = await _simulationService.StopSimulationAsync(id);

            if (simulation == null)
            {
                return NotFound($"Simulação com ID {id} não encontrada");
            }

            return Ok(simulation);
        }

        /// <summary>
        /// Obtém o status atual de uma simulação
        /// </summary>
        /// <param name="id">ID da simulação</param>
        /// <returns>Status atual da simulação</returns>
        /// <response code="200">Retorna o status da simulação</response>
        /// <response code="404">Se a simulação não for encontrada</response>
        [HttpGet("status/{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<Simulation>> GetSimulationStatus(string id)
        {
            var simulation = await _simulationService.GetAsync(id);

            if (simulation == null)
            {
                return NotFound($"Simulação com ID {id} não encontrada");
            }

            return Ok(simulation);
        }

        /// <summary>
        /// Obtém todas simulações
        /// </summary>
        /// <returns>Status atual da simulação</returns>
        /// <response code="200">Retorna o status da simulação</response>
        /// <response code="404">Se a simulação não for encontrada</response>
        [HttpGet("all")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<Simulation>> GetSimulations()
        {
            var simulation = await _simulationService.GetAsync();

            if (simulation == null)
            {
                return NotFound("Nenhuma simulação foi encontrada");
            }

            return Ok(simulation);
        }
    }
}