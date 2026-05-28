import abc
import io
import os
import re
from typing import TYPE_CHECKING, Any, Union, Optional
from decimal import Decimal

import qrcode
import qrcode.image.svg
from qrcode.compat.etree import ET
from qrcode.image.styles.moduledrawers.base import QRModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.main import QRCode

if TYPE_CHECKING:
    from qrcode.image.base import BaseImage
    from qrcode.main import ActiveWithNeighbors, QRCode

# Ensure SVG namespace is the default
ET.register_namespace("", "http://www.w3.org/2000/svg")


def parse_color(color_str: str) -> tuple[int, int, int, int]:
    """Parse a hex color string or a comma-separated RGBA string."""
    color_str = color_str.strip()
    if color_str.startswith("#"):
        color_str = color_str.lstrip("#")
        if len(color_str) == 6:
            r, g, b = (
                int(color_str[0:2], 16),
                int(color_str[2:4], 16),
                int(color_str[4:6], 16),
            )
            return (r, g, b, 255)
        elif len(color_str) == 8:
            r, g, b, a = (
                int(color_str[0:2], 16),
                int(color_str[2:4], 16),
                int(color_str[4:6], 16),
                int(color_str[6:8], 16),
            )
            return (r, g, b, a)
    elif "," in color_str:
        try:
            parts = [int(p.strip()) for p in color_str.split(",")]
            if len(parts) == 3:
                return (parts[0], parts[1], parts[2], 255)
            elif len(parts) == 4:
                return (parts[0], parts[1], parts[2], parts[3])
        except ValueError:
            pass
    raise ValueError(f"Invalid color format: {color_str}")


def color_to_svg(color):
    """Convert a color tuple or string to an SVG-compatible hex color string."""
    if isinstance(color, str):
        return color
    if len(color) >= 3:
        r, g, b = color[:3]
        if len(color) == 4 and color[3] == 0:
            return "none"
        return f"#{r:02x}{g:02x}{b:02x}"
    return "#000000"


def make_rounded_rect_path(x, y, w, h, r, corners=(True, True, True, True)):
    """Generate an SVG path for a rectangle with specific rounded corners."""
    c1, c2, c3, c4 = corners  # TL, TR, BR, BL

    path = f"M {x},{y + (r if c1 else 0)} "
    path += f"L {x},{y + h - (r if c4 else 0)} "
    if c4:
        path += f"Q {x},{y + h} {x + r},{y + h} "
    else:
        path += f"L {x},{y + h} "

    path += f"L {x + w - (r if c3 else 0)},{y + h} "
    if c3:
        path += f"Q {x + w},{y + h} {x + w},{y + h - r} "
    else:
        path += f"L {x + w},{y + h} "

    path += f"L {x + w},{y + (r if c2 else 0)} "
    if c2:
        path += f"Q {x + w},{y} {x + w - r},{y} "
    else:
        path += f"L {x + w},{y} "

    path += f"L {x + (r if c1 else 0)},{y} "
    if c1:
        path += f"Q {x},{y} {x},{y + r} "
    else:
        path += f"L {x},{y} "

    path += "Z"
    return path


class BaseSvgEyeDrawer(abc.ABC):
    """Base class for SVG eye drawers."""

    needs_processing = True
    needs_neighbors = False
    img: "StyledSvgImage"

    def initialize(self, img: "StyledSvgImage") -> None:
        self.img = img

    def draw(self):
        width = self.img.width
        # Eye outer is 7x7 modules. Eyeball is 3x3 modules.
        # Top-left eye (NW)
        self.draw_nw_eye(0, 0)
        self.draw_nw_eyeball(2, 2)

        # Top-right eye (NE)
        self.draw_ne_eye(0, width - 7)
        self.draw_ne_eyeball(2, width - 5)

        # Bottom-left eye (SW)
        self.draw_sw_eye(width - 7, 0)
        self.draw_sw_eyeball(width - 5, 2)

    def _get_box(self, row, col, size):
        """Helper to get coordinates for a box of modules."""
        # Top-left of the first module
        (x0, y0), _ = self.img.pixel_box(row, col)
        # Bottom-right of the last module
        _, (x1, y1) = self.img.pixel_box(row + size - 1, col + size - 1)
        return (x0, y0), (x1, y1)

    @abc.abstractmethod
    def draw_nw_eye(self, row, col): ...
    @abc.abstractmethod
    def draw_nw_eyeball(self, row, col): ...
    @abc.abstractmethod
    def draw_ne_eye(self, row, col): ...
    @abc.abstractmethod
    def draw_ne_eyeball(self, row, col): ...
    @abc.abstractmethod
    def draw_sw_eye(self, row, col): ...
    @abc.abstractmethod
    def draw_sw_eyeball(self, row, col): ...


