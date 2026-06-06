import random
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class EnvironmentService:
    @staticmethod
    async def get_current_metrics(latitude: Optional[float], longitude: Optional[float]) -> Dict[str, Any]:
        """
        Retrieves weather and soil data based on GPS coordinates.
        Uses OpenWeatherMap if API key is provided; otherwise, simulates realistic local values.
        """
        temp = 24.5
        humidity = 62.0
        rainfall = 4.2
        wind_speed = 12.0
        
        # OWM Integration if key is configured
        if settings.WEATHER_API_KEY and latitude is not None and longitude is not None:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&appid={settings.WEATHER_API_KEY}"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        temp = data["main"]["temp"]
                        humidity = data["main"]["humidity"]
                        wind_speed = data["wind"]["speed"] * 3.6  # m/s to km/h
                        # Rainfall extraction if available
                        rainfall = data.get("rain", {}).get("1h", 0.0) + data.get("rain", {}).get("3h", 0.0)
            except Exception as e:
                print(f"Weather API fetch failed: {e}. Falling back to simulator.")
        else:
            # Simulate realistic seasonal variance based on coordinates
            lat_factor = abs(latitude or 0.0)
            lon_factor = abs(longitude or 35.0)
            
            # Simple hash-based deterministic randoms to keep it consistent per farm
            seed = int(lat_factor * 100 + lon_factor * 100) % 100
            random.seed(seed)
            
            temp = round(20.0 + (seed % 10) + random.uniform(-2, 2), 1)
            humidity = round(50.0 + (seed % 25) + random.uniform(-5, 5), 1)
            rainfall = round(max(0.0, (seed % 15) / 2.0 + random.uniform(-1, 2)), 1)
            wind_speed = round(5.0 + (seed % 12) + random.uniform(-2, 3), 1)
            
            # Reset random seed
            random.seed(None)

        # Generate soil moisture (which is not available on standard weather APIs)
        # Low rainfall -> lower moisture, high temperature -> lower moisture
        if rainfall > 10:
            soil_moisture = random.uniform(65, 85)
        elif rainfall > 2:
            soil_moisture = random.uniform(45, 65)
        else:
            # Simulating drier states
            soil_moisture = random.uniform(22, 44)
            
        soil_moisture = round(soil_moisture, 1)

        # Calculate stress and disease risk scores
        stress_score = EnvironmentService._calculate_stress_score(soil_moisture, temp)
        risk_score = EnvironmentService._calculate_risk_score(humidity, temp)
        
        # Assemble recommendations
        recommendations = EnvironmentService._generate_recommendations(soil_moisture, temp, humidity, rainfall)

        return {
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "soil_moisture": soil_moisture,
            "stress_score": stress_score,
            "risk_score": risk_score,
            "recommendations": recommendations
        }

    @staticmethod
    def _calculate_stress_score(soil_moisture: float, temp: float) -> float:
        """
        Calculates crop stress on a scale of 0 to 100.
        Optimal moisture is 40% - 60%. Below 30% or above 80% increases stress significantly.
        Optimal temperature is 18°C - 28°C.
        """
        moisture_stress = 0.0
        if soil_moisture < 40:
            moisture_stress = (40 - soil_moisture) * 3.5  # Max 140
        elif soil_moisture > 70:
            moisture_stress = (soil_moisture - 70) * 2.5  # Max 75
            
        temp_stress = 0.0
        if temp < 15:
            temp_stress = (15 - temp) * 4.0
        elif temp > 32:
            temp_stress = (temp - 32) * 5.0

        score = (moisture_stress * 0.7) + (temp_stress * 0.3)
        return round(min(100.0, max(0.0, score)), 1)

    @staticmethod
    def _calculate_risk_score(humidity: float, temp: float) -> float:
        """
        Calculates fungal disease outbreak risk.
        Favored by warm temperatures (20-28C) and high relative humidity (>70%).
        """
        humidity_factor = 0.0
        if humidity > 60:
            humidity_factor = (humidity - 60) * 2.5  # Max 100 at 100% RH
            
        temp_factor = 0.0
        if 18 <= temp <= 30:
            temp_factor = 100.0
        else:
            dist = min(abs(temp - 18), abs(temp - 30))
            temp_factor = max(0.0, 100.0 - dist * 10)

        risk = (humidity_factor * 0.6) + (temp_factor * 0.4)
        return round(min(100.0, max(0.0, risk)), 1)

    @staticmethod
    def _generate_recommendations(soil_moisture: float, temp: float, humidity: float, rainfall: float) -> str:
        advices = []
        if soil_moisture < 30:
            advices.append("Soil is critically dry. Trigger irrigation immediately for 45 minutes to prevent leaf shedding.")
        elif soil_moisture < 45:
            advices.append("Soil moisture is low. Standard drip irrigation cycle of 20 minutes is recommended.")
        elif soil_moisture > 75:
            advices.append("Waterlogging detected. Ensure outlet drains are open to prevent fungal root rot.")
        else:
            advices.append("Soil moisture is optimal. Maintain default irrigation scheduling.")

        if humidity > 75 and temp > 22:
            advices.append("High humidity and warmth detected. Fungal spore germination is highly likely. Inspect leaf undersides for rust spots and mildew.")
            
        if rainfall > 15:
            advices.append("Heavy downpour logged. Suspend immediate chemical applications (sprays) as they will wash off.")
            
        if temp > 30:
            advices.append("High heat index. Avoid afternoon field operations to reduce manual labor stress and direct crop heat impact.")

        return " ".join(advices)
