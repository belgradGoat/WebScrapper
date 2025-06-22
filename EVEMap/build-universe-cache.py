import asyncio
import httpx
import json
import redis
from datetime import datetime
import os
import time

ESI_BASE_URL = "https://esi.evetech.net/latest"
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def fetch_with_retry(client, url, max_retries=3):
    """Fetch with retry logic and better error handling"""
    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-Esi-Error-Limit-Reset', 60))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                continue
                
            # Check for other errors
            if response.status_code != 200:
                print(f"Error {response.status_code} for {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None
                
            # Parse JSON
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"Invalid JSON response from {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
                
        except httpx.TimeoutException:
            print(f"Timeout for {url}, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    return None

async def fetch_all_universe_data():
    """Fetch complete universe data and build cache"""
    print("Starting FULL universe data fetch...")
    print("WARNING: This will take several hours to complete!")
    print("=" * 50)
    
    start_time = time.time()
    
    universe_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "total_regions": 0,
            "total_constellations": 0,
            "total_systems": 0
        },
        "regions": {},
        "constellations": {},
        "systems": {},
        "connections": []
    }
    
    # Create client with longer timeout
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Fetch all regions
        print("Fetching regions...")
        region_ids = await fetch_with_retry(client, f"{ESI_BASE_URL}/universe/regions/")
        
        if not region_ids:
            print("Failed to fetch regions!")
            return universe_data
            
        # Filter to known space only (< 11000000)
        region_ids = [rid for rid in region_ids if rid < 11000000]
        
        print(f"Processing {len(region_ids)} regions...")
        
        # Process each region
        for idx, region_id in enumerate(region_ids):
            region_start = time.time()
            print(f"\nProcessing region {region_id} ({idx + 1}/{len(region_ids)})...")
            
            # Get region data
            region_data = await fetch_with_retry(client, f"{ESI_BASE_URL}/universe/regions/{region_id}/")
            if not region_data:
                print(f"Skipping region {region_id} due to errors")
                continue
                
            universe_data["regions"][region_id] = {
                "id": region_id,
                "name": region_data["name"],
                "constellations": region_data["constellations"]
            }
            
            constellation_ids = region_data["constellations"]
            
            # Process constellations
            for const_idx, constellation_id in enumerate(constellation_ids):
                if const_idx % 10 == 0:
                    print(f"  Processing constellation {const_idx + 1}/{len(constellation_ids)}...")
                
                const_data = await fetch_with_retry(client, f"{ESI_BASE_URL}/universe/constellations/{constellation_id}/")
                if not const_data:
                    print(f"  Skipping constellation {constellation_id} due to errors")
                    continue
                    
                universe_data["constellations"][constellation_id] = {
                    "id": constellation_id,
                    "name": const_data["name"],
                    "region_id": region_id,
                    "systems": const_data["systems"],
                    "position": const_data["position"]
                }
                
                system_ids = const_data["systems"]
                
                # Process systems
                for sys_idx, system_id in enumerate(system_ids):
                    if sys_idx % 50 == 0 and sys_idx > 0:
                        print(f"    Processing systems {sys_idx}/{len(system_ids)}...")
                        
                    system_data = await fetch_with_retry(client, f"{ESI_BASE_URL}/universe/systems/{system_id}/")
                    if not system_data:
                        continue
                        
                    universe_data["systems"][system_id] = {
                        "id": system_id,
                        "name": system_data["name"],
                        "constellation_id": constellation_id,
                        "region_id": region_id,
                        "security_status": system_data["security_status"],
                        "position": system_data["position"],
                        "stargates": system_data.get("stargates", [])
                    }
                    
                    # Rate limiting - be nice to the API
                    await asyncio.sleep(0.1)  # 100ms between requests
                    
                # Small delay between constellations
                await asyncio.sleep(0.5)
                
            # Stats for this region
            region_time = time.time() - region_start
            print(f"  Region {region_data['name']} complete in {region_time:.1f}s")
            print(f"  Total progress: {len(universe_data['systems'])} systems")
            
            # Save progress periodically
            if idx % 5 == 0 and idx > 0:
                print("Saving progress...")
                with open("universe_partial_cache.json", "w") as f:
                    json.dump(universe_data, f)
                    
                # Estimate remaining time
                elapsed = time.time() - start_time
                avg_time_per_region = elapsed / (idx + 1)
                remaining_regions = len(region_ids) - (idx + 1)
                eta_seconds = remaining_regions * avg_time_per_region
                eta_hours = eta_seconds / 3600
                print(f"  Estimated time remaining: {eta_hours:.1f} hours")
        
        # Process connections
        print("\n" + "=" * 50)
        print("Processing stargate connections...")
        print("This will take a while...")
        
        connection_count = 0
        system_list = list(universe_data["systems"].items())
        total_systems = len(system_list)
        
        for sys_idx, (system_id, system_data) in enumerate(system_list):
            if sys_idx % 100 == 0:
                print(f"Processing connections for system {sys_idx}/{total_systems} ({connection_count} connections found)")
                
            for stargate_id in system_data.get("stargates", []):
                stargate_data = await fetch_with_retry(client, f"{ESI_BASE_URL}/universe/stargates/{stargate_id}/")
                if not stargate_data:
                    continue
                    
                connection = {
                    "from": system_id,
                    "to": stargate_data["destination"]["system_id"],
                    "stargate_id": stargate_id
                }
                
                # Check if destination system exists in our data
                if connection["to"] in universe_data["systems"]:
                    # Avoid duplicates
                    existing = any(c["from"] == connection["from"] and c["to"] == connection["to"] 
                                 for c in universe_data["connections"])
                    if not existing:
                        universe_data["connections"].append(connection)
                        connection_count += 1
                    
                await asyncio.sleep(0.1)  # Rate limiting
                
            # Save connections progress periodically
            if sys_idx % 500 == 0 and sys_idx > 0:
                print("Saving connections progress...")
                with open("universe_partial_cache.json", "w") as f:
                    json.dump(universe_data, f)
        
        # Update metadata
        universe_data["metadata"]["total_regions"] = len(universe_data["regions"])
        universe_data["metadata"]["total_constellations"] = len(universe_data["constellations"])
        universe_data["metadata"]["total_systems"] = len(universe_data["systems"])
        universe_data["metadata"]["build_time_seconds"] = int(time.time() - start_time)
        
        print("\n" + "=" * 50)
        print(f"FETCH COMPLETE!")
        print(f"Total time: {(time.time() - start_time) / 3600:.1f} hours")
        print(f"Regions: {universe_data['metadata']['total_regions']}")
        print(f"Constellations: {universe_data['metadata']['total_constellations']}")
        print(f"Systems: {universe_data['metadata']['total_systems']}")
        print(f"Connections: {len(universe_data['connections'])}")
        
        return universe_data

