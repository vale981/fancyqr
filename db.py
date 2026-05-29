import aiosqlite
import random
import string
import os

DB_PATH = os.environ.get("FANCYQR_DB_PATH", "links.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                slug TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                clicks INTEGER DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                referer TEXT,
                FOREIGN KEY (slug) REFERENCES links (slug)
            )
            """
        )
        await db.commit()

async def record_visit(slug: str, user_agent: str = None, referer: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE links SET clicks = clicks + 1 WHERE slug = ?", (slug,)
        )
        await db.execute(
            "INSERT INTO visits (slug, user_agent, referer) VALUES (?, ?, ?)",
            (slug, user_agent, referer)
        )
        await db.commit()

async def get_stats(slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT url, clicks, created_at FROM links WHERE slug = ?", (slug,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            url, clicks, created_at = row
            
            # Get last 10 visits
            async with db.execute(
                "SELECT timestamp, user_agent FROM visits WHERE slug = ? ORDER BY timestamp DESC LIMIT 10",
                (slug,)
            ) as v_cursor:
                recent_visits = await v_cursor.fetchall()
                
            return {
                "url": url,
                "clicks": clicks,
                "created_at": created_at,
                "recent_visits": [{"timestamp": v[0], "user_agent": v[1]} for v in recent_visits]
            }

async def generate_slug(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

async def create_link(url: str, slug: str = None):
    if not slug:
        slug = await generate_slug()
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if slug exists
        async with db.execute("SELECT slug FROM links WHERE slug = ?", (slug,)) as cursor:
            if await cursor.fetchone():
                if not slug: # if it was auto-generated, try again
                    return await create_link(url)
                else:
                    raise ValueError(f"Slug '{slug}' already exists")
        
        await db.execute("INSERT INTO links (slug, url) VALUES (?, ?)", (slug, url))
        await db.commit()
    return slug

async def get_url(slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT url FROM links WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def list_links():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT slug, url, clicks, created_at FROM links ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {"slug": r[0], "url": r[1], "clicks": r[2], "created_at": r[3]}
                for r in rows
            ]

async def update_link(slug: str, new_url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE links SET url = ? WHERE slug = ?", (new_url, slug)
        )
        await db.commit()

async def delete_link(slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM visits WHERE slug = ?", (slug,))
        await db.execute("DELETE FROM links WHERE slug = ?", (slug,))
        await db.commit()
