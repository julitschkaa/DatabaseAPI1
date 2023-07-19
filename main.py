import pymongo
import uvicorn
import requests

from collections.abc import Mapping

from fastapi import FastAPI, Body, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from typing import List, Union

from pydantic import BaseModel
from pymongo.mongo_client import MongoClient

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics

from models import PyObjectId, FastqReadModel, Bowtie2ResultModel, Kraken2ResultModel, Document

import os
from dotenv import load_dotenv

load_dotenv('.env')

app = FastAPI()
client = MongoClient(os.environ["MONGODB_URI"])
db = client.eva_ngs  # specify database name 'eva_ngs'
db["all_docs"].create_index([("sequence_id", pymongo.HASHED)])#creating single field index on sequence_id field


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


def recursively_find_keys_and_types(dict_obj, key_prefix="", dict_of_keys_and_types={}):
    for key, value in dict_obj.items():
        if isinstance(value, Mapping):
            recursively_find_keys_and_types(value, f"{key_prefix}{key}.", dict_of_keys_and_types)
        else:
            dict_of_keys_and_types[f"{key_prefix}{key}"] = type(value).__name__
    return dict_of_keys_and_types

@app.get("/dimensions/", response_description="returns list of all dimensions currently present in database",
         status_code=status.HTTP_200_OK
         )
async def list_all_possible_dimensions():
    field_types = {}
    for document in db['all_docs'].find():
        field_types.update(recursively_find_keys_and_types(document))
    return field_types


@app.get("/read_count/", response_description="returns count of available reads in data base",
         status_code=status.HTTP_200_OK,
         response_model=int
         )#TODO better exceptionhandling?
async def get_read_count():
    read_count = len(db["all_docs"].distinct('sequence_id'))
    return read_count

@app.get('/random_x_percent/{percentage}', response_description="get x percent of all reads, randomly selected",
         status_code=status.HTTP_200_OK)
async def get_random_reads(percentage: int):
    if percentage > 100:
        raise HTTPException(status_code=406, detail=f"sorry, I can't get you more than 100% of all reads")
    read_count = await get_read_count()
    num_documents = int(read_count * percentage / 100)
    if num_documents < 1:
        raise HTTPException(status_code=406,
                            detail=f"{percentage}percent results in less than 1 out of {read_count}reads. ")

    # Create the aggregation pipeline
    pipeline = [
        {"$group": {"_id": "$sequence_id"}},
        {"$sample": {"size": num_documents}}
    ]
    # Execute the aggregation pipeline
    distinct_sequence_ids = [doc['_id'] for doc in db['all_docs'].aggregate(pipeline)]
    random_reads = []
    for sequence_id in distinct_sequence_ids:
        random_reads.append(await get_read_by_seq_id(sequence_id))#TODO: this is horribly slow :')
    return random_reads

@app.get('/get_one_dimension/{dimension_name}/{percentage}',
         response_description="get one dimension of x percent of all reads",
         response_model=list, status_code=status.HTTP_200_OK)
async def get_one_dimension(dimension_name: str, percentage: int):
    if percentage > 100:
        raise HTTPException(status_code=406, detail=f"sorry, I can't get you more than 100% of all reads")
    read_count = await get_read_count()
    num_documents = int(read_count * percentage / 100)
    if num_documents < 1:
        raise HTTPException(status_code=406,
                            detail=f"{percentage}percent results in less than 1 out of {read_count}reads. ")


    # Build the aggregation pipeline
    pipeline = [
        {"$match": {dimension_name: {"$exists": True}}},
        {"$sample": {"size": num_documents}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension_name: f"${dimension_name}"}}
    ]

    # Execute the aggregation pipeline
    result = list(db['all_docs'].aggregate(pipeline))

    return result


@app.get('/get_two_dimensions/{dimension1_name}/{dimension2_name}/{percentage}',
         response_description="get two dimensions of x percent of all reads",
         response_model=list, status_code=status.HTTP_200_OK)
async def get_two_dimensions(dimension1_name: str, dimension2_name: str, percentage: int):
    if percentage > 100:
        raise HTTPException(status_code=406, detail=f"sorry, I can't get you more than 100% of all reads")
    read_count = await get_read_count()
    num_documents = int(read_count * percentage / 100)
    if num_documents < 1:
        raise HTTPException(status_code=406,
                            detail=f"{percentage}percent results in less than 1 out of {read_count}reads. ")

    # Build the aggregation pipeline for dimension1_name
    pipeline1 = [
        {"$match": {dimension1_name: {"$exists": True}}},
        {"$sample": {"size": num_documents}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension1_name: f"${dimension1_name}"}}
    ]

    # Build the aggregation pipeline for dimension2_name
    pipeline2 = [
        {"$match": {dimension2_name: {"$exists": True}}},
        #{"$sample": {"size": num_documents}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension2_name: f"${dimension2_name}"}}
    ]

    # Execute the aggregation pipelines
    result1 = list(db['all_docs'].aggregate(pipeline1))
    result2 = list(db['all_docs'].aggregate(pipeline2))

    # Merge the two results based on 'sequence_id'
    result = []
    for doc1 in result1:
        for doc2 in result2:
            if doc1['sequence_id'] == doc2['sequence_id']:
                result.append({**doc1, **doc2})

    return result


