
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, base64, requests
from urllib.parse import quote

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

class TempData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input = db.Column(db.String(400), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    shared = db.Column(db.Boolean, default=False)
    # filepath / image_data columns removed — images are never persisted

with app.app_context():
    db.create_all()

# Free, no-signup image generation API — good for experimenting
POLLINATIONS_URL = "https://gen.pollinations.ai/image/"

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    prompt = request.form.get("prompt")
    if not prompt:
        return render_template("main.html", filepath=None, prompt="")

    image_url = f"{POLLINATIONS_URL}{quote(prompt)}?nologo=true"

    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
    except requests.RequestException:
        return render_template("main.html", filepath=None, prompt=prompt, error="AI server error")

    # Encode directly to base64 and hand it to the template — nothing touches disk or the DB
    image_b64 = base64.b64encode(response.content).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{image_b64}"

    # Optional: logs just the prompt text (no image), purely for your own curiosity.
    # Delete these 3 lines if you want zero DB writes at all.
    temp = TempData(input=prompt)
    db.session.add(temp)
    db.session.commit()

    return render_template("main.html", filepath=data_uri, prompt=prompt)

@app.route('/gallery')
def gallery():
    items = TempData.query.filter_by(shared=True).all()
    return render_template("gallery.html", items=items)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
