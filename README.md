# DatabaseAPI1
## MangoDB1 Prototyp
Python API that reads .fastq reads , bowtie2 aligments or kraken2 classifiactions as seperate documents into Mongo-DB. 
The database accepts all different documents into one single collection. however, 
for every new data/file format a new model, schema and endpoint has to be implemented.
Current ERD: 
![one single table: all different kinds of documtens inserted](images/actualflatfilemongodb.png "data model for MongoDB")

to start:  
1. ``pip install -r requirements.txt```
2. start your local MongoDB
3. ```uvicorn main:app --reload --port 8080```
![screenshot of MongoDB1 endpoints](images/screenshot_endpoints_mongoDB1.png "Endpoints of MongoDB1 API")
![screenshot of get all dimensions endpoint](images/screenshot_get_dimensions_mongoDB1.png "screenshot of get all dimensions endpoint")
![screenshot of get one_dimension endpoint](images/screenshot_get_one_dimension_mongoDB1.png "screenshot of get one dimension endpoint")