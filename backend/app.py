from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import asyncio
import edge_tts

app = Flask(__name__)
CORS(app)

# Async function voice generate karne ke liye
async def generate_edge_voice(text, voice_name):
    communicate = edge_tts.Communicate(text, voice_name)
    fp = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            fp.write(chunk["data"])
    fp.seek(0)
    return fp

@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.json or {}
        text = data.get("text", "").strip()
        voice = data.get("voice", "") 

        if not text:
            return jsonify({"error": "Text is required"}), 400
        if not voice:
            return jsonify({"error": "Voice is required"}), 400

        # Serverless friendly tareeqa event loop chalane ka
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        audio_fp = loop.run_until_complete(generate_edge_voice(text, voice))

        return send_file(
            audio_fp, 
            mimetype="audio/mpeg", 
            as_attachment=True, 
            download_name="premium_edge_voice.mp3"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return jsonify({"status": "Edge-TTS VIP API running"})

# Vercel ko server instance batane ke liye
app.index = lambda: "Backend is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)