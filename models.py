from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError

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


class Document(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sequence_id: str = Field(...)
    file_name: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class FastqReadModel(Document):
    sequence: str = Field(...)
    sequence_length: int = Field(...)
    min_quality: int = Field(...)
    max_quality: int = Field(...)
    average_quality: float = Field(...)
    phred_quality: list = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Bowtie2ResultModel(Document):
    mapping_tags: dict = Field(...) #TODO: find way to make this flat. nested dict takes longer to search
    position_in_ref: int = Field(...)
    mapping_qual: int = Field(...)
    #I'm not including binary of origin but it might be a good option for later prototypes
    mapping_reference_file: str = Field(...)#this is not included in other db-s but might be necessary?
    #TODO find out if mapping reference file is something often requested for visualization

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Kraken2ResultModel(Document):
    classified: str = Field(...)
    taxonomy_id: str = Field(...)
    lca_mapping_list: list = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
