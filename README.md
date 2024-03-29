# DatabaseAPI1
## Postgres1_Prototyp  
Python API that reads .fastq and .sam as well as krakenOutput.txt files into a simplified PostgreSQL DB.
original file name is saved in file_name_and_uuid table, all reads/aligments/classification "data-points" are split up into seperate
"binary-results" and saved in respective table.
Current ERD: 
![three entity RD for postgres set up. separate tables for data from fastq reads, sam files as well as kraken output together, and file_id table](images/postgresDBV1ERD.png "ERD for the simplified postgresDB")

to start: 
1. run ``pip install -r requirements.txt``
2. start postgresql
3. run ```alembic revision --autogenerate -m "New Migration"```
4. ```alembic upgrade head```
5. ```uvicorn main:app --reload --port 8080```

![endpoints for simplified postgres API](images/postgres1_prototyp_endpoints.png "screenshot of api endpoints")
![get 3 dimension endpoint screensho1](images/postgres1_prototyp_get_dimensions.png "screenshot1 of get all dimensions endpoint")
![get 3 dimension endpoint screenshot2](images/postgres1_prototyp_get_one_dimension.png "sreenshot2 of get 1 dimension endpoint")