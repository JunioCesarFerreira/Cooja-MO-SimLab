from strategy.base import EngineStrategy
from pylib.rand_pts import network_gen
from pylib.dto import Simulation, SimulationConfig, Generation
from pylib.mongo_db import SimulationStatus
from datetime import datetime

class GeneratorRandomStrategy(EngineStrategy):
    def start(self):
        params = self.experiment.get("parameters", {})
        num = int(params.get("number", 10))
        region = tuple(params.get("region", (0, 0, 100, 100)))
        radius = float(params.get("radius", 25.0))

        simulation_ids = []
        for i in range(num):
            points = network_gen(amount=num, region=region, radius=radius)
            fixed = [{"name": f"m{j}", "position": [x, y], "sourceCode": "default", "radiusOfReach": radius, "radiusOfInter": radius}
                     for j, (x, y) in enumerate(points)]

            config: SimulationConfig = {
                "name": f"auto-{i}",
                "duration": 300.0,
                "radiusOfReach": radius,
                "radiusOfInter": radius,
                "region": region,
                "simulationElements": {
                    "fixedMotes": fixed,
                    "mobileMotes": []
                }
            }

            sim_doc: Simulation = {
                "id": i,
                "status": "Waiting",
                "start_time": None,
                "end_time": None,
                "parameters": config,
                "pos_file_id": "",
                "csc_file_id": "",
                "log_cooja_id": "",
                "runtime_log_id": "",
                "csv_log_id": ""
            }

            sim_id = self.mongo.simulation_repo.insert(sim_doc)
            simulation_ids.append(str(sim_id))

        queue: Generation = {
            "id": "",
            "status": SimulationStatus.WAITING,
            "start_time": datetime.now(),
            "end_time": None,
            "simulations_ids": simulation_ids
        }

        queue_id = self.mongo.simulation_queue_repo.insert(queue)

        self.mongo.experiment_repo.update(str(self.experiment["_id"]), {
            "status": SimulationStatus.RUNNING,
            "end_time": datetime.now(),
            "generations_ids": [str(queue_id)]
        })

    def on_simulation_result(self, result_doc: dict):
        pass  # não faz nada, pois é um algoritmo que executa uma única vez
