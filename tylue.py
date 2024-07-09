from flask import Flask, request, send_from_directory, render_template, abort , jsonify
import os
from werkzeug.utils import secure_filename
import pdf_processing
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import re
import requests
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PDF_OUTPUT_FOLDER'] = 'pdf_outputs/'
app.config['DOWNLOAD_FOLDER'] = 'download/'
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            original_filename = file.filename  # Keep the original filename
            filename = secure_filename(original_filename)  # Sanitize for secure file handling
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
              
            # Regex to extract invoice number
            match = re.search(r'Счет на оплату № (\d+)', original_filename)
            if match:
                invoice_number = f"Счет на оплату № {match.group(1)}"
            else:
                invoice_number = "UnknownInvoice Number"
                print("No invoice number found in filename.") 
                
            with open(file_path, 'rb') as file_stream:
                # Pass the extracted invoice number to the processing function if needed
                processed_tables = pdf_processing.process_pdf_file(file_stream, filename, invoice_number)
                if processed_tables:
                    csv_paths = pdf_processing.save_tables_to_csv(processed_tables, app.config['UPLOAD_FOLDER'], "output_table")
                    all_data = []
                    for csv_path in csv_paths:
                        data = pd.read_csv(csv_path)
                        all_data.append((data.to_html(classes='table table-striped', index=False), csv_path))
                    
                    return render_template('show_tables1.html', tables=all_data, invoice_number=filename)
                else:
                    return "Failed to process PDF file.", 400
        else:
            return render_template('upload.html', message="No file uploaded or file is invalid.")
    return render_template('upload.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    csv_paths = request.form.getlist('csv_paths')
    pdf_files = []
    for csv_path in csv_paths:
        data = pd.read_csv(csv_path)
        for index, item in data.iterrows():
            pdf_path = pdf_processing.create_pdf(item, index, app.config['PDF_OUTPUT_FOLDER'])
            pdf_files.append(pdf_path)
    merged_pdf_path = pdf_processing.merge_pdfs(pdf_files, os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'Combined_Document.pdf'))
    return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'Combined_Document.pdf', as_attachment=True)

@app.route('/generate-labels', methods=['POST'])
def generate_labels():
    csv_paths = request.form.getlist('csv_paths')
    image_files = []

    # Generate labels for each CSV and collect all image paths
    for csv_path in csv_paths:
        # Ensure the path is correctly assembled
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_path) if not csv_path.startswith(app.config['UPLOAD_FOLDER']) else csv_path
        try:
            data = pd.read_csv(full_path)  # Read the CSV from the correct path
            image_files.extend(create_labels(data, full_path))  # Call create_labels with correct data
        except Exception as e:
            print(f"Failed to read or process CSV at {full_path}: {e}")
            continue  # Optionally skip to the next file or handle the error differently

    # Combine all images into a single PDF if there are any images
    if image_files:
        pdf_filename = os.path.join(app.config['PDF_OUTPUT_FOLDER'], 'output_labels.pdf')
        combine_images_to_pdf(image_files, pdf_filename)
        return send_from_directory(app.config['PDF_OUTPUT_FOLDER'], 'output_labels.pdf', as_attachment=True)
    else:
        return "No images were created from the provided CSVs.", 400

