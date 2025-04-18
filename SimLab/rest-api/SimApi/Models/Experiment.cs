using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace SimAPI.Models
{

    /// <summary>
    /// Modelo de um experimento para armazenamento no MongoDB
    /// </summary>
    public class Experiment : ExperimentBase
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; } = null!;
    }

    /// <summary>
    /// Modelo de um experimento
    /// </summary>
    public class ExperimentBase
    {
        public string Name { get; set; } = "";
        public string Status { get; set; } = "Waiting";
        
        public DateTime EnqueuedTime { get; set; }
        public DateTime? StartTime { get; set; }
        public DateTime? EndTime { get; set; }

        public List<LinkedFile> LinkedFiles { get; set; } = [];

        public EvolutiveParameters EvolutiveParameters {get;set;};

        /// <summary>
        /// Modelo para simulações
        /// </summary>
        public SimulationElements SimulationModel { get; set; } = new SimulationElements();

        public List<Generation> Generations { get; set; }
    }
    
    public class LinkedFile
    {
        public string Name { get; set; } = null!;

        [BsonRepresentation(BsonType.ObjectId)]
        public string FileId { get; set; } = null!;
    }
    
    public class Generation
    {
        public int NumberOfGeneration;

        [BsonRepresentation(BsonType.ObjectId[])]
        public List<string> Population {get; set;} = null!;
        
        [BsonRepresentation(BsonType.ObjectId[])]
        public List<string> LogSimFiles { get; set; } = null!;
    }
}
