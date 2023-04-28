# build a schema using pydantic
from pydantic import BaseModel


class Raw_data(BaseModel):
    sequence_id: str
    sequence: str
    phred_quality: str
    file_id: int

    class Config:
        orm_mode = True

class Binary_results(BaseModel):
    sequence_id: str
    mapping_reference_file: str
    binary_of_origin: str
    type: str
    value: float

    class Config:
        orm_mode = True

class File_name_and_uuid(BaseModel):
    file_name: str
    uuid: str

    class Config:
        orm_mode = True
