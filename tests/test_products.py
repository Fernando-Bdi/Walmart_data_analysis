def test_get_products(client):

    response = client.get("/products")

    assert response.status_code == 200, "it's not returning the correct status code"

    assert isinstance(response.json(), list)

def test_create_product(client):

    response = client.post(
        "/products",
        json={
            "name": "Laptop"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Product added", "it's not returning the correct message"

    assert "product_id" in data, "it's not returning the correct product ID"