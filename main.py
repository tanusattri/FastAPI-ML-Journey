from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional  #used for adding description in pydantic model
import json 
app= FastAPI() #app is the object of the FastAPI class, which is used to create the API. It is the main entry point for the application and is used to define routes and handle requests.

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", examples=['P001'])]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the Patient")] #age cannot be negative 
    gender: Annotated[Literal['male','female','others'], Field(..., description="Gender of the patient") ]  #only 2 options 
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in mtrs")] #height cannot be negative
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kgs")] #weight cannot be negative 

    @computed_field
    @property
    def bmi(self)-> float:
        bmi= round(self.weight/(self.height**2),2)
        return bmi 
    
    @computed_field
    @property
    def verdict(self)-> str:
        if self.bmi<18.5:
            return 'Underweight'
        elif self.bmi<25:
            return "Normal"
        elif self.bmi<30:
            return "Normal"
        else:
            return "Obese"

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[str], Field(default=None)]
    gender: Annotated[Optional[Literal['male','female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]      
  
def load_data():
    with open ('patients.json','r') as f:
        data= json.load(f)
    return data

def save_data(data):
    with open("patients.json",'w') as f:
        json.dump(data,f)

@app.get("/") #@app.get("/") is a decorator that defines a route for the GET method at the root URL ("/"). When a GET request is made to this URL, the function hello() will be called to handle the request.
def hello(): #hello() is a function that will be called when a GET request is made to the root URL ("/"). It returns a JSON response with a message "Hello World".
    return {"message": "Patient Management System API"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get("/view")
def view():
    data= load_data()
    return data 

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str= Path(..., description="ID of the patient in the DB", example="P001")):
    data= load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by:str= Query(..., description="Sort on the basis of height, weight and bmi"), order: str= Query("asc",description="Sort order, either asc or desc")):
    valid_fields= ["height", "weight", "bmi"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Valid fields are: {', '.join(valid_fields)}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort order. Valid orders are: asc, desc")
    sort_order= True if order=="desc" else False
    data= load_data()
    sorted_data= sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order)
    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    #load existing data 
    data= load_data()
    #check if the patient already exist 
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exist")
    #if does not exist, add new patient to the database
    data[patient.id]= patient.model_dump(exclude=['id'])
    #save into json file 
    save_data(data)
    return JSONResponse(status_code=201, content={'message':"Patient created successfuly"})

@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data= load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    existing_patient_info= data[patient_id] #else block when information is correct and dictionary of patient is extracted now 
    #convert patient_update which is pydantic model into dictionary 
    updated_patient_info= patient_update.model_dump(exclude_unset=True)
    for key, value in updated_patient_info.items():
        existing_patient_info[key]= value
    
    # convert existing_patient_info into pydantic object as when weight is changed, then BMI and verdict can be calculated easily.
    existing_patient_info['id']= patient_id
    patient_pydantic_obj= Patient(**existing_patient_info)
    #then again convert pydantic object into dictionary
    existing_patient_info= patient_pydantic_obj.model_dump(exclude='id')
    #adding this data into dictionary now
    data[patient_id]= existing_patient_info
    #save data 
    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    #load data
    data= load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='patient not found')
    
    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient deleted'})