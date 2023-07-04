# DatabaseAPI1
Python API that reads .fastq and .sam as well as krakenOutput.txt files into a simplified PostgreSQL DB.
original file name is saved in file_name_and_uuid table, all reads/aligments/classification "data-points" are split up into seperate
"binary-results" and saved in respective table.
Current ERD: 
![three entity RD for postgres set up. separate tables for data from fastq reads, sam files as well as kraken output together, and file_id table](images/simpler_postgres_erd.png "ERD for the simplified postgresDB")

to start:  
1. start postgresql
2. run ```alembic revision --autogenerate -m "New Migration"```
3. ```alembic upgrade head```
4. ```uvicorn main:app --reload --port 8080```

![endpoints for simplified postgres API](images/simplifiedpostgresendpoints.png "screenshot of api endpoints")
![get 3 dimension endpoint screensho1](images/simplifiedpostgresget3dim1.png "schreenshot1 of get 3 dimension endpoint")
![get 3 dimension endpoint screenshot2](images/simplifiedpostgresget3dim2.png "sreenshot2 of get 3 dimension  endpoint")