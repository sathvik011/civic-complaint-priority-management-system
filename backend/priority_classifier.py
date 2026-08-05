import os
import sys
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

HEADERS = {"User-Agent": "CivicComplaintSystem/1.0"}
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

DEPARTMENTS = [
    "Municipal Corporation",
    "Police Department",
    "Fire Department",
    "Public Works Department (PWD)",
    "Electricity Board",
    "Water Supply Board",
    "Health Department",
    "Traffic Police",
    "Housing Board",
    "Education Department",
    "Environmental Department",
    "Department of Parks and Gardens",
    "Department of Consumer Protection",
    "Department of Labor",
    "Social Welfare Department"
]

def get_priority_groq(complaint):
    if not client:
        return "P1", "Groq not configured (default P1)"
    prompt = f"""You are a priority classifier for civic complaints in Indian cities.

PRIORITY LEVELS:
- P1 (CRITICAL): Immediate safety hazard, emergency, health risk, structural collapse, major accident, flooding, gas leak, fire
- P2 (MODERATE): Significant inconvenience, property damage, ongoing issue that needs attention within days
- P3 (LOW): Minor issues, cosmetic problems, routine maintenance, non-urgent

CLASSIFICATION RULES:
- When in doubt between P1 and P2, choose P1 (better safe than sorry)
- P1 examples: building collapse, gas leak, major fire, severe flooding, electrocution risk, bridge collapse, waterlogging during monsoon, road accident with injuries
- P2 examples: pothole, broken streetlight, garbage not collected, broken playground, water leakage, minor flooding, broken traffic signal
- P3 examples: faded paint, minor litter, cosmetic damage, scheduled maintenance, park maintenance request

INDIAN CONTEXT - P1 examples:
- "Oxygen mask not working in hospital" → P1 (health emergency)
- "Gas leak in residential area" → P1 (fire hazard)
- "Building showing cracks" → P1 (collapse risk)
- "Severe waterlogging" → P1 (safety hazard)
- "Fallen electric pole" → P1 (electrocution risk)

INDIAN CONTEXT - P2 examples:
- "Garbage not picked up" → P2 (health hazard but not emergency)
- "Street light not working" → P2 (inconvenience)
- "Pothole on road" → P2 (damage but not critical)

Complaint: "{complaint}"

Respond with ONLY P1, P2, or P3. No explanation."""
    try:
        chat = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant", temperature=0.1, max_tokens=10)
        response = chat.choices[0].message.content.strip().upper()
        if "P1" in response: return "P1", "Groq: " + response
        elif "P2" in response: return "P2", "Groq: " + response
        elif "P3" in response: return "P3", "Groq: " + response
        else: return "P1", "Groq unclear: " + response
    except Exception as e: return "P1", "Groq error: " + str(e)

