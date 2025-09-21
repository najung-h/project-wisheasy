from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# 정적 파일 디렉토리 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 루트 경로로 접근하면 index.html 반환
@app.get("/")
def read_index():
    return FileResponse("static/index.html")