def create_labels(data, pdf_filename):
    dpi = 300
    width_mm = 58
    height_mm = 40
    width = int(width_mm * dpi / 25.4)
    height = int(height_mm * dpi / 25.4)
    image_files = []

    for index, row in data.iterrows():
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        # ... (rest of the drawing logic here)
            # Optional: Create a light grid
        for x in range(0, img.width, int(dpi / 25.4)):  # Grid every 1mm
            draw.line([(x, 0), (x, img.height)], fill="#eeeeee")
        for y in range(0, img.height, int(dpi / 25.4)):
            draw.line([(0, y), (img.width, y)], fill="#eeeeee")

        # Load fonts
        try:
            font_regular = ImageFont.truetype("arial.ttf", int(dpi / 12.7))
            font_bold = ImageFont.truetype("arialbd.ttf", int(dpi / 12.7))
            font_small = ImageFont.truetype("arial.ttf", int(dpi / 24.7))
        except IOError:
            font_regular = ImageFont.load_default()
            font_bold = font_regular  # Fallback to default if not found
            font_small = ImageFont.load_default()

        # Draw data
        product_code = row['Товары (работы, услуги)']
        manufacturer = "Промышленная \nФурнитура и Тара"
        standard = row['ГОСТ/ОСТ Info']
        quantity = row['Количество']

        # Draw hardcoded titles in bold
        #draw.text((5, 5), "Продукт:", fill="black", font=font_bold)
        draw.text((10, 90), "Изготовитель:", fill="black", font=font_bold)
        draw.text((400, 90), "Стандарт:", fill="black", font=font_bold)
        draw.text((400, 185), "Количество:", fill="black", font=font_bold)

        # Draw data from CSV in regular font
        draw.text((10, 10), product_code, fill="black", font=font_bold)
        draw.text((10, 125), manufacturer, fill="black", font=font_regular)
        draw.text((400, 125), standard, fill="black", font=font_regular)
        draw.text((400, 215), f"{quantity} шт", fill="black", font=font_regular)
        draw.text((60,300),"198207, Санкт-Петербург, Трамвайный пр-т, 6 +7 (812) 983-70-83 metgost.ru zakaz@metgost.ru",fill="black",font=font_small)
           
        # Rectangle to highlight the area (optional)
        shape = [(30, 290), (width - 30, height - 175)]
        draw.rectangle(shape, fill="black", outline="black") 

        # Rectangle to highlight the area (optional)
        shape1 = [(330, 90), (width - 349, height - 180)]
        draw.rectangle(shape1, fill="black", outline="black") 

        # Rectangle to highlight the area (optional)
        shape1 = [(330, 45), (width - 349, height - 180)]
        draw.rectangle(shape1, fill="black", outline="black") 

        # Load and paste the barcode, resized to fit
        barcode_img = Image.open(r"C:\Users\User\Documents\fatality\barcode.gif")
        barcode_width, barcode_height = barcode_img.size
        scale_factor = min((width - 10) / barcode_width, (height - 70) / barcode_height)
        barcode_img = barcode_img.resize((int(barcode_width * scale_factor), int(barcode_height * scale_factor)))
        img.paste(barcode_img, (5, 325))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'output_label_{index}.png')
        img.save(image_path)
        image_files.append(image_path)
    return image_files

from PIL import Image

def combine_images_to_pdf(image_files, pdf_filename):
    if not image_files:
        print("No images to process.")
        return None

    print(f"Combining {len(image_files)} images into {pdf_filename}")
    try:
        with Image.open(image_files[0]) as first_image:
            first_image = first_image.convert('RGB')  # Ensure the image is in RGB
            subsequent_images = [Image.open(img).convert('RGB') for img in image_files[1:]]
            first_image.save(pdf_filename, save_all=True, append_images=subsequent_images, resolution=300)
            print("PDF created successfully.")
    except Exception as e:
        print(f"Failed to create PDF: {e}")

    # Close all opened images to prevent resource leakage
    for img in subsequent_images:
        img.close()

    return pdf_filename

def get_info(product_id, path="172.16.0.40:40"):
    
    if not product_id:
        return None  # Return None or raise an exception if no product_id is provided
    try:
        get_item_info = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        response = requests.get(get_item_info)
        item_json = response.content.decode('utf-8')
        item_data = json.loads(item_json)
        item_id, item_tool, item_quantity, item_contract = item_data

        #get_item_info_url = f'http://{path}/api/product-items/{product_id}/get_item_info/'
        #response = requests.get(get_item_info_url)
        #item_json = response.content.decode('utf-8')
        #response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        #item_data = response.json()  # Directly parse JSON from response
        
        return item_data
    except requests.RequestException as e:
        print(f"Error fetching product info: {e}")
        return None


@app.route('/product/<int:product_id>')
def product_label(product_id):
    product_data = get_info(product_id)
    if product_data is None:
        return jsonify({'error': 'Failed to retrieve product data'}), 500

    # Assuming product_data contains all required fields
    image_file = create_label_for_product(product_data)
    if image_file:
        return send_from_directory(app.config['UPLOAD_FOLDER'], image_file, as_attachment=True)
    else:
        return jsonify({'error': 'Failed to create label'}), 500
        
def create_label_for_product(data):
    dpi = 300
    width_mm = 58
    height_mm = 40
    width = int(width_mm * dpi / 25.4)
    height = int(height_mm * dpi / 25.4)

    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Fonts and drawing logic, using data directly
    font_bold = ImageFont.truetype("arialbd.ttf", int(dpi / 12.7))
    font_regular = ImageFont.load_default()

    item_id,  item_tool, item_quantity, item_contract = data

    

    draw.text((10, 10),item_id, fill="black", font=font_bold)
    draw.text((10, 125),item_tool, fill="black", font=font_regular)
    draw.text((400, 125),item_quantity, fill="black", font=font_regular)
    draw.text((400, 215), item_contract , fill="black", font=font_regular)

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_label.png')
    img.save(image_path)
    return image_path
        
@app.route('/download/csv/<path:filename>')
def download_csv(filename):
    # Ensure the path is safe to use
    directory = app.config['DOWNLOAD_FOLDER']  
    safe_filename = secure_filename(filename)
    try:
        return send_from_directory(directory, safe_filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)  # If the file is not found, return 404 error

if __name__ == '__main__':
    app.run(debug=True)
