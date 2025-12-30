import requests                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
import json
import time

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1344921317836591164/fMEeJftAqmxTTWneFhkm7z1btVoRIw-UnqWc-xt41Pz8DWWRYY5jSlJArIqqCyNwLXRC"  # <-- Replace with your webhook URL

def send_to_discord(file_path, search_type, items):
    """Uploads the JSON file to Discord webhook and sends all search results in one message."""
    # Create the message content
    message_content = f"📜 **New {search_type} Search Results Uploaded!**\n\n"

    for idx, item in enumerate(items, start=1):
        message_content += f"**{idx}. [{item['name']}]({item['itemUrl']})** - 💰 {item.get('price', 'Offsale')}\n"

    # Discord has a message character limit (2000 chars), so truncate if needed
    if len(message_content) > 1900:
        message_content = message_content[:1900] + "\n... (truncated due to length)"

    # Prepare the file upload and message
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "application/json")}
        payload = {"content": message_content}

        response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)

    if response.status_code == 200:
        print("✅ JSON file and results successfully sent to Discord!")
    else:
        print(f"❌ Failed to send data to Discord! Error: {response.text}")

def get_roblox_items(keyword, max_items, search_classic_tshirts, search_classic_shirts, search_classic_pants, enable_rate_limit, rate_limit_duration, search_ugc):
    base_url = "https://catalog.roblox.com/v1/search/items/details"
    headers = {}

    base_url = base_url.replace("roblox.com", "roproxy.com")

    params = {"Limit": 10}

    if search_classic_tshirts:
        params["Category"], params["Subcategory"], search_type = 3, 55, "Classic T-Shirts"
    elif search_classic_shirts:
        params["Category"], params["Subcategory"], search_type = 3, 3, "Classic Shirts"
    elif search_classic_pants:
        params["Category"], params["Subcategory"], search_type = 3, 4, "Classic Pants"
    elif search_ugc:
        params["Category"], search_type = 11, "UGC Accessories"
    else:
        search_type = "Unknown"

    params["Keyword"] = keyword

    file_name = f"{search_type.lower().replace(' ', '_')}_items.json"
    items_scraped = []
    next_cursor = None
    existing_ids = set()

    try:
        with open(file_name, "r") as f:
            existing_data = json.load(f)
            existing_ids = {item['id'] for item in existing_data}
    except FileNotFoundError:
        existing_data = []

    global_search_count = len(existing_data)

    while len(items_scraped) < max_items:
        if next_cursor:
            params["Cursor"] = next_cursor

        print(f"🔍 Searching with params: {params}")

        if enable_rate_limit:
            time.sleep(rate_limit_duration)

        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            items = data.get("data", [])
            print(f"✅ Items fetched: {len(items)}")

            for idx, item in enumerate(items):
                if item["id"] not in existing_ids:
                    global_search_count += 1
                    item["itemsearch"] = global_search_count
                    item["itemUrl"] = f"https://www.roblox.com/catalog/{item['id']}"
                    items_scraped.append(item)
                    existing_ids.add(item["id"])

            next_cursor = data.get("nextPageCursor")
            if not next_cursor:
                break

            if len(items_scraped) >= max_items:
                break
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            break

    items_scraped = items_scraped[:max_items]

    cleaned_items = []
    for item in items_scraped:
        cleaned_item = {
            "id": item.get("id"),
            "name": item.get("name"),
            "productId": item.get("productId"),
            "creatorHasVerifiedBadge": item.get("creatorHasVerifiedBadge", False),
            "creatorType": item.get("creatorType"),
            "creatorTargetId": item.get("creatorTargetId"),
            "creatorName": item.get("creatorName"),
            "price": item.get("price"),
            "itemsearch": item.get("itemsearch"),
            "itemUrl": item.get("itemUrl")
        }
        cleaned_items.append(cleaned_item)

    with open(file_name, "w") as outfile:
        json.dump(existing_data + cleaned_items, outfile, indent=4)

    print(f"📁 Items saved to {file_name}. Total new items scraped: {len(cleaned_items)}")

    # Send results to Discord (all in one message)
    send_to_discord(file_name, search_type, cleaned_items)

def main():
    keyword = input("Enter the keyword to search for: ")
    max_items = int(input("Enter the number of items you want to scrape: "))
    search_classic_tshirts = input("Do you want to search for Classic T-shirts? (yes/no): ").strip().lower() == "yes"
    search_classic_shirts = input("Do you want to search for Classic Shirts? (yes/no): ").strip().lower() == "yes"
    search_classic_pants = input("Do you want to search for Classic Pants? (yes/no): ").strip().lower() == "yes"
    search_ugc = input("Do you want to search for UGC items? (yes/no): ").strip().lower() == "yes"
    
    enable_rate_limit = input("Do you want to enable rate limit protection? (yes/no): ").strip().lower() == "yes"
    rate_limit_duration = 10
    if enable_rate_limit:
        rate_limit_duration = int(input("How many seconds should I wait between each request? (e.g., 5, 10): ").strip())

    print(f"🔎 Searching for {max_items} items with keyword: '{keyword}'...")
    get_roblox_items(keyword, max_items, search_classic_tshirts, search_classic_shirts, search_classic_pants, enable_rate_limit, rate_limit_duration, search_ugc)

if __name__ == "__main__":
    main()

    