class SvgCustomEyeDrawer(BaseSvgEyeDrawer):
    """Custom SVG eye drawer with rounded corners."""

    def _draw_eye(self, row, col, size, corners, fill=False):
        (x0, y0), (x1, y1) = self._get_box(row, col, size)

        # Scale to units
        ux0 = self.img.units(x0, text=False)
        uy0 = self.img.units(y0, text=False)
        ux1 = self.img.units(x1 + 1, text=False)
        uy1 = self.img.units(y1 + 1, text=False)

        w = ux1 - ux0
        h = uy1 - uy0

        # radius follows the original logic: 2 modules for eye, 1 module for eyeball
        u_box_size = self.img.units(self.img.box_size, text=False)
        radius = u_box_size * 2
        if fill:
            radius = u_box_size

        if not fill:
            # Inset the path so the stroke is drawn entirely within the bounds
            half_w = u_box_size / 2
            ux0 += half_w
            uy0 += half_w
            w -= u_box_size
            h -= u_box_size
            radius -= half_w

        path_data = make_rounded_rect_path(ux0, uy0, w, h, radius, corners)

        front_color = color_to_svg(getattr(self.img, "front_color", "black"))

        attribs = {
            "d": path_data,
            "fill": front_color if fill else "none",
        }
        if not fill:
            attribs["stroke"] = front_color
            attribs["stroke-width"] = str(u_box_size)

        el = ET.Element("{http://www.w3.org/2000/svg}path", **attribs)
        self.img._img.append(el)

    def draw_nw_eye(self, r, c):
        self._draw_eye(r, c, 7, (True, True, False, True))

    def draw_nw_eyeball(self, r, c):
        self._draw_eye(r, c, 3, (True, True, False, True), fill=True)

    def draw_ne_eye(self, r, c):
        self._draw_eye(r, c, 7, (True, True, True, False))

    def draw_ne_eyeball(self, r, c):
        self._draw_eye(r, c, 3, (True, True, True, False), fill=True)

    def draw_sw_eye(self, r, c):
        self._draw_eye(r, c, 7, (True, False, True, True))

    def draw_sw_eyeball(self, r, c):
        self._draw_eye(r, c, 3, (True, False, True, True), fill=True)


class SvgHorizontalBarsDrawer(QRModuleDrawer):
    """SVG module drawer for horizontal bars."""

    needs_neighbors = True

    def __init__(self, vertical_shrink=0.8):
        self.vertical_shrink = vertical_shrink

    def initialize(self, img):
        self.img = img

    def drawrect(self, box, is_active):
        if not is_active:
            return

        (x0, y0), (x1, y1) = box
        # Scale to units
        ux0 = self.img.units(x0, text=False)
        uy0 = self.img.units(y0, text=False)
        ux1 = self.img.units(x1 + 1, text=False)
        uy1 = self.img.units(y1 + 1, text=False)

        w = ux1 - ux0
        h = uy1 - uy0

        shrunken_h = h * Decimal(str(self.vertical_shrink))
        delta_y = (h - shrunken_h) / 2

        left_rounded = not is_active.W
        right_rounded = not is_active.E

        # Add tiny overlap to prevent aliasing gaps between adjacent horizontal modules
        overlap = Decimal("0.1")
        if not left_rounded:
            ux0 -= overlap
            w += overlap
        if not right_rounded:
            w += overlap

        r = shrunken_h / 2

        path_data = make_rounded_rect_path(
            ux0,
            uy0 + delta_y,
            w,
            shrunken_h,
            r,
            corners=(left_rounded, right_rounded, right_rounded, left_rounded),
        )

        front_color = color_to_svg(getattr(self.img, "front_color", "black"))

        el = ET.Element(
            "{http://www.w3.org/2000/svg}path", d=path_data, fill=front_color
        )
        self.img._img.append(el)


