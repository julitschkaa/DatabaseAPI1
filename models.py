import uuid

from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List

"""MangoDB stores data as BSON. FastAPI encodes to JSON.
BSON native ObjectId can't be directly encoded as JSON, 
therefore ObjectId is converted to String _id """
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
class ReadModel(BaseModel):
    #__tablename__ = 'reads'
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")#aliased because pydantic otherwise assumes private variablebrauchht's das hier überhaupt wenn Pk=seq_id?
    sequence_id : str = Field(...)
    sequence : str = Field(...)
    phred_quality : str = Field(...)
    file_id_fastq : str = Field(...) #could be session id instead?

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Update_ReadModel(BaseModel):
    file_id_sam: Optional[str]
    type: Optional[str]
    name: Optional[str]
    value: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

