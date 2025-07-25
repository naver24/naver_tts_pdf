import os
import urllib.request
import urllib.parse
import datetime
from uuid import uuid4
import boto3 
from dotenv import load_dotenv   

load_dotenv() # .env 파일에서 환경변수 로드

def javis_voice(text):
# [1] 네이버 클라우드 Clova 인증
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")

    # [2] 네이버 Object Storage 인증
    ACCESS_KEY = os.getenv("ACCESS_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    REGION = "kr-standard"
    ENDPOINT = "https://kr.object.ncloudstorage.com"
    BUCKET_NAME = os.getenv("BUCKET_NAME") # 본인 버킷 이름으로 교체

    # [3] 동적으로 받을곳
    #text = input("대화내용: ")
    text_voice = text
    encText = urllib.parse.quote(text_voice)

    data = f"speaker=nara&volume=0&speed=0&pitch=0&format=mp3&text={encText}"
    data_bytes = data.encode('utf-8')
    
    url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    
    
    request = urllib.request.Request(url, data=data_bytes)
    request.method = "POST"
    
    request.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
    request.add_header("X-NCP-APIGW-API-KEY", client_secret)
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    response = urllib.request.urlopen(request, data=data.encode('utf-8'))
    rescode = response.getcode()

    if rescode == 200:
        print(" TTS 음성 변환 성공")

    # [4] mp3 파일을 저장하자
        mp3_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{uuid4().hex[:6]}"
        filename = f"{mp3_name}.mp3"
        # 로컬에 저장하자
        local_path = os.path.join("./TTS_Resource", filename)
        # 저장폴더가 없으면 생성하자
        os.makedirs("./TTS_Resource", exist_ok=True)

        response_body = response.read()
        with open(local_path, 'wb') as f:
            f.write(response_body)

        print(f" 로컬 저장: {local_path}")

    # [5] Object Storage 업로드하자
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            region_name=REGION,
            
            endpoint_url=ENDPOINT,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        print("🔎 Endpoint:", ENDPOINT)
        print("🔎 Region:", REGION)
        print("🔎 Bucket:", BUCKET_NAME)
        try:
            s3.upload_file(local_path, BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
            file_url = f"{ENDPOINT}/{BUCKET_NAME}/{filename}"
            print(f" 업로드 성공 접근 URL: {file_url}")

            return file_url
        except Exception as e:
            print(f"❌ Object Storage 업로드 실패: {e}")
            return None

    else:
        print("❌ Error Code:" + str(rescode))

        
        """
    DB 저장
    mp3> object stoeage > url
    db > mp3 에 대한 메타데이터 db > messages chat 연결
    메타데이터 DB를 따로 만들건지 TTS, PDF 이것만 관리하는 DB table 생성

    개발 로직
    obj stoage 저장 버킷은 뭐로 할꺼냐=>네이버클라우드, 접근은 얼마나 시킬거냐 로직
    db 메타데이터 저장 로직
    반환 url 확인 로직
    """