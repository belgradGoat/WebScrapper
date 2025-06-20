import asyncio
import httpx
import json
import redis
from datetime import datetime
import os

ESI_BASE_URL = "https://esi.evetech.net/latest"
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def fetch_all_universe_data():
    """Fetch complete universe data and build cache"""
    print("Starting universe data fetch...")
    
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
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch all regions
        print("Fetching regions...")
        regions_response = await client.get(f"{ESI_BASE_URL}/universe/regions/")
        region_ids = regions_response.json()
        
        # Filter to known space only (< 11000000)
        region_ids = [rid for rid in region_ids if rid < 11000000]
        
        # Process each region
        for region_id in region_ids:
            print(f"Processing region {region_id}...")
            
            # Get region data
            region_response = await client.get(f"{ESI_BASE_URL}/universe/regions/{region_id}/")
            region_data = region_response.json()
            
            universe_data["regions"][region_id] = {
                "id": region_id,
                "name": region_data["name"],
                "constellations": region_data["constellations"]
            }
            
            # Process constellations
            for constellation_id in region_data["constellations"]:
                const_response = await client.get(f"{ESI_BASE_URL}/universe/constellations/{constellation_id}/")
                const_data = const_response.json()
                
                universe_data["constellations"][constellation_id] = {
                    "id": constellation_id,
                    "name": const_data["name"],
                    "region_id": region_id,
                    "systems": const_data["systems"],
                    "position": const_data["position"]
                }
                
                # Process systems
                for system_id in const_data["systems"]:
                    try:
                        system_response = await client.get(f"{ESI_BASE_URL}/universe/systems/{system_id}/")
                        system_data = system_response.json()
                        
                        universe_data["systems"][system_id] = {
                            "id": system_id,
                            "name": system_data["name"],
                            "constellation_id": constellation_id,
                            "region_id": region_id,
                            "security_status": system_data["security_status"],
                            "position": system_data["position"],
                            "stargates": system_data.get("stargates", [])
                        }
                        
                        # Add connections from stargates
                        for stargate_id in system_data.get("stargates", []):
                            try:
                                stargate_response = await client.get(f"{ESI_BASE_URL}/universe/stargates/{stargate_id}/")
                                stargate_data = stargate_response.json()
                                
                                connection = {
                                    "from": system_id,
                                    "to": stargate_data["destination"]["system_id"]
                                }
                                
                                # Avoid duplicates
                                reverse_connection = {"from": connection["to"], "to": connection["from"]}
                                if connection not in universe_data["connections"] and reverse_connection not in universe_data["connections"]:
                                    universe_data["connections"].append(connection)
                                    
                            except Exception as e:
                                print(f"Error fetching stargate {stargate_id}: {e}")
                                
                    except Exception as e:
                        print(f"Error fetching system {system_id}: {e}")
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
        
        # Update metadata
        universe_data["metadata"]["total_regions"] = len(universe_data["regions"])
        universe_data["metadata"]["total_constellations"] = len(universe_data["constellations"])
        universe_data["metadata"]["total_systems"] = len(universe_data["systems"])
        
        print(f"\nFetch complete!")
        print(f"Regions: {universe_data['metadata']['total_regions']}")
        print(f"Constellations: {universe_data['metadata']['total_constellations']}")
        print(f"Systems: {universe_data['metadata']['total_systems']}")
        print(f"Connections: {len(universe_data['connections'])}")
        
        return universe_data

async def main():
    # Fetch all data
    universe_data = await fetch_all_universe_data()
    
    # Save to file
    with open("universe_static_cache.json", "w") as f:
        json.dump(universe_data, f)
    print("\nSaved to universe_static_cache.json")
    
    # Also store in Redis with long TTL
    cache.setex("universe:complete", 2592000, json.dumps(universe_data))  # 30 days
    print("Stored in Redis cache")

if __name__ == "__main__":
    asyncio.run(main())