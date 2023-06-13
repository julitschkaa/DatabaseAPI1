# build a schema using pydantic
from pydantic import BaseModel


class Raw_data(BaseModel):
    sequence_id: str
    sequence: str
    sequence_length: int
    min_quality: int
    max_quality: int
    average_quality: float
    phred_quality: str
    binary_results: list
    file_id: int

    class Config:
        orm_mode = True

class Binary_results(BaseModel):
    sequence_id: str
    file_id: str
    type: str
    name: str
    value: str

    class Config:
        orm_mode = True

class File_name_and_uuid(BaseModel):
    file_name: str
    uuid: str

    class Config:
        orm_mode = True
