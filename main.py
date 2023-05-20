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

from Datafile_API.bio_python_script import get_fastq_metrics
from Datafile_API.simplesam_script import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics

from schema import Raw_data as SchemaRaw_data
from schema import Binary_results as SchemaBinary_result
from schema import File_name_and_uuid as SchemaFile_name_and_uuid
from models import ReadModel as ReadModel, PyObjectId

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

@app.get("/read/", response_description="list all reads", response_model=List[ReadModel])
async def list_reads():
    reads =[]
    for read in db["reads"].find():
        reads.append(read)
    #reads = await db["reads"].find().to_list(100)#hardcoded limit otherwise use skip and limit
    return reads


@app.get("/{sequence_id}", response_description="get a specific read", response_model=ReadModel)#read model not ideal here since additional data might be present in DB
async def get_read(sequence_id: Union[str]):#not sure if union is necessary here
    if (read := db["reads"].find_one({"sequence_id":sequence_id})) is not None:
        return read

    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found in database")

@app.put("/{sequence_id}", response_description="add entries to a specific read", response_model=ReadModel)
async def update_read(sequence_id: str, new_data: dict):
    #new_data = {k: v for k, v in read.items() if v is not None}
    if len(new_data) >= 1:
        update_result = await db["reads"].update_one({"sequence_id": sequence_id}, {"$set": new_data})

        if update_result.modified_count >= 1:
            if ( updated_read := await db["reads"].find_one({"sequence_id":sequence_id})) is not None:
                return updated_read

    if (existing_read := await db["reads"].find_one({"sequence_id":sequence_id})) is not None:
        return existing_read

    raise HTTPException(status_code=404, detail=f"read {sequence_id} not found for update")

@app.delete("/{sequence_id}", response_description="Delete a read") #bson.errors.InvalidDocument: cannot encode object: <built-in function id>, of type: <class 'builtin_function_or_method'>

async def delete_read(sequence_id: str):
    delete_result = db["reads"].delete_one({"sequence_id":sequence_id})

    if delete_result.deleted_count ==1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=f"deleted {sequence_id}")#RuntimeError: Response content longer than Content-Length


    raise HTTPException(status_code=404, detail=f"Read {sequence_id} not found for deletion")

@app.post('/fastq/')
async def fastq(filepath: Union[str]):
    file_id_fastq = uuid4()

    reads = get_fastq_metrics(filepath)

    for read in reads:
        await create_read(ReadModel(id=PyObjectId(),
                              sequence_id=str(read["sequence_id"]),
                              sequence=str(read["sequence"]),
                              phred_quality=str(read["phred_quality"]),
                              file_id_fastq=str(file_id_fastq)
                              ))
    return {"added ", len(reads), " reads to mangodb"}


@app.post('/sam/')
async def sam(filepath: Union[str]):

    binary_results = get_sam_metrics(filepath)

    #file_name = binary_results["mapping_reference_file"]
    file_id_sam = uuid4()#na ob das so smart ist hier...

    entry_count = 0
    for alignment in binary_results["alignments"]:
        update_read(alignment["sequence_id"],alignment)
        """update_read(Update_ReadModel(alignment["sequence_id"],
                                     type=str(type(alignment["position_in_ref"])),
                                     name="position_in_ref",
                                     value=alignment["position_in_ref"],
                                     file_id=file_id_sam
                                     ))"""
        entry_count += 1

    return {"added/updated ", entry_count, " reads to mangodb"}

@app.post('/kraken2/')
async def kraken(filepath: Union[str]):

    kraken_results = get_kraken_metrics(filepath)

    file_name = filepath
    file_id_kraken2 = uuid4()#idk

    entry_count = 0

    for classification in kraken_results:
        update_read(classification["sequence_id"],classification)
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
