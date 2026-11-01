import io


def test_save_experiment(client):
    payload = {
        "exps": 49,
        "exp_type": 1,
        "ill": 14,
        "intensity": 180,
        "pix_arr": 1.041667,
    }
    response = client.post("/api/experiments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 49
    assert data["settings"]["intensity"] == 180
    assert data["message"] == "Experiment settings saved successfully"


def test_get_experiment_49(client):
    response = client.get("/api/experiments/49")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 49
    assert data["settings"]["exps"] == 49
    assert data["settings"]["intensity"] == 180


def test_get_experiment_not_found(client):
    response = client.get("/api/experiments/-1")
    assert response.status_code == 404


def test_list_experiments(client):
    response = client.get("/api/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == 49


def test_upload_video_valid_avi(client):
    file_content = b"RIFF....AVI "
    files = {"file": ("test_video.avi", io.BytesIO(file_content), "video/x-msvideo")}
    response = client.post("/api/upload/video", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_video.avi"
    assert data["file_type"] == "video"
    assert data["size_bytes"] == len(file_content)


def test_upload_video_rejects_non_avi(client):
    file_content = b"fake mp4"
    files = {"file": ("test_video.mp4", io.BytesIO(file_content), "video/mp4")}
    response = client.post("/api/upload/video", files=files)
    assert response.status_code == 400
    assert "Only .avi files are supported" in response.json()["detail"]


def test_upload_illumination_valid_tiff(client):
    file_content = b"II*\x00TIFF"
    files = {"file": ("illumination14.tiff", io.BytesIO(file_content), "image/tiff")}
    response = client.post("/api/upload/illumination", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "illumination14.tiff"
    assert data["file_type"] == "illumination"


def test_upload_illumination_rejects_png(client):
    file_content = b"\x89PNG"
    files = {"file": ("illumination14.png", io.BytesIO(file_content), "image/png")}
    response = client.post("/api/upload/illumination", files=files)
    assert response.status_code == 400
    assert "Only .tiff and .tif files are supported" in response.json()["detail"]


def test_preview_valid_request(client):
    payload = {
        "frame_number": 5,
        "diameter": 5,
        "minmass": 180.0,
        "bg_method": "mean",
    }
    response = client.post("/api/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["frame_number"] == 5
    assert data["detected_cells"] > 0
    assert "frames/5" in data["image_url"]
    assert "sampled background" in data["note"]


def test_preview_rejects_even_diameter(client):
    payload = {
        "frame_number": 0,
        "diameter": 6,  # Even diameter must be rejected
    }
    response = client.post("/api/preview", json=payload)
    assert response.status_code == 422
