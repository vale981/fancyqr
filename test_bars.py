import qrcode
from qrcode.image.styles.moduledrawers.pil import HorizontalBarsDrawer

drawer = HorizontalBarsDrawer()
class FakeImg:
    box_size = 100
    border = 4
    mode = 'RGBA'
    class FakeMask:
        back_color = (255,255,255,0)
    color_mask = FakeMask()
    paint_color = (0,0,0,255)
    def __init__(self):
        self._img = None
    
drawer.initialize(img=FakeImg())
print(drawer.half_width)
print(drawer.delta)
