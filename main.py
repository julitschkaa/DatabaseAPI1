import uvicorn
import requests
from uuid import uuid4

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from typing import List, Union

from pydantic import BaseModel
from pymongo.mongo_client import MongoClient

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics

from models import FastqModel as ReadModel, PyObjectId, BinaryResultModel, FastqModel

import os
from dotenv import load_dotenv

load_dotenv('.env')

app = FastAPI()
client = MongoClient(os.environ["MONGODB_URI"])
db = client.reads  # specify database name 'reads'


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


@app.post('/read/', response_description="Add new Read", response_model=BaseModel)
async def create_read(read: BaseModel = Body(...)):
    read = jsonable_encoder(read)
    new_read = db["eva_ngs"].insert_one(read)
    created_read = db["eva_ngs"].find_one({"_id": new_read.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_read)


@app.get("/reads/", response_description="list all reads", response_model=List[FastqModel])
async def list_reads():  # TODO includng binary result_ids in reads resulsts in loooong lists, and that is in already tiny input files
    reads = []
    for read in db["reads"].find():
        reads.append(read)
    if reads:
        return JSONResponse(status_code=status.HTTP_200_OK, content=reads)
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                        detail=f"looks like there are no reads in the database yet")


@app.get("/binary_results/", response_description="list all binary results in db",
         response_model=List[BinaryResultModel])
async def list_binary_results():
    results = []
    for result in db["binary_results"].find():
        results.append(result)
    if results:
        return JSONResponse(status_code=status.HTTP_200_OK, content=results)
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                        detail=f"looks like there are no binary_results in the database yet")


@app.get("/binary_results_to_read/", response_description="list all binary results to one read",
         response_model=List[BinaryResultModel])
async def get_binary_results_to_read(sequence_id: Union[str]):
    binary_results_list = []
    for binary_result in db["binary_results"].find({"sequence_id": sequence_id}):
        binary_results_list.append(binary_result)
    if binary_results_list:
        return JSONResponse(status_code=status.HTTP_200_OK, content=binary_results_list)
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in binary_database")


@app.get("/read/{sequence_id}", response_description="get a specific read",
         response_model=FastqModel)  # TODO best practice endpoint design is what?
async def get_read(sequence_id: str):
    if (read := db["reads"].find_one({"sequence_id": sequence_id})) is not None:
        return JSONResponse(status_code=status.HTTP_200_OK, content=read)
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")


@app.put("/{sequence_id}", response_description="add entries to binary collection and to a specific read",
         response_model=FastqModel)
async def add_binary_results_for_specific_read(sequence_id: str, new_data: list[BinaryResultModel]):
    new_data_jsonabled = []
    for result in new_data:
        result = jsonable_encoder(result)
        new_data_jsonabled.append(result)

    if (db["reads"].find_one({"sequence_id": sequence_id})) is not None:
        new_binary_result_ids = db["binary_results"].insert_many(new_data_jsonabled).inserted_ids
        db["reads"].update_one({"sequence_id": sequence_id},
                               {"$push": {"binary_results": {"$each": new_binary_result_ids}}})
        updated_read = db["reads"].find_one({"sequence_id": sequence_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=updated_read)

    raise HTTPException(status_code=404,
                        detail=f"read {sequence_id} not found in read-collection for update, therefore not added to binary_result collection either")


@app.delete("/read/{sequence_id}",
            response_description="Delete a read")  # bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>
async def delete_read(sequence_id: str):
    delete_binary_results_count = db["binary_results"].delete_many(
        {"sequence_id": sequence_id}).deleted_count  # TODO mimics on delete cascade ob das so smart ist...
    deleted_read = db["reads"].delete_one({"sequence_id": sequence_id})
    if deleted_read.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f"deleted read {sequence_id} and {str(delete_binary_results_count)} adjacent binary_results")
    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for deletion")


@app.delete("/binary_results/{sequence_id}", response_description="delete binary results for a read")
async def delete_binary_results_for_read(sequence_id: str):
    if (binary_results := db["binary_results"].find({"sequence_id": sequence_id})) is not None:
        db["reads"].update_one({"sequence_id": sequence_id}, {"$set": {"binary_results": []}})
        delete_binary_results_count = db["binary_results"].delete_many({"sequence_id": sequence_id}).deleted_count
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f"deleted {str(delete_binary_results_count)} binary_results adjacent to read {sequence_id}")
    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for binary_result deletion")


