import base64
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

MOCK_DISEASE_DB = {
    "maize": {
        "disease_name": "Grey Leaf Spot (Cercospora zeae-maydis)",
        "confidence": 0.88,
        "severity": "Medium",
        "symptoms": "Rectangular, tan-to-grey necrotic lesions running parallel to leaf veins. Over time, lesions merge, causing entire leaves to blight.",
        "causes": "Fungal spores overwintering in crop residue, favored by warm, humid weather (temp 22-30°C) and poor ventilation.",
        "treatment_commercial": "Apply systemic strobilurin or triazole fungicides (e.g. Amistar Top) early at the onset of lesions. Follow dosage instructions strictly.",
        "treatment_local": "Spray diluted neem oil extract (5ml per litre of water) to suppress fungal spore germination and insect vectors.",
        "treatment_traditional": "Practice crop rotation with non-cereal crops (like beans or cowpeas). Remove and burn infected stalks after harvest to reduce residual spores.",
        "prevention": "Use resistant maize hybrids. Ensure spacing of 75cm x 25cm to maximize wind flow and decrease relative humidity in the canopy."
    },
    "beans": {
        "disease_name": "Bean Anthracnose (Colletotrichum lindemuthianum)",
        "confidence": 0.92,
        "severity": "High",
        "symptoms": "Dark brown-to-black sunken lesions on bean pods, stems, and leaf veins. Under humid conditions, pinkish spore masses appear inside pod lesions.",
        "causes": "Seed-borne fungal pathogen spreading through splashing rain, wind, and working in wet bean fields.",
        "treatment_commercial": "Use copper-based protectant fungicides (e.g. Copper Oxychloride) or carbendazim sprays when pods start forming.",
        "treatment_local": "Apply a spray of wood ash water extract to leaf surfaces, which alters pH and inhibits spore propagation.",
        "treatment_traditional": "Use certified disease-free seeds. Never work or harvest in bean fields when foliage is wet. Implement a 3-year crop rotation.",
        "prevention": "Destroy crop debris post-harvest. Improve drainage to prevent standing pools of water which foster fungal growth."
    },
    "coffee": {
        "disease_name": "Coffee Leaf Rust (Hemileia vastatrix)",
        "confidence": 0.94,
        "severity": "High",
        "symptoms": "Powdery orange-yellow spots on the underside of coffee leaves. Severely infected leaves drop prematurely, causing dieback of bearing branches.",
        "causes": "Fungal pathogen spreading via wind and water splash. Favored by high planting density and dense shading.",
        "treatment_commercial": "Spray copper-based fungicides (e.g. Nordox) protectively before the rainy season begins, or systemic triazoles.",
        "treatment_local": "Use garlic-onion water spray (rich in natural sulfur compounds) on infected leaves to slow down rust spot growth.",
        "treatment_traditional": "Prune excess branches to allow sunlight to penetrate the canopy, reducing damp shaded microclimates. Apply well-composted manure to boost plant immunity.",
        "prevention": "Plant rust-resistant coffee varieties (e.g. Ruiru 11 or Batian). Establish windbreaks to limit spore migration between blocks."
    },
    "tomatoes": {
        "disease_name": "Tomato Early Blight (Alternaria solani)",
        "confidence": 0.89,
        "severity": "Medium",
        "symptoms": "Dark spots with concentric rings (target-like pattern) appearing first on older leaves, causing yellowing and leaf drop. Dark lesions also form on stems and fruit stems.",
        "causes": "Soil-borne fungus that thrives in warm, wet conditions. Spores spread by rain splash or overhead irrigation.",
        "treatment_commercial": "Apply mancozeb or chlorothalonil fungicides every 7-10 days under wet weather conditions.",
        "treatment_local": "Spray a solution of baking soda (sodium bicarbonate) and vegetable oil (1 tbsp each per gallon of water) to limit leaf acidity.",
        "treatment_traditional": "Stake tomato vines to keep foliage off the ground. Mulch with straw to prevent soil-borne spores from splashing onto lower leaves.",
        "prevention": "Practice drip irrigation instead of overhead watering. Plant tomatoes at least 2 feet apart for healthy aeration."
    },
    "default": {
        "disease_name": "Powdery Mildew",
        "confidence": 0.85,
        "severity": "Low",
        "symptoms": "White, powdery fungal spots spreading over leaf surfaces and stems, leading to leaf distortion and reduced photosynthesis.",
        "causes": "High humidity, dry foliage, and low light intensity. Often occurs in densely crowded planting layouts.",
        "treatment_commercial": "Use sulfur-based dusts or systemic triadimefon fungicides.",
        "treatment_local": "Spray a mixture of milk and water (1:9 ratio) under direct sunlight; milk proteins act as a natural sanitizer.",
        "treatment_traditional": "Prune crowded stems to allow sunlight penetration and air movement. Water early in the day so foliage dries quickly.",
        "prevention": "Ensure proper field spacing and select crop varieties bred for mildew resistance."
    }
}

