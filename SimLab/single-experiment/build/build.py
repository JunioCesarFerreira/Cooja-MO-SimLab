import json
from pathlib import Path

import os
import sys

# Para utilizar a biblioteca interna
project_path = os.path.abspath(os.path.join(os.getcwd(), "../..")) 
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pylib import files

DATA_DIR = Path("data")
INPUT_JSON = DATA_DIR / "inputExample.json"
TEMPLATE_XML = DATA_DIR / "simulation_template.xml"

OUTPUT_DIR = Path("output")
OUTSIM_XML = OUTPUT_DIR / "simulation.xml"
OUTPOS_DAT = OUTPUT_DIR / "positions.dat"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    experiment_data = json.load(f)
    
sim_model = experiment_data["simulationModel"]

files.convert_simulation_files(sim_model, TEMPLATE_XML, OUTSIM_XML, OUTPOS_DAT)
