import uuid

from pydantic import BaseModel, Field
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


class FastqReadModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId,
                           alias="_id")  # aliased because pydantic otherwise assumes private variable
    sequence_id: str = Field(...)
    sequence: str = Field(...)
    sequence_length: int = Field(...)
    min_quality: int = Field(...)
    max_quality: int = Field(...)
    average_quality: float = Field(...)
    phred_quality: str = Field(...)
    file_name: str = Field(...)  # could be session id instead?

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Bowtie2ResultModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId,
                           alias="_id")  # aliased because pydantic otherwise assumes private variable
    sequence_id: str = Field(...)
    mapping_tags: dict = Field(...)
    position_in_ref: int = Field(...)
    mapping_qual: int = Field(...)
    file_name: str = Field(...)
    #I'm not including binary of origin, as its already in model name
    mapping_reference_file: str = Field(...)#this is not included in other db-s but might be necessary?
    #TODO find out if mapping reference file is something often requeted for visualizaion

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Kraken2ResultModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId,
                           alias="_id")  # aliased because pydantic otherwise assumes private variable
    sequence_id: str = Field(...)
    classified: str = Field(...)
    taxonomy_id: str = Field(...)
    sequence_length: int = Field(...)
    lca_mapping_list: list = Field(...)
    file_name: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