@app.get('/get_three_dimensions/{dimension1_name}/{dimension2_name}/{dimension3_name}/{percentage}',#TODO there is
         # no exception if dimension_name doesn't exist
         response_description="get three dimensions of x percent of all reads",
         response_model=list, status_code=status.HTTP_200_OK)
async def get_three_dimensions(dimension1_name: str, dimension2_name: str, dimension3_name: str, percentage: int):
    if percentage > 100:
        raise HTTPException(status_code=406, detail=f"sorry, I can't get you more than 100% of all reads")
    read_count = await get_read_count()
    num_documents = int(read_count * percentage / 100)
    if num_documents < 1:
        raise HTTPException(status_code=406,
                            detail=f"{percentage}percent results in less than 1 out of {read_count}reads. ")

    # Build the aggregation pipeline for dimension1_name
    pipeline1 = [
        {"$match": {dimension1_name: {"$exists": True}}},
        {"$sample": {"size": num_documents}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension1_name: f"${dimension1_name}"}}
    ]

    # Build the aggregation pipeline for dimension2_name
    pipeline2 = [
        {"$match": {dimension2_name: {"$exists": True}}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension2_name: f"${dimension2_name}"}}
    ]

    # Build the aggregation pipeline for dimension3_name
    pipeline3 = [
        {"$match": {dimension3_name: {"$exists": True}}},
        {"$project": {"_id": 0, "sequence_id": "$sequence_id", dimension3_name: f"${dimension3_name}"}}
    ]

    # Execute the aggregation pipelines
    result1 = list(db['all_docs'].aggregate(pipeline1))
    result2 = list(db['all_docs'].aggregate(pipeline2))
    result3 = list(db['all_docs'].aggregate(pipeline3))

    # Check if each dimension exists in the returned results
    if not result1:
        raise HTTPException(status_code=404, detail=f"Dimension '{dimension1_name}' not found in collection.")
    if not result2:
        raise HTTPException(status_code=404, detail=f"Dimension '{dimension2_name}' not found in collection.")
    if not result3:
        raise HTTPException(status_code=404, detail=f"Dimension '{dimension3_name}' not found in collection.")

    # Merge the three results based on 'sequence_id'
    result = []
    for doc1 in result1:
        for doc2 in result2:
            for doc3 in result3:
                if doc1['sequence_id'] == doc2['sequence_id'] == doc3['sequence_id']:
                    result.append({**doc1, **doc2, **doc3})

    return result

