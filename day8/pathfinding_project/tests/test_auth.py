def test_public_map_is_available_without_login(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"AI-Assisted Pathfinding System" in response.data


def test_public_pathfinding_works_without_authentication(client):
    response = client.post(
        "/",
        data={"start_id": "0", "end_id": "2"},
    )

    assert response.status_code == 200
    assert "0 → 1 → 2".encode("utf-8") in response.data
    assert b"300" in response.data


def test_editing_is_rejected_without_authentication(client):
    response = client.post(
        "/editor/node/add",
        data={
            "node_id": "9",
            "x": "90",
            "y": "50",
            "type_id": "4",
            "name": "New_Park",
        },
    )

    assert response.status_code == 302
    assert "/editor/login" in response.headers["Location"]


def test_wrong_editor_password_is_rejected(client):
    response = client.post(
        "/editor/login",
        data={"password": "wrong-password"},
    )

    assert response.status_code == 401
    assert b"Incorrect editor password" in response.data


def test_authorised_editor_can_add_node(client, map_files):
    login_response = client.post(
        "/editor/login",
        data={"password": "test-password"},
    )
    assert login_response.status_code == 302

    add_response = client.post(
        "/editor/node/add",
        data={
            "node_id": "9",
            "x": "90",
            "y": "50",
            "type_id": "4",
            "name": "New_Park",
        },
        follow_redirects=True,
    )

    assert add_response.status_code == 200
    assert b"Node 9 added" in add_response.data

    node_file, _ = map_files
    assert "9 90 50 4 New_Park" in node_file.read_text(encoding="utf-8")