class StyledSvgImage(qrcode.image.svg.SvgImage):
    """Styled SVG image factory that supports custom drawers, color masks, and logo embedding."""

    needs_processing = True

    def __init__(self, *args, **kwargs):
        color_mask = kwargs.pop("color_mask", None)
        self.logo_data = kwargs.pop("logo_data", None)
        self.logo_box = kwargs.pop("logo_box", None)
        self.logo_scale = kwargs.pop("logo_scale", Decimal("0.8"))

        if color_mask:
            self.front_color = getattr(color_mask, "front_color", "black")
            self.background = color_to_svg(getattr(color_mask, "back_color", "white"))
        else:
            self.front_color = "black"
            self.background = None

        super().__init__(*args, **kwargs)

        if self.eye_drawer:
            self.eye_drawer.initialize(self)
        if self.module_drawer:
            self.module_drawer.initialize(self)

    def _svg(self, tag="svg", **kwargs):
        # Override to ensure we use the local tag and add viewBox
        svg = super()._svg(tag=tag, **kwargs)
        viewbox_size = self.units(self.pixel_size, text=False)
        svg.set("viewBox", f"0 0 {viewbox_size} {viewbox_size}")
        return svg

    def drawrect_context(self, row: int, col: int, qr: QRCode[Any]):
        if self.is_eye(row, col):
            if getattr(self.eye_drawer, "needs_processing", False):
                return
            drawer = self.eye_drawer
        else:
            drawer = self.module_drawer

        box = self.pixel_box(row, col)
        is_active = (
            qr.active_with_neighbors(row, col)
            if drawer.needs_neighbors
            else bool(qr.modules[row][col])
        )
        drawer.drawrect(box, is_active)

    def process(self) -> None:
        if self.eye_drawer and getattr(self.eye_drawer, "needs_processing", False):
            self.eye_drawer.draw()

        if self.logo_data and self.logo_box:
            self._embed_logo()

    def _embed_logo(self):
        """Embed the logo SVG into the center box."""
        try:
            logo_tree = ET.fromstring(self.logo_data)

            # Get logo dimensions from its viewBox or width/height
            l_vb = logo_tree.get("viewBox")
            if l_vb:
                _, _, l_w, l_h = map(float, l_vb.split())
            else:
                l_w = float(
                    logo_tree.get("width", "1").replace("mm", "").replace("px", "")
                )
                l_h = float(
                    logo_tree.get("height", "1").replace("mm", "").replace("px", "")
                )

            # Target box in units
            (x0, y0), (x1, y1) = self.logo_box
            ux0 = self.units(x0, text=False)
            uy0 = self.units(y0, text=False)
            ux1 = self.units(x1 + 1, text=False)
            uy1 = self.units(y1 + 1, text=False)
            target_w = ux1 - ux0
            target_h = uy1 - uy0

            # Calculate scale and translation
            scale_x = target_w / Decimal(str(l_w))
            scale_y = target_h / Decimal(str(l_h))
            # Use configurable scale
            scale = min(scale_x, scale_y) * self.logo_scale

            # Center the logo in the target box
            off_x = ux0 + (target_w - Decimal(str(l_w)) * scale) / 2
            off_y = uy0 + (target_h - Decimal(str(l_h)) * scale) / 2

            # Create a group for the logo with transform
            g = ET.Element("{http://www.w3.org/2000/svg}g")
            g.set("transform", f"translate({off_x}, {off_y}) scale({scale})")

            # Filter and append only relevant graphic elements
            skip_tags = {"namedview", "metadata", "defs"}
            for child in logo_tree:
                tag_name = (
                    child.tag.split("}")[-1] if "}" in child.tag else child.tag
                )
                if tag_name not in skip_tags:
                    # Strip namespace from children too to keep it clean
                    child.tag = ET.QName("http://www.w3.org/2000/svg", tag_name)
                    g.append(child)

            self._img.append(g)
        except Exception as e:
            print(f"Warning: Could not embed logo: {e}")


def generate_qr_svg(
    data: str,
    front_color: tuple[int, int, int, int] = (0, 0, 0, 255),
    back_color: tuple[int, int, int, int] = (255, 255, 255, 0),
    box_size: int = 100,
    error_correction: int = qrcode.constants.ERROR_CORRECT_L,
    with_logo: bool = False,
    logo_scale: float = 0.8,
    logo_margin: float = 0.25,
) -> str:
    """Generate a styled SVG QR code and return it as a string."""

    qr = qrcode.QRCode(error_correction=error_correction, box_size=box_size)
    qr.add_data(data)
    qr.make()

    logo_data = None
    logo_box = None

    if with_logo and os.path.exists("logo.svg"):
        with open("logo.svg", "r") as f:
            logo_data = f.read()

        # Calculate center area to clear based on logo_margin
        mc = qr.modules_count
        size = int(mc * logo_margin)
        if size % 2 == 0:
            size += 1  # Ensure odd size for perfect centering

        start = (mc - size) // 2
        end = start + size

        for r in range(start, end):
            for c in range(start, end):
                qr.modules[r][c] = False

        # Define the logo box in pixels for the drawer
        logo_box = (
            ((start + qr.border) * qr.box_size, (start + qr.border) * qr.box_size),
            (
                (end + qr.border) * qr.box_size - 1,
                (end + qr.border) * qr.box_size - 1,
            ),
        )

    img = qr.make_image(
        image_factory=StyledSvgImage,
        module_drawer=SvgHorizontalBarsDrawer(),
        eye_drawer=SvgCustomEyeDrawer(),
        color_mask=SolidFillColorMask(front_color=front_color, back_color=back_color),
        logo_data=logo_data,
        logo_box=logo_box,
        logo_scale=Decimal(str(logo_scale)),
    )

    output = io.BytesIO()
    img.save(output)
    return output.getvalue().decode("utf-8")
