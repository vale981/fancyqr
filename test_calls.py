import qrcode
import main

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=100)
qr.add_data("Hello Michael")
qr.make()

drawer = main.SvgHorizontalBarsDrawer()
img = main.StyledSvgImage(qr.border, qr.modules_count, qr.box_size, qrcode_modules=qr.modules)
drawer.initialize(img)

for c in range(qr.modules_count):
    is_eye = (0 < 7 and c < 7) or (0 < 7 and c >= qr.modules_count - 7)
    if not is_eye:
        box = img.pixel_box(0, c)
        is_active = qr.active_with_neighbors(0, c)
        if is_active:
            print(f"Col {c} is_active=True, W={is_active.W}, E={is_active.E}")
            drawer.drawrect(box, is_active)
        else:
            print(f"Col {c} is_active=False")
