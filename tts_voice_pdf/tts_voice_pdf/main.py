from flask import Flask, request, jsonify 
from flask_cors import CORS
import gene_tts




app = Flask(__name__)


CORS(app, origins=["http://localhost:3000", "https://javis.shop","http://172.30.1.76:5173","http://192.168.0.164:5173"])





@app.route('/')
def home():

    return 'Hello, Flask!'

@app.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}!'

@app.route('/echo', methods=['POST'])
def echo():
    

    data = request.json
    return jsonify({
        'you_sent': data
    })
@app.route('/tts', methods=['POST'])
def generation_tts():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "텍스트 데이터가 없습니다."}), 400
    print(data)
    text = data['text']
    url = gene_tts.javis_voice(text)  # 텍스트 인자를 넘겨서 음성을 생성하자
    

    if url:
        return jsonify({ "status": "success", "url": url })
    else:
        return jsonify({ "status": "error", "message": "TTS 생성 실패" })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)