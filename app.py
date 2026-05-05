from flask import Flask, request, jsonify
import secrets, redis
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os, time

load_dotenv(dotenv_path=".env")

print("REDIS:", os.getenv("REDIS_URL"))
r = redis.from_url(os.getenv("REDIS_URL"))

app = Flask(__name__)

def make_code(length):
        code = ""
        for _ in range(length):
         code += str(secrets.randbelow(10))
        return code

def is_valid_email(email):
    return email and "@" in email and "." in email

@app.route("/generate_code", methods=["POST"])
def generate_code():
    data = request.json
    email_input = data.get("email")
    if not is_valid_email(email_input):
        return jsonify({"error": "invalid email"}), 400
    code = make_code(6)
    stored_code = r.get(email_input)
    if stored_code:
        return jsonify({"error": "code already sent"}), 429

    r.setex(email_input, 300, code)

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = email_input
    html = f"""
    <h1 style="color:#4f46e5;">Guardian</h1>
    <p>Your verification code:</p>

    <div style="
        font-size:28px;
        font-weight:bold;
        letter-spacing:6px;
        color:#111;
        background:#f3f4f6;
        padding:10px 20px;
        display:inline-block;
        border-radius:8px;
    ">
    {code}
    </div>

    <p style="color:#6b7280;">This code expires in 5 minutes.</p>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = "Verification Code"
    msg["From"] = sender
    msg["To"] = receiver
    error = False

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    
        return jsonify({"status": "sent"}), 200
    
    except Exception as e:
        r.delete(email_input)
        return jsonify({"error": str(e)}), 500
        
@app.route("/verify_code", methods=["POST"])
def verify_code():
    data = request.json
    email_input = data.get("email")
    sent_code = data.get("code")
    stored_code = r.get(email_input)
    if stored_code:
        stored_code = stored_code.decode("utf-8")
        if stored_code == sent_code:
            return jsonify("Verified succesfully")
        else:
            return jsonify("error")
    else:
        return jsonify("error")
    
print("Server starting...")

if __name__ == "__main__":
    app.run()
