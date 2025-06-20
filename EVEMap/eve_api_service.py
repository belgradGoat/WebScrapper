from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import httpx
import json
import redis
import os
import asyncio

# Initialize FastAPI app
app = FastAPI(title="EVE Universe API", version="1.0.0")

# Configure CORS - this is important!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

# EVE ESI base URL
ESI_BASE_URL = "https://esi.evetech.net/latest"

# Global universe cache
UNIVERSE_CACHE = None

@app.on_event("startup")
async def load_universe_cache():
    """Load universe cache on startup"""
    global UNIVERSE_CACHE
    
    # Try to load from Redis first
    cached = cache.get("universe:complete")
    if cached:
        UNIVERSE_CACHE = json.loads(cached)
        print(f"Loaded universe cache from Redis: {UNIVERSE_CACHE['metadata']['total_systems']} systems")
        return
    
    # Try to load from file
    if os.path.exists("universe_static_cache.json"):
        with open("universe_static_cache.json", "r") as f:
            UNIVERSE_CACHE = json.load(f)
            cache.setex("universe:complete", 2592000, json.dumps(UNIVERSE_CACHE))
            print(f"Loaded universe cache from file: {UNIVERSE_CACHE['metadata']['total_systems']} systems")
            return
    
    print("No universe cache found - API will be slower")

@app.get("/api/universe/complete")
async def get_complete_universe():
    """Get complete cached universe data"""
    if UNIVERSE_CACHE:
        return UNIVERSE_CACHE
    else:
        raise HTTPException(status_code=503, detail="Universe cache not loaded")

@app.get("/api/universe/optimized")
async def get_optimized_universe_data():
    """Get optimized universe data"""
    try:
        # Check cache first
        cached = cache.get("universe:optimized")
        if cached:
            return json.loads(cached)
        
        # If we have complete cache, use it
        if UNIVERSE_CACHE:
            regions = []
            for region_id, region_data in UNIVERSE_CACHE["regions"].items():
                regions.append({
                    "id": int(region_id),
                    "name": region_data["name"],
                    "constellation_count": len(region_data["constellations"]),
                    "system_count": sum(1 for s in UNIVERSE_CACHE["systems"].values() 
                                      if s["region_id"] == int(region_id))
                })
            
            result = {
                "regions": regions,
                "metadata": {
                    "total_regions": len(regions)
                }
            }
            
            # Cache for 1 hour
            cache.setex("universe:optimized", 3600, json.dumps(result))
            return result
        
        # Otherwise fetch from API
        regions = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get all regions
            response = await client.get(f"{ESI_BASE_URL}/universe/regions/")
            region_ids = response.json()
            
            # Filter known space only
            region_ids = [rid for rid in region_ids if rid < 11000000]
            
            # Limit to first 10 regions for quick loading
            for region_id in region_ids[:10]:
                try:
                    region_response = await client.get(f"{ESI_BASE_URL}/universe/regions/{region_id}/")
                    region_data = region_response.json()
                    
                    regions.append({
                        "id": region_id,
                        "name": region_data["name"],
                        "constellation_count": len(region_data.get("constellations", [])),
                        "system_count": 0  # Would need to count systems
                    })
                except Exception as e:
                    print(f"Error fetching region {region_id}: {e}")
        
        result = {
            "regions": regions,
            "metadata": {
                "total_regions": len(regions)
            }
        }
        
        # Cache for 1 hour
        cache.setex("universe:optimized", 3600, json.dumps(result))
        
        return result
        
    except Exception as e:
        print(f"Error in optimized endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add the other endpoints (kills, jumps, etc.)
@app.get("/api/universe/system_kills/")
async def get_system_kills():
    """Get system kills from EVE ESI"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ESI_BASE_URL}/universe/system_kills/")
            return response.json()
    except Exception as e:
        print(f"Error fetching kills: {e}")
        return []

@app.get("/api/universe/system_jumps/")
async def get_system_jumps():
    """Get system jumps from EVE ESI"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ESI_BASE_URL}/universe/system_jumps/")
            return response.json()
    except Exception as e:
        print(f"Error fetching jumps: {e}")
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)