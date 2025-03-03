using Microsoft.Extensions.Options;
using MongoDB.Driver;
using SimAPI.Models;

namespace SimAPI.Services
{
    public class SimulationService
    {
        private readonly IMongoCollection<SimulationStatus> _simulationsCollection;

        public SimulationService(IMongoDatabase database)
        {
            _simulationsCollection = database.GetCollection<SimulationStatus>("simulations");
        }

        public async Task<List<SimulationStatus>> GetAsync() =>
            await _simulationsCollection.Find(_ => true).ToListAsync();

        public async Task<SimulationStatus?> GetAsync(string id) =>
            await _simulationsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();

        public async Task<SimulationStatus> CreateAsync(SimulationConfig simulationConfig)
        {
            var simulationStatus = new SimulationStatus
            {
                Name = simulationConfig.Name,
                Status = "Running",
                StartTime = DateTime.UtcNow,
                Progress = 0
            };

            await _simulationsCollection.InsertOneAsync(simulationStatus);
            return simulationStatus;
        }

        public async Task UpdateAsync(string id, SimulationStatus updatedSimulation) =>
            await _simulationsCollection.ReplaceOneAsync(x => x.Id == id, updatedSimulation);

        public async Task<SimulationStatus?> StopSimulationAsync(string id)
        {
            var simulation = await _simulationsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();
            
            if (simulation != null)
            {
                simulation.Status = "Stopped";
                simulation.EndTime = DateTime.UtcNow;
                await _simulationsCollection.ReplaceOneAsync(x => x.Id == id, simulation);
            }
            
            return simulation;
        }
    }
}