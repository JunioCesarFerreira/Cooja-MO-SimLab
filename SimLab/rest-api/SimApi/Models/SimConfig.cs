namespace SimAPI.Models
{
    /// <summary>
    /// Configuração inicial da simulação
    /// </summary>
    public class SimulationConfig
    {
        public string Name { get; set; } = null!;
        public int Duration { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();

        /// <summary>
        /// Elementos da simulação
        /// </summary>
        public SimulationElements SimulationElements { get; set; } = new SimulationElements();
    }
}
