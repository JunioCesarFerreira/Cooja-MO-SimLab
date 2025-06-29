from fastapi import APIRouter
from api.endpoints import experiment, simulation, simqueue, source

api_router = APIRouter()
api_router.include_router(experiment.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(simulation.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(simqueue.router, prefix="/queues", tags=["simulation-queues"])
api_router.include_router(source.router, prefix="/sources", tags=["sources"])
