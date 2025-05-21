import time, json, os, io, uuid, base64, zipfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image, ImageDraw

# Establecer explícitamente la ruta de credenciales para Google Vertex AI
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                         "creds", "versatile-cove-460404-r6-b56c4f7864c4.json")

# ─────────── Imports para Vertex AI ────────────
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

# ─────────── Coste fijo por llamada (mayo-2025) ────────────
COSTO_POR_LLAMADA = {
    "google": 0.0015, 
    "azure": 0.001,
    "vertex": 2.002,  # USD por hora de disponibilidad del modelo
    "azure_custom": 0.002  # USD por predicción
}  # USD

# También necesitamos registrar el tiempo de inicio del modelo Vertex
VERTEX_START_TIME = datetime.now()

# ─────────── Registro acumulado ────────────
uso_api = {
    "google": {"object_localization": 0},
    "azure":  {"detect_objects": 0},
    "vertex": {"predict": 0},
    "azure_custom": {"detect": 0}
}
def guardar_uso_api():
    with open("uso_api.json", "w") as f:
        json.dump(uso_api, f)

def cargar_uso_api():
    """
    Carga el uso acumulado desde disco o reinicia si hay
    un esquema viejo/inválido.
    """
    global uso_api
    esquema_correcto = {
        "google": {"object_localization": 0},
        "azure":  {"detect_objects": 0},
        "vertex": {"predict": 0},
        "azure_custom": {"detect": 0}
    }
    if os.path.exists("uso_api.json"):
        try:
            with open("uso_api.json", "r") as f:
                data = json.load(f)
            if (isinstance(data, dict) and isinstance(data.get("google"), dict)
                    and "object_localization" in data["google"]
                    and isinstance(data.get("azure"), dict)
                    and "detect_objects" in data["azure"]):
                # Aseguramos que vertex y azure_custom estén presentes incluso en archivos antiguos
                if "vertex" not in data:
                    data["vertex"] = {"predict": 0}
                if "azure_custom" not in data:
                    data["azure_custom"] = {"detect": 0}
                uso_api = data
                return
        except Exception:
            pass
    # si llegamos aquí, reiniciamos
    uso_api = esquema_correcto.copy()

# ─────────── Config ────────────
load_dotenv()
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif"}
app = Flask(__name__)
app.config["SECRET_KEY"]        = os.getenv("SECRET_KEY", "changeme")
app.config["UPLOAD_FOLDER"]     = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"]= int(os.getenv("MAX_CONTENT_LENGTH", 5*1024*1024))
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ─────────── Clientes API ────────────
# Google
from google.cloud import vision
g_client = vision.ImageAnnotatorClient()
# Azure
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
AZURE_KEY      = os.getenv("AZURE_VISION_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
a_client       = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
# Vertex AI
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "231108728613")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_ENDPOINT_ID = os.getenv("VERTEX_ENDPOINT_ID", "939551377632264192")
VERTEX_API_ENDPOINT = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
client_options = {"api_endpoint": VERTEX_API_ENDPOINT}
v_client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
# Azure Custom Vision
AZURE_CUSTOM_ENDPOINT = "https://custompredictioncv.cognitiveservices.azure.com"
AZURE_CUSTOM_PROJECT_ID = "7d16935d-57c4-4e60-b1b9-c8c8234432ca"
AZURE_CUSTOM_ITERATION = "Electronics2"
AZURE_CUSTOM_KEY = "2QcyA03dkxSD2s1xv05pByxeiPXCfYoQlzPVvTtPIR9VcgF94HI9JQQJ99BEACLArgHXJ3w3AAAIACOGqp9X"

# ─────────── Helpers ────────────
def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

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

def detectar_azure(filepath):
    # Abrir la imagen para obtener sus dimensiones
    with Image.open(filepath) as img:
        img_width, img_height = img.size
    
    with open(filepath, "rb") as f:
        start = time.time()
        resp  = a_client.detect_objects_in_stream(f)
        elapsed = time.time() - start
    
    # Normalizar las coordenadas dividiendo por el ancho/alto de la imagen
    return [{
        "name": o.object_property,
        "score": f"{o.confidence*100:.2f} %",
        "source": "Azure",
        "elapsed": f"{elapsed:.4f} s",
        "box": [(o.rectangle.x / img_width, o.rectangle.y / img_height),
                ((o.rectangle.x + o.rectangle.w) / img_width, (o.rectangle.y + o.rectangle.h) / img_height)]
    } for o in resp.objects]

