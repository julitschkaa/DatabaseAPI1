# build a schema using pydantic
from pydantic import BaseModel


class RawData(BaseModel):
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


class BinaryResults(BaseModel):
    sequence_id: str
    type: str
    name: str
    value: str
    file_id: int
    raw_data_id: int

    class Config:
        orm_mode = True


class FileNameAndUuid(BaseModel):
    file_name: str
    file_uuid: str

    class Config:
        orm_mode = True
