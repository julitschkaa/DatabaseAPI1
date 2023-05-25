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

    class Config:
        orm_mode = True


class File_name_and_uuid(BaseModel):
    file_name: str
    uuid: str

    class Config:
        orm_mode = True
