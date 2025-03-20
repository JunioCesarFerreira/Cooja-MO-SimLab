using Microsoft.OpenApi.Models;
using SimAPI.Services;
using SimAPI.Models;
using System.Reflection;
using MongoDB.Driver;

namespace SimAPI
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            // Adiciona serviços ao container
            builder.Services.AddControllers();
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc("v1", new OpenApiInfo
                {
                    Title = "Simulation API",
                    Version = "v1",
                    Description = "API REST para gerenciar simulações"
                });

                var xmlFile = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
                var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFile);
                c.IncludeXmlComments(xmlPath);
            });

            // Registrar política de CORS
            builder.Services.AddCors(options =>
            {
                options.AddPolicy("AllowAll", policy =>
                {
                    policy.AllowAnyOrigin()
                          .AllowAnyMethod()
                          .AllowAnyHeader();
                });
            });

            // Configuração do MongoDB - Ajustada para usar MONGO_URI do ambiente
            var mongoUri = Environment.GetEnvironmentVariable("MONGO_URI") ?? "mongodb://localhost:27017/?replicaSet=rs0";
            var simulationDbSettings = new SimulationDatabaseSettings
            {
                ConnectionString = mongoUri,
                DatabaseName = "simulation_db",
                ExperimentsCollectionName = "experiments",
                SimulationsCollectionName = "simulations"
            };

            builder.Services.AddSingleton<IMongoClient>(sp =>
            {
                return new MongoClient(simulationDbSettings.ConnectionString);
            });

            builder.Services.AddSingleton(sp =>
            {
                var dbName = simulationDbSettings.DatabaseName;
                var client = sp.GetRequiredService<IMongoClient>();
                return client.GetDatabase(dbName);
            });

            builder.Services.AddScoped<SimulationService>();
            builder.Services.AddScoped<ExperimentService>();

            var app = builder.Build();

            // Configura o pipeline de solicitação HTTP
            app.UseSwagger();
            app.UseSwaggerUI(c =>
            {
                c.SwaggerEndpoint("/swagger/v1/swagger.json", "Simulation API v1");
            });

            // Habilitar essa política globalmente
            app.UseCors("AllowAll");

            app.UseAuthorization();
            app.MapControllers();

            app.Run();
        }
    }
}