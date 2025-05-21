# Proyecto de Detección de Objetos: Comparación y Evaluación de APIs de Visión Artificial

## Tabla de Contenidos

- [Descripción General del Proyecto](#descripción-general-del-proyecto)
- [Arquitectura del Sistema Original](#arquitectura-del-sistema-original)
- [Entorno de Desarrollo con Vagrant](#entorno-de-desarrollo-con-vagrant)
- [Página Web de Comparación: Características y Capacidades](#página-web-de-comparación-características-y-capacidades)
- [Integración con APIs Genéricas de Visión Artificial](#integración-con-apis-genéricas-de-visión-artificial)
- [Flujo de Trabajo del Sistema](#flujo-de-trabajo-del-sistema)
- [Resultados y Hallazgos Iniciales](#resultados-y-hallazgos-iniciales)
- [Proyecto de Detección de Objetos: Modelos Personalizados](#proyecto-de-detección-de-objetos-modelos-personalizados)
- [Guía de Implementación: Google Vertex AI](#guía-de-implementación-google-vertex-ai)
- [Guía de Implementación: Azure Custom Vision](#guía-de-implementación-azure-custom-vision)
- [Scripts de Conversión de Formatos](#scripts-de-conversión-de-formatos)
- [Comparación de Servicios](#comparación-de-servicios)
- [Consejos para Mejorar la Precisión](#consejos-para-mejorar-la-precisión)
- [Solución de Problemas Comunes](#solución-de-problemas-comunes)
- [Recursos Adicionales](#recursos-adicionales)

## Descripción General del Proyecto

Este proyecto implementa una plataforma web para comparar el rendimiento, precisión y costo de diferentes servicios de visión artificial en tareas de detección de objetos. La solución permite evaluar tanto las APIs genéricas de detección (Google Cloud Vision y Azure Computer Vision) como modelos personalizados (Google Vertex AI y Azure Custom Vision) en este caso entrenados específicamente para componentes electrónicos discretos.

El sistema está diseñado con una arquitectura modular que facilita la escalabilidad, y proporciona métricas comparativas detalladas que ayudan a tomar decisiones fundamentadas sobre qué servicio de IA utilizar según diferentes criterios de evaluación.

## Arquitectura del Sistema Original

La arquitectura base del sistema consta de los siguientes componentes principales:

- **Backend**: Aplicación Flask en Python que gestiona la lógica de negocio y la comunicación con las APIs
- **Frontend**: Interfaz web construida con Bootstrap para ofrecer una experiencia de usuario intuitiva
- **Integración con APIs**:
  - Google Cloud Vision API
  - Microsoft Azure Computer Vision API
- **Sistema de almacenamiento**: Gestión de imágenes cargadas y resultados generados
- **Módulo de análisis comparativo**: Evaluación de resultados entre diferentes servicios

### Diagrama de Arquitectura

```
┌─────────────────┐       ┌───────────────┐       ┌────────────────┐
│                 │       │               │       │                │
│  Frontend Web   │◄─────►│  Backend      │◄─────►│  Storage       │
│  (Bootstrap)    │       │  (Flask)      │       │  System        │
│                 │       │               │       │                │
└─────────────────┘       └───────┬───────┘       └────────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
          ┌───────▼───────┐ ┌─────▼─────────┐    │
          │               │ │               │    │
          │  Google Cloud │ │  Azure        │    │
          │  Vision API   │ │  Vision API   │    │
          │               │ │               │    │
          └───────────────┘ └───────────────┘    │
                                                 ▼
                                          ┌─────────────────┐
                                          │                 │
                                          │  Comparación    │
                                          │  de Resultados  │
                                          │                 │
                                          └─────────────────┘
```

## Entorno de Desarrollo con Vagrant

Para facilitar el desarrollo y minimizar problemas de compatibilidad, se implementó una configuración con Vagrant que establece un entorno virtualizado y estandarizado.

### Uso del Entorno Vagrant

Para iniciar el entorno de desarrollo:

```bash
# Iniciar la máquina virtual, esto además instalará todas las dependencias
vagrant up

# Conectarse a la máquina virtual
vagrant ssh

# Acceder al directorio compartido
source /home/vagrant/venv/bin/activate
cd /home/vagrant/app

# Ejecutar la aplicación
flask --app app run --host=0.0.0.0
```

## Página Web de Comparación: Características y Capacidades

La interfaz web proporciona las siguientes funcionalidades clave:

1. **Carga individual de imágenes**: Permite subir una imagen para ser analizada por ambos servicios de visión.
2. **Procesamiento por lotes**: Posibilidad de cargar múltiples imágenes en formato ZIP para su análisis simultáneo.
3. **Visualización de resultados**: Presentación clara de las detecciones con cuadros delimitadores coloreados.
4. **Métricas comparativas**: 
   - Número de objetos detectados por cada servicio
   - Puntuación de confianza promedio
   - Velocidad de procesamiento
   - Coste por ejecución
5. **Análisis de costos**: Seguimiento de costos acumulados y por ejecución para cada servicio.
6. **Exportación de resultados**: Posibilidad de descargar los resultados en formato JSON para análisis posteriores.

La interfaz web incluye:
- Panel principal para carga de imágenes
- Visualización comparativa de resultados
- Tablero de métricas y estadísticas
- Vista de análisis por lotes

## Integración con APIs Genéricas de Visión Artificial

El sistema integra inicialmente dos de las principales APIs de visión artificial del mercado:

### Google Cloud Vision API

- **Capacidades utilizadas**: Localización de objetos (`object_localization`)
- **Formato de respuesta**: Objetos detectados con cuadros delimitadores poligonales
- **Ventajas**: Alta precisión en la detección de objetos comunes
- **Implementación**: Mediante la librería `google-cloud-vision` de Python
- **Costo**: $0.0015 USD por imagen analizada

```python
# Ejemplo de implementación
from google.cloud import vision

def detectar_google(filepath):
    with io.open(filepath, "rb") as f:  content = f.read()
    image  = vision.Image(content=content)
    start  = time.time()
    resp   = g_client.object_localization(image=image)
    elapsed= time.time() - start
    return [{
        "name": o.name,
        "score": f"{o.score*100:.2f} %",
        "source": "Google",
        "elapsed": f"{elapsed:.4f} s",
        "box": [(v.x, v.y) for v in o.bounding_poly.normalized_vertices]
    } for o in resp.localized_object_annotations]
```

### Microsoft Azure Computer Vision API

- **Capacidades utilizadas**: Detección de objetos (`detect_objects_in_stream`)
- **Formato de respuesta**: Objetos detectados con cuadros delimitadores rectangulares
- **Ventajas**: Buena integración con otras herramientas de Microsoft y capacidades multimodales
- **Implementación**: Mediante la librería `azure-cognitiveservices-vision-computervision`
- **Costo**: $0.001 USD por imagen analizada

```python
# Ejemplo de implementación
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

def detectar_azure(filepath):
    with Image.open(filepath) as img:
        img_width, img_height = img.size
    
    with open(filepath, "rb") as f:
        start = time.time()
        resp  = a_client.detect_objects_in_stream(f)
        elapsed = time.time() - start
    
    return [{
        "name": o.object_property,
        "score": f"{o.confidence*100:.2f} %",
        "source": "Azure",
        "elapsed": f"{elapsed:.4f} s",
        "box": [(o.rectangle.x / img_width, o.rectangle.y / img_height),
                ((o.rectangle.x + o.rectangle.w) / img_width, (o.rectangle.y + o.rectangle.h) / img_height)]
    }]
```

## Flujo de Trabajo del Sistema

1. **Carga de Imagen**: El usuario sube una imagen a través de la interfaz web
2. **Procesamiento Paralelo**: La imagen se envía simultáneamente a las APIs de Google y Azure
3. **Normalización de Resultados**: Las respuestas se transforman a un formato común para comparación
4. **Visualización**: Se generan versiones de la imagen con las anotaciones superpuestas
5. **Análisis Comparativo**: Se calculan y presentan métricas comparativas entre servicios
6. **Registro de Costos**: Se actualiza el registro de uso y costos acumulados

## Resultados y Hallazgos Iniciales

Durante las pruebas iniciales con las APIs genéricas, se encontraron las siguientes observaciones:

- **Precisión**: Google Cloud Vision tiende a ofrecer una mayor precisión en la identificación de objetos comunes
- **Velocidad**: Google Cloud Vision generalmente responde con mayor rapidez
- **Categorización**: Ambos servicios tienen limitaciones al identificar objetos específicos o técnicos
- **Costo-Beneficio**: Para volúmenes bajos, Azure ofrece un precio más competitivo

Estas limitaciones en la detección de objetos específicos (como componentes electrónicos) fueron la principal motivación para la segunda fase del proyecto: la implementación de modelos personalizados que se describe a continuación.

---


# Proyecto de Detección de Objetos: Modelos Personalizados

## Introducción

Este documento describe la implementación de modelos personalizados de detección de objetos utilizando Google Vertex AI y Azure Custom Vision, detallando el proceso completo desde el etiquetado de imágenes hasta la integración con nuestra aplicación web Flask. El sistema permite comparar el rendimiento de ambos modelos personalizados, analizando métricas como precisión, velocidad y costo. Cabe destacar que los modelos desarrollados y utilizados específicamente en esta implementación no están accesibles en este repositorio debido a restricciones en compartir las claves API privadas necesarias para su funcionamiento. En su lugar, a continuación se ofrece una guía extensiva sobre cómo implementar modelos personalizados propios en cada plataforma y vincularlos correctamente a la aplicación Flask, permitiendo así replicar completamente la funcionalidad del sistema.

## Arquitectura del Sistema

El sistema se compone de:

- **Aplicación web Flask**: Interfaz de usuario para cargar imágenes y visualizar resultados
- **Google Vertex AI**: Modelo personalizado de detección de objetos
- **Azure Custom Vision**: Modelo personalizado de detección de objetos
- **Sistema de análisis comparativo**: Evaluación de rendimiento entre ambos servicios

## Guía de Implementación: Google Vertex AI

### 1. Preparación de Datos

#### 1.1 Recopilación de Imágenes

Se recomienda recopilar un mínimo de 100 imágenes por clase para obtener buenos resultados:

```bash
# Estructura de directorios recomendada
project_folder/
├── train/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── valid/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── test/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
└── annotations/
    └── annotations.jsonl
```

#### 1.2 Etiquetado de Datos para Vertex AI

Vertex AI requiere un formato JSONL específico para las anotaciones de detección de objetos. Cada línea del archivo debe ser un objeto JSON que represente una imagen y sus anotaciones.

**Ejemplo (`annotations.jsonl`):**
```jsonl
{"imageGcsUri": "gs://bucket-name/images/image1.jpg", "boundingBoxAnnotations": [{"displayName": "resistor", "xMin": 0.1, "yMin": 0.2, "xMax": 0.3, "yMax": 0.4, "annotationResourceLabels": {"aiplatform.googleapis.com/annotation_set_name": "default"}}], "dataItemResourceLabels": {"aiplatform.googleapis.com/ml_use": "training"}}
{"imageGcsUri": "gs://bucket-name/images/image2.jpg", "boundingBoxAnnotations": [{"displayName": "capacitor", "xMin": 0.5, "yMin": 0.6, "xMax": 0.7, "yMax": 0.8, "annotationResourceLabels": {"aiplatform.googleapis.com/annotation_set_name": "default"}}], "dataItemResourceLabels": {"aiplatform.googleapis.com/ml_use": "training"}}
```

Campos clave por línea:
- `imageGcsUri`: (Obligatorio) La ruta URI de Google Cloud Storage a tu archivo de imagen.
- `boundingBoxAnnotations`: (Opcional si no hay objetos en la imagen) Un array de anotaciones. Cada anotación de cuadro delimitador incluye:
    - `displayName`: (Obligatorio) El nombre de la etiqueta del objeto.
    - `xMin`, `yMin`, `xMax`, `yMax`: (Obligatorio) Coordenadas normalizadas del cuadro delimitador (valores entre 0 y 1). `xMin` y `yMin` representan la esquina superior izquierda, y `xMax` e `yMax` la esquina inferior derecha.
    - `annotationResourceLabels`: (Opcional) Etiquetas clave-valor para la anotación, como `{"aiplatform.googleapis.com/annotation_set_name": "NOMBRE_DEL_CONJUNTO_DE_ANOTACIONES"}`.
- `dataItemResourceLabels`: (Opcional) Etiquetas clave-valor para el ítem de datos (imagen), comúnmente usado para especificar el uso de la imagen: `{"aiplatform.googleapis.com/ml_use": "training"}` (puede ser `training`, `validation`, o `test`).

Para un ejemplo detallado, consulta el archivo `vertex_annotations.jsonl` proporcionado en el dataset de ejemplo.

### 2. Configuración de Google Cloud

#### 2.1 Crear un Proyecto y Habilitar APIs

1. Accede a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita las siguientes APIs:
   - Vertex AI API
   - Cloud Storage API
   - Compute Engine API

#### 2.2 Configurar Autenticación

Existen dos métodos principales para autenticar con Google Cloud:

**a) Autenticación de Usuario (para desarrollo local y CLI):**

Esto es útil cuando trabajas directamente con `gcloud` CLI en tu máquina local.
```bash
# Instala Google Cloud CLI
# Windows
https://cloud.google.com/sdk/docs/install-sdk#windows

# Mac
brew install google-cloud-sdk

# Linux
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-VERSION-linux-x86_64.tar.gz
tar -xf google-cloud-cli-VERSION-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh

# Autenticación
gcloud auth login
gcloud config set project [PROJECT_ID]

# Para que las bibliotecas cliente de Python usen tus credenciales de usuario
gcloud auth application-default login
```

**b) Autenticación mediante Cuenta de Servicio (Recomendado para Aplicaciones):**

Para aplicaciones (como este proyecto Flask) que se ejecutan en servidores o contenedores, se recomienda usar una cuenta de servicio. Una cuenta de servicio es una identidad especial que pertenece a tu proyecto en lugar de a un usuario individual.

**Pasos para crear y usar una cuenta de servicio:**

1.  **Crear una Cuenta de Servicio:**
    *   Ve a la sección "IAM y Administración" > "Cuentas de servicio" en la [Google Cloud Console](https://console.cloud.google.com/).
    *   Selecciona tu proyecto.
    *   Haz clic en "CREAR CUENTA DE SERVICIO".
    *   Dale un nombre (ej. `vertex-ai-app-runner`) y una descripción.
    *   Haz clic en "CREAR Y CONTINUAR".

2.  **Conceder Permisos (Roles):**
    *   En la sección "Conceder a esta cuenta de servicio acceso al proyecto", añade los siguientes roles (o los mínimos necesarios para tus operaciones):
        *   `Vertex AI User`: Para interactuar con los servicios de Vertex AI (entrenar, desplegar, predecir).
        *   `Storage Object Viewer`: Si las imágenes están en un bucket de GCS y el modelo necesita leerlas. Si la aplicación también sube datos, considera `Storage Object Admin` o roles más específicos.
    *   Haz clic en "CONTINUAR" y luego en "LISTO".

3.  **Generar una Clave JSON:**
    *   Busca la cuenta de servicio que acabas de crear en la lista.
    *   Haz clic en los tres puntos (Acciones) al final de la fila y selecciona "Administrar claves".
    *   Haz clic en "AGREGAR CLAVE" > "Crear clave nueva".
    *   Selecciona "JSON" como tipo de clave y haz clic en "CREAR".
    *   Un archivo JSON se descargará automáticamente. **Guarda este archivo de forma segura**, ya que contiene credenciales privadas. No lo subas a repositorios públicos. En este proyecto, se recomienda guardarlo en una carpeta `creds` (que debe estar en `.gitignore`).

4.  **Usar la Clave JSON en tu Aplicación:**
    *   La forma más común de proporcionar estas credenciales a tu aplicación es mediante la variable de entorno `GOOGLE_APPLICATION_CREDENTIALS`.
    *   Establece esta variable de entorno para que apunte a la ruta completa de tu archivo de clave JSON descargado.
        ```bash
        # En Linux/macOS (en tu terminal o script de inicio)
        export GOOGLE_APPLICATION_CREDENTIALS="/ruta/completa/a/tu/clave.json"

        # En Windows (PowerShell)
        $env:GOOGLE_APPLICATION_CREDENTIALS="C:\ruta\completa\a\tu\clave.json"
        ```
    *   En el código de la aplicación Flask (`app.py`), esto se puede configurar programáticamente si es necesario, aunque establecer la variable de entorno es preferible para la portabilidad y seguridad:
        ```python
        # app.py
        import os
        # Ejemplo de cómo se podría establecer si no está en el entorno, aunque es mejor hacerlo fuera del código.
        # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "c:\\CC\\PFINAL\\creds\\tu-clave.json"
        ```
        (Nota: El código actual en `app.py` ya establece esta variable de forma explícita, lo cual es una alternativa si no se puede configurar la variable de entorno globalmente).

#### 2.3 Crear Bucket en Cloud Storage

```bash
gsutil mb -l us-central1 gs://[BUCKET_NAME]/
```

### 3. Subir Datos a Cloud Storage

```bash
# Subir imágenes
gsutil -m cp -r ./images/* gs://[BUCKET_NAME]/images/

# Subir anotaciones
gsutil cp ./annotations/annotations.jsonl gs://[BUCKET_NAME]/annotations/
```

### 4. Entrenar el Modelo en Vertex AI

#### 4.1 Usando la Consola Web

1. Ve a [Vertex AI](https://console.cloud.google.com/vertex-ai) en Google Cloud Console
2. Navega a "Datasets" y crea un dataset de tipo "Image" para "Object Detection"
3. Importa las imágenes desde tu bucket
4. Selecciona "Automatic Labeling" para anotaciones en Cloud Storage o etiqueta manualmente
5. Navega a la pestaña "Train" y configura:
   - Modelo: Faster R-CNN
   - Presupuesto de entrenamiento: 8-24 horas (recomendado para detección de objetos)
   - Ubicación del modelo: us-central1 (o tu región preferida)
6. Inicia el entrenamiento y espera (puede tomar varias horas)

#### 4.2 Usando Python SDK

```python
from google.cloud import aiplatform

# Inicializar Vertex AI
aiplatform.init(project='[PROJECT_ID]', location='us-central1')

# Crear dataset
dataset = aiplatform.ImageDataset.create(
    display_name="electronics-components-dataset",
    gcs_source=["gs://[BUCKET_NAME]/annotations/annotations.jsonl"],
    import_schema_uri=aiplatform.schema.dataset.ioformat.image.bounding_box
)

# Entrenar modelo
job = aiplatform.AutoMLImageTrainingJob(
    display_name="electronics-detector",
    prediction_type="object_detection",
    multi_label=False,
    model_type="CLOUD",
    base_model=None
)

model = job.run(
    dataset=dataset,
    model_display_name="electronics-detector-model",
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    budget_milli_node_hours=20000,  # ~20 horas
    disable_early_stopping=False
)
```

### 5. Desplegar el Modelo

#### 5.1 Usando la Consola Web

1. En la sección "Models", selecciona tu modelo entrenado
2. Haz clic en "Deploy to Endpoint"
3. Configura la máquina (n1-standard-2 es suficiente para comenzar)
4. Establece un mínimo de nodos = 1
5. Completa el despliegue

#### 5.2 Usando Python SDK

```python
endpoint = model.deploy(
    machine_type="n1-standard-2",
    min_replica_count=1,
    max_replica_count=1,
)

print(f"Endpoint desplegado: {endpoint.resource_name}")
```

### 6. Integración con Flask

Usa la siguiente configuración para conectar tu aplicación Flask. Asegúrate de que la autenticación esté configurada correctamente, preferiblemente mediante la variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` apuntando a tu archivo de clave JSON de la cuenta de servicio, como se describe en la sección "Configurar Autenticación".

```python
import base64
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

# Configurar cliente
endpoint = "[ENDPOINT_ID]"  # Obtenido del despliegue
project = "[PROJECT_ID]"
location = "us-central1"

# Establecer variables de entorno
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/credentials.json"

# Inicializar cliente
client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

# Función para detectar objetos
def detect_objects(image_file):
    with open(image_file, "rb") as f:
        file_content = f.read()
    
    # Codificar imagen
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    
    # Crear instancia
    instance = predict.instance.ImageObjectDetectionPredictionInstance(
        content=encoded_content,
    ).to_value()
    
    # Parámetros
    parameters = predict.params.ImageObjectDetectionPredictionParams(
        confidence_threshold=0.3,
        max_predictions=20,
    ).to_value()
    
    # Obtener ruta del endpoint
    endpoint_path = client.endpoint_path(
        project=project,
        location=location,
        endpoint=endpoint
    )
    
    # Llamar a la API
    response = client.predict(
        endpoint=endpoint_path, 
        instances=[instance], 
        parameters=parameters
    )
    
    # Procesar resultados
    results = []
    for prediction in response.predictions:
        prediction_dict = dict(prediction)
        # Extraer bounding boxes, scores, etc.
        # Ver código de app.py para procesamiento completo
    
    return results
```

## Guía de Implementación: Azure Custom Vision

### 1. Preparación de Datos

#### 1.1 Recopilación de Imágenes

Igual que en Google Vertex AI, se necesitan imágenes etiquetadas. Azure Custom Vision acepta formatos más comunes como jpg, png, etc.

#### 1.2 Etiquetado de Datos para Azure Custom Vision

Azure Custom Vision utiliza un formato diferente para las anotaciones, donde cada etiqueta tiene un ID único:

```csv
image_filename,tag_id,left,top,width,height
image1.jpg,1,0.1,0.2,0.2,0.2
image2.jpg,2,0.5,0.6,0.2,0.2
```

Donde:
- `image_filename`: Nombre del archivo de imagen
- `tag_id`: ID único para la categoría/etiqueta
- `left`, `top`, `width`, `height`: Coordenadas normalizadas (0-1) del recuadro delimitador

### 2. Configuración de Azure

#### 2.1 Crear Recursos en Azure

1. Accede al [Portal Azure](https://portal.azure.com/)
2. Busca "Custom Vision" en el marketplace
3. Crea un recurso de tipo "Custom Vision" (necesitarás crear dos recursos):
   - Un recurso de "Training"
   - Un recurso de "Prediction"
4. Selecciona el plan de precios (Free para comenzar, Standard para producción)
5. Completa la creación

### 3. Crear Proyecto en Custom Vision

1. Ve al [Portal de Custom Vision](https://www.customvision.ai/) e inicia sesión
2. Crea un nuevo proyecto:
   - Nombre: "ElectronicComponentsDetector"
   - Descripción: "Detector de componentes electrónicos"
   - Recurso: Selecciona el recurso de entrenamiento creado
   - Tipo de proyecto: "Object Detection"
   - Dominio: "General (compact)" para modelos más livianos o "General" para mayor precisión
   - Capacidades de exportación: Selecciona según necesidades (ONNX, CoreML, etc.)

### 4. Subir y Etiquetar Imágenes

#### 4.1 Usando el Portal Web

1. Dentro de tu proyecto, haz clic en "Add images"
2. Selecciona imágenes de tu equipo o URL
3. Después de cargarlas, selecciona cada imagen
4. Dibuja rectángulos alrededor de los objetos
5. Etiqueta cada objeto con su clase
6. Guarda las etiquetas

#### 4.2 Usando Python SDK

```python
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry

# Credenciales
training_key = "<your_training_key>"
endpoint = "<your_endpoint>"

# Cliente de entrenamiento
trainer = CustomVisionTrainingClient(training_key, endpoint=endpoint)

# Obtener proyecto
project_id = "<your_project_id>"

# Cargar y etiquetar imágenes
with open("image.jpg", "rb") as image_file:
    image_data = image_file.read()
    
    regions = [
        # Formato: x,y,width,height (valores normalizados entre 0 y 1)
        {"tag_id": resistor_tag.id, "left": 0.1, "top": 0.2, "width": 0.2, "height": 0.2},
        {"tag_id": capacitor_tag.id, "left": 0.5, "top": 0.6, "width": 0.2, "height": 0.2}
    ]
    
    trainer.create_images_from_files(
        project_id,
        [ImageFileCreateEntry(name="image.jpg", contents=image_data, regions=regions)]
    )
```

### 5. Entrenar el Modelo

#### 5.1 Usando el Portal Web

1. Haz clic en "Train" para iniciar el entrenamiento
2. Selecciona el tipo de entrenamiento:
   - "Quick Training": más rápido pero menos preciso
   - "Advanced Training": mejor precisión pero más lento
3. Espera a que termine el entrenamiento (minutos a horas según cantidad de imágenes)

#### 5.2 Usando Python SDK

```python
import time

# Entrenar modelo
training_iteration = trainer.train_project(project_id)

# Esperar a que termine
while training_iteration.status == "Training":
    training_iteration = trainer.get_iteration(project_id, training_iteration.id)
    print("Entrenando...")
    time.sleep(10)

print("Entrenamiento completado")
```

### 6. Publicar el Modelo

#### 6.1 Usando el Portal Web

1. Selecciona la iteración entrenada
2. Haz clic en "Publish"
3. Introduce:
   - Nombre de publicación: "ElectronicsDetector"
   - Recurso de predicción: Selecciona el recurso de predicción creado anteriormente
4. Haz clic en "Publish"

#### 6.2 Usando Python SDK

```python
# Publicar modelo
prediction_resource_id = "<your_prediction_resource_id>"
publish_name = "ElectronicsDetector"

trainer.publish_iteration(
    project_id,
    training_iteration.id,
    publish_name,
    prediction_resource_id
)
```

### 7. Integración con Flask

```python
import requests

def detect_objects_azure_custom(image_file):
    # Endpoint y clave de predicción
    prediction_endpoint = "https://custompredictioncv.cognitiveservices.azure.com"
    prediction_key = "2QcyA03dkxSD2s1xv05pByxeiPXCfYoQlzPVvTtPIR9VcgF94HI9JQQJ99BEACLArgHXJ3w3AAAIACOGqp9X"
    project_id = "7d16935d-57c4-4e60-b1b9-c8c8234432ca"
    iteration_name = "Electronics2"
    
    # URL de predicción
    url = f"{prediction_endpoint}/customvision/v3.0/Prediction/{project_id}/detect/iterations/{iteration_name}/image"
    
    # Encabezados
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream"
    }
    
    # Leer archivo de imagen
    with open(image_file, "rb") as f:
        image_data = f.read()
    
    # Realizar petición
    response = requests.post(url, headers=headers, data=image_data)
    response.raise_for_status()
    
    # Procesar resultados
    predictions = response.json()["predictions"]
    results = []
    
    for prediction in predictions:
        if prediction["probability"] > 0.3:  # umbral de confianza
            name = prediction["tagName"]
            score = prediction["probability"]
            bbox = prediction["boundingBox"]
            
            # Convertir coordenadas
            x_min = bbox["left"]
            y_min = bbox["top"]
            x_max = x_min + bbox["width"]
            y_max = y_min + bbox["height"]
            
            # Añadir a resultados
            results.append({
                "name": name,
                "score": f"{score*100:.2f} %",
                "source": "Azure Custom",
                "box": [(x_min, y_min), (x_max, y_max)]
            })
    
    return results
```

## Scripts de Conversión de Formatos

El repositorio incluye dos scripts útiles para convertir desde el formato estándar COCO a los formatos específicos de cada plataforma:

### 1. Conversión de COCO a Vertex AI

Este script convierte anotaciones en formato COCO al formato JSONL requerido por Vertex AI:

```python
# Ejemplo de uso:
# python convert_to_vertex.py --input annotations.json --output vertex_annotations.jsonl --bucket-name my-gcs-bucket
```

### 2. Conversión de COCO a Azure Custom Vision

Este script convierte anotaciones en formato COCO al formato CSV requerido por Azure Custom Vision:

```python
# Ejemplo de uso:
# python convert_to_customvision.py --input annotations.json --output customvision_annotations.csv --tag-id-start 1
```

Estos scripts facilitan enormemente la importación de conjuntos de datos previamente anotados en herramientas como CVAT, LabelImg o similares que exportan en formato COCO.

## Comparación de Servicios

### Google Vertex AI
- **Ventajas**:
  - Modelos más potentes y personalizables
  - Mejor integración con entorno Google Cloud
  - Mejor rendimiento en conjuntos de datos grandes
- **Desventajas**:
  - Curva de aprendizaje más pronunciada
  - Mayor complejidad de configuración
  - Pricing basado en horas de disponibilidad ($2.002/hora)

### Azure Custom Vision
- **Ventajas**:
  - Interfaz más sencilla y amigable
  - Tiempos de entrenamiento más cortos
  - Etiquetado más rápido e intuitivo
- **Desventajas**:
  - Menos personalizable
  - Rendimiento ligeramente inferior en casos complejos
  - Pricing por predicción ($0.002/predicción)

## Consejos para Mejorar la Precisión

1. **Datos de Entrenamiento**:
   - Usa al menos 50 imágenes por clase (recomendado: 100+)
   - Incluye variedad en fondos, ángulos, iluminación
   - Asegúrate de tener distribución balanceada de clases

2. **Etiquetado**:
   - Etiqueta con precisión todos los objetos
   - Incluye el objeto completo en el bounding box
   - Sé consistente en el etiquetado

3. **Entrenamiento**:
   - Usa data augmentation cuando sea posible
   - Evalúa el modelo con datos de validación
   - Realiza múltiples iteraciones de entrenamiento

4. **Despliegue**:
   - Ajusta el umbral de confianza según necesidad
   - Monitorea el rendimiento del modelo
   - Planea reentrenamientos periódicos con nuevos datos

## Solución de Problemas Comunes

### Google Vertex AI

1. **Error de autenticación**:
   ```
   Solución: Verifica que GOOGLE_APPLICATION_CREDENTIALS apunte al archivo correcto
   ```

2. **Timeouts en peticiones**:
   ```
   Solución: Aumenta el timeout o reduce el tamaño de las imágenes
   ```

3. **Baja precisión**:
   ```
   Solución: Aumenta la cantidad de datos de entrenamiento.
   ```

### Azure Custom Vision

1. **Límites de API excedidos**:
   ```
   Solución: Verifica tu plan de servicio y límites
   ```

2. **Formato de imagen no soportado**:
   ```
   Solución: Convierte imágenes a JPEG/PNG antes de enviar
   ```

3. **Error de predicción key inválida**:
   ```
   Solución: Verifica que estás usando la Prediction Key, no la Training Key
   ```

---

## Recursos Adicionales

- [Documentación de Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Documentación de Azure Custom Vision](https://docs.microsoft.com/azure/cognitive-services/custom-vision-service/)
- [Guía sobre detección de objetos](https://blog.roboflow.com/object-detection/)
- [Guía de etiquetado de datos](https://blog.roboflow.com/tips-for-how-to-label-images/)

---

Desarrollado para el proyecto final de Computación en la Nube - Universidad Autónoma de Occidente - © 2025
