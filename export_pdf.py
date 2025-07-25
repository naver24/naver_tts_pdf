from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from uuid import uuid4
import boto3



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# [1] 저장경로
SAVE_DIR = "./TTS_Resource"

os.makedirs(SAVE_DIR, exist_ok=True)

# [2] 네이버 오브젝트스토리지 인증정보
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
REGION = "kr-standard"
ENDPOINT = "https://kr.object.ncloudstorage.com"
BUCKET_NAME = os.getenv("BUCKET_NAME")




class Conversation(BaseModel):
    conversation: str



@app.post("/export/pdf")
async def export_pdf(data: Conversation):
    pdf = FPDF()
    pdf.add_page()
# [3] 폰트를 정하자
    try:
        pdf.add_font('MaruBuri', '', 'MaruBuri-Regular.ttf')
        pdf.set_font('MaruBuri', '', 12)
    except RuntimeError:
        return JSONResponse(status_code=500, content={"error": "폰트 'MaruBuri-Regular.ttf'를 찾을 수 없습니다."})

    for line in data.conversation.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)

# [4] 파일저장이름 시간+생성네임 겹치지않도록uuid4사용하자
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")+ f"_{uuid4().hex[:6]}"
    file_name = f"javis-{timestamp}.pdf"   
    file_path = os.path.join(SAVE_DIR, file_name)

 # [5] 로컬저장 하자
    pdf.output(file_path)

# [6] Object Storage 업로드하자
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
        print(f"✅ 업로드 성공: {cloud_url}")  # 로그 확인용

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": "Object Storage upload failed",
            "details": str(e)
        })
    return FileResponse(file_path, filename=file_path, media_type="application/pdf")


