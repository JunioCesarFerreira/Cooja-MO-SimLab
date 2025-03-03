namespace SimAPI.Models
{
    /// <summary>
    /// Configuração inicial da simulação
    /// </summary>
    public class SimulationConfig
    {
        public string Name { get; set; } = null!;
        public int Duration { get; set; }

        /// <summary>
        /// Elementos da simulação
        /// </summary>
        public SimulationElements SimulationElements { get; set; } = new SimulationElements();
    }
}