def detectar_vertex_ai(filepath):
    try:
        print(f"[Vertex AI] Iniciando análisis de imagen: {filepath}")
        
        # Read the image file
        with open(filepath, "rb") as f:
            file_content = f.read()
        
        # Encode the image
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        print(f"[Vertex AI] Imagen codificada, longitud: {len(encoded_content)}")
        
        # Start timing
        start = time.time()
        
        # Create a properly formatted instance using the schema
        instance = predict.instance.ImageObjectDetectionPredictionInstance(
            content=encoded_content,
        ).to_value()
        instances = [instance]
        
        # Set prediction parameters - reduzco umbral para ver si hay más detecciones
        parameters = predict.params.ImageObjectDetectionPredictionParams(
            confidence_threshold=0.3,  # Reducido de 0.5 a 0.3 para detectar más objetos
            max_predictions=20,        # Aumentado de 10 a 20
        ).to_value()
        
        # Get the endpoint path
        endpoint = v_client.endpoint_path(
            project=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION,
            endpoint=VERTEX_ENDPOINT_ID
        )
        print(f"[Vertex AI] Usando endpoint: {endpoint}")
        
        # Call the API
        print("[Vertex AI] Enviando solicitud a la API...")
        response = v_client.predict(
            endpoint=endpoint, 
            instances=instances, 
            parameters=parameters
        )
        
        # End timing
        elapsed = time.time() - start
        print(f"[Vertex AI] Respuesta recibida en {elapsed:.4f}s")
        
        # Debug - imprimir la respuesta completa
        print(f"[Vertex AI] Respuesta completa: {response}")
        
        # Process results
        resultados = []
        
        # Handle the predictions according to the image_object_detection schema
        if not response.predictions:
            print("[Vertex AI] No se recibieron predicciones en la respuesta")
            return []
            
        for prediction in response.predictions:
            prediction_dict = dict(prediction)
            print(f"[Vertex AI] Predicción: {prediction_dict}")
            
            # Extract bounding boxes, scores, and display names
            boxes = prediction_dict.get('bboxes', [])
            
            # IMPORTANTE: El modelo usa 'confidences' en lugar de 'scores'
            scores = prediction_dict.get('confidences', [])
            if not scores:
                scores = prediction_dict.get('scores', [])  # Respaldo al formato anterior
                
            display_names = prediction_dict.get('displayNames', [])
            
            # En algunos modelos, los nombres pueden estar en otras claves
            if not display_names and 'ids' in prediction_dict:
                display_names = prediction_dict.get('ids', [])
            if not display_names and 'classes' in prediction_dict:
                display_names = prediction_dict.get('classes', [])
            if not display_names and 'labels' in prediction_dict:
                display_names = prediction_dict.get('labels', [])
                
            print(f"[Vertex AI] Boxes: {boxes}, Scores: {scores}, Names: {display_names}")
                
            # Process each detected object
            for i in range(min(len(boxes), len(scores))):
                if i < len(boxes) and i < len(scores):
                    # Get the confidence score
                    score = scores[i]
                    
                    # Get the name (either displayName or index)
                    name = "Object"
                    if i < len(display_names) and display_names[i]:
                        name = str(display_names[i])
                    
                    # Get the bounding box
                    if i < len(boxes):
                        box = boxes[i]
                        # Vertex AI devuelve coordenadas como [xmin, xmax, ymin, ymax]
                        if len(box) == 4:
                            # CORRECCIÓN: Extracción en el orden correcto
                            xmin, xmax, ymin, ymax = box
                            
                            # Asegurarse de que los valores estén ordenados (por si hay error de redondeo)
                            xmin, xmax = sorted((xmin, xmax))
                            ymin, ymax = sorted((ymin, ymax))
                            
                            resultados.append({
                                "name": name,
                                "score": f"{score*100:.2f} %",
                                "source": "Vertex",
                                "elapsed": f"{elapsed:.4f} s",
                                "box": [(xmin, ymin), (xmax, ymax)]  # Formato (x1,y1)-(x2,y2)
                            })
        
        print(f"[Vertex AI] Resultados procesados: {len(resultados)} objetos detectados")
        return resultados
        
    except Exception as e:
        # Mostrar más detalles sobre el error
        import traceback
        print(f"[ERROR] Error en Vertex AI: {e}")
        print(traceback.format_exc())
        flash(f"No se pudo acceder a Vertex AI: {str(e)}", "warning")
        return []  # Return empty list so the rest of the application works

