import webbrowser
import threading
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_from_directory,
    make_response
)

import tensorflow as tf
import numpy as np
import os
import json
import sqlite3

from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename


# ================= APP =================

app = Flask(__name__)
app.secret_key = "secret123"

# ================= FOLDERS =================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "user.db"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "model",
    "best_model.h5"
)

CLASS_PATH = os.path.join(
    BASE_DIR,
    "..",
    "model",
    "class_names.json"
)

DISEASE_PATH = os.path.join(
    BASE_DIR,
    "..",
    "model",
    "disease_info.json"
)


# ================= LOAD MODEL =================

model = tf.keras.models.load_model(
    MODEL_PATH
)

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

with open(DISEASE_PATH, "r") as f:
    disease_info = json.load(f)

print(
    "Classes Loaded:",
    len(class_names)
)


# ================= DATABASE =================

def init_db():

    conn = sqlite3.connect(DB_PATH
    )

    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT DEFAULT 'default.png'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        image TEXT,
        disease TEXT,
        confidence REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ================= PREDICT FUNCTION =================

def predict_image(img_path):

    img = image.load_img(
        img_path,
        target_size=(96, 96)
    )

    img_array = image.img_to_array(img)

    img_array = img_array / 255.0

    img_array = np.expand_dims(
        img_array,
        axis=0
    )

    prediction = model.predict(
        img_array,
        verbose=0
    )

    index = np.argmax(prediction)

    label = class_names[index]

    confidence = float(
        np.max(prediction) * 100
    )

    if confidence < 60:

        return (
            "Unknown Plant",
            confidence,
            {
                "status": "Unknown",
                "description":
                "The uploaded image could not be identified confidently. Please upload a clearer image of a supported plant leaf.",
                "solution":
                "Capture the leaf in good lighting, avoid blurry images, and upload a close view of the affected area."
            }
        )

    info = disease_info.get(
        label,
        {
            "status": "Unknown",
            "description":
            "No information available.",
            "solution":
            "No treatment information available."
        }
    )

    return (
        label,
        confidence,
        info
    )


# ================= HOME =================

@app.route("/")
def home():

    user = session.get("user")

    return render_template(
        "index.html",
        user=user
    )


# ================= PREDICT =================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    file = request.files["image"]

    if file.filename == "":
        return redirect("/")

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(filepath)

    label, confidence, info = predict_image(
        filepath
    )

    # ================= CONFIDENCE LEVEL =================

    if confidence >= 90:

        confidence_level = "High"

    elif confidence >= 75:

        confidence_level = "Medium"

    else:

        confidence_level = "Low"

    # ================= DISEASE SEVERITY =================

    if "Healthy" in label:

        severity = "Healthy"

    elif confidence >= 90:

        severity = "High"

    elif confidence >= 75:

        severity = "Moderate"

    else:

        severity = "Low"

    # ================= SAVE HISTORY =================

    conn = sqlite3.connect(
        DB_PATH
    )

    c = conn.cursor()

    username = session.get(
        "user",
        "Guest"
    )

    current_date = datetime.now().strftime(
        "%d-%m-%Y %H:%M"
    )

    c.execute(
        """
        INSERT INTO history
        (
            username,
            image,
            disease,
            confidence,
            date
        )
        VALUES (?,?,?,?,?)
        """,
        (
            username,
            filename,
            label,
            confidence,
            current_date
        )
    )

    conn.commit()

    conn.close()

    return render_template(
        "result.html",
        image=filename,
        label=label.replace("_", " "),
        confidence=round(
            confidence,
            2
        ),
        confidence_level=confidence_level,
        severity=severity,
        status=info["status"],
        description=info["description"],
        solution=info["solution"]
    )

# ================= LOGIN =================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)

        c = conn.cursor()

        c.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        user = c.fetchone()

        conn.close()

        print("USER FOUND =", user)

        if user:

            print("STORED PASSWORD =", user[2])
            print("ENTERED PASSWORD =", password)

        if user and check_password_hash(
            user[2],
            password
        ):

            session["user"] = username

            return redirect("/")

        return "Invalid Username or Password"

    return render_template(
        "login.html"
    )

# ================= SIGNUP =================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        username = request.form[
            "username"
        ]

        password = request.form[
            "password"
        ]

        hashed_password = generate_password_hash(
            password
        )

        conn = sqlite3.connect(
            DB_PATH
        )

        c = conn.cursor()

        try:

            c.execute(
                """
                INSERT INTO users
                (
                    username,
                    password
                )
                VALUES (?,?)
                """,
                (
                    username,
                    hashed_password
                )
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return (
                "Username already exists"
            )

        conn.close()

        return redirect("/login")

    return render_template(
        "signup.html"
    )


# ================= HISTORY =================

@app.route("/history")
def history():

    username = session.get(
        "user"
    )

    if not username:

        return redirect(
            "/login"
        )

    conn = sqlite3.connect(
        DB_PATH
    )

    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM history
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    )

    data = c.fetchall()

    conn.close()

    return render_template(
        "history.html",
        data=data
    )


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    username = session.get("user")

    if not username:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Profile Picture
    c.execute(
    """
    SELECT profile_pic
    FROM users
    WHERE username=?
    """,
    (username,)
    )
    pic = c.fetchone()
    profile_pic = "default.png"
    if pic:
        profile_pic = pic[0]

    # Total Predictions
    c.execute("""
        SELECT COUNT(*)
        FROM history
        WHERE username=?
    """, (username,))

    total = c.fetchone()[0]

    # Healthy Plants
    c.execute("""
        SELECT COUNT(*)
        FROM history
        WHERE username=?
        AND disease LIKE '%Healthy%'
    """, (username,))

    healthy = c.fetchone()[0]

    # Diseased Plants
    diseased = total - healthy

    # Average Confidence
    c.execute("""
        SELECT AVG(confidence)
        FROM history
        WHERE username=?
    """, (username,))

    avg_confidence = c.fetchone()[0]

    if avg_confidence is None:
        avg_confidence = 0

    avg_confidence = round(avg_confidence, 2)

    # Recent Predictions
    c.execute("""
        SELECT disease,
               confidence,
               date
        FROM history
        WHERE username=?
        ORDER BY id DESC
        LIMIT 5
    """, (username,))

    recent = c.fetchall()

    conn.close()

    return render_template(
    "dashboard.html",
    total=total,
    healthy=healthy,
    diseased=diseased,
    avg_confidence=avg_confidence,
    recent=recent,
    profile_pic=profile_pic
    )

