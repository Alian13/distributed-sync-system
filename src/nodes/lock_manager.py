import aioredis
import json
import time

class LockManager:
    def __init__(self):
        self.redis = None
        self.waiting = {}

    async def connect(self):
        self.redis = await aioredis.from_url("redis://redis:6379")

    async def acquire_lock(self, resource, node_id, lock_type):
        key = f"lock:{resource}"

        existing = await self.redis.get(key)

        if not existing:
            data = {
                "type": lock_type,
                "holders": [node_id]
            }
            await self.redis.set(key, json.dumps(data))
            return True

        # deadlock detection sederhana
        self.waiting[node_id] = time.time()

        if time.time() - self.waiting[node_id] > 5:
            return "deadlock_detected"

        return False

    async def release_lock(self, resource, node_id):
        key = f"lock:{resource}"

        existing = await self.redis.get(key)

        if existing:
            data = json.loads(existing)

            if node_id in data["holders"]:
                data["holders"].remove(node_id)

            if not data["holders"]:
                await self.redis.delete(key)
            else:
                await self.redis.set(key, json.dumps(data))