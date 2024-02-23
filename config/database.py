from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv 
from dotenv import dotenv_values
import os

load_dotenv()

URL_DATABASE = os.getenv('URL_DB') 

Engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=Engine) 

Base = declarative_base()