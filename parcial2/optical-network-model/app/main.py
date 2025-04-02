from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from model import OpticalNetworkModel
from pydantic import BaseModel
from typing import List, Optional

# Define request model for prediction
class PredictionRequest(BaseModel):
    nodeNumber: float
    threadNumber: float
    tr: float
    processorUtilization: float
    channelWaitingTime: float
    inputWaitingTime: float
    channelUtilization: float
    spatialDistribution: str
    temporalDistribution: str

# Define response model
class PredictionResponse(BaseModel):
    prediction: float
    inferenceTime: float

app = FastAPI()

# Añadir soporte CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las origenes (puedes restringir esto en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
model = OpticalNetworkModel()

@app.get("/")
async def root():
    return {"message": "Optical Network Neural Network API"}

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        # Extraer los datos del request
        numeric_inputs = [
            request.nodeNumber,
            request.threadNumber,
            request.tr,
            request.processorUtilization,
            request.channelWaitingTime,
            request.inputWaitingTime,
            request.channelUtilization
        ]
        spatial_dist = request.spatialDistribution
        temporal_dist = request.temporalDistribution
        
        # Mide el tiempo de inferencia
        start_time = time.time()
        prediction = model.predict(numeric_inputs, spatial_dist, temporal_dist)
        inference_time = (time.time() - start_time) * 1000000  # microsegundos
        
        # Retorna la respuesta
        return PredictionResponse(
            prediction=prediction,
            inferenceTime=inference_time
        )
    
    except Exception as e:
        # En una aplicación real, deberías manejar errores específicos
        # y retornar códigos de error HTTP apropiados
        return {"error": str(e)}