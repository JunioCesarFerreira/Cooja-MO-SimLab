from typing import TypedDict, Any
from datetime import datetime
from bson import ObjectId

class BaseMote(TypedDict):
    name: str
    sourceCode: str
    radiusOfReach: float # Atenção! no Cooja este atributo não é utilizado.
    radiusOfInter: float # Atenção! no Cooja este atributo não é utilizado.

class FixedMote(BaseMote, TypedDict):
    position: list[float] # A priori no plano

class MobileMote(BaseMote, TypedDict):
    functionPath: list[tuple[str, str]]  # Lista de tuplas cada par define uma parte da paremetrização
    isClosed: bool
    isRoundTrip: bool
    speed: float
    timeStep: float

class SimulationElements(TypedDict):
    fixedMotes: list[FixedMote]
    mobileMotes: list[MobileMote]
    
class SimulationConfig(TypedDict):
    name: str
    duration: float
    radiusOfReach: float # Cooja admite apenas redes homogeneas
    radiusOfInter: float # Cooja admite apenas redes homogeneas
    region: tuple[float, float, float, float]
    simulationElements: SimulationElements
    
    
# Database

class SourceFile(TypedDict):
    id: str          # ID do arquivo
    file_name: str   # Nome do arquivo
    
class SourceRepository(TypedDict):
    id: str
    name : str
    description: str
    source_files: list[SourceFile]
    
class Simulation(TypedDict):
    id: str
    experiment_id: ObjectId
    generation_id: ObjectId
    status: str
    start_time: datetime
    end_time: datetime
    parameters: SimulationConfig
    pos_file_id: str
    csc_file_id: str
    log_cooja_id: str
    runtime_log_id: str
    csv_log_id: str
    
class Generation(TypedDict):
    id: str
    index: int
    experiment_id: ObjectId
    status: str
    start_time: datetime
    end_time: datetime
    simulations_ids: list[ObjectId]
    
class Experiment(TypedDict):
    id: str
    name: str
    status: str
    created_time: datetime
    start_time: datetime
    end_time: datetime
    parameters: dict[str, Any]
    generations: list[ObjectId]
    source_repository_id: str
    