'''this singular document insert is from a previous stage and probably no longer needed'''
@app.post('/document/', response_description="Add new Document", response_model=BaseModel)
async def create_document(document: BaseModel = Body(...)):
    document = jsonable_encoder(document)
    new_document = db["all_docs"].insert_one(document)
    created_document = db["all_docs"].find_one({"_id": new_document.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_document)


@app.post('/documents/', response_description="Add new Documents", response_model=List[str])
async def create_documents(documents: List[Union[FastqReadModel, Bowtie2ResultModel, Kraken2ResultModel]] = Body(...)):
    if not documents:
        raise HTTPException(status_code=400, detail="No documents provided")

    try:
        jsonied_documents = [jsonable_encoder(document) for document in documents]
        result = db["all_docs"].insert_many(jsonied_documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while adding the documents.")

    return [str(id) for id in result.inserted_ids]


@app.get('/read_by_sequence_id/{sequence_id}', response_description="get read_object. an object combined of all "
                                                                    "document fields, matching a given sequence_id")
async def get_read_by_seq_id(sequence_id: Union[str]):
    # Fetch all relevant documents in a single query
    all_documents_for_id = await get_documents_by_id(sequence_id)

    # Get all dimensions from the fetched documents
    all_dimensions = set().union(*[set(doc.keys()) for doc in all_documents_for_id])

    # Create the read_object
    read_object = {}
    for dimension in all_dimensions:
        for document in all_documents_for_id:
            value = document.get(dimension)
            if value is not None:
                read_object[dimension] = value
                break

    return read_object


@app.get("/reads/", response_description="list all read objects")
async def get_all_reads():
    pipeline = [
        {
            "$group": {
                "_id": "$sequence_id",
                "fields": {
                    "$addToSet": "$$ROOT"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "sequence_id": "$_id",
                "fields": {
                    "$reduce": {
                        "input": "$fields",
                        "initialValue": {},
                        "in": { "$mergeObjects": ["$$value", "$$this"] }
                    }
                }
            }
        }
    ]

    all_read_objects = list(db['all_docs'].aggregate(pipeline))

    for read_object in all_read_objects:
        read_object.update(read_object.pop('fields'))

    return all_read_objects


@app.get("/documents/", response_description="list all documents")
async def list_all_documents(page_size: int = Query(10, gt=0), page: int = Query(1, gt=0)):
    skip = (page - 1) * page_size
    documents = list(db["all_docs"].find().skip(skip).limit(page_size))
    if not documents:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail=f"looks like there are no documents in the database yet")
    return documents


@app.get("/documents/{sequence_id}", response_description="get documents for a specific sequence_id",
         response_model=list[Document])
async def get_documents_by_id(sequence_id: str):
    documents: list[Document] = []
    for document in db["all_docs"].find({"sequence_id": sequence_id}):
        documents.append(document)
    if documents:
        return documents
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")


@app.delete("/documents/{sequence_id}",
            response_description="Delete all documents by sequence_id")  # bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>
async def delete_document_by_id(sequence_id: str):
    deleted_documents_count = db["all_docs"].delete_many({"sequence_id": sequence_id}).deleted_count
    if deleted_documents_count > 0:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f"deleted {str(deleted_documents_count)} documents for sequence {sequence_id}")
    raise HTTPException(status_code=404, detail=f"no documents for seq_id {sequence_id} found for deletion")


'''@app.post('/fastq/', response_description="list doc_ids of all reads from a fastq file added to database")
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

    return await create_documents(collected_fastq_reads)'''
@app.post('/fastq/', response_description="list doc_ids of all reads from a fastq file added to database")
async def upload_fastq(filepath: str):
    reads = get_fastq_metrics(filepath)
    if not reads:
        raise HTTPException(status_code=400, detail=f"Could not get any FASTQ metrics from filepath: {filepath}")

    # Generate the documents directly
    documents = [
        FastqReadModel(
            id=PyObjectId(),
            sequence_id=str(read["sequence_id"]),
            sequence=str(read["sequence"]),
            sequence_length=int(read["sequence_length"]),
            min_quality=int(read["min_quality"]),
            max_quality=int(read["max_quality"]),
            average_quality=float(read["average_quality"]),
            phred_quality=read["phred_quality"],
            file_name=filepath
        ) for read in reads
    ]

    return await create_documents(documents)



'''@app.post('/sam/', response_description="list of doc_ids of all alignments from sam file added to database")
async def upload_sam(filepath: Union[str]):
    sam_entries = get_sam_metrics(filepath)
    if not sam_entries:
        raise HTTPException(status_code=400, detail=f"Could not get any sam_entries from filepath: {filepath}")
    collected_alignments: list = []

    for alignment in sam_entries["alignments"]:
        collected_alignments.append(Bowtie2ResultModel(
            sequence_id=alignment["sequence_id"],
            mapping_tags=alignment["mapping_tags"], #TODO: consider making this several fields instead of nested dict!!
            position_in_ref=alignment["position_in_ref"],
            mapping_qual=alignment["mapping_qual"],
            file_name=filepath,
            mapping_reference_file=sam_entries["mapping_reference_file"]
        ))

    return await create_documents(collected_alignments)'''

@app.post('/sam/', response_description="list of doc_ids of all alignments from sam file added to database")
async def upload_sam(filepath: str):
    sam_entries = get_sam_metrics(filepath)
    if not sam_entries or "alignments" not in sam_entries:
        raise HTTPException(status_code=400, detail=f"Could not get any SAM metrics from filepath: {filepath}")

    # Generate the documents directly
    documents = [
        Bowtie2ResultModel(
            sequence_id=alignment["sequence_id"],
            mapping_tags=alignment["mapping_tags"],#TODO: consider making this several fields instead of nested dict!!
            position_in_ref=alignment["position_in_ref"],
            mapping_qual=alignment["mapping_qual"],
            file_name=filepath,
            mapping_reference_file=sam_entries["mapping_reference_file"]
        ) for alignment in sam_entries["alignments"]
    ]

    return await create_documents(documents)



@app.post('/kraken2/', response_description="list of doc_ids of all classifications from kraken2 added to database")
async def upload_kraken(filepath: str):
    kraken_results = get_kraken_metrics(filepath)
    if not kraken_results:
        raise HTTPException(status_code=400, detail=f"Could not get any kraken metrics from filepath: {filepath}")

    # Generate the kraken2documents
    documents = [
        Kraken2ResultModel(
            sequence_id=classification["sequence_id"],
            classified=classification["classified"],
            taxonomy_id=classification["taxonomy_id"],
            lca_mapping_list=classification["lca_mapping_list"],
            file_name=filepath
        ) for classification in kraken_results
    ]

    return await create_documents(documents)



@app.delete('/clear_all/')
async def delete_all_documents():
    if "all_docs" not in db.list_collection_names():
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="no table all_docs found in mangodb")
    db["all_docs"].drop()
    return JSONResponse(status_code=status.HTTP_200_OK, content="database collection all_docs cleared of all documents")


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
