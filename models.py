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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")#aliased because pydantic otherwise assumes private variable
    sequence_id : str = Field(...)
    sequence : str = Field(...)
    sequence_length : int = Field(...)
    min_quality : int = Field(...)
    max_quality : int = Field(...)
    average_quality : float = Field(...)
    phred_quality : str = Field(...)
    binary_results: list = []
    file_id_fastq : str = Field(...) #could be session id instead?

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class BinaryResultModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")  # aliased because pydantic otherwise assumes private variable
    sequence_id : str = Field(...)
    file_id: str = Field(...)
    type: str = Field(...)
    name: str = Field(...)
    value: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

