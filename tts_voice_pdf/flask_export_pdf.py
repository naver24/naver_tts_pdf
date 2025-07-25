from flask import Flask, request, send_file, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
import os
from uuid import uuid4
import boto3
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경변수 로드

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

SAVE_DIR = "./TTS_Resource"
os.makedirs(SAVE_DIR, exist_ok=True)

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
REGION = "kr-standard"
ENDPOINT = "https://kr.object.ncloudstorage.com"
BUCKET_NAME = os.getenv("BUCKET_NAME")

@app.route('/')
def index():
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(m for m in rule.methods if m not in ('HEAD', 'OPTIONS')))
        routes.append({'methods': methods, 'uri': str(rule)})
    template = """
    <!doctype html>
    <html>
    <head><title>API Routes</title></head>
    <body>
      <h1>Available API Endpoints</h1>
      <table border="1" cellpadding="5" cellspacing="0">
        <thead><tr><th>Method(s)</th><th>URI</th></tr></thead>
        <tbody>
          {% for route in routes %}
          <tr>
            <td>{{ route.methods }}</td>
            <td>
              {% if route.uri == '/export/pdf' %}
                <a href="{{ route.uri }}">{{ route.uri }}</a>
              {% else %}
                {{ route.uri }}
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </body>
    </html>
    """
    return render_template_string(template, routes=routes)

@app.route('/export/pdf', methods=[ 'POST'])
def export_pdf():
    """if request.method == 'GET':
        # 입력 폼 보여주기
        form_html = """
        #<!doctype html>
        #<html>
        #<head><title>Export PDF</title></head>
        #<body>
         # <h1>텍스트를 입력하세요</h1>
          #<form method="post">
           # <textarea name="conversation" rows="10" cols="50" placeholder="텍스트 입력..."></textarea><br>
            #<button type="submit">PDF 생성 및 다운로드</button>
         # </form>
          #<p><a href="{{ url_for('index') }}">← API 목록으로 돌아가기</a></p>
       # </body>
        #</html>
        #"""
        #return render_template_string(form_html)"""

    # POST 요청 처리 (폼 제출 or API 호출)
    conversation = None

    # JSON 요청일 경우 (API 호출)
    if request.is_json:
        data = request.get_json()
        conversation = data.get('conversation')

    # 폼 제출일 경우
    else:
        conversation = request.form.get('conversation')

    if not conversation:
        return jsonify({"error": "conversation 텍스트가 필요합니다."}), 400

    pdf = FPDF()
    pdf.add_page()

    try:
        pdf.add_font('Nanum', '', 'NanumGothic.ttf', uni=True)
        pdf.set_font('Nanum', '', 12)
    except RuntimeError:
        return jsonify({"error": "폰트 'NanumGothic.ttf'를 찾을 수 없습니다."}), 500

    for line in conversation.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{uuid4().hex[:6]}"
    file_name = f"javis-{timestamp}.pdf"
    file_path = os.path.join(SAVE_DIR, file_name)

    pdf.output(file_path)

    try:
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            region_name=REGION,
            endpoint_url=ENDPOINT,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.upload_file(file_path, BUCKET_NAME, file_name, ExtraArgs={'ACL': 'public-read'})
        cloud_url = f"{ENDPOINT}/{BUCKET_NAME}/{file_name}"
        print(f"✅ 업로드 성공: {cloud_url}")
    except Exception as e:
        return jsonify({
            "error": "Object Storage upload failed",
            "details": str(e)
        }), 500

    return send_file(file_path, as_attachment=True, mimetype='application/pdf', download_name=file_name)


if __name__ == "__main__":
    app.run(debug=True)