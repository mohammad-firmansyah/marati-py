import os
import random
import string
from fastapi import FastAPI,HTTPException,Depends,Response,status,Form,File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.declarative import DeclarativeMeta
from pydantic import BaseModel
from typing import List,Annotated,Dict
from config.database import Base,Engine,SessionLocal
from sqlalchemy.orm import Session
from model.Model import Models
import json
import uuid
from sqlalchemy import cast, String
import tensorflow as tf
import numpy as np
import pickle

app = FastAPI()
Base.metadata.create_all(bind=Engine)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependancy = Annotated[Session,Depends(get_db)]

@app.get("/models/")
async def get_models(db:db_dependancy):
    result = db.query(Models).all()

    return {
        "is_error":False,
        "message":"get all data",
        "data":result
    }

@app.get("/models/{id}")
async def get_model(id:str,db:db_dependancy):
    result = db.query(Models).filter(Models.id == id).first()
    if not result:
        return JSONResponse({
            "is_error":True,
            "message": "Model not found",
            "data": {}
        },404)
    
    return JSONResponse({
            "is_error":False,
            "message": "get model by id success",
            "data": result
        },200)

@app.post("/models/")
async def add_model(file:UploadFile,name:str,input:str,output:str,owner_id:str,desc:str,category:str,db:db_dependancy):
    type = file.filename.split(".")[1]
    
    if type != "h5" and type != "sav" :
         return JSONResponse({
            "is_error":True,
            "message": "Unsupported media type",
            "data": {}
        },400)

    
    letters = string.ascii_lowercase
    random1 = ''.join(random.choice(letters) for i in range(20))
    
    
    try:

        newFileName = f"{random1}.{type}"
        new_model = Models(name=name, filename=newFileName, input=json.loads(input),description=desc,category=category,output=json.loads(output), owner_id=owner_id)
        print(newFileName)

        with open(f"files/{newFileName}", "wb") as f:
            f.write(file.file.read())
        
        db.add(new_model)
        db.commit()

        if (new_model != None):
            return JSONResponse({
            'is_error': False,
            'message': 'Model created successfully'
        }, status_code=201)


        

    except Exception as e:
        db.rollback()
        db.flush()
        print(e)
        return JSONResponse({
            "is_error":True,
            "message": "Model build error",
            "data": {}
        },500)

@app.delete("/models/")
async def delete_model(id:str,db:db_dependancy):
    model_db = db.query(Models).filter(Models.id == id).first()
    
    if not model_db:
         return JSONResponse({
            "is_error":True,
            "message": "Model not found",
            "data": {}
        },400)
    
    file_path = f'./files/{model_db.filename}'

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File '{model_db.filename}' has been removed.")
        except Exception as e:
            print(f"Error removing file '{model_db.filename}': {str(e)}")
    else:
        print("Error: File not found.")

        
    model_db = db.query(Models).filter(Models.id == id).delete(synchronize_session=False)
    db.commit()
    
    return JSONResponse({
        'is_error': False,
        'message': 'Model deleted successfully'
    }, status_code=200)

@app.put("/models/{id}")
async def update_model(id: uuid.UUID, db: db_dependancy,
                       file:UploadFile = None,
                       name:str=None,
                       input:str= None,
                       output:str = None,
                       owner_id:str= None):
    
    model_db = db.query(Models).filter(Models.id == id).first()

    if not model_db:
         return JSONResponse({
            "is_error":True,
            "message": "Model not found",
            "data": {}
        },404)

    if file != None:
        # delete existing model
        file_path = f'./files/{model_db.filename}'
        if os.path.exists(file_path):
            try:
                os.remove(file_path)

                # add new file
                newFileName = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))+".h5"
                with open(f"files/{newFileName}", "wb") as f:
                    f.write(file.file.read())

                model_db.name = name
                model_db.input = json.loads(input)
                model_db.filename = newFileName
                model_db.output = json.loads(output)
                model_db.owner_id = owner_id
                
                db.commit()

                return JSONResponse({
                    'is_error': False,
                    'message': 'Model updated successfully'
                }, status_code=200)
            
            except Exception as e:
                print(f"Error removing file '{model_db.filename}': {str(e)}")
        else:
            print("Error: File not found.")
        
    # update model without updated file
    try:
        model_db.name = name
        model_db.input = json.loads(input)
        model_db.output = json.loads(output)
        model_db.owner_id = owner_id
    
        db.commit()

        return JSONResponse({
            'is_error': False,
            'message': 'Model updated successfully'
        }, status_code=201)

    except Exception as e:
        print(e)
        db.rollback()
        db.flush()
        raise HTTPException(status_code=500, detail='Internal Server Error')
   
@app.get("/models/user/")
async def get_model_by_owner_id(owner_id: uuid.UUID ,db:db_dependancy):
    result = db.query(Models).filter(cast(Models.owner_id, String) == cast(owner_id, String) ).all()
    if not result:
         return JSONResponse({
            "is_error":True,
            "message": "data not found",
            "data": []
        },200)
    
    return {
        "is_error":False,
        "message":"get all models by owner",
        "data":result
    }
   
@app.get("/models/category/")
async def get_model_by_category(category: str ,db:db_dependancy):
    result = db.query(Models).filter(Models.category == category ).all()
    if not result:
         return JSONResponse({
            "is_error":True,
            "message": "data not found",
            "data": []
        },200)
    
    return {
        "is_error":False,
        "message":"get all models by category",
        "data":result
    }

@app.get("/model/predict/")
async def predict(id:uuid.UUID,input:str,db:db_dependancy):
    model_db = db.query(Models).filter(Models.id == id).first()
        
    if not model_db:
        return JSONResponse({
            "is_error":True,
            "message": "Model not found",
            "data": {}
        },404)
    
    # load model
    modelPath = f"files/{model_db.filename}"
    model = tf.keras.models.load_model(modelPath)

    try:
        # change array from user to be arr 2d
        value = np.array([json.loads(input)["value"]])
        # predict model
        predict = model.predict(value)
        return JSONResponse({
            "is_error":False,
            "message": "Prediction has been succeed",
            "data": {}
        })
    except Exception as e:
        print(e)
        return JSONResponse({
            "is_error":True,
            "message": "Input not correctly provided by user",
            "data":{}
        },400)
        
