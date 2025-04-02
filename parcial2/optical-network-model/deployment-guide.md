# Guía de Despliegue para Optical Network Model

## Configuración previa

### Para conectarse al cluster AKS
az aks get-credentials --resource-group recursosParcial2 --name AKSparcial2

### 1. Crear el modelo en Python

Asegúrate de crear el archivo `model.py` en la carpeta `app` con la implementación de la clase `OpticalNetworkModel`:

```python
# app/model.py
import numpy as np
from sklearn.preprocessing import StandardScaler

class OpticalNetworkModel:
    def __init__(self):
        # Simulación de carga de modelo - En un caso real cargarías pesos de un modelo entrenado
        print("Inicializando modelo de red neuronal...")
        
    def predict(self, numeric_inputs, spatial_dist, temporal_dist):
        """
        Predice el tiempo de respuesta basado en los parámetros de la red
        
        Args:
            numeric_inputs (list): Lista de 7 valores numéricos [nodeNumber, threadNumber, tr, 
                                  processorUtilization, channelWaitingTime, inputWaitingTime, channelUtilization]
            spatial_dist (str): Distribución espacial (UN, HR, BR, PS)
            temporal_dist (str): Distribución temporal (Client-Server, Asynchronous)
            
        Returns:
            float: Tiempo de respuesta predicho
        """
        # Simulación simple - en un caso real usarías el modelo entrenado
        base_value = 0.1 * numeric_inputs[0] + 0.2 * numeric_inputs[1] + 0.15 * numeric_inputs[2]
        spatial_factor = 1.0
        if spatial_dist == "HR":
            spatial_factor = 1.2
        elif spatial_dist == "BR":
            spatial_factor = 1.5
        elif spatial_dist == "PS":
            spatial_factor = 1.3
            
        temporal_factor = 1.0 if temporal_dist == "Client-Server" else 1.3
        
        # Simulación de predicción
        prediction = base_value * spatial_factor * temporal_factor
        
        return prediction
```

### 2. Construir y publicar la imagen Docker

```bash
# Navegar al directorio raíz del proyecto
cd c:\CC\parcial2\optical-network-model

# Preparación para Docker Hub (necesitas una cuenta)
docker login

# Construir la imagen del backend
docker build -t miguelank/optical-network-api:latest .

# Construir la imagen del frontend
docker build -t miguelank/optical-network-frontend:latest -f Dockerfile.frontend .

# Publicar las imágenes en Docker Hub
docker push miguelank/optical-network-api:latest
docker push miguelank/optical-network-frontend:latest
```

Si utilizas un registro privado o tienes restricciones en Docker Hub, configura el acceso del clúster:

```bash
# Crear secreto para Docker Hub
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=miguelank \
  --docker-password=tucontraseña \
  --docker-email=tuemail@ejemplo.com

# Luego, asegúrate de que tus deployments usen este secreto añadiendo:
# imagePullSecrets:
# - name: regcred
```

## Despliegue en Kubernetes

### 1. Aplicar los manifiestos en orden

```bash
# 1. Desplegar el backend (asegúrate de haber actualizado el deployment con tu usuario de Docker Hub)
kubectl apply -f kubernetes/neural-network-deployment.yaml

# 2. Desplegar el frontend (asegúrate de haber actualizado el deployment con tu usuario de Docker Hub)
kubectl apply -f kubernetes/frontend-deployment.yaml

# 3. Configurar el ingress
kubectl apply -f kubernetes/ingress.yaml

## 4. Para reiniciar pods:
kubectl delete pod $(kubectl get pod -l app=neural-network -o jsonpath='{.items[0].metadata.name}')

kubectl delete pod $(kubectl get pod -l app=optical-network-frontend -o jsonpath='{.items[0].metadata.name}')
```

### 2. Verificar el despliegue

```bash
# Verificar que todos los pods estén ejecutándose
kubectl get pods

# Verificar los servicios
kubectl get services

# Obtener la IP externa del servicio frontend
kubectl get service frontend-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Verificar que el ingress esté configurado
kubectl get ingress
```

## Solución de problemas

### Si el backend muestra ErrImagePull:

1. Verifica que la imagen exista y sea accesible:
```bash
docker images | grep optical-network-api
```

2. Si usas un registro local, asegúrate de que esté ejecutándose:
```bash
docker ps | grep registry
```

3. Verifica la configuración de pull secrets si es necesario:
```bash
kubectl get secret regcred -o yaml
```

4. Modifica el deployment para usar `imagePullPolicy: IfNotPresent` o `Never` durante pruebas:
```bash
kubectl patch deployment neural-network -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","imagePullPolicy":"IfNotPresent"}]}}}}'
```

### Si el frontend muestra error 403:

1. Verifica que la imagen del frontend se haya construido correctamente:
```bash
docker images | grep optical-network-frontend
```

2. Verifica que los archivos estén presentes en la imagen:
```bash
# Crear un contenedor temporal para inspeccionar
docker run --rm -it optical-network-frontend:latest ls -la /usr/share/nginx/html/
```

3. Verifica que los archivos estén montados correctamente en el pod:
```bash
kubectl exec -it $(kubectl get pod -l app=optical-network-frontend -o jsonpath='{.items[0].metadata.name}') -- ls -la /usr/share/nginx/html/
```

4. Si es necesario, modifica la configuración de nginx para permitir directory listing:
```bash
kubectl exec -it $(kubectl get pod -l app=optical-network-frontend -o jsonpath='{.items[0].metadata.name}') -- cat /etc/nginx/conf.d/default.conf
```

### Si hay problemas con Docker Hub:

1. Verifica que has iniciado sesión correctamente:
```bash
docker login
```

2. Asegúrate de que las imágenes estén correctamente etiquetadas con tu nombre de usuario:
```bash
docker images
```

3. Verifica que las imágenes hayan sido publicadas a Docker Hub:
```bash
# Puedes verificar en la interfaz web o con
docker search miguelank/optical-network-api
docker search miguelank/optical-network-frontend
```

4. Si los pods muestran errores de "ErrImagePull" o "ImagePullBackOff", verifica la configuración de secretos:
```bash
kubectl get secret regcred -o yaml
kubectl describe pods
```
