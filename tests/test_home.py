def test_home(client):

    response = client.get("/")

    assert response.status_code == 200, "it's not returning the correct status code"

    assert response.json() == {
        "message": "Welcome to my Shipment API"
    }, "it's not returning the correct message"