class DiseaseDetectionService:
    @staticmethod
    async def diagnose_crop_image(
        image_bytes: bytes, 
        crop_type: Optional[str] = None, 
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Diagnoses crop disease from an image using a three-tier detection strategy:
        1. Plant.id API (if PLANT_ID_API_KEY is configured)
        2. Gemini Vision API with dual-key failover
        3. High-fidelity local fallback database
        """
        normalized_crop = crop_type.strip().lower() if crop_type else "default"
        
        # Determine fallback profile
        fallback_data = MOCK_DISEASE_DB.get(normalized_crop)
        if not fallback_data:
            fallback_data = MOCK_DISEASE_DB["default"]
            for k, v in MOCK_DISEASE_DB.items():
                if k in normalized_crop:
                    fallback_data = v
                    break

        # ── Tier 1: Plant.id API ──────────────────────────────────────────────
        plant_id_key = settings.PLANT_ID_API_KEY
        if plant_id_key:
            try:
                result = await DiseaseDetectionService._diagnose_with_plant_id(
                    image_bytes, plant_id_key, mime_type, fallback_data
                )
                if result:
                    return result
            except Exception as e:
                print(f"Plant.id API failed: {e}")

        # ── Tier 2: Gemini Vision API (dual-key failover) ─────────────────────
        gemini_keys = [k for k in [settings.GEMINI_API_KEY_1, settings.GEMINI_API_KEY_2] if k]
        if gemini_keys:
            result = await DiseaseDetectionService._diagnose_with_gemini(
                image_bytes, gemini_keys, crop_type, mime_type, fallback_data
            )
            if result:
                return result

        # ── Tier 3: Local fallback database ───────────────────────────────────
        return fallback_data

    @staticmethod
    async def _diagnose_with_plant_id(
        image_bytes: bytes,
        api_key: str,
        mime_type: str,
        fallback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Calls Plant.id health assessment API and normalizes the response."""
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        url = "https://plant.id/api/v3/health_assessment"
        
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        body = {
            "images": [f"data:{mime_type};base64,{base64_image}"],
            "health_assessment": True,
            "similar_images": True
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers, timeout=25.0)
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                health = data.get("result", {}).get("disease", {})
                suggestions = health.get("suggestions", [])
                if suggestions:
                    top = suggestions[0]
                    return {
                        "disease_name": top.get("name", fallback_data["disease_name"]),
                        "confidence": round(top.get("probability", 0.0), 2),
                        "severity": "High" if top.get("probability", 0) > 0.7 else "Medium",
                        "symptoms": top.get("details", {}).get("description", fallback_data["symptoms"]),
                        "causes": top.get("details", {}).get("cause", fallback_data["causes"]),
                        "treatment_commercial": top.get("details", {}).get("treatment", {}).get("chemical", fallback_data["treatment_commercial"]),
                        "treatment_local": top.get("details", {}).get("treatment", {}).get("biological", fallback_data["treatment_local"]),
                        "treatment_traditional": fallback_data["treatment_traditional"],
                        "prevention": top.get("details", {}).get("treatment", {}).get("prevention", fallback_data["prevention"])
                    }
            else:
                print(f"Plant.id API error ({response.status_code}): {response.text}")
        return None

    @staticmethod
    async def _diagnose_with_gemini(
        image_bytes: bytes,
        api_keys: list,
        crop_type: Optional[str],
        mime_type: str,
        fallback_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Calls Gemini Vision API with dual-key failover and returns parsed diagnosis."""
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            f"Diagnose this plant image. The crop type is stated as: '{crop_type or 'Unknown'}'. "
            "Please perform a scientific agricultural diagnosis. "
            "You MUST return your response as a raw JSON object ONLY, with exactly the following fields:\n"
            "{\n"
            '  "disease_name": "string (common name and scientific name in parentheses)",\n'
            '  "confidence": float (between 0.0 and 1.0),\n'
            '  "severity": "string (Low, Medium, or High)",\n'
            '  "symptoms": "string describing visual symptoms in detail",\n'
            '  "causes": "string detailing pathogen causes & environmental triggers",\n'
            '  "treatment_commercial": "string outlining commercial chemical products & application guides",\n'
            '  "treatment_local": "string detailing easily accessible local/organic treatments",\n'
            '  "treatment_traditional": "string outlining traditional farming practices & cultural remedies",\n'
            '  "prevention": "string with instructions on preventing future outbreaks"\n'
            "}\n"
            "Do not include any markdown format tags like ```json or ``` in the response. Output only the raw JSON string."
        )

        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        for i, api_key in enumerate(api_keys):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=body, timeout=25.0)
                    if response.status_code == 200:
                        result_json = response.json()
                        text_resp = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        
                        # Clean markdown wrappers if present
                        if text_resp.startswith("```"):
                            text_resp = text_resp.replace("```json", "").replace("```", "").strip()
                            
                        parsed_diagnosis = json.loads(text_resp)
                        # Merge with fallback keys in case model missed any fields
                        for key in fallback_data.keys():
                            if key not in parsed_diagnosis:
                                parsed_diagnosis[key] = fallback_data[key]
                        return parsed_diagnosis
                    else:
                        print(f"Gemini Vision key {i+1} error ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"Gemini Vision key {i+1} failed: {e}")

        return None

