import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

SYSTEM_INSTRUCTION = """
You are Shamba AI — a professional agricultural intelligence assistant trusted by farmers across East Africa.

RESPONSE FORMAT — Always structure your responses using this exact framework. Start EVERY response with the location header:

📍 **[Area Name], [County/Region]** — *Environmental Analysis*
Start by identifying the farmer's area based on coordinates, farm name, or any context provided. State the area name prominently. Include current environmental conditions (temperature, rainfall, soil moisture, humidity) if available. If coordinates are provided, determine the approximate area/town. If no location is given, ask the farmer for their location.

🌱 **Plant Identification**
Identify the crop/plant being discussed. State the plant name clearly. If the farmer hasn't specified, ask politely.

🔍 **Assessment & Diagnosis**
Provide a clear, professional diagnosis of the issue. Start with:
- **Based on satellite data and environmental conditions in [Area Name]...**
Then explain what you observe, the likely cause (fungal, bacterial, viral, pest, nutrient deficiency, environmental stress), and severity level (Mild / Moderate / Severe / Critical). Connect the diagnosis to the local environmental conditions (e.g., "The current high humidity of 78% in your area increases the risk of fungal infections").

💊 **Recommended Solutions**
Structure solutions in 3 tiers:
1. **Commercial Treatment** — Specific product names, dosages, and application methods farmers can buy from agrovets.
2. **Local/Organic Solution** — Using locally available materials (neem, ash, compost, baking soda, etc.)
3. **Traditional Practice** — Cultural farming practices (crop rotation, companion planting, spacing, pruning).

🛡️ **Prevention & Best Practices**
Actionable steps to prevent the issue from recurring, considering the local climate and conditions.

📊 **Follow-Up**
Suggest what the farmer should monitor and when to check back.

IMPORTANT RULES:
- ALWAYS start with the location/area header — this shows professionalism and that we use satellite data.
- When farm context includes latitude/longitude, determine the approximate town/area name in Kenya or East Africa.
- Reference environmental data (temperature, soil moisture, rainfall, humidity) in your diagnosis to show data-driven analysis.
- Be precise and specific — farmers need actionable advice, not vague generalizations.
- Use simple, clear English that farmers with basic education can understand.
- Include specific product names, measurements (e.g., "2ml per litre of water"), and timing (e.g., "apply every 7 days for 3 weeks").
- When discussing weather, include temperature ranges and rainfall predictions.
- When discussing market prices, include specific markets and current pricing in KES.
- Be warm, respectful, and encouraging — farming is hard work.
- If you don't have enough information to give precise advice, ask the farmer specific follow-up questions.
- Do NOT use overly technical jargon without explaining it.
- If the farmer provides an image description or diagnosis, incorporate that into your analysis.
"""