def get_department_groq(complaint):
    if not client: return "Municipal Corporation", "Groq not configured"
    
    # Detailed department descriptions for Indian civic system
    dept_info = {
        "Municipal Corporation": "garbage collection, street cleaning, drainage, sewage, waterlogging, illegal construction, building collapse, encroachments, parks, playgrounds, municipal roads, streetlights, market violations",
        "Police Department": "crime, theft, harassment, safety emergency, traffic accident, noise complaint after 10pm, suspicious activity, domestic violence, missing person",
        "Fire Department": "fire hazard, gas leak, building fire, vehicle fire, fire rescue, burnt smell, flammable materials, fire safety violations",
        "Public Works Department (PWD)": "potholes, road repair, bridge damage, footpath repair, road sign damage, highway issues, flyover maintenance",
        "Electricity Board": "power outage, fallen electric pole, exposed wires, transformer failure, illegal wiring, electricity theft, street light not working",
        "Water Supply Board": "no water supply, water leakage, pipeline burst, contaminated water, low water pressure, drainage issues",
        "Health Department": "health code violation, food safety, disease outbreak, hospital issues, sanitation in public places, mosquito breeding, stagnant water",
        "Traffic Police": "traffic signal not working, illegal parking, traffic congestion, road blockage, driving violations, missing road signs",
        "Housing Board": "housing society issues, flat disputes, rent issues, landlord problems, housing scheme complaints",
        "Education Department": "school issues, teacher complaints, school infrastructure, education quality, student safety",
        "Environmental Department": "air pollution, water pollution, noise pollution, industrial pollution, illegal mining, tree cutting, garbage burning",
        "Department of Parks and Gardens": "park maintenance, tree trimming, garden issues, playground equipment, park security",
        "Department of Consumer Protection": "consumer fraud, fake products, shop cheating, weight manipulation, expired food",
        "Department of Labor": "worker rights, wage issues, factory safety, child labor, employment disputes",
        "Social Welfare Department": "welfare schemes, old age pension, widow benefits, disabled person benefits, poverty alleviation"
    }
    
    dept_list = ", ".join(DEPARTMENTS)
    dept_descriptions = "\n".join([f"- {d}: {desc}" for d, desc in dept_info.items()])
    
    prompt = f"""You are a civic complaint classifier for Indian cities. Classify complaints into the correct department.

IMPORTANT: This is for INDIAN civic system - use Indian department names only!

CLASSIFICATION RULES:
1. Choose the department MOST directly responsible for handling the issue
2. If multiple departments could apply, pick the PRIMARY one
3. Be precise - don't confuse similar departments

DEPARTMENT RESPONSIBILITIES:
{dept_descriptions}

EXAMPLES (Indian context):
- "Pothole on main road" → Public Works Department (PWD)
- "Garbage not collected for days" → Municipal Corporation
- "Street light not working" → Municipal Corporation (not Electricity Board)
- "Broken traffic signal" → Traffic Police (not Police Department)
- "Water pipeline leaking" → Water Supply Board
- "Power cut in area" → Electricity Board
- "Noise from construction at night" → Police Department (not Traffic Police)
- "Dead animal on road" → Municipal Corporation
- "Smell from factory" → Environmental Department
- "Food from restaurant made me sick" → Health Department
- "Unpaid wages from factory" → Department of Labor
- "Road accident" → Police Department (not Traffic Police for emergency)
- "Fire in building" → Fire Department
- "Stray dog problem" → Municipal Corporation
- "Mosquitoes breeding in stagnant water" → Health Department

Complaint: "{complaint}"

Respond with ONLY the exact department name from the list above. No explanation needed."""

    try:
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], 
            model="llama-3.1-8b-instant", 
            temperature=0.1, 
            max_tokens=50
        )
        response = chat.choices[0].message.content.strip()
        
        # Exact match first
        for dept in DEPARTMENTS:
            if dept.lower() == response.lower():
                return dept, "Groq: " + dept
        
        # Partial match
        for dept in DEPARTMENTS:
            if dept.lower() in response.lower() or response.lower() in dept.lower():
                return dept, "Groq: " + dept
        
        # Keyword matching as fallback - Indian departments
        response_lower = response.lower()
        keywords = {
            "municipal": "Municipal Corporation",
            "garbage": "Municipal Corporation",
            "trash": "Municipal Corporation",
            "drainage": "Municipal Corporation",
            "sewage": "Municipal Corporation",
            "encroachment": "Municipal Corporation",
            "park": "Municipal Corporation",
            "streetlight": "Municipal Corporation",
            "construction": "Municipal Corporation",
            "illegal": "Municipal Corporation",
            "police": "Police Department",
            "crime": "Police Department",
            "theft": "Police Department",
            "harassment": "Police Department",
            "accident": "Police Department",
            "missing": "Police Department",
            "fire": "Fire Department",
            "gas leak": "Fire Department",
            "burning": "Fire Department",
            "road": "Public Works Department (PWD)",
            "pothole": "Public Works Department (PWD)",
            "bridge": "Public Works Department (PWD)",
            "footpath": "Public Works Department (PWD)",
            "electricity": "Electricity Board",
            "power": "Electricity Board",
            "wire": "Electricity Board",
            "transformer": "Electricity Board",
            "water": "Water Supply Board",
            "pipeline": "Water Supply Board",
            "leakage": "Water Supply Board",
            "health": "Health Department",
            "food": "Health Department",
            "disease": "Health Department",
            "mosquito": "Health Department",
            "traffic": "Traffic Police",
            "signal": "Traffic Police",
            "parking": "Traffic Police",
            "housing": "Housing Board",
            "landlord": "Housing Board",
            "rent": "Housing Board",
            "school": "Education Department",
            "education": "Education Department",
            "pollution": "Environmental Department",
            "environment": "Environmental Department",
            "factory": "Environmental Department",
            "consumer": "Department of Consumer Protection",
            "shop": "Department of Consumer Protection",
            "worker": "Department of Labor",
            "wage": "Department of Labor",
            "factory": "Department of Labor",
            "welfare": "Social Welfare Department",
            "pension": "Social Welfare Department",
        }
        
        for keyword, dept in keywords.items():
            if keyword in response_lower or keyword in complaint.lower():
                return dept, "Groq keyword: " + dept
        
        return "Municipal Corporation", "Default: " + response
    except Exception as e: return "Department of Sanitation", "Error: " + str(e)

def get_priority_score(priority_level, density_level):
    priority_scores = {"P1": 3, "P2": 2, "P3": 1}
    density_scores = {"High": 3, "Medium": 2, "Low": 1}
    return priority_scores.get(priority_level, 0), density_scores.get(density_level, 0)

def calculate_final_priority(description_priority, location_density):
    description_score, density_score = get_priority_score(description_priority, location_density)
    final_score = (description_score * 0.7) + (density_score * 0.3)
    if final_score >= 2.5: return "1"
    elif final_score >= 1.5: return "2"
    else: return "3"

def count_pois(lat, lon, radius_m=1000):
    q = "[out:json][timeout:25]; (node[\"amenity\"](around:" + str(radius_m) + "," + str(lat) + "," + str(lon) + "); node[\"leisure\"](around:" + str(radius_m) + "," + str(lat) + "," + str(lon) + "); node[\"shop\"](around:" + str(radius_m) + "," + str(lat) + "," + str(lon) + "); node[\"highway\"=\"bus_stop\"](around:" + str(radius_m) + "," + str(lat) + "," + str(lon) + ");); out count;"
    try:
        r = requests.post(OVERPASS_URL, data={"data": q}, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if not data.get("elements"): return 0
        return int(data["elements"][0]["tags"]["total"])
    except: return -1

def classify_density(poi_count):
    if poi_count > 50: return "High"
    elif poi_count >= 15: return "Medium"
    else: return "Low"

def get_location_density(lat, lon, radius=1000):
    count = count_pois(lat, lon, radius)
    return classify_density(count)

def get_priority_hybrid(complaint, mapping=None, model=None, threshold=80):
    return get_priority_groq(complaint)

def load_or_train_model(model_path="complaint_priority_model.joblib"):
    print("ML model loading disabled - using Groq only")
    return None

merged_priority_mapping = {}