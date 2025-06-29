import json
import argparse
import os


def overwrite_json_input_file(
    embed_file: str,
    region: tuple[float, float, float, float],
    radius: float,
    interference_radius: float
) -> dict:
    """
    Gera um dicionário no formato esperado para o arquivo de entrada JSON da simulação.

    Parameters:
    - embed_file: caminho para o arquivo JSON a ser embutido
    - region: tupla (x_min, y_min, x_max, y_max) definindo a região da simulação
    - radius: raio de comunicação dos motes
    - interference_radius: raio de interferência dos motes

    Returns:
    - Um dicionário com a estrutura especificada para o modelo de simulação
    """
    with open(embed_file, 'r', encoding='utf-8') as f:
        embed_json_data = json.load(f)

    simulation_model = {
        "simulationModel": {
            "name": "single-experiment-sim-lab",
            "duration": 60,
            "radiusOfReach": radius,
            "radiusOfInter": interference_radius,
            "region": list(region),
            "simulationElements": embed_json_data
        }
    }

    return simulation_model


def main():
    parser = argparse.ArgumentParser(description="Gera o arquivo de entrada para a simulação.")
    parser.add_argument("embed_file", type=str, help="Caminho para o JSON com os elementos de simulação.")
    parser.add_argument("--region", nargs=4, type=float, default=[-200, -200, 200, 200],
                        help="Região da simulação: x_min y_min x_max y_max")
    parser.add_argument("--radius", type=float, default=50, help="Raio de comunicação dos motes.")
    parser.add_argument("--interference_radius", type=float, default=60, help="Raio de interferência dos motes.")
    parser.add_argument("--output", type=str, default="data/inputExample.json", help="Arquivo de saída JSON.")

    args = parser.parse_args()

    result = overwrite_json_input_file(
        embed_file=args.embed_file,
        region=tuple(args.region),
        radius=args.radius,
        interference_radius=args.interference_radius
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"[✔] Arquivo gerado: {args.output}")


if __name__ == "__main__":
    main()
