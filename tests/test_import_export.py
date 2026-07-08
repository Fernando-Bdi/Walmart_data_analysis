import config

def test_import_csv(client):

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

def test_export_shipments(client):

    response = client.get("/export/shipments")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "shipments_" in response.headers["content-disposition"]

def test_export_products(client):

    response = client.get("/export/products")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "products_" in response.headers["content-disposition"]

def test_export_alias(client):
    # Backwards-compat alias should behave the same as /export/shipments
    response = client.get("/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
