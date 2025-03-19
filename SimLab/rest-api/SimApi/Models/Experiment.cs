using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace SimAPI.Models
{
    /// <summary>
    /// Modelo de um experimento
    /// </summary>
    public class Experiment
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; } = null!;
        public string Name { get; set; } = null!;
        public string Status { get; set; } = "Waiting";
        public DateTime StartTime { get; set; }
        public DateTime? EndTime { get; set; }

        /// <summary>
        /// Parâmetros para algoritmo evolutivo
        /// </summary>
        public Dictionary<string, object> Parameters { get; set; } = [];

        /// <summary>
        /// Modelo para simulações
        /// </summary>
        public SimulationElements SimulationElements { get; set; } = new SimulationElements();
    }
}
