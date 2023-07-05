import re
from typing import Union, List, Any

import uvicorn
import http3

import requests
from uuid import uuid4

from fastapi import FastAPI, status, HTTPException
from fastapi_sqlalchemy import DBSessionMiddleware, db
from requests import Response
from sqlalchemy import Table, select, func

from Datafile_API.fastq_parser import get_fastq_metrics
from Datafile_API.sam_parser import get_sam_metrics
from Datafile_API.kraken2_script import get_kraken_metrics
from schema import Raw_data as SchemaRaw_data
from schema import Binary_results as SchemaBinary_result
from schema import File_name_and_uuid as SchemaFile_name_and_uuid
from schema import Dimension as SchemaDimension
from schema import OneDimension as SchemaOneDimension
from models import Raw_data as ModelRaw_data
from models import Binary_result as ModelBinary_result
from models import File_name_and_uuid as ModelFile_name_and_uuid

from typehelper import typecast

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

@app.get("/binary_API_sam_json_from_fastq/")
async def call_binary_api_sam_json_from_fastq(fastqpath: Union[str],
                                              fastaurl: Union[str],
                                              rootpath: Union[str]):
    response = await call_binary_api(endpoint="/sam_json_from_fastq/", params={"fastqpath":fastqpath,
                                                                                "fastaurl":fastaurl,
                                                                                "rootpath":rootpath})
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
                                               fastafile:Union[str],
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
    response = await call_binary_api(endpoint="/init_by_path/", params={"config":configpath})
    return response.json()

@app.get("/binary_API_init_async/")
async def call_binary_api_init_async(configpath: Union[str], threadname: Union[str]):
    response = await call_binary_api(endpoint="/init_async/", params={"config":configpath, "threadname": threadname})
    return response.json()

@app.get("/binary_API_check_thread/")
async def call_binary_api_check_thread(threadname: Union[str]):
    response = await call_binary_api(endpoint="/check_thread/", params={"threadname": threadname})
    return response.json()

@app.get("/binary_API_json_from_bowtie_exec/")
async def call_binary_api_json_from_bowtie_execution(fastapath: Union[str], fastqpath: Union[str], rootpath: Union[str]):
    response = await call_binary_api(endpoint="/sam_json_from_bowtie_execution/", params={"fastapath":fastapath,
                                                                                          "fastqpath": fastqpath,
                                                                                          "rootpath": rootpath})
    return response.json()

@app.get("/binary_api/")
async def call_binary_api(endpoint: Union[str], params: dict[str, str]):
    binary_api_url = os.environ['BINARY_API_URL']
    response = requests.get(url=binary_api_url + endpoint, params=params)
    return response

@app.get("/read_count/", response_description="returns count of available reads in data base",
         status_code=status.HTTP_200_OK)#TODO better exceptionhandling in case realtion raw data doesnt exist already
async def get_read_cout():
    read_count = db.session.query(ModelRaw_data).count()
    return read_count


@app.get("/dimensions/", response_description="a list of dimensions currently saved in postgres db",
         status_code=status.HTTP_200_OK,
         response_model=List[SchemaDimension]
         )
async def list_all_possible_dimensions():#TODO dang how on earth do i combine both tables dimensions???
    raw_data_sample_dict = db.session.query(ModelRaw_data).first().__dict__
    raw_data_sample_dict.pop("_sa_instance_state")
    raw_data_dimensions =[]
    for key, value in raw_data_sample_dict.items():
        raw_data_dimensions.append((str(key), str(type(value))))#TODO not so pretty but hey...
    binary_result_dimensions_names = db.session.query(ModelBinary_result.name,ModelBinary_result.type).distinct().all()
    print(type(raw_data_dimensions[0]))
    print("###############")#TODO how to parse tuples into rows? or dimension objects :'(
    print(type(binary_result_dimensions_names[0]))
    if not raw_data_dimensions:
        raise HTTPException(status_code=404, detail="no dimensions found")
    return binary_result_dimensions_names

