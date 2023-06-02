from typing import Union, List

import uvicorn
import http3

import requests
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi_sqlalchemy import DBSessionMiddleware, db

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics
from schema import Raw_data as SchemaRaw_data
from schema import Binary_results as SchemaBinary_result
from schema import File_name_and_uuid as SchemaFile_name_and_uuid
from models import Raw_data as ModelRaw_data
from models import Binary_results as ModelBinary_results
from models import File_name_and_uuid as ModelFile_name_and_uuid

import os
from dotenv import load_dotenv

load_dotenv('.env')

app = FastAPI()
client = http3.AsyncClient()

# to avoid csrftokenError
app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/binary_api/") #TODO exchange filepath for params dict
async def call_binary_api(endpoint: Union[str], filepath: Union[str]):
    binary_api_url = os.environ['BINARY_API_URL']
    r = requests.get(url=binary_api_url + endpoint, params={"config": filepath})
    return r.json()


@app.post("/fastqlukas/")
async def fastq(filepath: Union[str]):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=filepath,
                                                    file_uuid=uuid4())
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    fastq_id = db_file_name_and_uuid.id

    readsjson = call_binary_api("fastq_json/", filepath)

    for read in readsjson:
        db_raw_data = ModelRaw_data(sequence_id=read["id"], sequence=str(read["sequence"]),
                                    phred_quality=read["phred_quality"], file_id=fastq_id)
        db.session.add(db_raw_data)
        db.session.commit()
    return {"added %d reads to postgresdb", len(readsjson)}


@app.post('/raw_data/', response_description="write entries to raw data table" ,
          response_model=SchemaRaw_data, status_code=status.HTTP_201_CREATED)
async def post_raw_data(raw_data: SchemaRaw_data):
    db_raw_data = ModelRaw_data(sequence_id=raw_data.sequence_id,
                                sequence=raw_data.sequence,
                                sequence_length=raw_data.sequence_length,
                                min_quality=raw_data.min_quality,
                                max_quality=raw_data.max_quality,
                                average_quality=raw_data.average_quality,
                                phred_quality=raw_data.phred_quality,
                                file_id=raw_data.file_id)
    db.session.add(db_raw_data)
    db.session.commit()
    return db_raw_data


@app.post('/binary_result/', response_description="write entries to binary_result table"
    ,response_model=SchemaBinary_result, status_code=status.HTTP_201_CREATED)
async def post_binary_result(binary_result: SchemaBinary_result):
    db_binary_result = ModelRaw_data(sequence_id=binary_result.sequence_id,
                                     type=binary_result.type,
                                     name=binary_result.name,
                                     value=binary_result.value,
                                     file_id=create_file_name_and_uuid_entries)
    db.session.add(db_binary_result)
    db.session.commit()
    return db_binary_result


@app.get('/sequence_id/', response_description="get read including all binary entries by sequence_id")
async def get_entries_by_sequence_id(sequence_id: Union[str]):
    raw_data = db.session.query(ModelRaw_data).all()#TODO join tables on sequence id
    raw_data_results = [read for read in raw_data if read.sequence_id == sequence_id]
    if len(raw_data_results)==0:
        return status.HTTP_404_NOT_FOUND
    binary_data = db.session.query(ModelBinary_results).all()
    binary_results = [entry for entry in binary_data if entry.sequence_id == sequence_id]
    combined_results = {}
    if len(binary_results)>0:
        for read in raw_data_results:
            combined_results[read]=binary_results

    #jointtables = db.session.query(ModelRaw_data).outerjoin(ModelBinary_results, ModelRaw_data.sequence_id==ModelBinary_results.sequence_id) #it says first here because "maximum recursion  depth exceeded error" otherwise
    # results = db.session.query(ModelRaw_data).filter(ModelRaw_data.sequence_id==dsequence_id).first() #it says first here because "maximum recursion  depth exceeded error" otherwise

    return raw_data_results, binary_results

@app.get('/raw_data/', response_description="list all reads in raw data table", response_model=List[SchemaRaw_data])
async def list_raw_data_entries():
    raw_data = db.session.query(ModelRaw_data).all() #too many results
    #raw_data = db.session.query(ModelRaw_data).first()  # just here because i needed a random sequence id
    # raw_data = db.session.query(ModelRaw_data).count()
    return raw_data


