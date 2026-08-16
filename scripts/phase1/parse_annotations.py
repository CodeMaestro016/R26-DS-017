import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

records = []

ann_root = Path("raw_data/annotations")

for xml_file in ann_root.rglob("*.xml"):

    video_name = xml_file.stem.replace("_annt", "")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for track in root.findall("track"):

        if track.attrib.get("label") != "pedestrian":
            continue

        for box in track.findall("box"):

            row = {
                "video": video_name,
                "frame": int(box.attrib["frame"]),
                "x1": float(box.attrib["xtl"]),
                "y1": float(box.attrib["ytl"]),
                "x2": float(box.attrib["xbr"]),
                "y2": float(box.attrib["ybr"])
            }

            for attr in box.findall("attribute"):
                row[attr.attrib["name"]] = attr.text

            records.append(row)

df = pd.DataFrame(records)

Path("processed_data/metadata").mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    "processed_data/metadata/annotations.csv",
    index=False
)

print("Saved:", len(df), "rows")