@app.get('/random_x_percent/{percentage}', response_description="get x percent of all reads, randomly selected, and matching list of binary_results",
         status_code=status.HTTP_200_OK)
async def get_random_reads(percentage: int):
    all_reads_random_order = db.session.query(ModelRaw_data).order_by(func.random()).all()
    x = int(len(all_reads_random_order)*percentage/100)
    if x<1:
        raise HTTPException(status_code=406, detail=f"{percentage}percent results in less than 1 out of {len(all_reads_random_order)}reads. there are not enough reads in the database yet. please add reads or choose higher percentage")
    random_reads = all_reads_random_order[:x]
    random_binary_results = []
    for read in random_reads:
        random_binary_results.append(await list_binary_results(read.sequence_id))
    return random_reads, random_binary_results

@app.get('/get_one_dimension/{dimension_name}/{percentage}', response_description="get one dimension of x percent of all reads",
         response_model=None, status_code=status.HTTP_200_OK)#TODO returns list of list not so pretty
async def get_one_dimension(dimension_name: str, percentage: int):
    reads, list_binary_results = await get_random_reads(percentage)
    filtered_binary_result_list=[]
    for list in list_binary_results:
        filtered_binary_result_list.append((x.sequence_id,x.name,x.value) for x in list if x.name==dimension_name)
    #temp = db.session.query(ModelBinary_result.sequence_id, ModelBinary_result.name, ModelBinary_result.value).filter(ModelBinary_result.name == dimension_name)#RecursionError: maximum recursion depth exceeded in comparison
    return filtered_binary_result_list

@app.get('/get_two_dimensions/{dimension1_name}/{dimension2_name}/{percentage}', response_description="get two dimensions of x percent of all reads",
         response_model=None, status_code=status.HTTP_200_OK)#TODO returns list of list not so pretty
async def get_two_dimension(dimension1_name: str, dimension2_name: str, percentage: int):
    reads, list_binary_results = await get_random_reads(percentage)
    filtered_binary_result_list=[]
    for list in list_binary_results:
        filtered_binary_result_list.append(x for x in list if x.name in [dimension1_name, dimension2_name])
    #temp = db.session.query(ModelBinary_result.sequence_id, ModelBinary_result.name, ModelBinary_result.value).filter(ModelBinary_result.name == dimension_name)#RecursionError: maximum recursion depth exceeded in comparison
    return filtered_binary_result_list


@app.get('/get_three_dimensions/{dimension1_name}/{dimension2_name}/{dimension3_name}/{percentage}', response_description="get three dimensions of x percent of all reads",
         response_model=None, status_code=status.HTTP_200_OK)#TODO returns list of list not so pretty
async def get_two_dimension(dimension1_name: str, dimension2_name: str, dimension3_name: str, percentage: int):
    reads, list_binary_results = await get_random_reads(percentage)
    filtered_binary_result_list=[]
    for list in list_binary_results:
        filtered_binary_result_list.append(x for x in list if x.name in [dimension1_name, dimension2_name, dimension3_name])
    #temp = db.session.query(ModelBinary_result.sequence_id, ModelBinary_result.name, ModelBinary_result.value).filter(ModelBinary_result.name == dimension_name)#RecursionError: maximum recursion depth exceeded in comparison
    return filtered_binary_result_list

@app.post('/raw_data/', response_description="write entries to raw data table",
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
    , response_model=SchemaBinary_result, status_code=status.HTTP_201_CREATED)
async def post_binary_result(binary_result: SchemaBinary_result):
    db_binary_result = ModelRaw_data(sequence_id=binary_result.sequence_id,
                                     type=binary_result.type,
                                     name=binary_result.name,
                                     value=binary_result.value,
                                     file_id=create_file_name_and_uuid_entries)
    db.session.add(db_binary_result)
    db.session.commit()
    return db_binary_result


