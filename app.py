import base64
import os

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import Config
from intelli_e_reader.reader.custom_reader import ConvertPdf

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Intelli-e-Reader API</h1>
<p>POST a base64-encoded PDF to /retrieve to get back a CEFR-simplified version.</p>'''


@app.route('/retrieve', methods=['POST'])
def retrieve():
    req_data = request.get_json()['request']
    byte_data = req_data['bytes']
    file_name = req_data.get('filename', 'upload.pdf')

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(Config.UPLOAD_FOLDER, file_name)

    with open(file_path, 'wb') as fout:
        fout.write(base64.b64decode(byte_data))

    result = ConvertPdf().convert(file_path)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5001)))
