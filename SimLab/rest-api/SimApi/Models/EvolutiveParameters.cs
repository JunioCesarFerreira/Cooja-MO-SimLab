using System;
using System.Collections.Generic;

namespace SimAPI.Models
{
    /// <summary>
    /// Representa a configuração de parâmetros evolutivos para algoritmos MOE.
    /// Este modelo pode ser serializado e armazenado como byte[] ou BsonDocument no MongoDB.
    /// </summary>
    public class EvolutiveParameters
    {
        public string Algorithm { get; set; } = "NSGA-III"; // Nome do algoritmo
        public int PopulationSize { get; set; } = 30;
        public int Generations { get; set; } = 10;
        public double CrossoverProbability { get; set; } = 0.9;
        public double MutationProbability { get; set; } = 0.1;

        /// <summary>
        /// Estratégia de seleção (ex: tournament, roulette, etc)
        /// </summary>
        public string SelectionStrategy { get; set; } = "tournament";

        /// <summary>
        /// Operador de crossover (ex: SBX, PMX)
        /// </summary>
        public string CrossoverOperator { get; set; } = "SBX";

        /// <summary>
        /// Operador de mutação (ex: Polynomial, Gaussian)
        /// </summary>
        public string MutationOperator { get; set; } = "Polynomial";

        /// <summary>
        /// Lista genérica de parâmetros adicionais por nome e valor.
        /// Pode ser usada para parâmetros específicos de cada algoritmo.
        /// </summary>
        public List<NamedParameter> AdditionalParameters { get; set; } = new();
    }

    /// <summary>
    /// Representa um parâmetro nomeado genérico (name-type-value).
    /// Pode ser estendido conforme necessário.
    /// </summary>
    public class NamedParameter
    {
        public string Name { get; set; } = null!;
        public string Type { get; set; } = "string"; // "int", "double", "bool", etc
        public string Value { get; set; } = "";      // Armazenado como string para flexibilidade
    }
}
