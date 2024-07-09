import requests
import json
from tabulate import tabulate

def get_info(product_id, path="172.16.0.40:40"):
    if product_id:
        get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        response = requests.get(get_item_info)
        if response.status_code == 200:
            item_json = response.content.decode('utf-8')
            item_data = json.loads(item_json)
            return item_data  # Directly returning the list containing product details
        else:
            return ["Error", "Could not retrieve data", "", ""]

while True:
    product_id = input('Enter Product ID (or "quit" to exit): ')
    if product_id.lower() == "quit":
        break
    product_info = get_info(product_id)
    headers = ["Product ID", "Product Tool", "Quantity", "Contract"]
    # Ensure product_info is a list of lists even if there's only one item
    if type(product_info[0]) is not list:
        product_info = [product_info]
    print(tabulate(product_info, headers=headers, tablefmt='grid'))
