using MongoDB.Driver;
using SimAPI.Models;

namespace SimAPI.Services
{
    public class SimulationService
    {
        private readonly IMongoCollection<Simulation> _simulationsCollection;

        public SimulationService(IMongoDatabase database)
        {
            _simulationsCollection = database.GetCollection<Simulation>("simulations");
        }

        public async Task<List<Simulation>> GetAsync() =>
            await _simulationsCollection.Find(_ => true).ToListAsync();

        public async Task<Simulation?> GetAsync(string id) =>
            await _simulationsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();

        public async Task<Simulation> CreateAsync(SimulationBase simulation)
        {
            var newSimulation = new Simulation
            {
                ExperimentId = simulation.ExperimentId,
                Generation = simulation.Generation,
                Name = simulation.Name,
                Duration = simulation.Duration,
                Status = simulation.Status,
                StartTime = simulation.StartTime,
                EndTime = simulation.EndTime,
                CurrentValue = simulation.CurrentValue,
                Progress = simulation.Progress,
                SimulationElements = simulation.SimulationElements,
            };
            await _simulationsCollection.InsertOneAsync(newSimulation);
            return newSimulation;
        }

        public async Task UpdateAsync(string id, Simulation updatedSimulation) =>
            await _simulationsCollection.ReplaceOneAsync(x => x.Id == id, updatedSimulation);

        public async Task<Simulation?> StopSimulationAsync(string id)
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