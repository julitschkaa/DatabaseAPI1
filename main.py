import pymongo
import uvicorn
import requests

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from typing import List, Union

from pydantic import BaseModel
from pymongo.mongo_client import MongoClient

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics

from models import PyObjectId, FastqReadModel, Bowtie2ResultModel, Kraken2ResultModel

import os
from dotenv import load_dotenv

load_dotenv('.env')

app = FastAPI()
client = MongoClient(os.environ["MONGODB_URI"])
db = client.eva_ngs  # specify database name 'eva_ngs'
db["all_docs"].create_index([("sequence_id", pymongo.HASHED)])


# uncomment to avoid csrftokenError
# app.add_middleware(DBSessionMiddleware, db_url=os.environ['MONGODB_URL'])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/binary_API_sam_json_from_fastq/")
async def call_binary_api_sam_json_from_fastq(fastqpath: Union[str],
                                              fastaurl: Union[str],
                                              rootpath: Union[str]):
    response = await call_binary_api(endpoint="/sam_json_from_fastq/", params={"fastqpath": fastqpath,
                                                                               "fastaurl": fastaurl,
                                                                               "rootpath": rootpath})
    return response.json()


@app.get("/binary_API_sam_json/")  # TODO write json to db
async def call_binary_api_sam_sjon_endpoint(sampath: Union[str]):
    response = await call_binary_api(endpoint="/sam_json/", params={"sampath": sampath})
    return response.json()


@app.get("/binary_API_sam_csv/")
async def call_binary_api_sam_csv_endpoint(sampath: Union[str]):
    response = await call_binary_api(endpoint="/sam_csv/", params={"sampath": sampath})
    return response.json()


@app.get("/binary_API_fastq_json/")
async def call_binary_api_fastq_json_endpoint(fastqpath: Union[str]):
    response = await call_binary_api(endpoint="/fastq_json/", params={"fastqpath": fastqpath})
    return response.json()


@app.get("/binary_API_fastq_csv/")
async def call_binary_api_fastq_csv_endpoint(fastqpath: Union[str]):
    response = await call_binary_api(endpoint="/fastq_csv/", params={"fastqpath": fastqpath})
    return response.json()


@app.get("/binary_API_kraken_json/")
async def call_binary_api_kraken_json_endpoint(krakendb: Union[str],
                                               fastafile: Union[str],
                                               output: Union[str]):
    response = await call_binary_api(endpoint="/kraken_json/", params={"krakendb": krakendb,
                                                                       "fastafile": fastafile,
                                                                       "output": output})
    return response.json()


@app.get("/binary_API_init/")
async def call_binary_api_init_by_config_obj(config: Union[str]):
    response = await call_binary_api(endpoint="/init/", params={"config": config})
    return response.json()


@app.get("/binary_API_init_by_path/")
async def call_binary_api_init_by_path(configpath: Union[str]):
    response = await call_binary_api(endpoint="/init_by_path/", params={"config": configpath})
    return response.json()


@app.get("/binary_API_init_async/")
async def call_binary_api_init_async(configpath: Union[str], threadname: Union[str]):
    response = await call_binary_api(endpoint="/init_async/", params={"config": configpath, "threadname": threadname})
    return response.json()


@app.get("/binary_API_check_thread/")
async def call_binary_api_check_thread(threadname: Union[str]):
    response = await call_binary_api(endpoint="/check_thread/", params={"threadname": threadname})
    return response.json()


@app.get("/binary_API_json_from_bowtie_exec/")
async def call_binary_api_json_from_bowtie_execution(fastapath: Union[str], fastqpath: Union[str],
                                                     rootpath: Union[str]):
    response = await call_binary_api(endpoint="/sam_json_from_bowtie_execution/", params={"fastapath": fastapath,
                                                                                          "fastqpath": fastqpath,
                                                                                          "rootpath": rootpath})
    return response.json()


@app.get("/binary_api/")
async def call_binary_api(endpoint: Union[str], params: dict[str, str]):
    binary_api_url = os.environ['BINARY_API_URL']
    response = requests.get(url=binary_api_url + endpoint, params=params)
    return response

@app.get("/dimensions/")
async def get_all_field_names():#TODO doesnt work yet
    field_names =[]
    cursor=db['all_docs'].find()
    for document in cursor:
        field_names.append(type(document))
    return field_names


