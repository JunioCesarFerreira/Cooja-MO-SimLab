namespace SimAPI.Models
{
    public class SimulationDatabaseSettings
    {
        public string ConnectionString { get; set; } = null!;
        public string DatabaseName { get; set; } = null!;
        public string ExperimentsCollectionName { get; set; } = null!;
        public string SimulationsCollectionName { get; set; } = null!;
    }
}