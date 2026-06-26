# FastAPI Machine Learning Journey

Welcome to my **FastAPI for Machine Learning** development and deployment repository! This project documents my hands-on journey mastering the art of building, testing, and deploying production-grade APIs for Machine Learning models.

This repository is more than a code archive—it forms the backbone of a fully automated **Continuous Deployment (CD)** engine that instantly translates local Python code alterations into a live cloud-hosted environment.

---

## Project Architecture & Workflow

The architecture is built to support a continuous loop of local development and instantaneous web updates with zero downtime or manual infrastructure management.

1. **Local Coding & Testing:** Features are constructed using FastAPI and isolated locally within a custom Python virtual environment.
2. **Version Control Storage:** Refactored, production-ready iterations are updated in this GitHub repository.
3. **Automated Live Deployment:** Render listens directly to this repository via webhooks. The second a change is registered on the `main` branch, Render initiates a new containerized build pipeline, runs requirements compilation, and rotates the old server out for the new live application seamlessly.

---

## Live Production Access Links

The application is fully operational and publicly queryable at the following production access points:

* **Live Root Gateway API:** https://fastapi-ml-journey.onrender.com/
* **Live Metadata Route:** https://fastapi-ml-journey.onrender.com/about
* **Interactive OpenAPI Swagger Documentation:** https://fastapi-ml-journey.onrender.com/docs

*Note: The `/docs` portal provides full interactive capabilities to directly test schema request and response structures directly within the web page.*

---

## Project Milestones & Modules (In Continuation)

### Module 1: Patient Management System (Fundamentals)
Before deploying complex ML model inference logic, I focused on mastering essential backend mechanics, input validation, data persistence, and robust exception handling. 

* **Pydantic Data Schemas (`BaseModel`)**: Structuring strict schema layout blueprints enforcing static validation guarantees on nested runtime inputs.
* **Annotated Field Metadata (`Field`, `Literal`)**: Restricting inputs to inline value constraints (`gt=0`, `lt=120`), handling conditional choice matrices natively (`Literal['male', 'female', 'others']`), and provisioning embedded OpenAPI documentation examples.
* **Computed Fields (`@computed_field`)**: Implementing complex runtime features using Pydantic getters. This allows on-the-fly properties like **`bmi`** and medical **`verdict`** states to be natively generated during serialization without overloading database storage properties.
* **Path Parameters (`{patient_id}`)**: Dynamically fetching or altering individual records directly via URL paths.
* **Path Functions & Metadata (`Path()`)**: Enforcing explicit parameter descriptions and inline documentation examples.
* **Query Parameters (`Query()`)**: Implementing filtering, sorting criteria (`sort_by`), and ordering (`order`) for data manipulation.
* **State Mutation via HTTP POST (`@app.post`)**: Progressing beyond static reads into state modification. Implemented persistent record ingestion using structural JSON body validation payload matrices.
* **Partial Updates via HTTP PUT (`@app.put`)**: Created a dedicated `PatientUpdate` model leveraging `Optional` fields. Mastered using `.model_dump(exclude_unset=True)` to selectively patch only user-provided attributes while leaving other database values preserved.
* **Dynamic Re-serialization for Computed Fields**: Implemented a data-pipeline pattern within the PUT endpoint that unpacks modified records back into the original `Patient` Pydantic model to automatically recalculate runtime properties like `bmi` and `verdict` before saving.
* **Resource Destructuring via HTTP DELETE (`@app.delete`)**: Implementing state removal tracking to cleanly delete dictionary records via primary key safely protected behind `404 Not Found` exception handlers.
* **Data Persistence Engine (`json.dump`)**: Constructing lightweight file-system read/write helper layers (`load_data` and `save_data`) to act as a structured temporary local document store.
* **Semantic HTTP Status Responses (`JSONResponse`)**: Explicitly returning precise operational states such as `201 Created` for resource generations, `200 OK` for modifications/deletions, alongside automated safety blocks against primary-key record conflicts.

---

## Current Implementation (`main.py`)

```python
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional  # used for adding description in pydantic model
import json 

app = FastAPI() # app is the object of the FastAPI class, which is used to create the API. It is the main entry point for the application and is used to define routes and handle requests.

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", examples=['P001'])]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the Patient")] # age cannot be negative 
    gender: Annotated[Literal['male','female','others'], Field(..., description="Gender of the patient")] # only 3 choices 
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in mtrs")] # height cannot be negative
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kgs")] # weight cannot be negative 

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi 
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120)]
    gender: Annotated[Optional[Literal['male','female','others']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]      
        
def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)
    return data

def save_data(data):
    with open("patients.json", 'w') as f:
        json.dump(data, f)

@app.get("/") # @app.get("/") is a decorator that defines a route for the GET method at the root URL ("/").
def hello(): 
    return {"message": "Patient Management System API"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get("/view")
def view():
    data = load_data()
    return data 

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="ID of the patient in the DB", example="P001")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(
    sort_by: str = Query(..., description="Sort on the basis of height, weight and bmi"), 
    order: str = Query("asc", description="Sort order, either asc or desc")
):
    valid_fields = ["height", "weight", "bmi"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Valid fields are: {', '.join(valid_fields)}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort order. Valid orders are: asc, desc")
    
    sort_order = True if order == "desc" else False
    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order)
    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    # load existing data 
    data = load_data()
    
    # check if the patient already exists 
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists")
        
    # if does not exist, add new patient to the database
    data[patient.id] = patient.model_dump(exclude={'id'})
    
    # save into json file 
    save_data(data)
    return JSONResponse(status_code=201, content={'message': "Patient created successfully"})

@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient_info = data[patient_id]
    
    # convert patient_update which is pydantic model into dictionary extracting only updated values
    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value
    
    # re-serialize into original Patient Pydantic object to compute updated BMI and Verdict
    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    
    # convert back to dictionary excluding ID and store
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')
    data[patient_id] = existing_patient_info
    
    save_data(data)
    return JSONResponse(status_code=200, content={'message': 'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='patient not found')
    
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200, content={'message': 'patient deleted'})