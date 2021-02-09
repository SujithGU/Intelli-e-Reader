from flask import Flask, request, jsonify
import slate3k as slate
import os, base64
from flask_cors import CORS

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Distant Reading Archive</h1>
<p>A prototype API for distant reading of science fiction novels.</p>'''


@app.route('/hello', methods=['GET', 'POST'])
def welcome():
    return "Hello world"

@app.route('/retrieve', methods=['POST'])
def get_data():
    
    req_data = request.get_json()['request']
    byteData = req_data['bytes']
    # flash(req_data)
    # app.logger.debug(req_data)
    if request.method == 'POST':
        with open(os.path.expanduser('~/Desktop/test.pdf'), 'wb') as fout:
            pdfByteData = base64.b64decode(byteData)
            fout.write(pdfByteData)
        
        # with open('/Users/prajyotsuvarna/Desktop/test.pdf', 'rb') as fin:
        #     extractedText = slate.PDF(fin)
            
            # if extractedText:
            #     return jsonify(extractedText)
        #     obj = {
        #         "extractedText": extractedText
        #     }
                # f = request.files[]
            #     extractedData = slate.PDF(req_data)
        return jsonify(req_data)
    


app.run()