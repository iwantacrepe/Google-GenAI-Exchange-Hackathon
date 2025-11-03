from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os

from agents.summarizer_agent import summarize_file
# in future you’ll import other agents here

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("/tmp", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.secret_key = "secret_key_for_demo"

@app.route("/", methods=["GET", "POST"])
def welcome():
    if request.method == "POST":
        files = request.files.getlist("case_files")
        if not files:
            return "⚠️ Please upload at least one file."

        saved_files = []
        for file in files:
            if file.filename:
                path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
                file.save(path)
                saved_files.append(path)

        # Store in session
        session["language"] = request.form.get("language", "English")
        session["files"] = saved_files

        return redirect(url_for("dashboard"))
    return render_template("welcome.html")

@app.route("/dashboard")
def dashboard():
    summary_text, jargon_text = None, None
    language = session.get("language", "English")
    files = session.get("files", [])

    if files:
        summary_text = summarize_file(files[0], language)
        jargon_text = explain_jargons(files[0], language)

    # Pass both results to frontend
    return render_template(
        "dashboard.html",
        language=language,
        summary=summary_text,
        jargons=jargon_text,
    )

# these endpoints will later call the right agents dynamically
@app.route("/api/summarizer", methods=["POST"])
def summarizer_api():
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
    path = request.json.get("path")
    language = session.get("language", "English")
    return jsonify({"output": summarize_file(path, language)})

from agents.related_cases_agent import find_related_cases

@app.route("/api/related_cases", methods=["POST"])
def related_cases_api():
    try:
        files = session.get("files", [])
        language = session.get("language", "English")

        if not files:
            return jsonify({"output": "⚠️ No file found."})

        result = find_related_cases(files[0], language)
        return jsonify({"output": result})
    except Exception as e:
        print(f"Related Cases API error: {e}")
        return jsonify({"output": "⚠️ Failed to generate related cases."})



from agents.jargons_agent import explain_jargons

@app.route("/api/jargons", methods=["POST"])
def jargon_api():
    files = session.get("files", [])
    language = session.get("language", "English")

    if not files:
        return jsonify({"output": "⚠️ No file uploaded."})

    jargons_md = explain_jargons(files[0], language)
    return jsonify({"output": jargons_md})



from agents.thinker_agent import chat_with_thinker

@app.route("/api/thinker_chat", methods=["POST"])
def thinker_chat():
    data = request.get_json()
    history = data.get("history", [])
    language = session.get("language", "English")
    history = session.get("thinker_history", [])
    session["thinker_history"] = history
    files = session.get("files", [])

    reply = chat_with_thinker(history, language=language, files=files)
    return jsonify({"reply": reply})


from agents.timeline_agent import extract_timeline

@app.route("/api/timeline", methods=["POST"])
def timeline_api():
    try:
        files = session.get("files", [])
        language = session.get("language", "English")

        if not files:
            print("⚠️ No files found in session.")
            return jsonify({"output": "[]"})
        
        file_path = files[0]
        print(f"🕒 Timeline agent started for file: {file_path}")
        output = extract_timeline(files[0], language)
        return jsonify({"output": output})
    except Exception as e:
        print(f"Timeline API error: {e}")
        return jsonify({"output": "[]"})

from agents.graph_agent import build_graph_from_document

@app.route("/api/graph", methods=["POST"])
def graph_api():
    language = session.get("language", "English")
    files = session.get("files", [])
    if not files:
        return jsonify({"output": "⚠️ No file found in session."})
    result = build_graph_from_document(files[0], language)
    return jsonify({"output": result})

@app.route("/healthz")
def healthz():
    """Simple health check for Azure container probes."""
    return "OK", 200

if __name__ == "__main__":
    print(" Flask app starting on port 80...")
    app.run(host="0.0.0.0", port=80, debug=True)
