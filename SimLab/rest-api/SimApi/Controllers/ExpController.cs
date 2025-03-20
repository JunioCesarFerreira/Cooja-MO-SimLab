using Microsoft.AspNetCore.Mvc;
using SimAPI.Models;
using SimAPI.Services;

namespace SimAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ExperimentController : ControllerBase
    {
        private readonly ExperimentService _experimentService;

        public ExperimentController(ExperimentService experimentService)
        {
            _experimentService = experimentService;
        }

        /// <summary>
        /// Inicia um novo experimento
        /// </summary>
        /// <param name="config">Configuração do experimento</param>
        /// <returns>Status da experimento recém-criada</returns>
        /// <response code="201">Retorna a experimento recém-criada</response>
        /// <response code="400">Se o objeto de configuração for nulo</response>
        [HttpPost("start")]
        [ProducesResponseType(StatusCodes.Status201Created)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public async Task<ActionResult<Experiment>> StartExperiment(ExperimentBase config)
        {
            if (config == null)
            {
                return BadRequest("Configuração de experimento é obrigatória");
            }

            var simulationStatus = await _experimentService.CreateAsync(config);

            return CreatedAtAction(nameof(GetExperimentStatus), new { id = simulationStatus.Id }, simulationStatus);
        }

        /// <summary>
        /// Para um experimento em execução
        /// </summary>
        /// <param name="id">ID da experimento</param>
        /// <returns>Status atualizado da experimento</returns>
        /// <response code="200">Retorna o status atualizado</response>
        /// <response code="404">Se a experimento não for encontrado</response>
        [HttpPut("stop/{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<ExperimentBase>> StopExperiment(string id)
        {
            var simulation = await _experimentService.StopExperimentAsync(id);

            if (simulation == null)
            {
                return NotFound($"Experimento com ID {id} não encontrado");
            }

            return Ok(simulation);
        }

        /// <summary>
        /// Obtém o status atual de um experimento
        /// </summary>
        /// <param name="id">ID da experimento</param>
        /// <returns>Status atual da experimento</returns>
        /// <response code="200">Retorna o status da experimento</response>
        /// <response code="404">Se a experimento não for encontrado</response>
        [HttpGet("status/{id}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<ExperimentBase>> GetExperimentStatus(string id)
        {
            var simulation = await _experimentService.GetAsync(id);

            if (simulation == null)
            {
                return NotFound($"Experimento com ID {id} não encontrado");
            }

            return Ok(simulation);
        }

        /// <summary>
        /// Obtém todas simulações
        /// </summary>
        /// <returns>Status atual da experimento</returns>
        /// <response code="200">Retorna o status da experimento</response>
        /// <response code="404">Se a experimento não for encontrado</response>
        [HttpGet("all")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<ActionResult<ExperimentBase>> GetExperiments()
        {
            var simulation = await _experimentService.GetAsync();

            if (simulation == null)
            {
                return NotFound("Nenhuma experimento foi encontrado");
            }

            return Ok(simulation);
        }
    }
}