def detectar_azure_custom(filepath):
    try:
        print(f"[Azure Custom Vision] Iniciando análisis de imagen: {filepath}")
        
        # Read the image file
        with open(filepath, "rb") as f:
            file_content = f.read()
        
        # API endpoint
        url = f"{AZURE_CUSTOM_ENDPOINT}/customvision/v3.0/Prediction/{AZURE_CUSTOM_PROJECT_ID}/detect/iterations/{AZURE_CUSTOM_ITERATION}/image"
        
        # Headers
        headers = {
            "Prediction-Key": AZURE_CUSTOM_KEY,
            "Content-Type": "application/octet-stream"
        }
        
        # Start timing
        start = time.time()
        
        # Make request
        import requests
        response = requests.post(url, headers=headers, data=file_content)
        response.raise_for_status()  # Raise exception for non-2xx responses
        
        # End timing
        elapsed = time.time() - start
        print(f"[Azure Custom] Respuesta recibida en {elapsed:.4f}s")
        
        # Parse response
        json_response = response.json()
        print(f"[Azure Custom] Respuesta: {json_response}")
        
        # Get image dimensions
        with Image.open(filepath) as img:
            img_width, img_height = img.size
        
        resultados = []
        
        # Process predictions
        if "predictions" in json_response:
            predictions = json_response["predictions"]
            
            for prediction in predictions:
                if "probability" in prediction and float(prediction["probability"]) >= 0.3:  # Threshold for comparison
                    name = prediction.get("tagName", "Object")
                    score = float(prediction["probability"])
                    
                    # Get coordinates
                    if "boundingBox" in prediction:
                        bbox = prediction["boundingBox"]
                        # Convert to normalized coordinates
                        xmin = bbox["left"]
                        ymin = bbox["top"]
                        xmax = xmin + bbox["width"]
                        ymax = ymin + bbox["height"]
                        
                        resultados.append({
                            "name": name,
                            "score": f"{score*100:.2f} %",
                            "source": "Azure Custom",
                            "elapsed": f"{elapsed:.4f} s",
                            "box": [(xmin, ymin), (xmax, ymax)]
                        })
        
        print(f"[Azure Custom] Resultados procesados: {len(resultados)} objetos detectados")
        return resultados
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error en Azure Custom Vision: {e}")
        print(traceback.format_exc())
        flash(f"No se pudo acceder a Azure Custom Vision: {str(e)}", "warning")
        return []

def dibujar_bounding_boxes(filepath, resultados, tipo="comparar"):
    img = Image.open(filepath)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for r in resultados:
        if tipo == "comparar":
            color = "red" if r["source"]=="Google" else "blue"
        elif tipo == "vertex":
            color = "green"
        else:  # tipo azure_custom
            color = "blue"
            
        box = r["box"]
        
        # Forma estandarizada de dibujar - dos puntos: esquina superior izquierda, esquina inferior derecha
        if len(box) == 2:  # Formato [(x1,y1), (x2,y2)]
            (x1, y1), (x2, y2) = box
            # Convertir de coordenadas normalizadas a píxeles
            x1, y1, x2, y2 = int(x1*w), int(y1*h), int(x2*w), int(y2*h), 
            
            # Dibujar rectángulo
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            lbl_pos = (x1, y1)
        else:  # Formato poligonal (múltiples puntos)
            pts = [(int(x*w), int(y*h)) for x, y in box]
            draw.polygon(pts, outline=color, width=3)
            lbl_pos = pts[0]
            
        # Dibujar etiqueta
        draw.text(lbl_pos, r["name"], fill=color)
    
    img.save(filepath)

def calc_resumen_comparacion(obj_google, obj_azure, 
                           conf_google, conf_azure,
                           t_google, t_azure, 
                           imgs):
    """Crea un pequeño dict-resumen comparativo para Google y Azure."""
    mas_obj = "Empate"
    if obj_google > obj_azure: 
        mas_obj = "Google"
    elif obj_azure > obj_google: 
        mas_obj = "Azure"

    mejor_conf = "Empate"
    if conf_google > conf_azure: 
        mejor_conf = "Google"
    elif conf_azure > conf_google: 
        mejor_conf = "Azure"

    mas_rapida = "Empate"
    if t_google < t_azure: 
        mas_rapida = "Google"
    elif t_azure < t_google: 
        mas_rapida = "Azure"

    # "ganador" = el que gana en más categorías
    score = {"Google": 0, "Azure": 0}
    for cat in (mas_obj, mejor_conf, mas_rapida):
        if cat in score: score[cat] += 1
    ganador = "Empate"
    max_score = max(score.values())
    if max_score > 0:
        ganadores = [k for k, v in score.items() if v == max_score]
        if len(ganadores) == 1:
            ganador = ganadores[0]

    return dict(
        imagenes_analizadas=imgs,
        objetos_google=obj_google,
        objetos_azure=obj_azure,
        mayor_objetos=mas_obj,
        confianza_google=conf_google,
        confianza_azure=conf_azure,
        mayor_confianza=mejor_conf,
        tiempo_google=t_google,
        tiempo_azure=t_azure,
        mas_rapida=mas_rapida,
        mejor_api=ganador
    )

