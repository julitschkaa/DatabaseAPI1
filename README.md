# DatabaseAPI1
Python API that reads .fastq and .sam files into three separate tables in a PostgreSQL DB.
Current ERD: 
![three entity RD for postgres set up. seperate tables for data from fastq reads, sam files as well as kraken output together, and file_id table](images/postgresV1.png "ERD for postgresDB")

to start:  
1. start postgresql
2. run ```alembic revision --autogenerate -m "New Migration"```
3. ```alembic upgrade head```
4. ```uvicorn main:app --reload --port 8080```
![screenshot of three entity postgres API](images/main_endpoints.png "Screenshot of three entity postgres db API")
5. now with added get dimensions endpoints.
![screenshot of threedimensionendpoint](images/main_get_dimensions.png "return format of get dimensions endpoint")
6. please keep in mind, that "phred_quality is saved as "string" here, but is returned as list of ints in the actual endpoints
![screenshot of threedimensionendpoint2](images/main_get_one_dimension.png "get one dimensions endpoint")