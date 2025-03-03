namespace SimAPI.Models
{
    /// <summary>
    /// Representa uma configuração de rede de motes
    /// </summary>
    public class SimulationElements
    {
        // Coleção de motes fixos
        public List<FixedMote> FixedMotes { get; set; } = new List<FixedMote>();
        // Coleção de motes móveis
        public List<MobileMote> MobileMotes { get; set; } = new List<MobileMote>();
    }

    /// <summary>
    /// Mote Fixo
    /// </summary>
    public class FixedMote
    {
        // Posição do mote no espaço euclidiano
        public List<int> Position { get; set; } = new List<int>();

        // Nome do mote
        public string Name { get; set; } = null!;

        // Caminho do código fonte a ser executado no mote
        public string SourceCode { get; set; } = null!;
    }

    /// <summary>
    /// Mote móvel
    /// </summary>
    public class MobileMote
    {
        // Função f:[0,1]-->R^2 que determina o caminho do mote
        public List<string> FunctionPath { get; set; } = new List<string>();

        // Indica que o caminho é fechado
        public bool IsClosed { get; set; }

        // Indica que o mote deve ir e voltar no caminho definido
        public bool IsRoundTrip { get; set; }

        // Velociade do mote
        public int Speed { get; set; }

        // Tamanho dos passos do movimento simulado
        public int TimeStep { get; set; }

        // Nome do mote
        public string Name { get; set; } = null!;

        // Caminho do código fonte a ser executado no mote
        public string SourceCode { get; set; } = null!;
    }
}