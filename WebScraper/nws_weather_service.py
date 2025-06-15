#!/usr/bin/env python3
# filepath: /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/WebScraper/nws_weather_service.py

import json
import sys
import requests
from datetime import datetime, timezone

class NWSWeatherService:
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.user_agent = "NewsAggregator/1.0 (contact@newsaggregator.com)"
        
    def get_location_by_ip(self):
        """Get approximate location using IP geolocation"""
        try:
            # Free IP geolocation service
            response = requests.get('http://ip-api.com/json/', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'timezone': data.get('timezone')
                    }
        except Exception as e:
            print(f"Error getting location: {e}", file=sys.stderr)
        
        # Fallback to Washington DC (good for US-focused news dashboard)
        return {
            'lat': 38.9072,
            'lon': -77.0369,
            'city': 'Washington',
            'region': 'District of Columbia',
            'country': 'United States',
            'timezone': 'America/New_York'
        }
    
    def get_nws_office_and_grid(self, lat, lon):
        """Get the NWS office and grid coordinates for a location"""
        try:
            url = f"{self.base_url}/points/{lat},{lon}"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            properties = data.get('properties', {})
            
            office_info = {
                'office': properties.get('gridId'),
                'gridX': properties.get('gridX'),
                'gridY': properties.get('gridY'),
                'forecast_url': properties.get('forecast'),
                'forecast_hourly_url': properties.get('forecastHourly'),
                'city': properties.get('relativeLocation', {}).get('properties', {}).get('city', 'Unknown'),
                'state': properties.get('relativeLocation', {}).get('properties', {}).get('state', 'Unknown')
            }
            
            return office_info
            
        except Exception as e:
            print(f"Error getting NWS office info: {e}", file=sys.stderr)
            return None
    
    def get_current_conditions(self, lat, lon):
        """Get current weather conditions from nearby observation station"""
        try:
            # Find nearby observation stations
            url = f"{self.base_url}/points/{lat},{lon}/stations"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            stations_data = response.json()
            stations = stations_data.get('features', [])
            
            if not stations:
                print("No observation stations found nearby", file=sys.stderr)
                return None
            
            # Try the first few stations until we get current conditions
            for station in stations[:3]:
                try:
                    station_id = station['properties']['stationIdentifier']
                    obs_url = f"{self.base_url}/stations/{station_id}/observations/latest"
                    
                    obs_response = requests.get(obs_url, headers=headers, timeout=5)
                    if obs_response.status_code == 200:
                        obs_data = obs_response.json()
                        props = obs_data.get('properties', {})
                        
                        # Convert temperature from Celsius to Fahrenheit
                        temp_c = props.get('temperature', {}).get('value')
                        temp_f = round((temp_c * 9/5) + 32) if temp_c is not None else None
                        
                        # Get wind speed in mph
                        wind_speed_ms = props.get('windSpeed', {}).get('value')
                        wind_speed_mph = round(wind_speed_ms * 2.237) if wind_speed_ms is not None else None
                        
                        current = {
                            'station': station_id,
                            'station_name': station['properties'].get('name', station_id),
                            'temperature_f': temp_f,
                            'temperature_c': round(temp_c) if temp_c is not None else None,
                            'humidity': props.get('relativeHumidity', {}).get('value'),
                            'wind_speed_mph': wind_speed_mph,
                            'wind_direction': props.get('windDirection', {}).get('value'),
                            'visibility_miles': props.get('visibility', {}).get('value'),
                            'description': props.get('textDescription', ''),
                            'timestamp': props.get('timestamp', ''),
                            'barometric_pressure': props.get('barometricPressure', {}).get('value')
                        }
                        
                        return current
                        
                except Exception as station_error:
                    print(f"Failed to get data from station {station.get('properties', {}).get('stationIdentifier', 'N/A')}: {station_error}", file=sys.stderr)
                    continue
            
            print("Could not get current conditions from any nearby station", file=sys.stderr)
            return None
            
        except Exception as e:
            print(f"Error getting current conditions: {e}", file=sys.stderr)
            return None
    
    def get_forecast(self, office_info):
        """Get weather forecast from NWS"""
        try:
            if not office_info or not office_info.get('forecast_url'):
                return []
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(office_info['forecast_url'], headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            periods = data.get('properties', {}).get('periods', [])
            
            forecast = []
            for period in periods[:10]:  # Get next 10 periods (5 days typically)
                forecast_item = {
                    'name': period.get('name', ''),
                    'temperature': period.get('temperature'),
                    'temperature_unit': period.get('temperatureUnit', 'F'),
                    'temperature_trend': period.get('temperatureTrend'),
                    'wind_speed': period.get('windSpeed', ''),
                    'wind_direction': period.get('windDirection', ''),
                    'description': period.get('detailedForecast', ''),
                    'short_forecast': period.get('shortForecast', ''),
                    'is_daytime': period.get('isDaytime', True),
                    'icon': period.get('icon', ''),
                    'start_time': period.get('startTime', ''),
                    'end_time': period.get('endTime', '')
                }
                forecast.append(forecast_item)
            
            return forecast
            
        except Exception as e:
            print(f"Error getting forecast: {e}", file=sys.stderr)
            return []
    
    def get_weather_alerts(self, lat, lon):
        """Get weather alerts for the area"""
        try:
            # Get alerts for the point
            url = f"{self.base_url}/alerts/active?point={lat},{lon}"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                
                alerts = []
                for feature in features:
                    props = feature.get('properties', {})
                    alert = {
                        'event': props.get('event', ''),
                        'headline': props.get('headline', ''),
                        'description': props.get('description', ''),
                        'severity': props.get('severity', ''),
                        'urgency': props.get('urgency', ''),
                        'areas': props.get('areaDesc', ''),
                        'effective': props.get('effective', ''),
                        'expires': props.get('expires', '')
                    }
                    alerts.append(alert)
                
                return alerts
        except Exception as e:
            print(f"Error getting weather alerts: {e}", file=sys.stderr)
        
        return []
    
    def get_complete_weather(self, lat=None, lon=None):
        """Get complete weather information for location"""
        try:
            # Get location if not provided
            if lat is None or lon is None:
                location = self.get_location_by_ip()
                lat = location['lat']
                lon = location['lon']
                city = location['city']
                region = location['region']
                country = location['country']
            else:
                city = "Unknown"
                region = "Unknown"
                country = "Unknown"
            
            print(f"🌍 Getting NWS weather for {city}, {region} ({lat}, {lon})", file=sys.stderr)
            
            # Check if location is in US (NWS only covers US territories)
            if country != 'United States':
                return {
                    'success': False,
                    'error': f'US National Weather Service only covers United States territories. Location detected: {city}, {country}',
                    'suggestion': 'Consider using another weather API for international locations.'
                }
            
            # Get NWS office and grid info
            office_info = self.get_nws_office_and_grid(lat, lon)
            if not office_info:
                raise Exception("Could not determine NWS office for location")
            
            # Update location info with NWS data
            if office_info.get('city') != 'Unknown':
                city = office_info['city']
                region = office_info['state']
            
            # Get current conditions
            current = self.get_current_conditions(lat, lon)
            
            # Get forecast
            forecast = self.get_forecast(office_info)
            if not forecast:
                raise Exception("Could not retrieve forecast data")
            
            # Get alerts
            alerts = self.get_weather_alerts(lat, lon)
            
            return {
                'success': True,
                'location': {
                    'city': city,
                    'state': region,
                    'country': country,
                    'lat': lat,
                    'lon': lon,
                    'nws_office': office_info.get('office', 'Unknown')
                },
                'current': current,
                'forecast': forecast,
                'alerts': alerts,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'US National Weather Service',
                'note': 'Official US government weather data'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

def main():
    try:
        weather_service = NWSWeatherService()
        
        # Check if coordinates provided
        lat = float(sys.argv[1]) if len(sys.argv) > 1 else None
        lon = float(sys.argv[2]) if len(sys.argv) > 2 else None
        
        result = weather_service.get_complete_weather(lat, lon)
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()