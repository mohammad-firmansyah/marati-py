from sqlalchemy import Column,String,DateTime,JSON
from config.database import Base
from sqlalchemy.dialects.postgresql import UUID,JSONB

import uuid
from datetime import datetime

class Models(Base):

    __tablename__ = 'model'

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4,unique=True, nullable=False)
    name = Column(String)
    filename = Column(String)
    created_at = Column(name='createdAt',type_= DateTime,default=datetime.utcnow,nullable=False)
    input = Column(JSONB)
    description = Column(String)
    category = Column(String)
    output = Column(JSONB)
    owner_id = Column(String)
