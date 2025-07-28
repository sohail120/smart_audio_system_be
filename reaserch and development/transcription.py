import json

# Path to your segments.json file
json_file = "uploads/segments.json"

# Load and print JSON content
with open(json_file, "r") as f:
    segments = json.load(f)

# Print each segment in a readable format
for segment in segments:
    print(f"Filename: {segment['filename']}")
    print(f"Speaker: {segment['speaker']}")
    print(f"Start: {segment['start']}s")
    print(f"End: {segment['end']}s")
    print("-" * 40)
