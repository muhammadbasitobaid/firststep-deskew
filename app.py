from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
import cv2
import numpy as np
import os
import io
from datetime import datetime
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

def generate_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return f"{timestamp}_{random_number}.jpg"

def save_and_resize_image(file, max_dim=1000):
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    height, width = img.shape[:2]

    if max(height, width) > max_dim:
        if height > width:
            new_height = max_dim
            new_width = int(max_dim * (width / height))
        else:
            new_width = max_dim
            new_height = int(max_dim * (height / width))
        img = cv2.resize(img, (new_width, new_height))

    if len(img.shape) == 2 or img.shape[2] == 1:  # Convert to 3 channels if not already
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    filename = generate_filename()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv2.imwrite(filepath, img)
    return filepath

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        img_path = save_and_resize_image(file)
        web_img_path = img_path.replace('\\', '/')
        return render_template('select_points.html', img_path=web_img_path)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename.split("\\")[-1])

@app.route('/outputs/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename.split("\\")[-1])

import traceback
import logging

@app.route('/deskew', methods=['POST'])
def deskew():
    try:
        points = request.form.getlist('points')
        points = np.array([list(map(float, p.split(','))) for p in points], dtype='float32')

        img_path = request.form['img_path'].replace('/', os.sep)

        img_filename = os.path.basename(img_path)
        local_img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
        img = cv2.imread(local_img_path)

        if img is None:
            raise ValueError(f"Error loading image from {local_img_path}")

        img_height, img_width = img.shape[:2]  # Original image dimensions

        # Calculate average width and height based on the selected points
        avg_width = int(np.mean([points[1][0] - points[0][0], points[2][0] - points[3][0]]))
        avg_height = int(np.mean([points[3][1] - points[0][1], points[2][1] - points[1][1]]))

        dst_points = np.float32([[0, 0], [avg_width, 0], [avg_width, avg_height], [0, avg_height]])

        if points.shape != (4, 2) or dst_points.shape != (4, 2):
            raise ValueError("Invalid points shape")

        # Perform the perspective transformation
        M = cv2.getPerspectiveTransform(points, dst_points)
        deskewed_img = cv2.warpPerspective(img, M, (avg_width, avg_height))

        # Calculate padding to match the original image dimensions
        pad_top = (img_height - avg_height) // 2
        pad_bottom = img_height - avg_height - pad_top
        pad_left = (img_width - avg_width) // 2
        pad_right = img_width - avg_width - pad_left

        # Apply padding to the deskewed image
        deskewed_img = cv2.copyMakeBorder(deskewed_img, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[255, 255, 255])

        output_folder = app.config['OUTPUT_FOLDER']
        os.makedirs(output_folder, exist_ok=True)
        deskewed_filename = f"{os.path.splitext(img_filename)[0]}_deskew.jpg"
        deskewed_img_path = os.path.join(output_folder, deskewed_filename)
        cv2.imwrite(deskewed_img_path, deskewed_img)

        web_img_path = deskewed_img_path.replace('\\', '/')

        return render_template('select_points.html', img_path=request.form['img_path'], deskewed_img_path=web_img_path)

    except Exception as e:
        logging.error(f"Error during deskew: {e}")
        traceback.print_exc()
        return render_template('select_points.html', img_path=request.form['img_path'], error_message="Error with deskew. Please upload again.")




if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5005)
