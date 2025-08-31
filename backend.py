from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, uuid, requests, base64

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

class TempData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input = db.Column(db.String(400), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    shared = db.Column(db.Boolean, default=False)
    filepath = db.Column(db.String(255), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)  # store image as BLOB

with app.app_context():
    db.create_all()

# absolute path to the app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# this guarantees the correct static folder
IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "generated_images")
os.makedirs(IMAGE_FOLDER, exist_ok=True)



AI_SERVER = "http://192.168.1.127:5000"  # replace with your AI server IP
@app.route('/')
def home():
    return render_template('main.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    prompt = request.form.get("prompt")
    if not prompt:
        return render_template("main.html", filepath=None, prompt="")

    # Call AI server to generate image
    response = requests.post(f"{AI_SERVER}/generate", json={"prompt": prompt})
    if response.status_code != 200:
        return render_template("main.html", filepath=None, prompt=prompt, error="AI server error")

    data = response.json()
    image_b64 = data.get("image_base64")
    image_bytes = base64.b64decode(image_b64)

    # Optionally save to static folder (so frontend can render via path if needed)
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    #use static path for browser
    web_path = f"/static/generated_images/{filename}"

    #relative_path = os.path.join("generated_images", filename)
    temp = TempData(input=prompt, filepath=web_path, image_data=image_bytes)
    db.session.add(temp)
    db.session.commit()

    # Render HTML
    return render_template("main.html", filepath=web_path, prompt=prompt)

@app.route('/gallery')
def gallery():
    items = TempData.query.filter_by(shared=True).all()
    return render_template("gallery.html", items=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
    

 
 