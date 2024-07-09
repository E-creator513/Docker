from flask import Flask, request, render_template_string, send_file, redirect, url_for, Response
import requests
import json
import uuid
from tabulate import tabulate
import pdfkit

app = Flask(__name__)

def get_info(product_id, path="172.16.0.40:40"):
    if product_id:
        get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        response = requests.get(get_item_info)
        if response.status_code == 200:
            item_json = response.content.decode('utf-8')
            item_data = json.loads(item_json)
            # Append a unique code to each item's data
            item_data.append(str(uuid.uuid4()))
            return item_data
        else:
            return ["Error", "Could not retrieve data", "", "", ""]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        if product_id:
            product_info = get_info(product_id)
            headers = ["Product ID", "Product Tool", "Quantity", "Contract", "Unique Code"]
            if type(product_info[0]) is not list:
                product_info = [product_info]
            table = tabulate(product_info, headers=headers, tablefmt='html')
            return render_template_string('''
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        form {
                            margin-bottom: 20px;
                        }
                        input, button {
                            padding: 10px;
                            font-size: 16px;
                            margin: 5px;
                        }
                        table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        th, td {
                            padding: 10px;
                            border: 1px solid #ccc;
                            text-align: left;
                        }
                    </style>
                </head>
                <body>
                    <h1>Product Information</h1>
                    <form method="post">
                        <input type="text" name="product_id" placeholder="Enter Product ID" required>
                        <button type="submit">Submit</button>
                    </form>
                    {{ table|safe }}
                    <form method="post" action="/generate-pdf">
                        <input type="hidden" name="html_table" value="{{ table }}">
                        <button type="submit">Generate PDF</button>
                    </form>
                </body>
                </html>
            ''', table=table)
    return render_template_string('''
        <html>
        <body>
            <h1>Product Information</h1>
            <form method="post">
                <input type="text" name="product_id" placeholder="Enter Product ID" required>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    html_table = request.form.get('html_table')
    if html_table:
        pdf = pdfkit.from_string(html_table, False)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=product_info.pdf'
        return response
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
