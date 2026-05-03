from aiohttp import web
from src.nodes.lock_manager import LockManager
from src.nodes.base_node import BaseNode
from src.consensus.raft import Raft
from src.utils.config import NODE_ID, NODE_MAP, PORT, PEERS
import aiohttp

lock_manager = LockManager()
node = BaseNode(NODE_ID, PEERS)
raft = Raft(node)

raft.elect_leader()


def log(msg):
    print(f"[NODE {NODE_ID}] {msg}")


async def forward_to_leader(endpoint, data):
    leader_url = NODE_MAP.get(node.leader_id)

    log("Forwarding request to leader")
    log(f"Leader ID: {node.leader_id}")
    log(f"Leader URL: {leader_url}")
    log(f"Endpoint: {endpoint}")
    log(f"Payload: {data}")

    if not leader_url:
        log("ERROR: Leader tidak ditemukan")
        return {"error": "leader not found"}

    url = f"http://{leader_url}{endpoint}"
    log(f"Full URL: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                log(f"Response dari leader: {result}")
                return result
    except Exception as e:
        log(f"ERROR saat forward: {str(e)}")
        return {"error": str(e)}


async def acquire(request):
    data = await request.json()
    event_id = data.get("event_id")

    log("===== REQUEST LOCK =====")
    log(f"Data masuk: {data}")
    log(f"Node leader sekarang: {node.leader_id}")
    log(f"Apakah node ini leader? {node.is_leader()}")

    if event_id:
        log(f"Cek event_id: {event_id}")
        is_new = await lock_manager.redis.setnx(f"event:{event_id}", 1)

        if not is_new:
            log(f"DUPLICATE EVENT: {event_id}")
            return web.json_response({
                "success": False,
                "message": "duplicate event"
            })

        log(f"Event baru dicatat: {event_id}")

    if not node.is_leader():
        log("Node bukan leader, forward ke leader")
        result = await forward_to_leader("/lock", data)
        return web.json_response(result)

    log("Leader memproses lock")

    try:
        success = await lock_manager.acquire_lock(
            data["resource"],
            data["node_id"],
            data["type"]
        )

        log(f"Hasil lock: {success}")
        return web.json_response({"success": success})

    except Exception as e:
        log(f"ERROR saat lock: {str(e)}")
        return web.json_response({"error": str(e)})


async def release(request):
    data = await request.json()

    log("===== REQUEST UNLOCK =====")
    log(f"Data masuk: {data}")
    log(f"Node leader sekarang: {node.leader_id}")
    log(f"Apakah node ini leader? {node.is_leader()}")

    if not node.is_leader():
        log("Node bukan leader, forward ke leader")
        result = await forward_to_leader("/unlock", data)
        return web.json_response(result)

    log("Leader memproses unlock")

    try:
        await lock_manager.release_lock(
            data["resource"],
            data["node_id"]
        )

        log("Unlock berhasil")
        return web.json_response({"status": "released"})

    except Exception as e:
        log(f"ERROR saat unlock: {str(e)}")
        return web.json_response({"error": str(e)})


async def init_app():
    await lock_manager.connect()
    log("Connected ke Redis")

    app = web.Application()
    app.router.add_post("/lock", acquire)
    app.router.add_post("/unlock", release)

    return app


def main():
    log(f"Starting node di port {PORT}")
    web.run_app(init_app(), port=PORT)


if __name__ == "__main__":
    main()