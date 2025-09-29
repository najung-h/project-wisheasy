# 베이스 이미지
FROM python:3.11-slim

# 아래 두 줄은 없어도 동작은 합니다.
# 그치만 로그 및 이미지 관리를 위해 관습적으로 넣는다니
# 저도 넣어볼게요.
# 구체적으로는 

# PYTHONDONTWRITEBYTECODE=1
# .pyc  캐시 파일을 만들지 않음으로써,
# 커테이너 안에서 불필요한 파일이 쌓이지 않아 
# 이미지가 가벼워지고 깔끔해집니다.

# 그리고, 
# PYTHONUNBUFFERED=1
# 파이썬 출력이 버퍼링 없이 즉시 출력되어
# docker logs로 바로바로 로그가 확인이 가능합니다.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# - python:3.11-slim에서 pkg-config/libmysqlclient 헤더 누락으로 pip install 실패 
# -> build-essential, default-libmysqlclient-dev, pkg-config 설치

# mysqlclient를 빌드/실행하기 위한 OS 의존성 설치
# - apt 인덱스 갱신 후 최소 패키지만 설치(--no-install-recommends)
# - build-essential: gcc/g++/make 등 컴파일 도구
# - default-libmysqlclient-dev: MySQL C 클라이언트 헤더/라이브러리(mysqlclient가 필요)
# - pkg-config: 빌드시 라이브러리 경로/플래그 탐색 도구
# - 마지막 rm: APT 캐시 삭제로 이미지 용량 절감
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*


# 이후 명령이 실행될 작업 디렉터리 지정
WORKDIR /app


COPY requirements.txt .
# pip 업그레이드 후 의존성 설치(캐시 미사용으로 이미지 용량/재현성 관리)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 전체 복사
COPY . .

# docker-compose 파일에도 포트 8000으로 변경
EXPOSE 8000

# uvicorn -> gunicorn
# server:app -> config.wsgi:application -> Django는 WSGI 규약을 따르면서, APPLICATION이라는 객체로 진입점을 정함.
# FastAPI는 uvicorn, Django는 기본 WSGI 기반 gunicorn 을 많이 쓴다.
# "--bind", "0.0.0.0:8000" 컨테이너 내부에서 모든 인터페이스로 8000포트를 리슨
# 그래야 호스트 / 로드밸런서가 포트 매핑으로 접근할 수 있게 됨.
# --access-logfile : 도커에서 엑세스 로그를 수집하기 좋게끔
# --error-logfile : 도커에서 에러 로그를 수집하기 좋게끔
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]