def costo_ejecucion(llamadas_google=0, llamadas_azure=0, llamadas_vertex=0, llamadas_azure_custom=0):
    # Para Vertex calculamos el costo basado en el tiempo que lleva desplegado
    horas_vertex = (datetime.now() - VERTEX_START_TIME).total_seconds() / 3600
    costo_vertex = horas_vertex * COSTO_POR_LLAMADA["vertex"] if llamadas_vertex else None
    
    return (llamadas_google*COSTO_POR_LLAMADA["google"] if llamadas_google else None,
            llamadas_azure *COSTO_POR_LLAMADA["azure"] if llamadas_azure else None,
            costo_vertex,
            llamadas_azure_custom*COSTO_POR_LLAMADA["azure_custom"] if llamadas_azure_custom else None)

def costo_acumulado(api):
    if api=="google":
        return uso_api["google"]["object_localization"]*COSTO_POR_LLAMADA["google"]
    elif api=="azure":
        return uso_api["azure"]["detect_objects"]*COSTO_POR_LLAMADA["azure"]
    elif api=="vertex":
        # Para Vertex calculamos el costo basado en el tiempo que lleva desplegado
        horas_vertex = (datetime.now() - VERTEX_START_TIME).total_seconds() / 3600
        return horas_vertex * COSTO_POR_LLAMADA["vertex"]
    elif api=="azure_custom":
        return uso_api["azure_custom"]["detect"]*COSTO_POR_LLAMADA["azure_custom"]
    return 0

# ─────────── Rutas ────────────
cargar_uso_api()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/comparar", methods=["POST"])
def comparar():
    file=request.files.get("image")
    if not file or file.filename=="":
        flash("Selecciona una imagen válida","warning"); return redirect(url_for('index'))
    if not allowed(file.filename):
        flash("Formato no permitido","danger"); return redirect(url_for('index'))

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Detectamos con Google y Azure
    resultados_google = detectar_google(filepath)
    resultados_azure = detectar_azure(filepath)
    
    resultados = resultados_google + resultados_azure
    
    uso_api["google"]["object_localization"]+=1
    uso_api["azure"]["detect_objects"]+=1
    guardar_uso_api()

    dibujar_bounding_boxes(filepath, resultados, tipo="comparar")

    # métricas
    num_google=len(resultados_google)
    num_azure=len(resultados_azure)

    def avg(lst): return sum(lst)/len(lst) if lst else 0
    prom_g=avg([float(r["elapsed"].split()[0]) for r in resultados_google])
    prom_a=avg([float(r["elapsed"].split()[0]) for r in resultados_azure])
    
    conf_g=avg([float(r["score"].split()[0]) for r in resultados_google]) if resultados_google else 0
    conf_a=avg([float(r["score"].split()[0]) for r in resultados_azure]) if resultados_azure else 0

    resumen = calc_resumen_comparacion(
        num_google, num_azure,
        conf_g, conf_a,
        prom_g, prom_a, 
        imgs=1
    )

    # coste de ESTA ejecución (1 llamada c/u)
    costo_run_g, costo_run_a, _, _ = costo_ejecucion(1, 1)  # Now unpack 4 values instead of 3

    # img embebida
    with open(filepath,"rb") as img_f:
        img_data = base64.b64encode(img_f.read()).decode()

    resultados.sort(key=lambda x: float(x["score"].split()[0]), reverse=True)

    return render_template("result.html",
        img_data=img_data,
        objetos=resultados,
        resumen=resumen,
        costo_run_google=f"{costo_run_g:.6f}",
        costo_run_azure=f"{costo_run_a:.6f}",
        costo_tot_google=f"{costo_acumulado('google'):.6f}",
        costo_tot_azure=f"{costo_acumulado('azure'):.6f}"
    )

