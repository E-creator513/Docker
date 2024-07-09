from flask import Flask, request, render_template_string
import requests
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'path/to/upload'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product_data = get_info(product_id)
        if isinstance(product_data, dict):  # Checking if the returned data is a dictionary
            return render_template_string(MAIN_PAGE, product_info=product_data, product_id=product_id)
        else:
            return render_template_string(MAIN_PAGE, error=product_data)
    return render_template_string(MAIN_PAGE)

def get_info(product_id, path="172.16.0.40:40"):
    if product_id:
        get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        try:
            response = requests.get(get_item_info, timeout=5)
            if response.status_code == 200:
                try:
                    item_data = response.json()  # directly use .json() method
                    return item_data
                except json.JSONDecodeError:
                    return "Error: Received non-JSON response"
            else:
                return f"Error: Server responded with status code {response.status_code}"
        except requests.RequestException as e:
            return f"Request Error: {str(e)}"


MAIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <title>Product Info Fetcher</title>
</head>
<body>
  <h1>Product Information Fetcher</h1>
  <form method="post">
    <label for="product_id">Enter Product ID:</label>
    <input type="text" id="product_id" name="product_id" required>
    <button type="submit">Fetch Information</button>
  </form>
  {% if product_info %}
    <h2>Results for Product ID: {{ product_id }}</h2>
    <table border="1">
      {% if product_info is mapping %}
        <tr>
          {% for key in product_info.keys() %}
          <th>{{ key }}</th>
          {% endfor %}
        </tr>
        <tr>
          {% for value in product_info.values() %}
          <td>{{ value }}</td>
          {% endfor %}
        </tr>
      {% elif product_info is iterable and product_info is not string %}
        {% for item in product_info %}
          {% if loop.first %}
            <tr>
              {% for key in item.keys() %}
              <th>{{ key }}</th>
              {% endfor %}
            </tr>
          {% endif %}
          <tr>
            {% for value in item.values() %}
            <td>{{ value }}</td>
            {% endfor %}
          </tr>
        {% endfor %}
      {% else %}
        <tr><td>{{ product_info }}</td></tr>
      {% endif %}
    </table>
  {% elif error %}
    <h2>Error</h2>
    <p>{{ error }}</p>
  {% endif %}
</body>
</html>

"""

if __name__ == '__main__':
    app.run(debug=True)