@app.post('/document/', response_description="Add new Document", response_model=BaseModel)
async def create_document(document: BaseModel = Body(...)):
    document = jsonable_encoder(document)
    new_document = db["all_docs"].insert_one(document)
    created_document = db["all_docs"].find_one({"_id": new_document.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_document)


@app.post('/documents/', response_description="Add new Documents")
async def create_documents(documents: List[BaseModel] = Body(...)):
    jsonied_documents = []  # TODO exceptionhandling needed
    for document in documents:
        jsonied_documents.append(jsonable_encoder(document))
    new_documents_ids_list = db["all_docs"].insert_many(jsonied_documents).inserted_ids
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content=f"created {len(new_documents_ids_list)} new documents in eva_ngs collection")


@app.get("/documents/", response_description="list all documents", response_model=List[BaseModel])
async def list_all_documents():
    documents = []
    for document in db["all_docs"].find():
        documents.append(document)
    if documents:
        return JSONResponse(status_code=status.HTTP_200_OK, content=documents)
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                        detail=f"looks like there are no documents in the database yet")


@app.get("/documents/{sequence_id}", response_description="get documents for a specific sequence_id",
         response_model=list[BaseModel])  # TODO doesnt find any seuqence ids... whelp
async def get_documents_by_id(sequence_id: str):
    documents: list[BaseModel] = []
    for document in db["all_docs"].find({"sequence_id": sequence_id}):
        documents.append(document)
    if documents:
        return JSONResponse(status_code=status.HTTP_200_OK, content=documents)
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")


@app.delete("/documents/{sequence_id}",
            response_description="Delete all documents by sequence_id")  # bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>
async def delete_document_by_id(sequence_id: str):
    deleted_documents_count = db["all_docs"].delete_many({"sequence_id": sequence_id}).deleted_count
    if deleted_documents_count > 0:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f"deleted {str(deleted_documents_count)} documents for sequence {sequence_id}")
    raise HTTPException(status_code=404, detail=f"no documents for seq_id {sequence_id} found for deletion")


@app.post('/fastq/', response_description="Add all reads from a fastq file to database")
async def upload_fastq(filepath: Union[str]):
    reads = get_fastq_metrics(filepath)
    collected_fastq_reads = []

    for read in reads:
        # TODO check if sequence ID exists already
        collected_fastq_reads.append(FastqReadModel(id=PyObjectId(),
                                             sequence_id=str(read["sequence_id"]),
                                             sequence=str(read["sequence"]),
                                             sequence_length=int(read["sequence_length"]),
                                             min_quality=int(read["min_quality"]),
                                             max_quality=int(read["max_quality"]),
                                             average_quality=float(read["average_quality"]),
                                             phred_quality=read["phred_quality"],
                                             file_name=filepath
                                             ))

    return await create_documents(collected_fastq_reads)


@app.post('/sam/', response_description="Add all alignments from sam file to database")
async def upload_sam(filepath: Union[str]):  # TODO noch nicht fertig :')
    sam_entries = get_sam_metrics(filepath)
    file_name_sam = filepath
    collected_alignments: list = []

    for alignment in sam_entries["alignments"]:
        collected_alignments.append(Bowtie2ResultModel(
            sequence_id=alignment["sequence_id"],
            mapping_tags=alignment["mapping_tags"],
            position_in_ref=alignment["position_in_ref"],
            mapping_qual=alignment["mapping_qual"],
            file_name=file_name_sam,
            mapping_reference_file=sam_entries["mapping_reference_file"]
        ))

    return await create_documents(collected_alignments)


@app.post('/kraken2/', response_description="Add all classifications from kraken2 output to database")
async def upload_kraken(filepath: Union[str]):
    kraken_results = get_kraken_metrics(filepath)
    file_name_kraken2 = filepath
    collected_classifications: list = []

    for classification in kraken_results:
        collected_classifications.append(Kraken2ResultModel(
            sequence_id=classification["sequence_id"],
            classified=classification["classified"],
            taxonomy_id=classification["taxonomy_id"],
            sequence_length=classification["sequence_length"],
            lca_mapping_list=classification["lca_mapping_list"],
            file_name=file_name_kraken2
        ))
    return await create_documents(collected_classifications)


@app.delete('/clear_all/')
async def delete_all_documents():
    if "all_docs" not in db.list_collection_names():
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="no table all_docs found in mangodb")
    db["all_docs"].drop()
    return JSONResponse(status_code=status.HTTP_200_OK, content="database collection all_docs cleared of all documents")


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
