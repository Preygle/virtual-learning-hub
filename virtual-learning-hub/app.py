from flask import Flask, render_template, request, jsonify
from google.cloud import storage
from werkzeug.utils import secure_filename
import datetime
import os
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

logging.basicConfig(level=logging.INFO)

BUCKET_NAME = "23bce1746_vlh"
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    bucket.reload()
    logging.info(f"Successfully connected to GCS bucket: {BUCKET_NAME}")
except Exception as e:
    logging.error(f"Failed to connect to GCS bucket '{BUCKET_NAME}'. Check bucket name and credentials/permissions. Error: {e}")
    bucket = None

@app.route('/')
def home():
    return render_template('studysphere.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/about')
def about_page():
    return render_template('about_us.html')

@app.route('/contact')
def contact_page():
    return render_template('contact_us.html')
@app.route('/organized-notes')
def organized_notes():
    return render_template('storage.html')

@app.route('/todo-list')
def todo_list():
    return render_template('todo_list.html')

@app.route('/online-courses')
def online_courses():
    return render_template('courses.html')

@app.route('/online-tools')
def online_tools():
    return render_template('useful_tools.html')

@app.route('/storage')
def storage_page():
    return render_template('storage.html')

@app.route('/list-files')
def list_files():
    if not bucket:
        return jsonify({"error": "GCS Bucket not configured or accessible"}), 500

    blobs = bucket.list_blobs()
    files = []
    folders = set()
    for blob in blobs:
        files.append(blob.name)
        if '/' in blob.name:
            folders.add(blob.name.split('/')[0])

    distinct_folders = sorted(list(folders))
    return jsonify({'files': sorted(files), 'folders': distinct_folders})

@app.route('/create-folder', methods=['POST'])
def create_folder():
    if not bucket:
        return jsonify({"error": "GCS Bucket not configured or accessible"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    folder_name = data.get('folder')
    if not folder_name or '/' in folder_name.strip('/'):
        return jsonify({"error": "Valid folder name required (no slashes allowed for top-level folder)"}), 400

    folder_path = f"{folder_name.strip()}/"
    blob = bucket.blob(folder_path)

    if blob.exists():
        return jsonify({"message": f"Folder '{folder_name}' already exists or an object conflicts"}), 200

    try:
        blob.upload_from_string('', content_type='application/x-directory')
        logging.info(f"Created folder object: {folder_path}")
        return jsonify({"message": f"Folder '{folder_name}' created successfully"}), 201
    except Exception as e:
        logging.error(f"Error creating folder '{folder_name}': {e}")
        return jsonify({"error": f"Failed to create folder: {e}"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if not bucket:
        return jsonify({"error": "GCS Bucket not configured or accessible"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    folder = request.form.get('folder')

    if not folder:
        return jsonify({"error": "No folder specified"}), 400

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        folder_prefix = folder.strip('/')
        if folder_prefix:
             object_name = f"{folder_prefix}/{filename}"
        else:
             object_name = filename

        blob = bucket.blob(object_name)

        try:
            blob.upload_from_file(file.stream, content_type=file.content_type)
            logging.info(f"File {filename} uploaded to {object_name}.")
            return jsonify({"message": f"File '{filename}' uploaded successfully to folder '{folder}'"}), 200
        except Exception as e:
            logging.error(f"Error uploading file '{filename}' to '{object_name}': {e}")
            return jsonify({"error": f"Failed to upload file: {e}"}), 500

    return jsonify({"error": "Missing file or folder information"}), 400

import logging 

@app.route('/download')

@app.route('/delete-file', methods=['DELETE'])
def delete_file():
    if not bucket:
        return jsonify({"error": "GCS Bucket not configured or accessible"}), 500
    file_name = request.args.get('file')
    if not file_name:
        return jsonify({"error": "File name query parameter required"}), 400

    blob = bucket.blob(file_name)

    if not blob.exists():
         logging.warning(f"Delete request for non-existent file: {file_name}")
         return jsonify({"message": f"File '{file_name}' does not exist or already deleted"}), 200

    try:
        blob.delete()
        logging.info(f"File {file_name} deleted.")
        return jsonify({"message": f"File '{file_name}' deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting file '{file_name}': {e}")
        return jsonify({"error": f"Failed to delete file: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
