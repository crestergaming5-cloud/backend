from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend running"

print("Server starting...")

if __name__ == "__main__":
    app.run(debug=True)