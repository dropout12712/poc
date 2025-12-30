import requests
import json
import time
import schedule
from datetime import datetime
import os
import tensorflow.lite as tflite
import numpy as np
from PIL import Image
import io

# Roblox Catalog API
CATALOG_API = "https://catalog.roproxy.com/v1/search/items/details"
THUMBNAIL_API = "https://thumbnails.roproxy.com/v1/assets"

# TFLite Model Files
MODEL_PATH = "model.tflite"  # Update with your downloaded model path
LABELS_PATH = "labels.txt"   # Update with your labels file path

# Load TFLite Model
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load Labels
with open(LABELS_PATH, "r") as f:
    labels = [line.strip() for line in f.readlines()]

def preprocess_image(image_url):
    """Download and preprocess image for TFLite model."""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).resize((224, 224))  # Teachable Machine default size
        img = img.convert("RGB")
        img_array = np.array(img, dtype=np.float32) / 255.0  # Normalize to [0, 1]
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        return img_array
    except Exception as e:
        print(f"Error preprocessing image {image_url}: {e}")
        return None

def is_class_1(image_url):
    """Classify image with TFLite model; return True if Class 1 (inappropriate)."""
    img_array = preprocess_image(image_url)
    if img_array is None:
        return False

    interpreter.set_tensor(input_details[0]["index"], img_array)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]["index"])
    prediction = np.argmax(output_data[0])
    confidence = output_data[0][prediction]

    # Assuming "Class 1" is the label for inappropriate items (check your labels.txt)
    return labels[prediction] == "Class 1" and confidence > 0.7  # Threshold for confidence

def fetch_catalog_items(keywords, limit=100):
    """Fetch items from the Roblox catalog based on keywords."""
    items = []
    for keyword in keywords:
        params = {
            "keyword": keyword,
            "limit": 10,
            "cursor": None
        }
        for _ in range(limit // 10):
            try:
                response = requests.get(CATALOG_API, params=params)
                response.raise_for_status()
                data = response.json()
                items.extend(data.get("data", []))
                next_cursor = data.get("nextPageCursor")
                if not next_cursor:
                    break
                params["cursor"] = next_cursor
                time.sleep(0.5)
            except requests.RequestException as e:
                print(f"Error fetching catalog for {keyword}: {e}")
                break
    return items[:limit]

def get_thumbnail_url(item_id):
    """Get thumbnail URL for an item."""
    try:
        response = requests.get(THUMBNAIL_API, params={"assetIds": item_id, "size": "420x420", "format": "Png"})
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["imageUrl"] if data["data"] else None
    except requests.RequestException as e:
        print(f"Error fetching thumbnail for {item_id}: {e}")
        return None

def scan_catalog():
    """Scan catalog and log Class 1 items to not-moderated.txt."""
    keywords = input("Enter keywords to scan (comma-separated): ").split(",")
    keywords = [kw.strip() for kw in keywords]
    print(f"Scanning catalog with keywords: {keywords}")
    
    items = fetch_catalog_items(keywords)
    class_1_items = []

    for item in items:
        item_id = item["id"]
        thumbnail_url = get_thumbnail_url(item_id)
        if thumbnail_url and is_class_1(thumbnail_url):
            class_1_items.append({
                "id": item_id,
                "name": item.get("name", "Unnamed"),
                "price": item.get("price", 0),
                "creatorName": item.get("creatorName", "Unknown"),
                "thumbnail": thumbnail_url
            })
            print(f"Flagged {item['name']} as Class 1")

    if class_1_items:
        with open("not-moderated.txt", "a", encoding="utf-8") as f:
            for item in class_1_items:
                f.write(json.dumps(item) + "\n")
        print(f"Added {len(class_1_items)} items to not-moderated.txt")
    else:
        print("No Class 1 items found.")

def daily_scan():
    """Schedule the scan to run daily."""
    print(f"Starting daily scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    scan_catalog()

if __name__ == "__main__":
    schedule.every().day.at("10:00").do(daily_scan)
    print("Scanner started. Waiting for scheduled time...")
    while True:
        schedule.run_pending()
        time.sleep(60)