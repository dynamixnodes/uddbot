import aiosqlite
import asyncio

DB_PATH = "deployments.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                deployer_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                expires_at REAL NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.commit()

async def set_config(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        await db.commit()

async def get_config(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM config WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def create_deployment(product_name: str, user_id: int, deployer_id: int, guild_id: int, expires_at: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO deployments (product_name, user_id, deployer_id, guild_id, expires_at, active) VALUES (?, ?, ?, ?, ?, 1)",
            (product_name, user_id, deployer_id, guild_id, expires_at)
        )
        await db.commit()
        return cursor.lastrowid

async def get_active_deployment(user_id: int, product_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM deployments WHERE user_id = ? AND LOWER(product_name) = LOWER(?) AND active = 1",
            (user_id, product_name)
        ) as cursor:
            return await cursor.fetchone()

async def get_suspended_deployment(user_id: int, product_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM deployments WHERE user_id = ? AND LOWER(product_name) = LOWER(?) AND active = 0 ORDER BY id DESC LIMIT 1",
            (user_id, product_name)
        ) as cursor:
            return await cursor.fetchone()

async def get_any_deployment(user_id: int, product_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM deployments WHERE user_id = ? AND LOWER(product_name) = LOWER(?) ORDER BY id DESC LIMIT 1",
            (user_id, product_name)
        ) as cursor:
            return await cursor.fetchone()

async def get_all_deployments_for_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT product_name, active, expires_at FROM deployments WHERE user_id = ? ORDER BY active DESC, product_name ASC",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def get_all_active_deployments():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM deployments WHERE active = 1") as cursor:
            return await cursor.fetchall()

async def deactivate_deployment(deployment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE deployments SET active = 0 WHERE id = ?", (deployment_id,))
        await db.commit()

async def delete_deployment(deployment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM deployments WHERE id = ?", (deployment_id,))
        await db.commit()

async def update_deployment_expiry(deployment_id: int, expires_at: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE deployments SET expires_at = ?, active = 1 WHERE id = ?", (expires_at, deployment_id))
        await db.commit()
