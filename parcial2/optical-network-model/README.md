# Optical Network Model

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoftazure&logoColor=white)

Un sistema de predicción del tiempo de respuesta en redes ópticas basado en redes neuronales artificiales, implementado como una aplicación cloud-native.

## Descripción

Esta aplicación utiliza modelos de machine learning para predecir tiempos de respuesta en redes ópticas basado en diversos parámetros de red. Diseñada con una arquitectura de microservicios, facilita su despliegue en entornos cloud y contenedores.

### Componentes

- **Backend (API REST)**: Implementado con FastAPI, proporciona endpoints para:
  - Predicción de tiempos de respuesta basada en parámetros de red
  - Análisis de correlación entre variables
  
- **Frontend**: Interfaz web interactiva que incluye:
  - Formulario para ingresar parámetros de red
  - Visualización en tiempo real de predicciones
  - Matriz de correlación interactiva
  - Animación de fondo que simula una red óptica

## Tecnologías

- **Backend**: Python, FastAPI, Numpy, Pandas, Scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, D3.js
- **Contenedores**: Docker
- **Orquestación**: Kubernetes (AKS)
- **Cloud**: Microsoft Azure

## Guía de Despliegue

### Requisitos Previos

- Cuenta de Azure con acceso a AKS
- Azure CLI configurado
- kubectl instalado
- Docker instalado (para construcción local)

### Creación y Conexión al Cluster AKS

```bash
# Crear cluster AKS (si no existe)
az aks create --resource-group recursosParcial2 --name AKSparcial2 --node-count 3 --enable-addons monitoring --generate-ssh-keys

# Conectarse al cluster
az aks get-credentials --resource-group recursosParcial2 --name AKSparcial2

# Verificar nodos
kubectl get nodes
```

### Construcción y Publicación de Imágenes

```bash
# Login a Docker Hub
docker login

# Construir imágenes
docker build -t <usuario>/optical-network-api:latest .
docker build -t <usuario>/optical-network-frontend:latest -f Dockerfile.frontend .

# Publicar imágenes
docker push <usuario>/optical-network-api:latest
docker push <usuario>/optical-network-frontend:latest
```

> **Nota**: Puedes usar las imágenes ya publicadas: `miguelank/optical-network-api:latest` y `miguelank/optical-network-frontend:latest`

### Despliegue en Kubernetes

```bash
# 1. Desplegar backend
kubectl apply -f kubernetes/neural-network-deployment.yaml

# 2. Desplegar frontend
kubectl apply -f kubernetes/frontend-deployment.yaml

# 3. Configurar ingress
kubectl apply -f kubernetes/ingress.yaml

# Verificar despliegue
kubectl get pods
kubectl get services
kubectl get ingress
```

## Funcionalidades

- Predicción de tiempos de respuesta en redes ópticas
- Análisis de correlación entre variables de red
- Visualización interactiva de matrices de correlación
- Simulación visual de redes ópticas

## Autores

Desarrollado como proyecto para el curso de Cloud Computing en la Universidad Autónoma de Occidente (2025).

