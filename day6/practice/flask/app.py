from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Flask!"

@app.route("/greet", methods=["GET"])
def greet():
    return "Send me a POST with your name!"

@app.route("/greet", methods=["POST"])
def greet_post():
    return "Thanks, got your POST."

@app.route("/square/<int:n>")
def square(n):
    return str(n * n)

@app.route("/greet/<name>")
def greet_name(name):
    return f"Hello, {name}!"

@app.route("/search")
def search():
    # GET /search?q=vulkan&limit=5
    query = request.args.get("q", "")
    limit = request.args.get("limit", 10, type=int)
    return f"Searching for '{query}', limit={limit}"

@app.route("/vector/dot", methods=["POST"])
def dot_product():
    data = request.get_json()
    a, b = data["a"], data["b"]
    result = sum(x * y for x, y in zip(a, b))
    return jsonify({"result": result})

scene_objects = []   # list of dicts — gone on restart
next_id = 1

@app.route("/objects", methods=["GET"])
def list_objects():
    return jsonify(scene_objects)

@app.route("/objects", methods=["POST"])
def add_object():
    global next_id
    data = request.get_json()
    obj = {"id": next_id, "name": data["name"], "position": data.get("position", [0, 0, 0])}
    scene_objects.append(obj)
    next_id += 1
    return jsonify(obj), 201          # 201 Created

@app.route("/objects/<int:obj_id>", methods=["DELETE"])
def delete_object(obj_id):
    global scene_objects
    scene_objects = [o for o in scene_objects if o["id"] != obj_id]
    return jsonify({"status": "deleted"})

@app.route("/objects/<int:obj_id>", methods=["GET"])
def get_object(obj_id):
    for obj in scene_objects:
        if obj["id"] == obj_id:
            return jsonify(obj)
    return jsonify({"error": "not found"}), 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "That route doesn't exist"}), 404


if __name__ == "__main__":
    app.run(debug=True)    