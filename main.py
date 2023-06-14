from pydantic import BaseModel, Field, EmailStr

import uvicorn
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from typing import Optional, List, Union
import motor.motor_asyncio
from pymongo.mongo_client import MongoClient

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics

from schema import Raw_data as SchemaRaw_data
from schema import Binary_results as SchemaBinary_result
from schema import File_name_and_uuid as SchemaFile_name_and_uuid
from models import ReadModel as ReadModel, PyObjectId, BinaryResultModel

import os
from dotenv import load_dotenv

load_dotenv('.env')

app = FastAPI()
client = MongoClient(os.environ["MONGODB_URI"])
db = client.reads #specify database name 'reads'

# to avoid csrftokenError
#app.add_middleware(DBSessionMiddleware, db_url=os.environ['MONGODB_URL'])


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/read/', response_description="Add new Read", response_model=ReadModel)
async def create_read(read: ReadModel = Body(...)):
    read = jsonable_encoder(read)
    new_read = db["reads"].insert_one(read)
    created_read = db["reads"].find_one({"_id":new_read.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_read)

@app.get("/reads/", response_description="list all reads", response_model=List[ReadModel])
async def list_reads():#TODO includng binary result_ids in reads resulsts in loooong lists, and that is in already tiny input files
    reads =[]
    for read in db["reads"].find():
        reads.append(read)
    if reads:
        return JSONResponse(status_code=status.HTTP_200_OK, content=reads)
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"looks like there are no reads in the database yet")

@app.get("/binary_results/", response_description="list all binary results in db", response_model=List[BinaryResultModel])
async def list_binary_results():
    results =[]
    for result in db["binary_results"].find():
        results.append(result)
    if results:
        return JSONResponse(status_code=status.HTTP_200_OK, content=results)
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"looks like there are no binary_results in the database yet")

@app.get("/binary_results_to_read/", response_description="list all binary results to one read", response_model=List[BinaryResultModel])
async def get_binary_results_to_read(sequence_id: Union[str]):
    binary_results_list =[]
    for binary_result in db["binary_results"].find({"sequence_id":sequence_id}):
        binary_results_list.append(binary_result)
    if binary_results_list:
        return JSONResponse(status_code=status.HTTP_200_OK, content=binary_results_list)
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in binary_database")


@app.get("/read/{sequence_id}", response_description="get a specific read", response_model=ReadModel)#TODO best practice endpoint design is what?
async def get_read(sequence_id: str):
    if (read := db["reads"].find_one({"sequence_id":sequence_id})) is not None:
        return JSONResponse(status_code=status.HTTP_200_OK, content=read)
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")

@app.put("/{sequence_id}", response_description="add entries to binary collection and to a specific read", response_model=ReadModel)
async def add_binary_results_for_specific_read(sequence_id: str, new_data: list[BinaryResultModel]):

    new_data_jsonabled = []
    for result in new_data:
        result = jsonable_encoder(result)
        new_data_jsonabled.append(result)

    if (db["reads"].find_one({"sequence_id":sequence_id})) is not None:

        new_binary_result_ids = db["binary_results"].insert_many(new_data_jsonabled).inserted_ids
        db["reads"].update_one({"sequence_id": sequence_id},
                                               {"$push": {"binary_results": {"$each": new_binary_result_ids}}})
        updated_read = db["reads"].find_one({"sequence_id":sequence_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=updated_read)

    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in read-collection for update, therefore not added to binary_result collection either")

@app.delete("/read/{sequence_id}", response_description="Delete a read") #bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>
async def delete_read(sequence_id: str):
    delete_binary_results_count = db["binary_results"].delete_many({"sequence_id":sequence_id}).deleted_count#TODO mimics on delete cascade ob das so smart ist...
    deleted_read = db["reads"].delete_one({"sequence_id":sequence_id})
    if deleted_read.deleted_count ==1:
        return JSONResponse(status_code=status.HTTP_200_OK, content=f"deleted read {sequence_id} and {str(delete_binary_results_count)} adjacent binary_results")
    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for deletion")

@app.delete("/binary_results/{sequence_id}", response_description="delete binary results for a read")
async def delete_binary_results_for_read(sequence_id: str):
    if (binary_results := db["binary_results"].find({"sequence_id": sequence_id})) is not None:
        db["reads"].update_one({"sequence_id": sequence_id}, {"$pull":{"binary_results":{}}})#TODO how to delete all elements in array?
        delete_binary_results_count = db["binary_results"].delete_many({"sequence_id": sequence_id}).deleted_count
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f"deleted {str(delete_binary_results_count)} binary_results adjacent to read {sequence_id}")
    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for binary_result deletion")

@app.post('/fastq/')
async def postfastq(filepath: Union[str]):
    file_id_fastq = uuid4()#TODO rausfinden ob das hier überhaupt sinnvoll ist, und nicht eine sessionid oder besser

    reads = get_fastq_metrics(filepath)

    for read in reads:
        #TODO check if sequence ID exists already
        await create_read(ReadModel(id=PyObjectId(),
                              sequence_id=str(read["sequence_id"]),
                              sequence=str(read["sequence"]),
                              sequence_length=int(read["sequence_length"]),
                              min_quality=int(read["min_quality"]),
                              max_quality=int(read["max_quality"]),
                              average_quality=float(read["average_quality"]),
                              phred_quality=str(read["phred_quality"]),
                              file_id_fastq=str(file_id_fastq)
                              ))
    return {"added "+ str(len(reads))+ " reads to mangodb"}


@app.post('/sam/')
async def sam(filepath: Union[str]):

    all_binary_results = get_sam_metrics(filepath)
    file_id_sam = str(uuid4())#na ob das so smart ist hier...
    updated_reads=0
    all_inserted_binary_results=0

    for alignment in all_binary_results["alignments"]:

        current_read = alignment["sequence_id"]
        binary_results_for_read:list = []

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
                              type=str(type(tag[1])),#the sam.tags function ommits the type of tags :(
                              name=str(tag[0]),
                              value=str(tag[1]),
                              ))

        mango_response = await add_binary_results_for_specific_read(current_read, binary_results_for_read)
        if mango_response.status_code==201:
            updated_reads += 1
            all_inserted_binary_results+= len(binary_results_for_read)

    return {"added "+ str(all_inserted_binary_results)+ " binary results to "+ str(updated_reads) +" reads in mangodb"}
    #TODO it's a bit sketchy the numbers. can't i get that from mongodb insert response?

@app.post('/kraken2/')
async def kraken(filepath: Union[str]):

    kraken_results = get_kraken_metrics(filepath)
    file_id_kraken2 = str(uuid4())#idk

    updated_reads = 0
    all_inserted_binary_results = 0

    for classification in kraken_results:
        current_read = classification["sequence_id"]
        binary_results_for_read= []
        for key in classification.keys():
            if key != "sequence_id":
                binary_results_for_read.append(BinaryResultModel(sequence_id=classification["sequence_id"],
                                                      file_id=file_id_kraken2,
                                                      type=str(type(classification[key])),
                                                      name= str(key),
                                                      value= str(classification[key])
                                                      ))
        mango_response = await add_binary_results_for_specific_read(current_read, binary_results_for_read)
        if mango_response.status_code == 201:
            updated_reads += 1
            all_inserted_binary_results += len(binary_results_for_read)

    return {
        "added " + str(all_inserted_binary_results) + " binary results to " + str(updated_reads) + " reads in mangodb"}
    # TODO it's a bit sketchy the numbers. can't i get that from mongodb insert response?



# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
