import os

NODE_ID = os.getenv("NODE_ID", "node1")
PORT = int(os.getenv("PORT", 8000))

PEERS = os.getenv("PEERS", "").split(",") if os.getenv("PEERS") else []

NODE_MAP = {
    "node1": "node1:8001",
    "node2": "node2:8002",
    "node3": "node3:8003"
}