@app.post('/fastq/', response_description="Add all reads from a fastq file to database")
async def postfastq(filepath: Union[str]):
    file_id_fastq = uuid4()  # TODO rausfinden ob das hier überhaupt sinnvoll ist, und nicht eine sessionid oder besser

    reads = get_fastq_metrics(filepath)

    for read in reads:
        # TODO check if sequence ID exists already
        await create_read(FastqModel(id=PyObjectId(),
                                     sequence_id=str(read["sequence_id"]),
                                     sequence=str(read["sequence"]),
                                     sequence_length=int(read["sequence_length"]),
                                     min_quality=int(read["min_quality"]),
                                     max_quality=int(read["max_quality"]),
                                     average_quality=float(read["average_quality"]),
                                     phred_quality=str(read["phred_quality"]),
                                     file_id_fastq=str(file_id_fastq)
                                     ))
    return {"added " + str(len(reads)) + " reads to mangodb"}


@app.post('/sam/', response_description="Add all alignments from sam file to database")
async def sam(filepath: Union[str]):
    all_binary_results = get_sam_metrics(filepath)
    file_name_sam = filepath
    updated_reads = 0
    all_inserted_binary_results = 0

    for alignment in all_binary_results["alignments"]:

        current_read = alignment["sequence_id"]
        binary_results_for_read: list = []

        binary_results_for_read.append(BinaryResultModel(
            sequence_id=alignment["sequence_id"],
            file_id=file_id_sam,
            type=str(type(alignment["position_in_ref"])),
            name="position_in_ref",
            value=alignment["position_in_ref"],
        ))

        binary_results_for_read.append(BinaryResultModel(
            sequence_id=alignment["sequence_id"],
            file_id=file_id_sam,
            type=str(type(alignment["mapping_qual"])),
            name="mapping_qual",
            value=alignment["mapping_qual"],
        ))

        for tag in alignment["mapping_tags"].items():
            binary_results_for_read.append(BinaryResultModel(
                sequence_id=alignment["sequence_id"],
                file_id=file_id_sam,
                type=str(type(tag[1])),  # the sam.tags function ommits the type of tags :(
                name=str(tag[0]),
                value=str(tag[1]),
            ))

        mango_response = await add_binary_results_for_specific_read(current_read, binary_results_for_read)
        if mango_response.status_code == 201:
            updated_reads += 1
            all_inserted_binary_results += len(binary_results_for_read)

    return {
        "added " + str(all_inserted_binary_results) + " binary results to " + str(updated_reads) + " reads in mangodb"}
    # TODO it's a bit sketchy the numbers. can't i get that from mongodb insert response?


@app.post('/kraken2/', response_description="Add all classifications from kraken2 output to database")
async def kraken(filepath: Union[str]):
    kraken_results = get_kraken_metrics(filepath)
    file_id_kraken2 = str(uuid4())  # idk

    updated_reads = 0
    all_inserted_binary_results = 0

    for classification in kraken_results:
        current_read = classification["sequence_id"]
        binary_results_for_read = []
        for key in classification.keys():
            if key != "sequence_id":
                binary_results_for_read.append(BinaryResultModel(sequence_id=classification["sequence_id"],
                                                                 file_id=file_id_kraken2,
                                                                 type=str(type(classification[key])),
                                                                 name=str(key),
                                                                 value=str(classification[key])
                                                                 ))
        mango_response = await add_binary_results_for_specific_read(current_read, binary_results_for_read)
        if mango_response.status_code == 201:
            updated_reads += 1
            all_inserted_binary_results += len(binary_results_for_read)

    return {
        "added " + str(all_inserted_binary_results) + " binary results to " + str(updated_reads) + " reads in mangodb"}
    # TODO it's a bit sketchy the numbers. can't i get that from mongodb insert response?
    # TODO also Kraken files have an lca mapping list, which is saved whole as a string, is that what we want?


@app.delete('/clear_all_binary_results/')
async def delete_all_binary_results():
    modified_reads_count = db["reads"].update_many({}, {"$set": {"binary_results": []}}).modified_count
    db["binary_results"].drop()
    if "binary_results" not in db.list_collection_names():
        if modified_reads_count > 0:
            return JSONResponse(status_code=status.HTTP_200_OK, content="database cleared of binary_results")
    raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,
                        detail="either couldn't delete binary_result_collection or couldn't delete them from reads")


@app.delete('/clear_all/')
async def delete_all_collections():
    db["binary_results"].drop()
    if "binary_results" not in db.list_collection_names():
        db["reads"].drop()
        if "reads" not in db.list_collection_names():
            return JSONResponse(status_code=status.HTTP_200_OK, content="database cleared of all collections")
    raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,
                        detail="either couldn't drop one of the collections or both")


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
