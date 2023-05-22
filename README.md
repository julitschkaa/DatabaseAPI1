# DatabaseAPI1
Python API that reads .fastq and .sam files into a PostgreSQL DB.
Current ERD: 
![flatfile Datatable: reads from fastq (mandatory) optional: fields from sam file or kraken outut](images/mongoDBV2.png "ERD for mongoDB")

to start:  
1. start postgresql
2. run ```alembic init alembic```
3. ```alembic revision --autogenerate -m "New Migration"```
4. ```uvicorn main:app --reload```