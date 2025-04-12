from flask import Flask, request, jsonify
import openai
import os
from dotenv import load_dotenv
import json
import time

# Load your .env variables
load_dotenv()

#print("🔍 OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
#print("🔍 ASSISTANT_ID:", os.getenv("ASSISTANT_ID"))

# Set OpenAI API key and Assistant ID
openai.api_key = os.getenv("OPENAI_API_KEY")  # ✅ Reads from Render or .env

ASSISTANT_ID = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

# Your custom function: message generator
def generate_message(tone, context):
    if tone == "playful":
        return f"Hey 😄 Just wanted to say... I kinda like you. Like, more-than-friends like you. No pressure tho!"
    elif tone == "serious":
        return f"I've been holding back some feelings because I value our friendship. But I need to be honest: I’ve started seeing you as more than a friend."
    elif tone == "poetic":
        return f"In the quiet between our laughter, I realized my heart had quietly fallen for you."
    else:
        return f"I think I’m falling for you, but I don’t want to mess things up. Just wanted to be honest."

@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message", "")

    # 1. Create a new thread
    thread = openai.beta.threads.create()

    # 2. Add user message
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # 3. Run the assistant
    run = openai.beta.threads.runs.create(
        assistant_id=ASSISTANT_ID,
        thread_id=thread.id
    )

    # 4. Wait for the assistant to respond
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            result = generate_message(args["tone"], args["context"])

            openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool_call.id,
                        "output": result
                    }
                ]
            )
        else:
            time.sleep(1)

    # 5. Get the final response
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    final_response = messages.data[0].content[0].text.value

    return jsonify({"response": final_response})

@app.route("/", methods=["GET"])
def index():
    return """
        <html>
            <head><title>Love Assistant</title></head>
            <body>
                <h1>💖 The Love Assistant is Live!</h1>
                <p>Send a POST request to <code>/ask</code> with your message to begin.</p>
            </body>
        </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
