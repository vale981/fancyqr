import diff_extra
from diff_extra import found_cols_by_row, qr, mc

in_eye = []
for r, cols in found_cols_by_row.items():
    for c in cols:
        is_eye = (r < 7 and c < 7) or (r < 7 and c >= mc - 7) or (r >= mc - 7 and c < 7)
        if is_eye:
            in_eye.append((r, c))

print(f"Modules in eye: {in_eye}")
