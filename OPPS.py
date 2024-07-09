from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Serve the HTML page with AJAX JavaScript
    return render_template('index.html')

@app.route('/get-product-info', methods=['GET'])
def get_product_info():
    product_id = request.args.get('product_id')
    if product_id:
        # Simulate database access or external API call
        product_data = {
            "Product ID": product_id,
            "Product Tool": item_data,
            "Quantity": "100",
            "Contract": "Contract XYZ"
        }
        return jsonify(product_data)
    return jsonify({"error": "Product ID not provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
