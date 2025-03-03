using Microsoft.OpenApi.Models;
using SimAPI.Services;
using SimAPI.Models;
using System.Reflection;

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

            // Configuração do MongoDB
            builder.Services.Configure<SimulationDatabaseSettings>(
                builder.Configuration.GetSection("SimulationDatabase"));

            builder.Services.AddSingleton<SimulationService>();

            var app = builder.Build();

            // Configura o pipeline de solicitação HTTP
            app.UseSwagger();
            app.UseSwaggerUI(c =>
            {
                c.SwaggerEndpoint("/swagger/v1/swagger.json", "Simulation API v1");
            });

            app.UseHttpsRedirection();
            app.UseAuthorization();
            app.MapControllers();

            app.Run();
        }
    }
}