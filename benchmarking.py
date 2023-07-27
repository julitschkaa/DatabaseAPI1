import gc
import os

from dotenv import load_dotenv

import requests
import timeit

load_dotenv()#making .env variables availabe to os.getenv

#naming file for benchmarking results
benchmark_file = open('TrialMongoDB_2000reads_10runs_benchmarking.txt', 'w')
#defining number of runs to be evaluated
num_of_runs = 10

#getting environment variables
fastq_file = os.getenv('PATH_TO_FASTQ')
sam_file = os.getenv('PATH_TO_SAM')
kraken_file = os.getenv('PATH_TO_KRAKEN_TXT')
base_url = os.getenv('DATABASE_API_URL')
random_seq_id = os.getenv('RANDOM_SEQ_ID')
random_80_percent = os.getenv('RANDOM_80_PERCENT')
random_100_percent = os.getenv('RANDOM_100_PERCENT')
dimension1 = os.getenv('DIMENSION1')
dimension1nested = os.getenv('DIMENSION1NESTED')
dimension2 = os.getenv('DIMENSION2')
dimension3 = os.getenv('DIMENSION3')

#setting API endpoint variables
post_fastq_url = f"{base_url}/fastq/?filepath={fastq_file}"
post_sam_url = f"{base_url}/sam/?filepath={sam_file}"
post_kraken2_url = f"{base_url}/kraken2/?filepath={kraken_file}"

delete_all_url = f"{base_url}/clear_all/"
get_read_count_url = f"{base_url}/get_read_count/"
get_dimensions_url = f"{base_url}/dimensions/"
get_read_by_seq_id_url = f"{base_url}/read_by_sequence_id/{random_seq_id}"

get_random_80_percent_url = f"{base_url}/random_x_percent/{random_80_percent}"
get_random_100_percent_url = f"{base_url}/random_x_percent/{random_100_percent}"

get_one_nested_dimension_80_url = f"{base_url}/get_one_dimension/{dimension1nested}/{random_80_percent}"
get_one_nested_dimension_100_url = f"{base_url}/get_one_dimension/{dimension1nested}/{random_100_percent}"
get_one_dimension_80_url = f"{base_url}/get_one_dimension/{dimension1}/{random_80_percent}"
get_one_dimension_100_url = f"{base_url}/get_one_dimension/{dimension1}/{random_100_percent}"
get_two_dimensions_80_url = f"{base_url}/get_two_dimensions/{dimension1}/{dimension2}/{random_80_percent}"
get_two_dimensions_100_url = f"{base_url}/get_two_dimensions/{dimension1}/{dimension2}/{random_100_percent}"
get_three_dimensions_80_url = f"{base_url}/get_three_dimensions/{dimension1}/{dimension2}/{dimension3}/{random_80_percent}"
get_three_dimensions_100_url = f"{base_url}/get_three_dimensions/{dimension1}/{dimension2}/{dimension3}/{random_100_percent}"


#wrapper is needed because timeit.repeat expects function without arguments
def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped


# delete all_docs table from database
def clean_db():
    response = requests.delete(delete_all_url)
    assert response.status_code in [200, 304], f"delete failed with status {response.status_code}"


#    post fastq file, verify http200, delete_all, verify http200
def upload_fastq():
    response = requests.post(post_fastq_url)
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

#post sam file, verify http200
def upload_sam():
    response = requests.post(post_sam_url)
    assert response.status_code == 200, f"Request failed with status {response.status_code}"


#post kraken2 file, verify http200
def upload_kraken2():
    response = requests.post(post_kraken2_url)
    assert response.status_code == 200, f"Request failed with status {response.status_code}"


#post fastq, sam and kraken file, verify http200
def upload_all():
    response = requests.post(post_fastq_url)
    assert response.status_code == 200, f"upload fastq failed with status {response.status_code}"
    response = requests.post(post_sam_url)
    assert response.status_code == 200, f"upload sam failed with status {response.status_code}"
    response = requests.post(post_kraken2_url)
    assert response.status_code == 200, f"upload kraken.txt failed with status {response.status_code}"


def get_dimensions():
    response = requests.get(get_dimensions_url)
    assert response.status_code == 200, f"get dimensions failed with status {response.status_code}"


def get_read_by_id():
    response = requests.get(get_read_by_seq_id_url)
    assert response.status_code == 200, f"get read by id failed with status {response.status_code}"


def get_random_80_percent():
    response = requests.get(get_random_80_percent_url)
    assert response.status_code == 200, f"get random 80 failed with status {response.status_code}"


def get_random_100_percent():
    response = requests.get(get_random_100_percent_url)
    assert response.status_code == 200, f"get random 100 failed with status {response.status_code}"


def get_one_dimension_80():
    response = requests.get(get_one_dimension_80_url)
    assert response.status_code == 200, f"get one dimension 80 failed with status {response.status_code}"


def get_one_dimension_100():
    response = requests.get(get_one_dimension_100_url)
    assert response.status_code == 200, f"get one dimension 100 failed with status {response.status_code}"


def get_one_nested_dimension_80():
    response = requests.get(get_one_nested_dimension_80_url)
    assert response.status_code == 200, f"get one dimension 80 failed with status {response.status_code}"


def get_one_nested_dimension_100():
    response = requests.get(get_one_nested_dimension_100_url)
    assert response.status_code == 200, f"get one dimension 100 failed with status {response.status_code}"


def get_two_dimensions_80():
    response = requests.get(get_two_dimensions_80_url)
    assert response.status_code == 200, f"get two dimensions 80 failed with status {response.status_code}"


def get_two_dimensions_100():
    response = requests.get(get_two_dimensions_100_url)
    assert response.status_code == 200, f"get two dimensions 100 failed with status {response.status_code}"


def get_three_dimensions_80():
    response = requests.get(get_three_dimensions_80_url)
    assert response.status_code == 200, f"get two dimensions 80 failed with status {response.status_code}"


def get_three_dimensions_100():
    response = requests.get(get_three_dimensions_100_url)
    assert response.status_code == 200, f"get two dimensions 100 failed with status {response.status_code}"


def benchmark_and_write_to_file(function, clean_up=False):
    def setup():
        if clean_up:
            clean_db()

    wrapped = wrapper(function)
    times = timeit.repeat(wrapped, setup=setup, repeat=num_of_runs, number=1)

    benchmark_file.write(f"Execution Times {function.__name__} , {num_of_runs} executions\n")
    benchmark_file.write(f"min_time: {min(times)} seconds\n")
    benchmark_file.write(f"\n")


benchmark_and_write_to_file(upload_fastq, True)
clean_db()

benchmark_and_write_to_file(upload_sam, True)
clean_db()

benchmark_and_write_to_file(upload_kraken2, True)
clean_db()

benchmark_and_write_to_file(upload_all, True)
clean_db()

upload_all()
benchmark_and_write_to_file(get_dimensions)
benchmark_and_write_to_file(get_read_by_id)
benchmark_and_write_to_file(get_random_80_percent)
benchmark_and_write_to_file(get_random_100_percent)
benchmark_and_write_to_file(get_one_nested_dimension_80)
benchmark_and_write_to_file(get_one_nested_dimension_100)
benchmark_and_write_to_file(get_one_dimension_80)
benchmark_and_write_to_file(get_one_dimension_100)
benchmark_and_write_to_file(get_two_dimensions_80)
benchmark_and_write_to_file(get_two_dimensions_100)
benchmark_and_write_to_file(get_three_dimensions_80)
benchmark_and_write_to_file(get_three_dimensions_100)
