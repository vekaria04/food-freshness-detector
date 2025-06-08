from flask import Flask, render_template, request
import os
import cv2
from freshness import analyze_freshness

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('image')

        print("DEBUG: file received =", bool(file))
        if not file or file.filename == '':
            print("DEBUG: No file selected")
            return render_template('index.html', score=None, advisory="⚠️ No file selected.", image=None)

        print("DEBUG: filename =", file.filename)
        if not allowed_file(file.filename):
            print("DEBUG: Invalid file type")
            return render_template('index.html', score=None, advisory="⚠️ Invalid file type. Please upload a PNG, JPG, or WEBP.", image=None)

        filename = file.filename
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print("DEBUG: file saved at", filepath)

        try:
            score, advisory, processed_img = analyze_freshness(filepath)

            # Save processed result
            base, ext = os.path.splitext(filepath)
            result_path = f"{base}_result{ext}"
            cv2.imwrite(result_path, processed_img)
            print("DEBUG: result image saved at", result_path)

            return render_template('index.html', score=round(score, 2), advisory=advisory, image=result_path)

        except Exception as e:
            print("ERROR:", e)
            return render_template('index.html', score=None, advisory=f"⚠️ Error processing image: {e}", image=None)

    # GET request fallback
    return render_template('index.html', score=None, advisory=None, image=None)

if __name__ == '__main__':
    app.run(debug=True)
