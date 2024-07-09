from flask import Flask, jsonify, request
import requests
import json

app = Flask(__name__)

# Define route with product_id as a URL parameter
@app.route('/info/<product_id>')
def get_info(product_id):
    path = "172.16.0.40:40"  # Define the path as a constant or make it configurable
    get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
    try:
        response = requests.get(get_item_info)
        if response.status_code == 200:
            # Use the built-in .json() method to decode the JSON response
            return jsonify(response.json())
        else:
            return jsonify({"error": "Could not retrieve data"}), 404
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