@app.get('/binary_results_by_seq_id/', response_description="list all reads with matching seq_id in binary_results table", response_model=List[SchemaBinary_result])
async def list_binary_results(sequence_id: Union[str]):
    binary_results = db.session.query(ModelBinary_results).all()
    results = [x for x in binary_results if x.sequence_id == sequence_id]
    return results


@app.get('/file_name_and_uuid/', response_description="list all entries in file_name_and_id", response_model=List[SchemaFile_name_and_uuid])
async def list_file_name_and_uuid():
    file_name_and_uuids = db.session.query(ModelFile_name_and_uuid).all()
    return file_name_and_uuids


@app.post('/file_name_and_uuid/', response_description="write entries to file_name_and_id table" ,
          response_model=SchemaFile_name_and_uuid, status_code=status.HTTP_201_CREATED)
async def create_file_name_and_uuid_entries(file_name_and_uuid: SchemaFile_name_and_uuid):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=file_name_and_uuid.name,
                                                    file_uuid=file_name_and_uuid.uuid)
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    return db_file_name_and_uuid


@app.post('/fastq/', status_code=status.HTTP_201_CREATED)
async def create_fastq_entries(filepath: Union[str]):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=filepath,
                                                    file_uuid=uuid4())
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    fastq_id = db_file_name_and_uuid.id

    reads = get_fastq_metrics(filepath)

    for read in reads:
        db_raw_data = ModelRaw_data(sequence_id=read["id"],
                                    sequence=str(read["sequence"]),
                                    sequence_length=read["sequence_length"],
                                    min_quality=read["min_quality"],
                                    max_quality=read["max_quality"],
                                    average_quality=read["average_quality"],
                                    phred_quality=read["phred_quality"],
                                    file_id=fastq_id)
        db.session.add(db_raw_data)
        db.session.commit()
    return {"added "+str(len(reads))+" reads to postgresDB"}


@app.post('/sam/', status_code=status.HTTP_201_CREATED)
async def create_sam_enries(filepath: Union[str]):
    binary_results = get_sam_metrics(filepath)

    file_name = binary_results["mapping_reference_file"]
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=file_name,
                                                    file_uuid=uuid4())
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    sam_id = db_file_name_and_uuid.id

    entry_count = 0
    for alignment in binary_results["alignments"]:
        db_binary_results = ModelBinary_results(sequence_id=alignment["sequence_id"],
                                                type=str(type(alignment["position_in_ref"])),
                                                name="position_in_ref",
                                                value=alignment["position_in_ref"],
                                                file_id=sam_id)
        db.session.add(db_binary_results)
        db.session.commit()
        entry_count += 1

        db_binary_results = ModelBinary_results(sequence_id=alignment["sequence_id"],
                                                type=str(type(alignment["mapping_qual"])),
                                                name="mapping_qual",
                                                value=alignment["mapping_qual"],
                                                file_id=sam_id)
        db.session.add(db_binary_results)
        db.session.commit()
        entry_count += 1

        mapping_tags = alignment["mapping_tags"]
        for mapping_tag in mapping_tags:
            db_binary_results = ModelBinary_results(sequence_id=alignment["sequence_id"],
                                                    type=str(type(mapping_tags[mapping_tag])),
                                                    name=mapping_tag,
                                                    value=mapping_tags[mapping_tag],
                                                    file_id=sam_id)
            db.session.add(db_binary_results)
            db.session.commit()
            entry_count += 1
    return {"added "+str(entry_count)+" entries from sam file to postgresdb"}


@app.post('/kraken2/', status_code=status.HTTP_201_CREATED)
async def create_kraken_entries(filepath: Union[str]):
    kraken_results = get_kraken_metrics(filepath)

    file_name = filepath
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=file_name,
                                                    file_uuid=uuid4())
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    file_id = db_file_name_and_uuid.id
    entry_count = 0

    for classification in kraken_results:
        for key in classification.keys():
            if key != "sequence_id":
                db_binary_results = ModelBinary_results(sequence_id=classification["sequence_id"],
                                                        type=str(type(classification[key])),
                                                        name=str(key),
                                                        value=str(classification[key]),
                                                        file_id=file_id)
                db.session.add(db_binary_results)
                db.session.commit()
                entry_count += 1
    return {"added " + str(entry_count) + "entries from kraken execution to postgresdb"}


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8080)
