# build a schema using pydantic
from pydantic import BaseModel

class Binary_results(BaseModel):
    sequence_id: str
    file_id: int
    name: str
    type: str
    value: str

    class Config:
        orm_mode = True


class File_name_and_uuid(BaseModel):
    file_name: str
    binary_of_origin: str
    file_uuid: str

    class Config:
        orm_mode = True

class Dimension(BaseModel):
    name: str
    type: str

    class Config:
        orm_mode = True