@app.get('/read_inlc_binary_results/{sequence_id}', response_description="get read including adjacent binary entries")
async def get_entries_by_sequence_id(sequence_id: Union[str]):
    joined_data = db.session.query(ModelRaw_data, ModelBinary_result).join(ModelRaw_data.binary_results)\
        .filter(ModelRaw_data.sequence_id==sequence_id)

    if joined_data.count() == 0:
        return status.HTTP_404_NOT_FOUND

    readObject = {'sequence_id' : joined_data.first()[0].sequence_id,#only returning the pretty data  <3
                  'sequence' : joined_data.first()[0].sequence,
                  'sequence_length': joined_data.first()[0].sequence_length,
                  'min_quality': joined_data.first()[0].min_quality,
                  'max_quality': joined_data.first()[0].max_quality,
                  'average_quality': joined_data.first()[0].average_quality,
                  'phred_quality': joined_data.first()[0].phred_quality
                  }
    for entry in joined_data.all():#now adding the binary_data entries for that read_object
        readObject[entry[1].name] = typecast(entry[1].type, entry[1].value)
        #readObject[entry[1].name] = entry[1].type+"("+entry[1].value+")" #this works but is ugly af
        #readObject[entry[1].name] = entry[1].type(entry[1].value)#TypeError: 'str' object is not callable

    return readObject

@app.get('/raw_data/', response_description="list all reads in raw data table", response_model=List[SchemaRaw_data])
async def list_raw_data_entries():
    raw_data = db.session.query(ModelRaw_data).all()
    return raw_data

@app.delete('/raw_data_by_id/{sequence_id}', response_description="delete all entries in raw_data table")
async def delete_raw_data(sequence_id: Union[str]):
    to_be_deleted = db.session.query(ModelRaw_data).filter(ModelRaw_data.sequence_id == sequence_id).first()
    await delete_binary_results_by_id(sequence_id)
    if not to_be_deleted:
        raise HTTPException(status_code=404, detail="read not found")
    db.session.delete(to_be_deleted)
    db.session.commit()
    return status.HTTP_200_OK

@app.delete('/binary_results_by_id/{sequence_id}', response_description="delete all entries with matching id in binary_results table")
async def delete_binary_results_by_id(sequence_id: Union[str]):
    to_be_deleted_list = await list_binary_results(sequence_id)
    if not to_be_deleted_list:
        raise HTTPException(status_code=404, detail="no binary results with matching sequence_id found")
    for result in to_be_deleted_list:
        db.session.delete(result)
    db.session.commit()
    return status.HTTP_200_OK

@app.delete('/delete_binary_results/', response_description="delete all entries in binary_results table")
async def delete_all_binary_results():#TODO add exceptionhandling and better return status
    modifiedcount = db.session.query(ModelBinary_result).delete()
    if modifiedcount < 1:
        raise HTTPException(status_code=404, detail="no entries ind binary_results found")
    db.session.commit()
    return status.HTTP_200_OK


@app.delete('/delete_raw_data/', response_description="delete all entries in raw_data table")
async def delete_all_raw_data():#TODO add exceptionhandling and better return status
    modifiedcount = db.session.query(ModelRaw_data).delete()
    if modifiedcount < 1:
        raise HTTPException(status_code=404, detail="no entries ind raw_data found")
    db.session.commit()
    return status.HTTP_200_OK

@app.delete('/filename_and_uuid/', response_description="delete all entries in file_name_and_uuid table")
async def delete_all_filename_and_uuid():
    modifiedcount  = db.session.query(ModelFile_name_and_uuid).delete()
    if modifiedcount < 1:
        raise HTTPException(status_code=404, detail="no entries ind file_name_and_uuid found")
    db.session.commit()
    return status.HTTP_200_OK



@app.get('/binary_results_by_seq_id/',
         response_description="list all reads with matching seq_id in binary_results table",
         response_model=List[SchemaBinary_result])
