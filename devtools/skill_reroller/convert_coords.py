import json


def convert(coords, w=2560, h=1440):
    if len(coords) == 2:
        return [round(coords[0] / w, 5), round(coords[1] / h, 5)]
    elif len(coords) == 4:
        return [
            round(coords[0] / w, 5),
            round(coords[1] / h, 5),
            round(coords[2] / w, 5),
            round(coords[3] / h, 5),
        ]
    return coords


coordinates = {
    "auto_select_btn": [248, 1417],
    "reroll_btn": [460, 773],
    "skill_area": [2150, 710, 2560, 800],
    "back_btn": [40, 1419],
    "material_rows": [[680, 340, 920, 390], [680, 460, 920, 510], [680, 580, 920, 630]],
    "weapon_name": [1620, 252, 2020, 303],
    "weapon_element": [1790, 560, 2030, 600],
}

output = []
output.append("[coordinates]")
for key, val in coordinates.items():
    if key == "material_rows":
        converted_rows = [convert(row) for row in val]
        output.append(f"{key} = [")
        for row in converted_rows:
            output.append(f"    {str(row).replace('[', '[').replace(']', '],')}")
        output.append("]")
    else:
        output.append(f"{key} = {convert(val)}")

with open("temp_coords_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
