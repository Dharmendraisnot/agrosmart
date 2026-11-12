import zlib
import urllib.request
from pathlib import Path
from PIL import Image
import io

def encode6bit(b):
    if b < 10: return chr(48 + b)
    b -= 10
    if b < 26: return chr(65 + b)
    b -= 26
    if b < 26: return chr(97 + b)
    b -= 26
    if b == 0: return '-'
    if b == 1: return '_'
    return '?'

def encode3bytes(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return encode6bit(c1 & 0x3F) + encode6bit(c2 & 0x3F) + encode6bit(c3 & 0x3F) + encode6bit(c4 & 0x3F)

def plantuml_encode(text):
    data = zlib.compress(text.encode('utf-8'))[2:-4]
    res = ''
    for i in range(0, len(data), 3):
        if i + 2 == len(data):
            res += encode3bytes(data[i], data[i+1], 0)
        elif i + 1 == len(data):
            res += encode3bytes(data[i], 0, 0)
        else:
            res += encode3bytes(data[i], data[i+1], data[i+2])
    return res

def render_save(code, puml_name, png_name):
    out_dir = Path(r"D:\minor 1\Agrosmart\docs\uml_diagrams\simplified")
    puml_path = out_dir / puml_name
    png_path = out_dir / png_name
    
    puml_path.write_text(code.strip(), encoding="utf-8")
    enc = plantuml_encode(code.strip())
    url = f"https://www.plantuml.com/plantuml/png/{enc}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    png_path.write_bytes(data)
    img = Image.open(io.BytesIO(data))
    print(f"Verified: {puml_name} -> {png_name} ({img.size[0]}x{img.size[1]})")

# 1. Use Case Diagram
uc_code = """@startuml use_case_diagram
' AgroSmart - Simplified Use Case Diagram (16:9 Presentation View)
left to right direction
skinparam packageStyle rectangle
skinparam monochrome true
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 14
skinparam roundCorner 8
skinparam arrowThickness 1.5

actor "Farmer / User" as Farmer

rectangle "AgroSmart" {
  usecase "View Analysis History" as UC8
  usecase "View Irrigation Advice" as UC7
  usecase "View Fertilizer Advice" as UC6
  usecase "View Crop Recommendations" as UC5
  usecase "Run Soil Analysis" as UC4
  usecase "Upload Soil Image (Optional)" as UC3
  usecase "Enter Soil Parameters" as UC2
  usecase "View Dashboard" as UC1
}

Farmer --> UC1
Farmer --> UC2
Farmer --> UC3
Farmer --> UC4
Farmer --> UC5
Farmer --> UC6
Farmer --> UC7
Farmer --> UC8
@enduml"""

# 2. Class Diagram
class_code = """@startuml class_diagram
' AgroSmart - Simplified Class Diagram (16:9 Presentation View)
left to right direction
skinparam classAttributeIconSize 0
skinparam monochrome true
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 13
skinparam roundCorner 6
skinparam arrowThickness 1.5
skinparam linetype ortho

package "Data Persistence" {
    class SensorReading {
        + id: Integer
        + moisture, rainfall, ph: Float
        + nitrogen, phosphorus, potassium: Float
        + soil_temp, air_temp, humidity: Float
        --
        + to_dict(): dict
    }

    class SoilAnalysis {
        + id: Integer
        + soil_type: String
        + health_score: Float
        --
        + to_dict(): dict
    }
}

package "Service Orchestration" {
    class SensorService {
        + capture_reading(): SensorReading
        + get_latest_reading(): SensorReading
    }

    class AnalysisService {
        + run_analysis(params: dict): dict
        + get_analysis(id: int): dict
    }
}

package "ML & Rule Engines" {
    class SoilCNNModel {
        + predict_soil_type(img): dict
    }

    class CropModel {
        + predict_crops(sensor): list
    }

    class FertilizerModel {
        + predict_fertilizer(sensor, soil, crop): dict
    }

    class RecommendationService {
        + generate_irrigation_advice(sensor, crop): dict
    }
}

SensorReading "1" o-- "0..*" SoilAnalysis : stores
SensorService ..> SensorReading : captures
AnalysisService --> SensorService : fetches telemetry
AnalysisService --> SoilAnalysis : persists results

AnalysisService --> SoilCNNModel : classifies soil
AnalysisService --> CropModel : recommends crops
AnalysisService --> FertilizerModel : recommends fertilizer
AnalysisService --> RecommendationService : advises irrigation
@enduml"""

# 3. Sequence Diagram
seq_code = """@startuml sequence_diagram
' AgroSmart - Simplified Sequence Diagram (16:9 Presentation View)
autonumber
skinparam monochrome true
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 13
skinparam roundCorner 6
skinparam arrowThickness 1.5

actor "Farmer" as User
participant "React Frontend" as UI
participant "Flask REST API" as API
participant "AnalysisService" as Pipeline
participant "ML Models & Rules" as ML
database "SQLite Database" as DB

User -> UI: Enter soil parameters / upload photo
activate UI
UI -> API: POST /api/analysis/run
activate API

API -> API: Validate request data
API -> Pipeline: run_analysis(parameters)
activate Pipeline

Pipeline -> ML: Execute CNN, Crop RF, Fertilizer DT & Irrigation Rules
activate ML
ML --> Pipeline: Return predictions & advisories
deactivate ML

Pipeline -> DB: Save SensorReading & SoilAnalysis records
activate DB
DB --> Pipeline: Confirm saved
deactivate DB

Pipeline --> API: Consolidated analysis result
deactivate Pipeline

API --> UI: 200 OK (JSON response)
deactivate API

UI --> User: Display recommendations & soil health
deactivate UI

@enduml"""

# 4. Component Diagram
comp_code = """@startuml component_diagram
' AgroSmart - Simplified Component Diagram (16:9 Presentation View)
left to right direction
skinparam componentStyle rectangle
skinparam monochrome true
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 14
skinparam roundCorner 6
skinparam arrowThickness 1.5

package "Presentation Tier" {
    [React Frontend] as UI
}

package "Application Tier" {
    [Flask REST API] as API
    [Analysis Service] as Service
    [Sensor Simulator] as Simulator
    note bottom of Simulator: Software simulation active (Hardware sensors planned)
}

package "Intelligence & ML Tier" {
    [ML Models] as ML
    [Irrigation Rule Engine] as Irrigation
}

package "Persistence Tier" {
    database "SQLite Database" as DB
}

UI --> API : HTTP / REST Calls
API --> Simulator : Reads simulated parameters
API --> Service : Triggers analysis pipeline
API --> DB : Queries history records

Service --> ML : Executes model inference
Service --> Irrigation : Evaluates moisture rules
Service --> DB : Persists analysis records

@enduml"""

render_save(uc_code, "use_case_diagram.puml", "use_case_diagram.png")
render_save(class_code, "class_diagram.puml", "class_diagram.png")
render_save(seq_code, "sequence_diagram.puml", "sequence_diagram.png")
render_save(comp_code, "component_diagram.puml", "component_diagram.png")

print("All 4 simplified diagrams generated and verified.")
