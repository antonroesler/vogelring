import pickle
import json


FILE = "/Users/anton/Downloads/sightings.pkl"
OUT_FILE = "/Users/anton/Downloads/sightings.json"

with open(FILE, "rb") as f:
    sightings = pickle.load(f)


jsons = [s.model_dump() for s in sightings]

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(jsons, f, ensure_ascii=False)
    