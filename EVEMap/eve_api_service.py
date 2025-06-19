from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis
import json

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis cache
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

ESI_BASE_URL = "https://esi.evetech.net/latest"
CACHE_TTL = 600  # 10 minutes

class RateLimiter:
    def __init__(self, rate_limit=150):
        self.rate_limit = rate_limit
        self.last_request = datetime.now()
        
    async def wait(self):
        elapsed = (datetime.now() - self.last_request).total_seconds() * 1000
        if elapsed < self.rate_limit:
            await asyncio.sleep((self.rate_limit - elapsed) / 1000)
        self.last_request = datetime.now()

rate_limiter = RateLimiter()

async def cached_request(endpoint: str, cache_key: str = None, ttl: int = CACHE_TTL):
    """Make cached API request"""
    cache_key = cache_key or endpoint
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Rate limit
    await rate_limiter.wait()
    
    # Make request
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ESI_BASE_URL}{endpoint}")
        response.raise_for_status()
        data = response.json()
    
    # Cache result
    cache.setex(cache_key, ttl, json.dumps(data))
    return data

# IMPORTANT: Specific routes MUST come before the generic proxy endpoint

@app.get("/api/universe/optimized")
async def get_optimized_universe_data(max_regions: int = 10):
    """Get optimized universe data with minimal API calls"""
    
    # Check if we have recent data
    cached_universe = cache.get("universe:optimized")
    if cached_universe:
        return json.loads(cached_universe)
    
    universe_data = {
        "regions": [],
        "systems": [],
        "connections": [],
        "generated_at": datetime.now().isoformat()
    }
    
    # Get regions
    region_ids = await cached_request("/universe/regions/")
    known_space_regions = [id for id in region_ids if id < 11000000][:max_regions]
    
    # Process regions concurrently
    async def process_region(region_id):
        region_data = await cached_request(f"/universe/regions/{region_id}/")
        return {
            "id": region_id,
            "name": region_data["name"],
            "constellations": region_data["constellations"][:3]  # Limit constellations
        }
    
    # Fetch regions in parallel
    tasks = [process_region(region_id) for region_id in known_space_regions]
    universe_data["regions"] = await asyncio.gather(*tasks)
    
    # Cache the optimized data
    cache.setex("universe:optimized", 3600, json.dumps(universe_data))
    
    return universe_data

@app.get("/api/search/systems")
async def search_systems(query: str):
    """Search for systems by name"""
    search_endpoint = f"/search/?search={query}&categories=solar_system&strict=false"
    results = await cached_request(search_endpoint, cache_key=f"search:{query}", ttl=300)
    
    if not results.get("solar_system"):
        return []
    
    # Get details for each system
    system_details = []
    for system_id in results["solar_system"][:10]:
        system = await cached_request(f"/universe/systems/{system_id}/")
        system_details.append({
            "id": system_id,
            "name": system["name"],
            "security": system["security_status"],
            "region_id": system.get("constellation_id")
        })
    
    return system_details

@app.post("/api/route/calculate")
async def calculate_route(data: Dict):
    """Calculate route between systems"""
    origin = data.get("origin")
    destination = data.get("destination")
    avoid = data.get("avoid", "secure")
    
    route_data = await cached_request(
        f"/route/{origin}/{destination}/?avoid={avoid}&flag=shortest",
        cache_key=f"route:{origin}:{destination}:{avoid}",
        ttl=300
    )
    return {"route": route_data, "jumps": len(route_data) - 1}

@app.post("/api/batch")
async def batch_request(data: Dict):
    """Batch request multiple endpoints"""
    endpoints = data.get("endpoints", [])
    results = {}
    for endpoint in endpoints:
        try:
            results[endpoint] = await cached_request(endpoint)
        except Exception as e:
            results[endpoint] = {"error": str(e)}
    return results

# Specific handlers for common endpoints
@app.get("/api/universe/regions/")
async def get_regions():
    """Get all region IDs"""
    return await cached_request("/universe/regions/")

@app.get("/api/universe/regions/{region_id}/")
async def get_region_info(region_id: int):
    """Get region information"""
    return await cached_request(f"/universe/regions/{region_id}/")

@app.get("/api/universe/constellations/{constellation_id}/")
async def get_constellation_info(constellation_id: int):
    """Get constellation information"""
    return await cached_request(f"/universe/constellations/{constellation_id}/")

@app.get("/api/universe/systems/{system_id}/")
async def get_system_info(system_id: int):
    """Get system information"""
    return await cached_request(f"/universe/systems/{system_id}/")

@app.get("/api/universe/stargates/{stargate_id}/")
async def get_stargate_info(stargate_id: int):
    """Get stargate information"""
    return await cached_request(f"/universe/stargates/{stargate_id}/")

@app.get("/api/universe/system_kills/")
async def get_system_kills():
    """Get system kills"""
    return await cached_request("/universe/system_kills/", ttl=300)

@app.get("/api/universe/system_jumps/")
async def get_system_jumps():
    """Get system jumps"""
    return await cached_request("/universe/system_jumps/", ttl=300)

# Generic proxy endpoint - MUST BE LAST!
@app.get("/api{endpoint:path}")
async def proxy_endpoint(endpoint: str):
    """Generic proxy for all API endpoints"""
    try:
        data = await cached_request(endpoint)
        return data
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)