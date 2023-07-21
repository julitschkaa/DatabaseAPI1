import os
from starlette.testclient import TestClient

import sampledimension
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_delete_all_binaryies():
    response = client.delete("/delete_binary_results/")
    assert response.status_code in [200,404]

def test_delete_all_filename_and_uuid():
    response = client.delete("/delete_binary_results/")
    assert response.status_code in [200,404]

def test_upload_fastq():
    filepath = os.environ['PATH_TO_FASTQ']
    response = client.post(f"/fastq/?filepath={filepath}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_upload_sam():
    filepath = os.environ['PATH_TO_SAM']
    response = client.post(f"/sam/?filepath={filepath}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_upload_kraken2():
    filepath = os.environ['PATH_TO_KRAKEN_TXT']
    response = client.post(f"/kraken2/?filepath={filepath}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_get_read_by_id():
    random_id = os.environ['RANDOM_SEQ_ID']
    response = client.get(f"/read_by_sequence_id/{random_id}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"


def test_get_all_dimensions():
    response = client.get("/dimensions/")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"
    #assert response.json == sampledimension.dimensions #tja wie?

def test_get_randoom_x_percent():
    percentage = 50
    response = client.get(f"/random_x_percent/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_get_one_dimension():
    percentage = 50
    dimension = "YT"
    response = client.get(f"get_one_dimension/{dimension}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_get_two_dimensions():
    percentage = 50
    dimension1 = "mapping_tags.YT"
    dimension2 = "mapping_qual"
    response = client.get(f"/get_two_dimensions/{dimension1}/{dimension2}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"

def test_get_three_dimensions():
    percentage = 50
    dimension1 = "mapping_tags.YT"
    dimension2 = "mapping_qual"
    dimension3 = "min_quality"
    response = client.get(f"/get_three_dimensions/{dimension1}/{dimension2}/{dimension3}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"