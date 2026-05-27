def color_to_hex(color):
    if isinstance(color, str):
        return color, 1.0
    if len(color) == 4:
        r, g, b, a = color
        return f"#{r:02x}{g:02x}{b:02x}", a / 255.0
    if len(color) == 3:
        r, g, b = color
        return f"#{r:02x}{g:02x}{b:02x}", 1.0
    return "#000000", 1.0

print(color_to_hex((255, 146, 50, 255)))