@app.route("/comparar_modelos", methods=["POST"])
def comparar_modelos():
    file=request.files.get("image")
    if not file or file.filename=="":
        flash("Selecciona una imagen válida","warning"); return redirect(url_for('index'))
    if not allowed(file.filename):
        flash("Formato no permitido","danger"); return redirect(url_for('index'))

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    print(f"Archivo guardado en {filepath}, iniciando detección con modelos personalizados")
    
    # Detectamos con Vertex AI
    resultados_vertex = detectar_vertex_ai(filepath)
    
    # Detectamos con Azure Custom Vision
    resultados_azure_custom = detectar_azure_custom(filepath)
    
    # Combinamos resultados para dibujar
    resultados = resultados_vertex + resultados_azure_custom
    
    print(f"Resultados de Vertex AI: {len(resultados_vertex)} objetos")
    print(f"Resultados de Azure Custom: {len(resultados_azure_custom)} objetos")
    
    # Incrementar contadores si hay resultados
    if resultados_vertex:
        uso_api["vertex"]["predict"] += 1
        print("Contador de uso de Vertex AI incrementado")
    if resultados_azure_custom:
        uso_api["azure_custom"]["detect"] += 1
        print("Contador de uso de Azure Custom Vision incrementado")
    
    if resultados_vertex or resultados_azure_custom:
        guardar_uso_api()

    # Hacer una copia de la imagen original para cada modelo
    vertex_img_path = filepath.replace('.', '_vertex.')
    azure_custom_img_path = filepath.replace('.', '_azure_custom.')
    import shutil
    shutil.copy(filepath, vertex_img_path)
    shutil.copy(filepath, azure_custom_img_path)
    
    # Dibujar bounding boxes por separado
    dibujar_bounding_boxes(vertex_img_path, resultados_vertex, tipo="vertex")
    dibujar_bounding_boxes(azure_custom_img_path, resultados_azure_custom, tipo="comparar")  # Usamos azul para Azure

    # métricas para Vertex AI
    def avg(lst): return sum(lst)/len(lst) if lst else 0
    confianza_vertex = avg([float(r["score"].split()[0]) for r in resultados_vertex if r["score"] != "N/A %"]) if resultados_vertex else 0
    tiempo_vertex = avg([float(r["elapsed"].split()[0]) for r in resultados_vertex]) if resultados_vertex else 0
    
    # métricas para Azure Custom Vision
    confianza_azure_custom = avg([float(r["score"].split()[0]) for r in resultados_azure_custom if r["score"] != "N/A %"]) if resultados_azure_custom else 0
    tiempo_azure_custom = avg([float(r["elapsed"].split()[0]) for r in resultados_azure_custom]) if resultados_azure_custom else 0

    # Calcular costos
    # Para Vertex AI, el costo es por hora de disponibilidad
    horas_vertex = (datetime.now() - VERTEX_START_TIME).total_seconds() / 3600
    costo_vertex = horas_vertex * COSTO_POR_LLAMADA["vertex"]
    
    # Para Azure Custom Vision, el costo es por predicción
    costo_azure_custom = COSTO_POR_LLAMADA["azure_custom"] if resultados_azure_custom else 0
    
    # Totales acumulados
    costo_total_vertex = costo_acumulado('vertex')
    costo_total_azure_custom = costo_acumulado('azure_custom')

    # Imágenes embebidas
    with open(vertex_img_path, "rb") as img_f:
        vertex_img_data = base64.b64encode(img_f.read()).decode()
    
    with open(azure_custom_img_path, "rb") as img_f:
        azure_custom_img_data = base64.b64encode(img_f.read()).decode()

    # Ordenar resultados por confianza
    if resultados_vertex:
        resultados_vertex.sort(key=lambda x: float(x["score"].split()[0]) if x["score"] != "N/A %" else 0, reverse=True)
    
    if resultados_azure_custom:
        resultados_azure_custom.sort(key=lambda x: float(x["score"].split()[0]) if x["score"] != "N/A %" else 0, reverse=True)

    # Determinamos quién es mejor
    mejor_modelo = ""
    if confianza_vertex > confianza_azure_custom and len(resultados_vertex) >= len(resultados_azure_custom):
        mejor_modelo = "Vertex AI"
    elif confianza_azure_custom > confianza_vertex and len(resultados_azure_custom) >= len(resultados_vertex):
        mejor_modelo = "Azure Custom Vision"
    elif tiempo_vertex < tiempo_azure_custom:
        mejor_modelo = "Vertex AI (más rápido)"
    elif tiempo_azure_custom < tiempo_vertex:
        mejor_modelo = "Azure Custom Vision (más rápido)"
    else:
        mejor_modelo = "Empate"

    return render_template("comparacion_modelos.html",
        img_data=vertex_img_data,
        img_data_azure=azure_custom_img_data,
        objetos=resultados_vertex,
        objetos_azure=resultados_azure_custom,
        confianza_media=confianza_vertex,
        confianza_media_azure=confianza_azure_custom,
        tiempo_procesamiento=tiempo_vertex,
        tiempo_procesamiento_azure=tiempo_azure_custom,
        costo_run=f"{costo_vertex:.6f}",
        costo_run_azure=f"{costo_azure_custom:.6f}",
        costo_total=f"{costo_total_vertex:.6f}",
        costo_total_azure=f"{costo_total_azure_custom:.6f}",
        mejor_modelo=mejor_modelo,
        modelo_vertex_tarifa="$2.002/hora",
        modelo_azure_tarifa="$0.002/predicción"  
    )

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return redirect(url_for("static", filename=f"uploads/{filename}"))

