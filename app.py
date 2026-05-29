from fastapi import FastAPI, Response, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from fancy_qr import generate_qr_svg, parse_color
import qrcode
import db

class ShortenRequest(BaseModel):
    url: str
    slug: str = Field(None, min_length=1, max_length=50)
    password: str = Field(None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await db.init_db()
    yield

app = FastAPI(title="FancyQR Generator", lifespan=lifespan)

# Map error correction strings to constants
ERROR_LEVELS = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


@app.get("/generate")
async def generate(
    data: str = Query(..., description="Data to encode"),
    fc: str = Query("#ff9232", description="Foreground color"),
    bc: str = Query("255,255,255,0", description="Background color"),
    size: int = Query(100, ge=10, le=500, description="Box size"),
    ec: str = Query("L", pattern="^[LMQH]$"),
    logo: bool = Query(False, description="Include logo"),
    ls: float = Query(0.9, ge=0.1, le=1.0, description="Logo scale"),
    lm: float = Query(0.2, ge=0.1, le=0.5, description="Logo margin"),
):
    try:
        front = parse_color(fc)
        back = parse_color(bc)

        svg_content = generate_qr_svg(
            data=data,
            front_color=front,
            back_color=back,
            box_size=size,
            error_correction=ERROR_LEVELS[ec],
            with_logo=logo,
            logo_scale=ls,
            logo_margin=lm,
        )

        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=400)


@app.post("/shorten")
async def shorten(request: ShortenRequest):
    # Basic password protection
    required_password = os.environ.get("FANCYQR_PASSWORD")
    if required_password and request.password != required_password:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid password")

    try:
        slug = await db.create_link(request.url, request.slug)
        return {"slug": slug, "url": request.url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def index():
    path = "static/index.html"
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(path)


@app.get("/{slug}")
async def redirect(slug: str):
    url = await db.get_url(slug)
    if url:
        return RedirectResponse(url)
    # If not a slug, might be a static file or 404
    # But since we have other routes above, they take precedence.
    # We could also check if it's a file in static/
    raise HTTPException(status_code=404, detail="Not found")


# Create static directory if it doesn't exist for the frontend
if not os.path.exists("static"):
    # Only try to create if we're not in a read-only environment like Nix
    try:
        os.makedirs("static", exist_ok=True)
    except OSError:
        pass


def main():
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="FancyQR Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--uds", default=None, help="Unix domain socket to bind to")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, uds=args.uds)


if __name__ == "__main__":
    main()
