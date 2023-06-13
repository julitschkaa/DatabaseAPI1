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
#client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"]) #async motor driver to create mongo client
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
async def list_reads():
    reads =[]
    for read in db["reads"].find():
        reads.append(read)
    #reads = await db["reads"].find().to_list(100)#hardcoded limit otherwise use skip and limit
    return reads

@app.get("/binary_results_to_read/", response_description="list all binary results to one read", response_model=BinaryResultModel)
async def get_binary_results(sequence_id: Union[str]):
    binary_results_list =[]
    if (binary_results := db["binary_results"].find({"sequence_id":sequence_id})) is not None:
        binary_results_list.append(binary_results)
        return binary_results
    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in binary_database")


@app.get("/{sequence_id}", response_description="get a specific read", response_model=ReadModel)#read model not ideal here since additional data might be present in DB
async def get_read(sequence_id: Union[str]):#not sure if union is necessary here
    if (read := db["reads"].find_one({"sequence_id":sequence_id})) is not None:
        return read

    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")

@app.put("/{sequence_id}", response_description="add entries to binary collection and to a specific read", response_model=ReadModel)
async def add_binary_result(sequence_id: str, new_data: list[BinaryResultModel]):

    #new_data = jsonable_encoder(new_data)

    if (existing_read := db["reads"].find_one({"sequence_id":sequence_id})) is not None:

        new_binary_result_id = db["binary_results"].insert_many(new_data, ordered=True, bypass_document_validation=True).inserted_ids
        #new_binary_result_id = new_binary_result.inserted_id
        updated_read = db["reads"].update_one({"sequence_id": sequence_id},
                                               {"$push": {"binary_results": new_binary_result_id}})# might be smarter to add all binary results for one read first and den push many
        new_result = db["reads"].find_one({"sequence_id":sequence_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_result)

    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in read-collection for update, therefore not added to binary_result collection either")

@app.delete("/{sequence_id}", response_description="Delete a read") #bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>
async def delete_read(sequence_id: str):
    delete_result = db["reads"].delete_one({"sequence_id":sequence_id})

    if delete_result.deleted_count ==1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=f"deleted {sequence_id}")#RuntimeError: Response content longer than Content-Length


    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for deletion")

@app.post('/fastq/')
async def postfastq(filepath: Union[str]):
    file_id_fastq = uuid4()

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

    for alignment in all_binary_results["alignments"]:

        current_sequence_id = alignment["sequence_id"]
        binary_results_for_read:list = [BinaryResultModel]
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
        await add_binary_result(current_sequence_id,binary_results_for_read)

    return {"added/updated "+ str(len(binary_results_for_read))+ " reads to mangodb"}

@app.post('/kraken2/')
async def kraken(filepath: Union[str]):

    kraken_results = get_kraken_metrics(filepath)

    file_name = filepath
    file_id_kraken2 = uuid4()#idk

    entry_count = 0

    for classification in kraken_results:
        add_binary_result(classification["sequence_id"], classification)
        """for key in classification.keys():
            if key != "sequence_id":
                db_binary_results = ModelBinary_results(sequence_id=classification["sequence_id"],
                                                        type=str(type(classification[key])),
                                                        name= str(key),
                                                        value= str(classification[key]),
                                                        file_id=file_id)
                db.session.add(db_binary_results)
                db.session.commit()"""
        entry_count += 1
    return {"added " + str(entry_count) + "entries from binary of choice to postgresdb"}



# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