@app.route("/subir_carpeta", methods=["GET","POST"])
def subir_carpeta():
    if request.method=="POST":
        zfile = request.files.get("carpeta_zip")
        if not zfile or zfile.filename == "":
            flash("Selecciona un .zip válido","warning"); return redirect(request.url)
        if not zfile.filename.lower().endswith(".zip"):
            flash("Solo se admite .zip","danger"); return redirect(request.url)

        # ───── Descomprimir dentro de static/uploads ──────────
        folder_id = uuid.uuid4().hex
        extract_path = os.path.join(app.config["UPLOAD_FOLDER"], folder_id)
        os.makedirs(extract_path, exist_ok=True)

        zip_path = os.path.join(extract_path, secure_filename(zfile.filename))
        zfile.save(zip_path)
        with zipfile.ZipFile(zip_path,"r") as zf:
            zf.extractall(extract_path)
        os.remove(zip_path)

        resultados=[]
        tot_g_obj=tot_a_obj=0
        sum_conf_g=sum_conf_a=sum_time_g=sum_time_a=0.0

        # ───── Recorremos las imágenes ───────────────────────
        for root,_,files in os.walk(extract_path):
            for f in files:
                if not allowed(f): continue
                img_path = os.path.join(root,f)
                rel_static = os.path.relpath(img_path, app.config["UPLOAD_FOLDER"])   # p/ mostrar en html

                g_objs = detectar_google(img_path)
                a_objs = detectar_azure(img_path)
                
                res = g_objs + a_objs
                
                uso_api["google"]["object_localization"]+=1
                uso_api["azure"]["detect_objects"]+=1

                # dibujar cajas en la propia imagen
                dibujar_bounding_boxes(img_path, res, tipo="comparar")

                tot_g_obj+=len(g_objs)
                tot_a_obj+=len(a_objs)
                
                sum_conf_g+=sum(float(r["score"].split()[0]) for r in g_objs) if g_objs else 0
                sum_conf_a+=sum(float(r["score"].split()[0]) for r in a_objs) if a_objs else 0
                
                sum_time_g+=sum(float(r["elapsed"].split()[0]) for r in g_objs) if g_objs else 0
                sum_time_a+=sum(float(r["elapsed"].split()[0]) for r in a_objs) if a_objs else 0

                resultados.append({
                    "archivo": rel_static,              # <- para <img src>
                    "google_detectados": len(g_objs),
                    "azure_detectados": len(a_objs)
                })

        guardar_uso_api()

        imgs=len(resultados)
        prom_conf_g = sum_conf_g/tot_g_obj if tot_g_obj else 0
        prom_conf_a = sum_conf_a/tot_a_obj if tot_a_obj else 0
        
        prom_time_g = sum_time_g/tot_g_obj if tot_g_obj else 0
        prom_time_a = sum_time_a/tot_a_obj if tot_a_obj else 0

        resumen = calc_resumen_comparacion(
            tot_g_obj, tot_a_obj,
            prom_conf_g, prom_conf_a,
            prom_time_g, prom_time_a,
            imgs
        )

        costo_run_g, costo_run_a, _, _ = costo_ejecucion(imgs, imgs)

        return render_template("resultados_batch.html",
                resultados=resultados,
                resumen=resumen,
                costo_run_google=f"{costo_run_g:.6f}",
                costo_run_azure=f"{costo_run_a:.6f}",
                costo_tot_google=f"{costo_acumulado('google'):.6f}",
                costo_tot_azure=f"{costo_acumulado('azure'):.6f}"
        )
    return render_template("subir_carpeta.html")