async def list_binary_results(sequence_id: Union[str]):
    binary_results = db.session.query(ModelBinary_result).all()
    results = [x for x in binary_results if x.sequence_id == sequence_id]
    if not results:
        raise HTTPException(status_code=404, detail="no binary results with matching sequence_id found")
    return results


@app.get('/file_name_and_uuid/', response_description="list all entries in file_name_and_id",
         response_model=List[SchemaFile_name_and_uuid])
async def list_file_name_and_uuid():
    file_name_and_uuids = db.session.query(ModelFile_name_and_uuid).all()
    if not file_name_and_uuids:
        raise HTTPException(status_code=204, detail="no entries in file_name_uuid found")
    return file_name_and_uuids


@app.post('/file_name_and_uuid/', response_description="write entries to file_name_and_id table",
          response_model=SchemaFile_name_and_uuid, status_code=status.HTTP_201_CREATED)
async def create_file_name_and_uuid_entries(file_name_and_uuid: SchemaFile_name_and_uuid):
    db_file_name_and_uuid = ModelFile_name_and_uuid(file_name=file_name_and_uuid.name,
                                                    file_uuid=file_name_and_uuid.uuid)
    db.session.add(db_file_name_and_uuid)
    db.session.commit()
    return db_file_name_and_uuid


@app.post('/fastq/', status_code=status.HTTP_201_CREATED)  # TODO: better exception handling for read already in db exception
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
    return {"added " + str(len(reads)) + " reads to postgresDB"}


@app.post('/sam/', status_code=status.HTTP_201_CREATED)  # TODO: check if file is already in filename_and_uuid_table
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
        raw_data_id = db.session.query(ModelRaw_data.id).filter(ModelRaw_data.sequence_id==alignment["sequence_id"])
        db_binary_results = ModelBinary_result(sequence_id=alignment["sequence_id"],
                                               type=re.split("'", str(type(alignment["position_in_ref"])))[1],
                                               name="position_in_ref",
                                               value=alignment["position_in_ref"],
                                               file_id=sam_id,
                                               raw_data_id=raw_data_id)
        db.session.add(db_binary_results)
        db.session.commit()
        entry_count += 1

        db_binary_results = ModelBinary_result(sequence_id=alignment["sequence_id"],
                                               type=re.split("'", str(type(alignment["mapping_qual"])))[1],
                                               name="mapping_qual",
                                               value=alignment["mapping_qual"],
                                               file_id=sam_id,
                                               raw_data_id=raw_data_id)
        db.session.add(db_binary_results)
        db.session.commit()
        entry_count += 1

        mapping_tags = alignment["mapping_tags"]
        for mapping_tag in mapping_tags:
            db_binary_results = ModelBinary_result(sequence_id=alignment["sequence_id"],
                                                   type=re.split("'", str(type(mapping_tags[mapping_tag])))[1],
                                                   name=mapping_tag,
                                                   value=mapping_tags[mapping_tag],
                                                   file_id=sam_id,
                                               raw_data_id=raw_data_id)
            db.session.add(db_binary_results)
            db.session.commit()
            entry_count += 1
    return {"added " + str(entry_count) + " entries from sam file to postgresdb"}


@app.post('/kraken2/', status_code=status.HTTP_201_CREATED)  # TODO: check if file is already in filename_and_uuid_table
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
        raw_data_id = db.session.query(ModelRaw_data.id).filter(ModelRaw_data.sequence_id==classification["sequence_id"])
        for key in classification.keys():
            if key != "sequence_id":
                db_binary_results = ModelBinary_result(sequence_id=classification["sequence_id"],
                                                       type=re.split("'",str(type(classification[key])))[1],
                                                       name=str(key),
                                                       value=str(classification[key]),
                                                       file_id=file_id,
                                                       raw_data_id=raw_data_id)
                db.session.add(db_binary_results)
                db.session.commit()
                entry_count += 1
    return {"added " + str(entry_count) + "entries from kraken execution to postgresdb"}


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8080)
