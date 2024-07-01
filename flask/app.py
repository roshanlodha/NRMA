from flask import Flask, request, redirect, url_for, send_file, render_template
import os
import NRMA

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Ensure this directory exists

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file_post():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        filepath = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Debug statement to ensure file is saved correctly
        if not os.path.exists(filepath):
            return "File save failed. Please try again."

        # Run the NRMA script
        NRMA.main(filepath)

        # Path to the assignment file
        assignment_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'assignment.csv')

        return render_template('upload.html', filepath=filepath, assignment_filepath=assignment_filepath)

@app.route('/download')
def download_file():
    assignment_filepath = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'assignment.csv')
    if os.path.exists(assignment_filepath):
        return send_file(assignment_filepath, as_attachment=True)
    return "Assignment file not found."

if __name__ == "__main__":
    app.run(debug=True)
