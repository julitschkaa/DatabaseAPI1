# build a schema using pydantic
#TODO find out if schema is actually needed if typing is used in models

from pydantic import BaseModel


class FastqRead(BaseModel):
    sequence_id: str
    sequence: str
    sequence_length: int
    min_quality: int
    max_quality: int
    average_quality: float
    phred_quality: str
    binary_results: list
    file_name: str

    class Config:
        orm_mode = True


class Bowtie2Result(BaseModel):
    sequence_id: str
    mapping_tags: dict
    position_in_ref: int
    mapping_qual: int
    file_name: str
    mapping_reference_file:  str

    class Config:
        orm_mode = True


class Kraken2Result(BaseModel):
    sequence_id: str
    classified: str
    taxonomy_id: str
    sequence_length: int
    lca_mapping_list: list
    file_name: str

    class Config:
        orm_mode = True
