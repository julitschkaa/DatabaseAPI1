# build a schema using pydantic
from pydantic import BaseModel


class Raw_data(BaseModel):
    sequence_id: str
    sequence: str
    sequence_length: int
    min_quality: int  # new
    max_quality: int  # new
    average_quality: float  # new
    phred_quality: str
    file_id: int

    class Config:
        orm_mode = True


class Binary_results(BaseModel):
    sequence_id: str
    type: str
    name: str
    value: str
    file_id: int
    raw_data_id:  int

    class Config:
        orm_mode = True


class File_name_and_uuid(BaseModel):
    file_name: str
    file_uuid: str

    class Config:
        orm_mode = True

class Dimension(BaseModel):
    name: str
    type: str

    class Config:
        orm_mode = True

class OneDimension(BaseModel):
    sequence_id: str
    name: str
    value: float

    class Config:
        orm_mode = True

class TwoDimensions(BaseModel):
    sequence_id: str
    name1: str
    value1: float
    name2: str
    value2: float

    class Config:
        orm_mode = True

class ThreeDimensions(BaseModel):
    sequence_id: str
    name1: str
    value1: float
    name2: str
    value2: float
    name3: str
    value3: float

    class Config:
        orm_mode = True