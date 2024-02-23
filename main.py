import os
import random
import string
from fastapi import FastAPI,HTTPException,Depends,Response,status,Form,File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Annotated,Dict
from config.database import Base,Engine,SessionLocal
from sqlalchemy.orm import Session
from model.Model import Models
import json

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
    return result

@app.get("/models/{id}")
async def get_model(id:str,db:db_dependancy):
    result = db.query(Models).filter(Models.id == id).first()
    if not result:
        return HTTPException(status_code=404,detail='Model Not Found')
    
    return result

@app.post("/models/")
async def add_model(file:UploadFile,name:str,input:str,output:str,owner_id:str,db:db_dependancy):
    if file.content_type != 'application/octet-stream':
        raise HTTPException(status_code=415, detail='Unsupported Media Type')

    try:
        newFileName = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))+".h5"
        with open(f"files/{newFileName}", "wb") as f:
            f.write(file.file.read())

        new_model = Models(name=name, filename=newFileName, input=json.loads(input), output=json.loads(output), owner_id=owner_id)
        db.add(new_model)
        db.commit()

        return JSONResponse({
            'is_error': False,
            'message': 'Model created successfully'
        }, status_code=201)

    except Exception as e:
        db.rollback()
        db.flush()
        raise HTTPException(status_code=500, detail='Internal Server Error')

@app.delete("/models/")
async def delete_model(id:str,db:db_dependancy):
    model_db = db.query(Models).filter(Models.id == id).first()
    
    if not model_db:
        return HTTPException(status_code=404,detail='Model Not Found')
    
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
async def update_model(id: str, db: db_dependancy,
                       file:UploadFile = None,
                       name:str=None,
                       input:str= None,
                       output:str = None,
                       owner_id:str= None,):
    
    model_db = db.query(Models).filter(Models.id == id).first()

    if not model_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Model not found')

    if (file!=None):
        # delete existing model
        file_path = f'./files/{model_db.filename}'
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                newFileName = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))+".h5"
                with open(f"files/{newFileName}", "wb") as f:
                    f.write(file.file.read())

                new_model = Models(name=name, filename=newFileName, input=json.loads(input), output=json.loads(output), owner_id=owner_id)
                db.add(new_model)
                db.commit()

                return JSONResponse({
                    'is_error': False,
                    'message': 'Model created successfully'
                }, status_code=201)
            
            except Exception as e:
                print(f"Error removing file '{model_db.filename}': {str(e)}")
        else:
            print("Error: File not found.")
        
    # update model without updated file
    try:
        new_model = Models(name=name, filename=model_db.filename, input=json.loads(input), output=json.loads(output), owner_id=owner_id)
        db.add(new_model)
        db.commit()

        return JSONResponse({
            'is_error': False,
            'message': 'Model created successfully'
        }, status_code=201)

    except Exception as e:
        db.rollback()
        db.flush()
        raise HTTPException(status_code=500, detail='Internal Server Error')
   