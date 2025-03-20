using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace SimAPI.Models
{
    /// <summary>
    /// Modelo de um experimento
    /// </summary>
    public class ExperimentBase
    {
        public string Name { get; set; } = "";
        public string Status { get; set; } = "Waiting";
        public DateTime StartTime { get; set; }
        public DateTime? EndTime { get; set; }

        public KeyValue[] Parameters { get; set; } = [];

        /// <summary>
        /// Modelo para simulações
        /// </summary>
        public SimulationElements SimulationElements { get; set; } = new SimulationElements();
    }

    /// <summary>
    /// Modelo de um experimento
    /// </summary>
    public class Experiment : ExperimentBase
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; } = null!;
    }
    
    public class KeyValue
    {
        public string Key { get; set; } = null!;
        public string Value { get; set; } = null!;
    }
}
