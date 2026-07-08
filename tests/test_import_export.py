from pathlib import Path

import config

def test_import_csv(client):

    source = config.DATA_FOLDER / "shipping_data_0.csv"

    response = client.post(
        "/import",
        params={
            "file_name":"shipping_data_0.csv"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Import completed"

def test_import_missing_file(client):

    response = client.post(
        "/import",
        params={
            "file_name":"missing.csv"
        }
    )

    assert response.status_code == 200

    assert response.json()["message"] == \
        "CSV file not found.", "it's not returning the correct message"

def test_export(client):

    response = client.get("/export")

    assert response.status_code == 200

    data = response.json()
    exported = Path(data["location"])

    assert exported.exists(), "Exported file does not exist"
    assert exported.suffix == ".csv", "Exported file is not a CSV"