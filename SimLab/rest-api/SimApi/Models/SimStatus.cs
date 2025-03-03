using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace SimAPI.Models
{
    /// <summary>
    /// Status atual da simulação
    /// </summary>
    public class SimulationStatus
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; } = null!;
        
        public string Name { get; set; } = null!;
        public string Status { get; set; } = "Stopped";
        public DateTime StartTime { get; set; }
        public DateTime? EndTime { get; set; }
        public double CurrentValue { get; set; }
        public int Progress { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
    }
}