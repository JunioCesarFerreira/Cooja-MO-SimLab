from strategy.base import EngineStrategy
from pylib.rand_pts import network_gen
from pylib.dto import Simulation, SimulationConfig, Generation
from pylib.mongo_db import SimulationStatus
from pylib import visual
from datetime import datetime
from strategy.build_sim_input import create_files

class GeneratorRandomStrategy(EngineStrategy):
    def start(self):
        exp_id = self.experiment["_id"]
        params = self.experiment.get("parameters", {})
        num = int(params.get("number", 10))
        size = int(params.get("size", 10))
        region = tuple(params.get("region", (-100, -100, 100, 100)))
        radius = float(params.get("radius", 50))
        interf = float(params.get("interf", 60))

        gen: Generation = {
            "index": 1,
            "experiment_id": exp_id,
            "status": SimulationStatus.WAITING,
            "start_time": datetime.now(),
            "end_time": None,
            "simulations_ids": []
        }
        
        gen_id = self.mongo.generation_repo.insert(gen)
        
        simulation_ids = []
        for i in range(num):
            points = network_gen(amount=size, region=region, radius=radius)
            fixed = [{"name": f"m{j}", "position": [x, y], "sourceCode": "default", "radiusOfReach": radius, "radiusOfInter": interf}
                     for j, (x, y) in enumerate(points)]

            config: SimulationConfig = {
                "name": f"auto-{i}",
                "duration": 120,
                "radiusOfReach": radius,
                "radiusOfInter": interf,
                "region": region,
                "simulationElements": {
                    "fixedMotes": fixed,
                    "mobileMotes": []
                }
            }
            
            files_ids = create_files(config, self.mongo.fs_handler)
            
            visual.plot_network_save_from_sim(f'./tmp/{exp_id}-{gen_id}-{i}', config)

            sim_doc: Simulation = {
                "id": i,
                "experiment_id": exp_id,
                "generation_id": gen_id,
                "status": "Waiting",
                "start_time": None,
                "end_time": None,
                "parameters": config,
                "pos_file_id": files_ids["pos_file_id"],
                "csc_file_id": files_ids["csc_file_id"],
                "log_cooja_id": "",
                "runtime_log_id": "",
                "csv_log_id": ""
            }
            

            sim_id = self.mongo.simulation_repo.insert(sim_doc)
            simulation_ids.append(str(sim_id))

        gen["simulations_ids"] = simulation_ids

        self.mongo.generation_repo.update(str(gen_id), gen)

        self.mongo.experiment_repo.update(str(exp_id), {
            "status": SimulationStatus.RUNNING,
            "end_time": datetime.now(),
            "generations_ids": [str(gen_id)]
        })

    def on_simulation_result(self, result_doc: dict):
        pass  # não faz nada, pois é um algoritmo que executa uma única vez
