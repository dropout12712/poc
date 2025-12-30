import os
import requests
import time

# Define the base URL for accessing the Roblox inventory API
BASE_URL = "https://inventory.roblox.com/v2/users/{user_id}/inventory/13?limit=100"

# Function to fetch asset IDs from a Roblox user's inventory
def fetch_asset_ids(user_id):
    url = BASE_URL.format(user_id=user_id)
    asset_ids = []
    next_page = url  # Start with the initial URL for pagination

    while next_page:
        try:
            response = requests.get(next_page)
            response.raise_for_status()
            data = response.json()
            # Add asset IDs from this page to the list
            asset_ids.extend(item['assetId'] for item in data.get('data', []))
            # Check if there is a next page
            next_page = data.get('nextPageCursor')
            if next_page:
                next_page = url + f"&cursor={next_page}"
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            if response.status_code == 429:  # Rate-limited
                print("Rate limited. Pausing for 5 minutes...")
                time.sleep(300)  # 5 minutes
            else:
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return asset_ids

# Function to save asset IDs to a text file
def save_asset_ids_to_file(user_id, asset_ids):
    file_path = f"{user_id}_asset_ids.txt"
    with open(file_path, "w") as file:
        for asset_id in asset_ids:
            file.write(f"{asset_id}\n")
    print(f"Asset IDs saved to {file_path}")

# Main function to run the script
def main():
    user_id = input("Enter the Roblox user ID: ")
    print("Fetching asset IDs...")
    asset_ids = fetch_asset_ids(user_id)
    if asset_ids:
        save_asset_ids_to_file(user_id, asset_ids)
    else:
        print("No asset IDs found or failed to fetch data.")

# Automatically install required packages if missing
def install_dependencies():
    try:
        import requests
    except ImportError:
        print("Installing required libraries...")
        os.system("pip install requests")

# Run dependency installation and main script
if __name__ == "__main__":
    install_dependencies()
    main()
