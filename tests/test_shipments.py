def test_create_shipment(client):

    response = client.post(
        "/shipments",
        json={
            "product_id":1,
            "quantity":50,
            "origin":"Warehouse A",
            "destination":"Store B"
        }
    )

    assert response.status_code == 200

    shipment = response.json()
    assert shipment["message"] == "Shipment successfully created", "it's not returning \
                    the correct message"
    assert "shipment_id" in shipment, "it's not returning the correct shipment ID"

def test_get_shipments(client):

    response = client.get("/shipments")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_existing_shipment(client):

    response = client.get("/shipments/1")
    assert response.status_code == 200

def test_invalid_quantity(client):

    response = client.post(
        "/shipments",
        json={
            "product_id":1,
            "quantity":"ABC",
            "origin":"Warehouse",
            "destination":"Store"
        }
    )
    # Check that the response status code is 422 (Unprocessable Entity) for invalid quantity
    assert response.status_code == 422
