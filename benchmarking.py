import os
import requests
import timeit

# filepath = os.environ['PATH_TO_FASTQ']
requests.delete(url="http://localhost:8080/clear_all/")
post_fastq_api_url = "http://localhost:8080/fastq/?filepath=%2Fhome%2Fjulis%2Ffastqfiles%2F220427_22-05227_Lambda_DNS_S17_L000_R1_001.fastq"
def post_fastq():
    response = requests.post(url=post_fastq_api_url)
def upload_fastq(filepath: str, expected_read_count: int, num_of_exec: int):


    print(timeit.repeat(post_fastq(), repeat=5, number=num_of_exec))
   # start_time = timeit.default_timer()
    #response = requests.post(url=post_fastq_api_url)
    #elapsed = timeit.default_timer() - start_time
    readcount = requests.get("http://localhost:8080/read_count/")
   # assert (len(response.json())) == expected_read_count, f"Readcount of inserted reads doesnt match expectations"
   # assert response.status_code == 200, f"Request failed with status {response.status_code}"


    #print( elapsed)
filepath = '/home/julis/fastqfiles/220427_22-05227_Lambda_DNS_S17_L000_R1_001.fastq'
upload_fastq(filepath,20,100000)