from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from groq import Groq

app = Flask(__name__)
CORS(app)

# Initialize Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# List of possible departments/agencies
DEPARTMENTS = [
    "Department of Buildings",
    "Department of Consumer and Worker Protection",
    "Department of Transportation",
    "Department of Sanitation",
    "Department of Parks and Recreation",
    "Department of Environmental Protection",
    "Department of Health",
    "Department of Police",
    "Department of Fire",
    "Department of Housing",
    "Department of Education",
    "Department of Business Services",
    "Department of Cultural Affairs",
    "Department of Aging",
    "Department of Homeless Services",
    "Department of Social Services",
    "Department of Youth and Community Development",
    "Department of Veterans Services",
    "Department of Media and Entertainment",
    "Department of City Planning"
]


def get_department_groq(complaint):
    """
    Assign department/agency using Groq LLM API.
    """
    if not client:
        return "Department of Sanitation"

    dept_list = ", ".join(DEPARTMENTS)
    
    prompt = f"""You are a civic complaint department classifier. Classify the following complaint into ONE of these departments:
{dept_list}

Complaint: "{complaint}"

Respond with ONLY the department name and nothing else. Choose the most appropriate department based on the complaint description."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=50,
        )
        response = chat_completion.choices[0].message.content.strip()
        
        # Validate response is in our department list
        for dept in DEPARTMENTS:
            if dept.lower() in response.lower():
                return dept
        
        return "Department of Sanitation"
    except Exception as e:
        print(f"Groq error: {e}")
        return "Department of Sanitation"


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("description", "").strip()
        if not text:
            return jsonify({"error": "Empty description"}), 400

        # Use Groq to classify department
        department = get_department_groq(text)
        return jsonify({"department": department})

    except Exception as e:
        print("Error during prediction:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if client:
        print("🚀 Groq client initialized - using LLM for classification")
    else:
        print("⚠️ Groq API key not found - using default department")
    print("Starting server on http://127.0.0.1:5001")
    app.run(debug=True, port=5001)from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
from sentence_transformers import SentenceTransformer
import contextlib  # <-- for suppressing stdout

app = Flask(__name__)
CORS(app)

# Load model and label encoder
loaded_best_model = joblib.load("frontend/complaint_agency_bert_classifier.joblib")
loaded_le = joblib.load("frontend/label_encoder_bert.joblib")

embedder = SentenceTransformer('all-MiniLM-L6-v2')

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("description", "").strip()
        if not text:
            return jsonify({"error": "Empty description"}), 400

        # ---------------------------
        # Step 2: Suppress stray logs
        # ---------------------------
        # This ensures only JSON is returned, no TF / ST logs appear
        with contextlib.redirect_stdout(None):
            embedding = embedder.encode([text])
            pred = loaded_best_model.predict(embedding)

        dept = loaded_le.inverse_transform(pred)[0]
        return jsonify({"department": dept})

    except Exception as e:
        # Log exception on server for debugging
        print("Error during prediction:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Model and label encoder loaded successfully.")
    print("SentenceTransformer loaded successfully.")
    print("Starting server on http://127.0.0.1:5000")
    app.run(debug=True)
