from flask import Flask, request, render_template,jsonify
import os
import check_pdf_signature as p

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return 'No file part'
    file = request.files['pdf_file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.pdf'):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

        ret = f"uploaded {filename}"
        print(ret)

        return ret
        # python_code = f"""

@app.route('/is_signed', methods=['POST'])
def is_signed():
    pdf_unsigned = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Template.pdf'
    pdf_predict = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Signed.pdf'
    file_name = request.form.get('file_name')
    if not file_name:
        return jsonify({"error": "Missing 'file_name' parameter"}), 400
    prompt = p.create_signed_pdf_prompt_with_example(pdf_unsigned, file_name)
    resp = p.llm.invoke(prompt)
    print(resp)
    return jsonify(resp)


def upload(filename = 'Federal SW Signed.pdf'):
    """
    Uploads a PDF file to the server.
    """
    url = 'http://127.0.0.1:5001/upload'
    with open('Federal SW Signed.pdf', 'rb') as f:
        files = {'pdf_file': f}
        response = requests.post(url, files=files)
        print(response.text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port = 5001)


# curl -X POST -F "file_name=https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Signed.pdf" http://127.0.0.1:5001/is_signed
