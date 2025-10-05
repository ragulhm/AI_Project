import os
import json
import traceback
from flask import Flask, jsonify, request, render_template
from flask_caching import Cache
from dotenv import load_dotenv
import google.generativeai as genai

# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # or gemini-1.5-pro
CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT_SECONDS", "600"))

if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ GEMINI_API_KEY not set in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# ------------------------------------------------------------
# Flask app + caching
# ------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_mapping({
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": CACHE_TIMEOUT
})
cache = Cache(app)

# ------------------------------------------------------------
# Prompt Template
# ------------------------------------------------------------
BASE_PROMPT = """
You are an expert curriculum designer.

Create a JSON object describing a learning skill tree for the given domain.

Follow this structure exactly:

{
  "domain": "<domain name>",
  "primary_skills": [
    {
      "name": "<skill name>",
      "description": "<brief description>",
      "estimated_hours": <number>,
      "milestones": [
        {
          "name": "<milestone>",
          "target": "<goal>",
          "estimated_hours": <number>,
          "resources": [
            { "title": "<resource title>", "url": "<link>" }
          ]
        }
      ]
    }
  ]
}

Generate 5–8 primary skills, each with 3–6 milestones.
Respond ONLY with JSON. Do not include ```json fences.
"""

# ------------------------------------------------------------
# Helper: Extract text from Gemini response
# ------------------------------------------------------------
def extract_text(resp):
    """Safely extract text from Gemini response object."""
    if not resp:
        return ""
    if hasattr(resp, "text") and resp.text:
        return resp.text
    if hasattr(resp, "candidates"):
        for cand in resp.candidates:
            if cand.content and hasattr(cand.content, "parts"):
                return "".join(
                    p.text for p in cand.content.parts if hasattr(p, "text")
                )
    return ""

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")  # Make sure templates/index.html exists


@app.route("/generate_skill_tree", methods=["POST"])
def generate_skill_tree():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    # Build prompt
    prompt = BASE_PROMPT + f"\nDomain: {domain}\n"

    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 6000,
                "temperature": 0.3
            }
        )

        text = extract_text(resp).strip()
        if not text:
            raise ValueError("Gemini returned no text output (likely max tokens issue).")

        print("Raw Gemini response:", text)  # Debugging

        # ✅ Clean response (remove unwanted wrappers)
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        # ✅ Try parsing JSON
        try:
            skill_tree = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                skill_tree = json.loads(match.group(0))
            else:
                raise ValueError("Failed to extract valid JSON")

        # Cache and return response
        cache.set(domain, skill_tree)
        return jsonify(skill_tree)

    except Exception as e:
        print("Error generating skill tree:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------
# Run the Flask server
# ------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting EduPlanner Flask App...")
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