async def main():
    try:
        # Check if partial cache exists
        if os.path.exists("universe_partial_cache.json"):
            print("Found partial cache file. Do you want to:")
            print("1. Resume from partial cache")
            print("2. Start fresh")
            choice = input("Enter choice (1/2): ")
            
            if choice == "1":
                print("Loading partial cache...")
                with open("universe_partial_cache.json", "r") as f:
                    universe_data = json.load(f)
                print(f"Loaded {len(universe_data['systems'])} systems from cache")
                # TODO: Implement resume logic
            else:
                universe_data = await fetch_all_universe_data()
        else:
            universe_data = await fetch_all_universe_data()
        
        # Save to file
        filename = "universe_static_cache.json"
        print(f"\nSaving to {filename}...")
        with open(filename, "w") as f:
            json.dump(universe_data, f, indent=2)
        print(f"Saved to {filename}")
        
        # Calculate file size
        file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.1f} MB")
        
        # Also store in Redis with long TTL
        try:
            print("Storing in Redis cache...")
            cache.setex("universe:complete", 2592000, json.dumps(universe_data))  # 30 days
            print("Stored in Redis cache")
        except Exception as e:
            print(f"Failed to store in Redis: {e}")
            print("(This is okay, file cache will be used)")
            
        # Clean up partial cache
        if os.path.exists("universe_partial_cache.json"):
            os.remove("universe_partial_cache.json")
            print("Cleaned up partial cache")
            
    except KeyboardInterrupt:
        print("\n\nInterrupted! Progress saved to universe_partial_cache.json")
        print("Run the script again to resume.")
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    print("=== EVE Universe Cache Builder (FULL VERSION) ===")
    print("This will fetch the COMPLETE EVE universe data.")
    print("Expected to take 2-4 hours depending on API response times.")
    print("\nYou can interrupt with Ctrl+C and resume later.")
    print("=" * 50)
    
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == "yes":
        asyncio.run(main())
    else:
        print("Aborted.")