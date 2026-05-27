def test():
    # If the bounding box is ux0, uy0 with w, h.
    # We want the stroke to be completely inside.
    # We shrink the box by stroke_width/2 on all sides.
    ux0 = 40.0
    uy0 = 40.0
    w = 70.0
    h = 70.0
    stroke_w = 10.0
    
    half_w = stroke_w / 2
    ux0 += half_w
    uy0 += half_w
    w -= stroke_w
    h -= stroke_w
    print(f"Inset Box: x={ux0}, y={uy0}, w={w}, h={h}")

test()
