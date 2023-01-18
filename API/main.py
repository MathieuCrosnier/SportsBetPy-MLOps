from fastapi import FastAPI
import access
import prediction
import init_databases
import train_model

api = FastAPI(title = "API SportsBetPy")
api.include_router(access.router)
api.include_router(prediction.router)
api.include_router(init_databases.router)
api.include_router(train_model.router)

@api.get("/" , name = "Welcome message")
async def welcome_message():
    return "Bienvenue sur l'API de SportsBetPy"