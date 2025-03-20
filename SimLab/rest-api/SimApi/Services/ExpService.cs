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

        public async Task<ExperimentBase?> GetAsync(string id) =>
            await _experimentsCollection.Find(x => x.Id == id).FirstOrDefaultAsync();

        public async Task<ExperimentBase?> GetByNameAsync(string name) =>
            await _experimentsCollection.Find(x => x.Name == name).FirstOrDefaultAsync();

        public async Task<Experiment> CreateAsync(ExperimentBase experiment)
        {
            var newExperiment = new Experiment{
                Name = experiment.Name,
                Status = experiment.Status,
                StartTime = experiment.StartTime,
                EndTime = experiment.EndTime,
                SimulationElements = experiment.SimulationElements,
            };
            await _experimentsCollection.InsertOneAsync(newExperiment);
            return newExperiment;
        }

        public async Task UpdateAsync(string id, Experiment updatedExperiment) =>
            await _experimentsCollection.ReplaceOneAsync(x => x.Id == id, updatedExperiment);

        public async Task<ExperimentBase?> StopExperimentAsync(string id)
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
}