# ================= DOWNLOAD PDF REPORT =================

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

@app.route("/download_report")
def download_report():

    username = session.get("user")

    if not username:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        SELECT image,
               disease,
               confidence,
               date
        FROM history
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    )

    rows = c.fetchall()

    conn.close()

    pdf_file = "plant_detection_report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    # ================= TITLE =================

    elements.append(
        Paragraph(
            "Plant Disease Detection Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    total_predictions = len(rows)
    healthy_count = 0
    diseased_count = 0
    unknown_count = 0

    # ================= ALL PREDICTIONS =================

    for i, row in enumerate(rows, start=1):

        image_name = row[0]
        disease = row[1]
        confidence = round(row[2], 2)
        date = row[3]

        disease_name = disease.replace(
            "_",
            " "
        )

        if "Healthy" in disease:

            status = "Healthy"
            healthy_count += 1

        elif disease == "Unknown Plant":

            status = "Unknown"
            unknown_count += 1

        else:

            status = "Diseased"
            diseased_count += 1

        solution = disease_info.get(
            disease,
            {}
        ).get(
            "solution",
            "No solution available."
        )

        # ================= IMAGE =================

        image_path = os.path.join(
            UPLOAD_FOLDER,
            image_name
        )

        elements.append(
            Paragraph(
                f"<b>Prediction #{i}</b>",
                styles["Heading2"]
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        if os.path.exists(image_path):

            try:

                img = Image(
                    image_path,
                    width=200,
                    height=150
                )

                elements.append(img)

                elements.append(
                    Spacer(1, 10)
                )

            except:
                pass

        report_text = f"""
        <b>Disease Name:</b> {disease_name}<br/><br/>

        <b>Plant Status:</b> {status}<br/><br/>

        <b>Prediction Confidence:</b> {confidence}%<br/><br/>

        <b>Recommended Solution:</b> {solution}<br/><br/>

        <b>Detection Time:</b> {date}
        """

        elements.append(
            Paragraph(
                report_text,
                styles["BodyText"]
            )
        )

        elements.append(
            Spacer(1, 20)
        )

    # ================= SUMMARY =================

    elements.append(PageBreak())

    elements.append(
        Paragraph(
            "Report Summary",
            styles["Heading1"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    summary = f"""
    <b>Total Predictions:</b> {total_predictions}<br/><br/>

    <b>Healthy Plants:</b> {healthy_count}<br/><br/>

    <b>Diseased Plants:</b> {diseased_count}<br/><br/>

    <b>Unknown Predictions:</b> {unknown_count}
    """

    elements.append(
        Paragraph(
            summary,
            styles["BodyText"]
        )
    )

    doc.build(elements)

    return send_from_directory(
        os.getcwd(),
        pdf_file,
        as_attachment=True
    )

# ================= PROFILE =================

@app.route("/profile")
def profile():

    username = session.get("user")

    if not username:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        SELECT profile_pic
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    result = c.fetchone()

    profile_pic = "default.png"

    if result:
        profile_pic = result[0]

    c.execute(
        """
        SELECT COUNT(*)
        FROM history
        WHERE username=?
        """,
        (username,)
    )

    total = c.fetchone()[0]

    c.execute(
        """
        SELECT COUNT(*)
        FROM history
        WHERE username=?
        AND disease LIKE '%Healthy%'
        """,
        (username,)
    )

    healthy = c.fetchone()[0]

    diseased = total - healthy

    conn.close()

    return render_template(
        "profile.html",
        username=username,
        total=total,
        healthy=healthy,
        diseased=diseased,
        profile_pic=profile_pic
    )

# ================= UPLOAD PROFILE PIC =================

@app.route(
    "/upload_profile_pic",
    methods=["POST"]
)
def upload_profile_pic():

    username = session.get("user")

    if not username:
        return redirect("/login")

    file = request.files.get("profile_pic")

    if file and file.filename != "":

        filename = f"{username}_{secure_filename(file.filename)}"

        save_path = os.path.join(
            "static",
            "profile_pics",
            filename
        )

        file.save(save_path)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            UPDATE users
            SET profile_pic=?
            WHERE username=?
            """,
            (filename, username)
        )

        conn.commit()
        conn.close()

    return redirect("/profile")

# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.pop(
        "user",
        None
    )

    return redirect("/")


# ================= IMAGE DISPLAY =================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# ================= RUN APP =================

if __name__ == "__main__":

    threading.Timer(
        1,
        open_browser
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )