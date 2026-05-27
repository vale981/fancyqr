import qrcode
from qrcode.main import QRCode
import main

qr = QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=100)
qr.add_data("Hello Michael")

img_1 = qr.make_image(
    image_factory=main.StyledSvgImage,
    module_drawer=main.SvgHorizontalBarsDrawer(),
    eye_drawer=main.SvgCustomEyeDrawer(),
    color_mask=main.SolidFillColorMask(
        front_color=(0, 0, 0, 255), back_color=(255, 255, 255, 255)
    ),
)

with open("image_white.svg", "wb") as f:
    img_1.save(f)