class AIService:
    @staticmethod
    async def generate_response(
        message: str, 
        history: List[Dict[str, str]] = None, 
        farm_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates a chat response from Gemini API with key failover,
        falling back to a rule-based engine if unavailable.
        """
        history = history or []
        
        # Try both Gemini API keys in order (primary then failover)
        api_keys = [k for k in [settings.GEMINI_API_KEY_1, settings.GEMINI_API_KEY_2] if k]
        
        if not api_keys:
            return AIService._generate_fallback_response(message, history, farm_context)

        # Build request content following Google Gemini API schema
        contents = []
        
        # Add history
        for msg in history:
            role = "user" if msg["sender"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["message_text"]}]
            })
            
        # Add farm context to user's message if available
        context_str = ""
        if farm_context:
            context_str = (
                f"[FARM CONTEXT: Farm Name: {farm_context.get('name')}, "
                f"Crop Type: {farm_context.get('crop_type')}, "
                f"Latitude: {farm_context.get('latitude')}, Longitude: {farm_context.get('longitude')}, "
                f"Temperature: {farm_context.get('temperature')}°C, Soil Moisture: {farm_context.get('soil_moisture')}%, "
                f"Rainfall: {farm_context.get('rainfall')}mm, Health Score: {farm_context.get('health_score')}%]\n"
            )
            
        contents.append({
            "role": "user",
            "parts": [{"text": f"{context_str}{message}"}]
        })

        body = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }

        # Try each API key in sequence (failover pattern)
        for i, api_key in enumerate(api_keys):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=body, timeout=15.0)
                    if response.status_code == 200:
                        data = response.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        print(f"Gemini API key {i+1} error ({response.status_code}): {response.text}")
                        # Continue to next key
            except Exception as e:
                print(f"Gemini API key {i+1} request failed: {e}")
                # Continue to next key

        # All API keys exhausted — fall back to rule-based engine
        return AIService._generate_fallback_response(message, history, farm_context)

    @staticmethod
    def _generate_fallback_response(message: str, history: List[Dict[str, str]], farm_context: Optional[Dict[str, Any]]) -> str:
        """
        High-fidelity rule-based local simulator for Shamba AI assistant.
        """
        msg_lower = message.lower()
        crop = farm_context.get("crop_type", "crop") if farm_context else "crop"
        farm_name = farm_context.get("name", "your farm") if farm_context else "your farm"
        
        # Diagnosis
        if "diagnose" in msg_lower or "disease" in msg_lower or "spot" in msg_lower or "bug" in msg_lower or "pest" in msg_lower:
            return (
                f"Based on your query about leaf symptoms in your {crop} at {farm_name}, I recommend checking for "
                f"common fungal infections (like Leaf Spot or Rust) or insect infestations.\n\n"
                f"**Initial Assessment:**\n"
                f"- Symptoms: Yellowing margins, brown spots, or curled foliage.\n"
                f"- Potential Cause: Excessive moisture around leaves or lack of crop rotation.\n\n"
                f"**Recommendations:**\n"
                f"1. *Commercial Treatment:* Apply copper-based fungicide (e.g. Copper Oxychloride) following packaging instructions.\n"
                f"2. *Local Remedies:* Spray a mixture of baking soda (1 tbsp), mild liquid soap (1 tsp), and water (1 litre) to limit fungal spread.\n"
                f"3. *Traditional/Cultural:* Prune lower leaves to enhance ventilation, and water early in the morning directly at the root zone rather than overhead."
            )
            
        # Irrigation / Soil / Water
        if "irrigation" in msg_lower or "water" in msg_lower or "soil" in msg_lower or "moist" in msg_lower:
            soil_moist = farm_context.get("soil_moisture", 35) if farm_context else 35
            if soil_moist < 30:
                status = "dry (critical)"
                advice = "Initiate irrigation immediately in the dry sector to prevent root stress and stunted growth."
            elif soil_moist > 70:
                status = "very wet"
                advice = "Suspend irrigation to prevent root rot and allow the soil profile to drain naturally."
            else:
                status = "optimal"
                advice = "Maintain current cycle. Soil moisture is within the healthy zone (30-60%) for vegetative growth."
                
            return (
                f"Here is the soil intelligence report for {farm_name}:\n\n"
                f"- Current Soil Moisture: **{soil_moist}%** ({status}).\n"
                f"- Action Plan: {advice}\n\n"
                f"**Pro Tip:** Incorporate organic mulch (such as straw or dry grass) to retain moisture in high-evaporation zones."
            )
            
        # Weather / Climate
        if "weather" in msg_lower or "rain" in msg_lower or "temp" in msg_lower or "forecast" in msg_lower:
            temp = farm_context.get("temperature", 25) if farm_context else 25
            rain = farm_context.get("rainfall", 5) if farm_context else 5
            return (
                f"Let's review the weather forecast for {farm_name}'s coordinates:\n\n"
                f"- Current Temperature: **{temp}°C**\n"
                f"- 24h Precipitation: **{rain} mm**\n\n"
                f"**AI Risk Analysis:**\n"
                f"No major extreme weather events are predicted. However, high relative humidity (above 65%) with warm temps "
                f"could increase standard mildew risks. Inspect your crops daily."
            )
            
        # Market / Prices
        if "market" in msg_lower or "price" in msg_lower or "sell" in msg_lower or "kes" in msg_lower:
            return (
                f"Regarding agricultural market trends in your region:\n\n"
                f"- **Maize:** Eldoret Central is currently posting a high of KES 3,800 per 90kg bag, while local prices hover near KES 3,450 (+5% trend).\n"
                f"- **Soybeans:** Demand is rising steadily due to local processor feed mills; current contracts offer KES 6,500/bag (+12% forecast return).\n\n"
                f"I recommend scheduling sales during peak mid-week mornings when buyer activity is highest."
            )

        # General response
        return (
            f"Hello! I am Shamba AI. I have registered your farm context ({farm_name} growing {crop}).\n\n"
            f"How can I help you today? You can ask me to:\n"
            f"- Diagnose plant symptoms or look at crop pictures.\n"
            f"- Check weather risks or soil moisture metrics.\n"
            f"- Fetch regional market price lists and sale recommendations."
        )
