def test_docs_accessible(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_loads(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Moving Chlamydomonas API"