@app.route("/subir_carpeta_modelos", methods=["GET","POST"])
def subir_carpeta_modelos():
    if request.method=="POST":
        zfile = request.files.get("carpeta_zip")
        if not zfile or zfile.filename == "":
            flash("Selecciona un .zip válido","warning"); return redirect(request.url)
        if not zfile.filename.lower().endswith(".zip"):
            flash("Solo se admite .zip","danger"); return redirect(request.url)

        # ───── Descomprimir dentro de static/uploads ──────────
        folder_id = uuid.uuid4().hex
        extract_path = os.path.join(app.config["UPLOAD_FOLDER"], folder_id)
        os.makedirs(extract_path, exist_ok=True)

        zip_path = os.path.join(extract_path, secure_filename(zfile.filename))
        zfile.save(zip_path)
        with zipfile.ZipFile(zip_path,"r") as zf:
            zf.extractall(extract_path)
        os.remove(zip_path)

        resultados = []
        total_objetos_vertex = 0
        total_objetos_azure = 0
        sum_conf_vertex = sum_time_vertex = 0.0
        sum_conf_azure = sum_time_azure = 0.0
        vertex_llamadas = 0
        azure_custom_llamadas = 0

        # ───── Recorremos las imágenes ───────────────────────
        for root, _, files in os.walk(extract_path):
            for f in files:
                if not allowed(f): continue
                img_path = os.path.join(root, f)
                rel_static = os.path.relpath(img_path, app.config["UPLOAD_FOLDER"])

                # Detectar con ambos modelos
                v_objs = detectar_vertex_ai(img_path)
                a_objs = detectar_azure_custom(img_path)
                
                # Solo si se procesó correctamente
                if v_objs:
                    vertex_llamadas += 1
                if a_objs:
                    azure_custom_llamadas += 1
                
                # Hacer una copia de la imagen original para cada modelo
                vertex_img_path = img_path.replace('.', '_vertex.')
                azure_custom_img_path = img_path.replace('.', '_azure_custom.')
                import shutil
                shutil.copy(img_path, vertex_img_path)
                shutil.copy(img_path, azure_custom_img_path)
                
                # Dibujar bounding boxes por separado
                dibujar_bounding_boxes(vertex_img_path, v_objs, tipo="vertex")
                dibujar_bounding_boxes(azure_custom_img_path, a_objs, tipo="comparar")
                
                # Calcular métricas para esta imagen
                num_objetos_vertex = len(v_objs)
                num_objetos_azure = len(a_objs)
                
                total_objetos_vertex += num_objetos_vertex
                total_objetos_azure += num_objetos_azure
                
                # Calcular confianza media y tiempo para esta imagen con Vertex AI
                conf_img_vertex = sum(float(r["score"].split()[0]) for r in v_objs if r["score"] != "N/A %") / num_objetos_vertex if num_objetos_vertex else 0
                tiempo_img_vertex = sum(float(r["elapsed"].split()[0]) for r in v_objs) / num_objetos_vertex if num_objetos_vertex else 0
                
                # Calcular confianza media y tiempo para esta imagen con Azure Custom Vision
                conf_img_azure = sum(float(r["score"].split()[0]) for r in a_objs if r["score"] != "N/A %") / num_objetos_azure if num_objetos_azure else 0
                tiempo_img_azure = sum(float(r["elapsed"].split()[0]) for r in a_objs) / num_objetos_azure if num_objetos_azure else 0
                
                # Acumular para métricas globales
                sum_conf_vertex += conf_img_vertex * num_objetos_vertex if num_objetos_vertex else 0
                sum_time_vertex += tiempo_img_vertex * num_objetos_vertex if num_objetos_vertex else 0
                
                sum_conf_azure += conf_img_azure * num_objetos_azure if num_objetos_azure else 0
                sum_time_azure += tiempo_img_azure * num_objetos_azure if num_objetos_azure else 0

                # Determinar el mejor modelo para esta imagen
                mejor_modelo = "Empate"
                if conf_img_vertex > conf_img_azure and num_objetos_vertex >= num_objetos_azure:
                    mejor_modelo = "Vertex AI"
                elif conf_img_azure > conf_img_vertex and num_objetos_azure >= num_objetos_vertex:
                    mejor_modelo = "Azure Custom Vision"
                elif tiempo_img_vertex < tiempo_img_azure:
                    mejor_modelo = "Vertex AI (más rápido)"
                elif tiempo_img_azure < tiempo_img_vertex:
                    mejor_modelo = "Azure Custom Vision (más rápido)"

                # Guardar info relativa
                rel_vertex_path = os.path.relpath(vertex_img_path, app.config["UPLOAD_FOLDER"])
                rel_azure_path = os.path.relpath(azure_custom_img_path, app.config["UPLOAD_FOLDER"])
                
                resultados.append({
                    "archivo": rel_static,
                    "vertex_img": rel_vertex_path,
                    "azure_img": rel_azure_path,
                    "objetos_vertex": num_objetos_vertex,
                    "objetos_azure": num_objetos_azure,
                    "confianza_vertex": conf_img_vertex,
                    "confianza_azure": conf_img_azure,
                    "tiempo_vertex": tiempo_img_vertex,
                    "tiempo_azure": tiempo_img_azure,
                    "mejor_modelo": mejor_modelo
                })

        # Actualizar contadores de uso
        if vertex_llamadas > 0:
            uso_api["vertex"]["predict"] += vertex_llamadas
        if azure_custom_llamadas > 0:
            uso_api["azure_custom"]["detect"] += azure_custom_llamadas
        if vertex_llamadas > 0 or azure_custom_llamadas > 0:
            guardar_uso_api()

        total_imagenes = len(resultados)
        
        # Calcular métricas globales
        confianza_media_vertex = sum_conf_vertex / total_objetos_vertex if total_objetos_vertex else 0
        tiempo_medio_vertex = sum_time_vertex / total_objetos_vertex if total_objetos_vertex else 0
        
        confianza_media_azure = sum_conf_azure / total_objetos_azure if total_objetos_azure else 0
        tiempo_medio_azure = sum_time_azure / total_objetos_azure if total_objetos_azure else 0

        # Determinar el mejor modelo general
        mejor_modelo_general = "Empate"
        if confianza_media_vertex > confianza_media_azure and total_objetos_vertex >= total_objetos_azure:
            mejor_modelo_general = "Vertex AI"
        elif confianza_media_azure > confianza_media_vertex and total_objetos_azure >= total_objetos_vertex:
            mejor_modelo_general = "Azure Custom Vision"
        elif tiempo_medio_vertex < tiempo_medio_azure:
            mejor_modelo_general = "Vertex AI (más rápido)"
        elif tiempo_medio_azure < tiempo_medio_vertex:
            mejor_modelo_general = "Azure Custom Vision (más rápido)"

        # Calcular costos
        # Para Vertex AI, el costo es por hora de disponibilidad
        horas_vertex = (datetime.now() - VERTEX_START_TIME).total_seconds() / 3600
        costo_vertex = horas_vertex * COSTO_POR_LLAMADA["vertex"]
        
        # Para Azure Custom Vision, el costo es por predicción
        costo_azure = azure_custom_llamadas * COSTO_POR_LLAMADA["azure_custom"]
        
        costo_total_vertex = costo_acumulado('vertex')
        costo_total_azure = costo_acumulado('azure_custom')

        return render_template("comparacion_modelos_batch.html",
                resultados=resultados,
                total_imagenes=total_imagenes,
                total_objetos_vertex=total_objetos_vertex,
                total_objetos_azure=total_objetos_azure,
                confianza_media_vertex=confianza_media_vertex,
                confianza_media_azure=confianza_media_azure,
                tiempo_medio_vertex=tiempo_medio_vertex,
                tiempo_medio_azure=tiempo_medio_azure,
                mejor_modelo=mejor_modelo_general,
                costo_run_vertex=f"{costo_vertex:.6f}",
                costo_run_azure=f"{costo_azure:.6f}",
                costo_total_vertex=f"{costo_total_vertex:.6f}",
                costo_total_azure=f"{costo_total_azure:.6f}",
                modelo_vertex_tarifa="$2.002/hora",  # Agregar información de tarifa
                modelo_azure_tarifa="$0.002/predicción"  # Agregar información de tarifa
        )
    return render_template("subir_carpeta_modelos.html")

@app.route('/resultados/<json_filename>')
def descargar_reporte(json_filename):
    if not json_filename.endswith('.json'): abort(404)
    ruta=os.path.join(os.getcwd(),'resultados',json_filename)
    if not os.path.isfile(ruta): abort(404)
    return send_from_directory(os.path.dirname(ruta),
                               os.path.basename(ruta),
                               as_attachment=True,
                               mimetype='application/json')

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
