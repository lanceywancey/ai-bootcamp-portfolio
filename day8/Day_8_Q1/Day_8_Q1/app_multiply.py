from flask import Flask
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    r1 = subprocess.check_output(["./multiply", "3", "4"], text=True).strip()
    r2 = subprocess.check_output(["./multiply", "5", "6"], text=True).strip()
    total = int(r1) + int(r2)

    return f"""
    <h1>AI Review CI/CD Demo</h1>
    <p>C++ result 1: 3 × 4 = {r1}</p>
    <p>C++ result 2: 5 × 6 = {r2}</p>
    <p>Python sum: {r1} + {r2} = {total}</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)