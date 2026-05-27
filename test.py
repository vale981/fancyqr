from typing import Any, Union
import qrcode
from qrcode.main import QRCode, ActiveWithNeighbors
from decimal import Decimal

# simulate SvgHorizontalBarsDrawer behavior
qr = QRCode(box_size=10, border=4)
qr.add_data('Hello Michael')
qr.make()

is_active_count = 0
for r in range(qr.modules_count):
    for c in range(qr.modules_count):
        # BaseImageWithDrawer logic for eyes
        if (r < 7 and c < 7) or (r < 7 and c >= qr.modules_count - 7) or (r >= qr.modules_count - 7 and c < 7):
            continue # skipped for eye
        is_active = qr.active_with_neighbors(r, c)
        if is_active:
            is_active_count += 1
            # In our drawer:
            # if not is_active: return  (but it's truthy, so it doesn't return)

print(f"is_active_count (excluding eyes): {is_active_count}")
