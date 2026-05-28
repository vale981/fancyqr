from fastapi import FastAPI, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fancy_qr import generate_qr_svg, parse_color
import qrcode

app = FastAPI(title="FancyQR Generator")

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
    ec: str = Query("L", regex="^[LMQH]$"),
    logo: bool = Query(False, description="Include logo"),
    ls: float = Query(0.8, ge=0.1, le=1.0, description="Logo scale"),
    lm: float = Query(0.25, ge=0.1, le=0.5, description="Logo margin"),
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

@app.get("/")
async def index():
    return FileResponse("static/index.html")

# Create static directory if it doesn't exist for the frontend
if not os.path.exists("static"):
    os.makedirs("static")
