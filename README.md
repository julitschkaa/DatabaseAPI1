# DatabaseAPI1
Python API that reads .fastq reads into a Mongo-DB flatfile database and enhances them further with .sam file data and kraken2 classifications.
Current ERD: 
![one single table: sequence_id followed by further datapoints](images/postgresV1.png "ERD for postgresDB")

to start:  
1. start mongoDB
2. ```uvicorn main:app --reload```