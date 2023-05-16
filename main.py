from typing import Union, Optional

import uvicorn
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi_sqlalchemy import DBSessionMiddleware, db

from Datafile_API.bio_python_script import get_fastq_metrics
from Datafile_API.simplesam_script import get_sam_metrics
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

# to avoid csrftokenError
app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/raw_data/', response_model=SchemaRaw_data)
async def raw_data(raw_data: SchemaRaw_data):
    db_raw_data = ModelRaw_data(sequence_id=raw_data.sequence_id, sequence=raw_data.sequence, phred_quality=raw_data.phred_quality, file_id=raw_data.file_id)
    db.session.add(db_raw_data)
    db.session.commit()
    return db_raw_data


@app.post('/binary_result/', response_model=SchemaBinary_result)
async def binary_result(binary_result: SchemaBinary_result):
    db_binary_result = ModelRaw_data(sequence_id=binary_result.sequence_id,
                        type=binary_result.type, name=binary_result.name, value=binary_result.value, file_id=file_name_and_uuid)
    db.session.add(db_binary_result)
    db.session.commit()
    return db_binary_result

@app.get('/sequence_id/')
async def sequence_id(sequence_id: Union[str]):
    raw_data = db.session.query(ModelRaw_data).all()
    results = [read for read in raw_data if read.sequence_id==sequence_id]
    #results = db.session.query(ModelRaw_data).filter(ModelRaw_data.sequence_id==dsequence_id).first() #it says first here because "maximum recursion  depth exceeded error" otherwise
    return results

@app.get('/raw_data/')
async def raw_data():
    #raw_data = db.session.query(ModelRaw_data).all() #too many results
    raw_data = db.session.query(ModelRaw_data).first() #just here because i needed a random sequence id
    #raw_data = db.session.query(ModelRaw_data).count()
    return raw_data


@app.get('/binary_results/')
async def binary_results(sequence_id: Union[str]):
    binary_results = db.session.query(ModelBinary_results).all()
    results = [x for x in binary_results if x.sequence_id==sequence_id]
    return results


@app.get('/file_name_and_uuid/')
async def file_name_and_uuid():
    file_name_and_uuids = db.session.query(ModelFile_name_and_uuid).all()
    return file_name_and_uuids


@app.post('/file_name_and_uuid/', response_model=SchemaFile_name_and_uuid)
async def file_name_and_uuid(file_name_and_uuid: SchemaFile_name_and_uuid):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=file_name_and_uuid.name, file_uuid=file_name_and_uuid.uuid)
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    return db_file_name_and_uuid


@app.post('/fastq/')
async def fastq(filepath: Union[str]):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=filepath,
                                                    file_uuid=uuid4())
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    fastq_id = db_file_name_and_uuid.id

    reads = get_fastq_metrics(filepath)

    for read in reads:
        db_raw_data = ModelRaw_data(sequence_id=read["id"] , sequence=str(read["sequence"]),
                                    phred_quality=read["phred_quality"],file_id=fastq_id)
        db.session.add(db_raw_data)
        db.session.commit()
    return {"added %d reads to postgresdb", len(reads)}


@app.post('/sam/')
async def sam(filepath: Union[str]):

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
                entry_count +=1
    return {"added %d entries from binary of choice to postgresdb", entry_count}

@app.post('/kraken2/')
async def kraken(filepath: Union[str]):

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
                                                        name= str(key),
                                                        value= str(classification[key]),
                                                        file_id=file_id)
                db.session.add(db_binary_results)
                db.session.commit()
                entry_count += 1
    return {"added " + str(entry_count) + "entries from binary of choice to postgresdb"}



# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
