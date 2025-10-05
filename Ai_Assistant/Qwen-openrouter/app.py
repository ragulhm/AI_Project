import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI, APIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
MODEL_NAME = 'qwen/qwen3-235b-a22b:free' # Already updated by user
MAX_MESSAGE_LENGTH = 8000 # Already updated by user

class AIAssistant:
    """Handles interaction with the qwen3-235b-a22b:free model via OpenRouter (using OpenAI SDK)."""
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

    def generate_response(self, user_message: str) -> str:
        """Sends a message to the AI and returns the response."""
        try:
            # Call the chat completions endpoint (syntax is the same as OpenRouter/OpenAI)
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    # --- EDITED SYSTEM PROMPT FOR COMPLEXITY ---
                    {"role": "system", "content": "You are a highly professional, expert-level AI assistant. When asked a complex question, provide a detailed, well-structured, and comprehensive answer, using markdown for formatting, headings, and lists where appropriate."},
                    # -------------------------------------------
                    {"role": "user", "content": user_message}
                ],
                # --- EDITED TEMPERATURE FOR CREATIVE/COMPLEX ANSWERS ---
                temperature=0.9 # Higher temperature encourages more diverse and detailed responses
                # --------------------------------------------------------
            )

            # Extract the content from the response
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                return "The AI returned an empty response."

        except APIError as e:
            # OpenAI APIError uses status_code instead of code
            print(f"OpenRouter API Error: {e}")
            return f"Error: Failed to get response from AI. Details: HTTP {e.status_code}"
        except Exception as e:
            # Handle other potential errors (e.g., network issues)
            print(f"General Error during AI request: {e}")
            return "An unexpected error occurred while communicating with the AI service."

# --- Flask Application Setup ---
app = Flask(__name__)
# The assistant is initialized here, loading the API key
assistant = AIAssistant()

@app.route('/')
def index():
    """Renders the main chat interface."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint to handle chat messages."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        # 1. Input Validation and Sanitization (Protect against large inputs)
        if not user_message:
            return jsonify({'response': 'Please enter a message.'}), 400
        
        if len(user_message) > MAX_MESSAGE_LENGTH:
            return jsonify({'response': f'Message exceeds the maximum length of {MAX_MESSAGE_LENGTH} characters.'}), 400

        # 2. Generate AI Response
        ai_response = assistant.generate_response(user_message)
        
        # 3. Secure and Efficient Response
        return jsonify({'response': ai_response})

    except Exception as e:
        # Catch unexpected errors during request processing
        print(f"Request processing error: {e}")
        return jsonify({'response': 'Internal Server Error. Please try again.'}), 500

if __name__ == '__main__':
    # WARNING: Do not use debug=True in production. 
    # Use gunicorn as recommended in the deployment section.
    app.run(debug=True, port=7000)