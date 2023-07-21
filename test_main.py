import os
from starlette.testclient import TestClient

from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_delete_all_docs():
    response = client.delete("/clear_all/")
    assert response.status_code in [200,304]
    read_count_response = client.get("/read_count/")
    read_count = read_count_response.json()
    assert read_count == 0

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
    response_body = response.json()

    possible_dimension_keys = ["_id", "sequence_id", "file_name", "sequence", "sequence_length", "min_quality",
                               "max_quality",
                               "average_quality", "phred_quality", "mapping_tags.AS", "mapping_tags.XN",
                               "mapping_tags.XM", "mapping_tags.XO", "mapping_tags.XG", "mapping_tags.NM",
                               "mapping_tags.MD", "mapping_tags.YT",
                               "position_in_ref", "mapping_qual", "mapping_reference_file", "classified", "taxonomy_id",
                               "lca_mapping_list"]
    # Now you can access the response body as a normal Python dictionary
    for key, value in response_body.items():
        assert key in possible_dimension_keys
    assert len(response_body.keys()) == len(possible_dimension_keys)

def test_get_randoom_x_percent():
    percentage = 50
    response = client.get(f"/random_x_percent/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"
    read_count_response = client.get("/read_count/")
    read_count = read_count_response.json()
    random_x_percent_count = len(response.json())
    assert random_x_percent_count == read_count * percentage / 100, f"random x percent count doesnt match actual reads num"


def test_get_one_dimension():
    percentage = 50
    dimension = "YT"
    response = client.get(f"get_one_dimension/{dimension}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"
    response_body = response.json()
    assert all([dimension in item.keys() for item in response_body]), f"not all items have {dimension}"


def test_get_two_dimensions(): #this test sucks in case one of the nested dimensions is called!!
    percentage = 50
    dimension1 = "max_quality"
    dimension2 = "mapping_qual"
    response = client.get(f"/get_two_dimensions/{dimension1}/{dimension2}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"
    response_body = response.json()
    assert all([dimension1 in item.keys() and dimension2 in item.keys() for item in
                response_body]), f"Not all items have both {dimension1} and {dimension2}"


def test_get_three_dimensions():
    percentage = 50
    dimension1 = "classified"
    dimension2 = "mapping_qual"
    dimension3 = "min_quality"
    response = client.get(f"/get_three_dimensions/{dimension1}/{dimension2}/{dimension3}/{percentage}")
    assert response.status_code == 200, f"Request failed with status {response.status_code}"
    response_body = response.json()
    assert all([dimension1 in item.keys() and dimension2 in item.keys() and dimension3 in item.keys() for item in
                response_body]), f"Not all items have all of {dimension1} and {dimension2} and {dimension3}"
