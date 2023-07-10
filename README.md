# DatabaseAPI1
Python API that reads .fastq reads , bowtie2 aligments or kraken2 classifiactions into a Mongo-DB flatfile database. The database accepts all different documents into one single collection. however, for every new data/file format a new model, schema and endpoint has to be implemented.
Current ERD: 
![one single table: all different kinds of documtens inserted](images/actualflatfilemongodb.png "flatfile model for MongoDB")

to start:  
1. start mongoDB
2. ```uvicorn main:app --reload --port 8080```
![screenshot of flatfiledb endpoints](images/atual_flatfile_endpoints_screenshot.png "Endpoints of flatfile db API")
![screenshot of get all dimensions endpoint](images/actual_flatfile_dimensions_endpoint_screenshot.png "screenshot of get all dimensions endpoint")
![screenshot of get one_dimension endpoint](images/actual_flatfile_get_one_dimension_endpoint_screenshot.png "screenshot of get one dimension endpoint")