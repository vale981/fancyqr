import argparse
import os
import re
import qrcode
from qrcode.main import QRCode
from qrcode.image.styles.colormasks import SolidFillColorMask
from fancy_qr import (
    parse_color,
    StyledSvgImage,
    SvgHorizontalBarsDrawer,
    SvgCustomEyeDrawer,
    generate_qr_svg,
)


def main():
    parser = argparse.ArgumentParser(description="Batch generate styled SVG QR codes.")
    parser.add_argument("data", nargs="+", help="Data strings to encode into QR codes.")
    parser.add_argument(
        "-o", "--output-dir", default=".", help="Output directory for SVG files."
    )
    parser.add_argument(
        "-f",
        "--front-color",
        default="255,146,50,255",
        help="Foreground color (hex or R,G,B,A).",
    )
    parser.add_argument(
        "-b",
        "--back-color",
        default="255,255,255,0",
        help="Background color (hex or R,G,B,A).",
    )
    parser.add_argument(
        "-s", "--box-size", type=int, default=100, help="Box size for the QR code."
    )
    parser.add_argument(
        "-e",
        "--error-correction",
        choices=["L", "M", "Q", "H"],
        default=None,
        help="Error correction level (default: L, or H if logo is used).",
    )
    parser.add_argument(
        "--logo", action="store_true", help="Embed logo.svg in the center."
    )
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.9,
        help="Scale factor for the logo (default: 0.8).",
    )
    parser.add_argument(
        "--logo-margin",
        type=float,
        default=0.2,
        help="Percentage of QR modules to clear for logo (default: 0.25).",
    )

    args = parser.parse_args()

    # Smart default for error correction
    ec_level = args.error_correction
    if ec_level is None:
        ec_level = "H" if args.logo else "L"

    # Map error correction strings to constants
    error_levels = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }

    try:
        front = parse_color(args.front_color)
        back = parse_color(args.back_color)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    for i, data in enumerate(args.data):
        # Create a safe filename
        safe_data = re.sub(r"[^a-zA-Z0-9]+", "_", data[:20])
        filename = os.path.join(args.output_dir, f"qr_{i:03d}_{safe_data}.svg")

        svg_content = generate_qr_svg(
            data=data,
            front_color=front,
            back_color=back,
            box_size=args.box_size,
            error_correction=error_levels[ec_level],
            with_logo=args.logo,
            logo_scale=args.logo_scale,
            logo_margin=args.logo_margin,
        )

        with open(filename, "w") as f:
            f.write(svg_content)
        print(f"Saved QR code for '{data}' to {filename}")


if __name__ == "__main__":
    main()
