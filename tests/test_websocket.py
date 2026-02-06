from fastapi.testclient import TestClient
from secumator.api.main import app


def test_websocket_global_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_websocket_scan_subscription():
    client = TestClient(app)
    with client.websocket_connect("/ws/scan/1") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
        assert data["scan_id"] == 1


def test_websocket_subscribe_to_scan():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "subscribe", "scan_id": "123"})
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
