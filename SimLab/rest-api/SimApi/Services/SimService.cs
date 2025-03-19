using MongoDB.Driver;
using SimAPI.Models;

namespace SimAPI.Services
{
    public class ExperimentService
    {
        private readonly IMongoCollection<Experiment> _experimentsCollection;

        public ExperimentService(IMongoDatabase database)
        {
            _experimentsCollection = database.GetCollection<Experiment>("experiments");
        }

        public async Task<List<Experiment>> GetAsync() =>
            await _experimentsCollection.Find(_ => true).ToListAsync();

        public async Task<Experiment?> GetAsync(string id) =>
            await _experimentsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();

        public async Task<Experiment?> GetByNameAsync(string name) =>
            await _experimentsCollection.Find(x => x.Name == name).FirstOrDefaultAsync();

        public async Task<Experiment> CreateAsync(Experiment experiment)
        {
            await _experimentsCollection.InsertOneAsync(experiment);
            return experiment;
        }

        public async Task UpdateAsync(string id, Experiment updatedExperiment) =>
            await _experimentsCollection.ReplaceOneAsync(x => x.Id == id, updatedExperiment);

        public async Task<Experiment?> StopExperimentAsync(string id)
        {
            var experiment = await _experimentsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();
            
            if (experiment != null)
            {
                experiment.Status = "Stopped";
                experiment.EndTime = DateTime.UtcNow;
                await _experimentsCollection.ReplaceOneAsync(x => x.Id == id, experiment);
            }
            
            return experiment;
        }
    }

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

        public async Task<Simulation> CreateAsync(Simulation simulation)
        {
            await _simulationsCollection.InsertOneAsync(simulation);
            return simulation;
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