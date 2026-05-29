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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()

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
