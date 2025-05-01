# Discord LLM 봇

Discord LLM 봇은 강력한 로컬 또는 클라우드 기반 AI 모델을 사용하여 Discord 서버에 질문 응답, 웹 검색, 정보 검색 기능을 제공하는 통합 솔루션입니다.

**주요 기능:**
- 🤖 로컬 Gemma 3 모델 또는 OpenAI/Anthropic 클라우드 AI와 자유롭게 대화
- 🔍 웹 검색 기능으로 최신 정보 제공
- 📚 벡터 데이터베이스(RAG)를 통한 문서 검색 및 질의응답
- 🔄 다양한 AI 제공자 선택 (로컬 LLM, OpenAI, Anthropic Claude)
- 🐳 Docker 컨테이너로 쉬운 배포 및 관리

## 목차

- [시스템 요구사항](#시스템-요구사항)
- [아키텍처 개요](#아키텍처-개요)
- [설치 방법](#설치-방법)
  - [Docker 설치](#1-docker-설치)
  - [프로젝트 다운로드](#2-프로젝트-다운로드)
  - [환경 설정](#3-환경-설정)
  - [모델 다운로드](#4-모델-다운로드-로컬-llm-사용시)
  - [Discord 봇 설정](#5-discord-봇-설정)
- [실행 방법](#실행-방법)
  - [배포 스크립트 사용](#배포-스크립트-사용)
  - [로그 확인](#로그-확인)
  - [서비스 중지](#서비스-중지)
- [사용 가이드](#사용-가이드)
  - [Discord 명령어](#discord-명령어)
  - [웹 검색 활용](#웹-검색-활용)
- [LLM 제공자 변경](#llm-제공자-변경)
  - [로컬 LLM 사용](#로컬-llm-사용)
  - [OpenAI API 사용](#openai-api-사용)
  - [Anthropic Claude API 사용](#anthropic-claude-api-사용)
- [고급 설정](#고급-설정)
  - [하드웨어 가속 설정](#하드웨어-가속-설정)
  - [모델 변경](#모델-변경)
  - [쿠키 설정](#쿠키-설정)
- [문제 해결](#문제-해결)
- [개발 정보](#개발-정보)
- [라이선스](#라이선스)

## 시스템 요구사항

### Docker 배포 시 (권장)
- Docker 및 Docker Compose 설치됨
- 인터넷 연결
- 최소 8GB RAM, 권장 16GB 이상
- 최소 20GB 이상의 디스크 공간
- Discord 봇 토큰

### 로컬 LLM 사용 시 추가 요구사항
- NVIDIA GPU (CUDA 지원) 또는 Apple Silicon Mac (Metal 지원)
- 최소 16GB RAM, 권장 24GB 이상
- 모델 파일을 위한 최소 30GB 이상의 디스크 공간

## 아키텍처 개요

Discord LLM 봇은 다음과 같은 컴포넌트로 구성됩니다:

1. **Discord Bot**: Discord API와 통신하며 사용자 메시지를 처리합니다.
2. **MCP Server**: 모델 컨텍스트 프로토콜 서버로, 다양한 LLM 제공자와 통신합니다.
3. **Llama.cpp Server**: 로컬 LLM을 실행하는 고성능 추론 서버입니다(로컬 LLM 모드에서만 사용).
4. **Qdrant**: 벡터 데이터베이스로 RAG(Retrieval-Augmented Generation)를 지원합니다.
5. **SearxNG**: 프라이빗 메타 검색 엔진으로 웹 검색 기능을 제공합니다.

시스템은 Docker Compose를 통해 관리되며, 모든 서비스가 컨테이너로 실행됩니다.

## 설치 방법

### 1. Docker 설치

시스템에 Docker와 Docker Compose가 설치되어 있어야 합니다.

#### Linux (Ubuntu/Debian):
```bash
# Docker 설치
sudo apt-get update
sudo apt-get install docker.io

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Docker 서비스 시작 및 활성화
sudo systemctl start docker
sudo systemctl enable docker
```

#### macOS:
[Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac/) 설치

#### Windows:
[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows/) 설치

### 2. 프로젝트 다운로드

```bash
# Git을 사용하여 프로젝트 클론
git clone https://github.com/SGT-Cho/DiscordLLM.git
cd DiscordLLM
```

### 3. 환경 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 설정을 변경합니다:

```bash
cp .env.example .env
```

텍스트 에디터로 `.env` 파일을 열고 다음 필수 항목을 설정합니다:

- `DISCORD_TOKEN`: Discord 개발자 포털에서 생성한 봇 토큰
- `LLM_PROVIDER`: 사용할 LLM 제공자 선택 (`local`, `openai`, `anthropic`)

외부 API 사용 시 추가 설정:
- OpenAI 사용 시: `OPENAI_API_KEY`와 `OPENAI_MODEL` 설정
- Anthropic 사용 시: `ANTHROPIC_API_KEY`와 `ANTHROPIC_MODEL` 설정

로컬 LLM 사용 시 추가 설정:
- `THREADS`: 사용할 CPU 쓰레드 수
- `METAL_LAYERS`: Apple Silicon Mac에서 Metal 가속 사용 시 레이어 수
- `GPU_LAYERS`: NVIDIA GPU 사용 시 CUDA 가속 레이어 수

### 4. 모델 다운로드 (로컬 LLM 사용시)

로컬 LLM을 사용하려면 모델 파일을 다운로드해야 합니다:

1. `models` 디렉토리 생성:
```bash
mkdir -p models
```

2. Gemma 3 27B Instruct 모델을 다운로드합니다. [Hugging Face](https://huggingface.co/google/gemma-3-27b-it/tree/gguf)에서 GGUF 형식의 모델을 다운로드할 수 있습니다:
```bash
# 예시: Q4_0 양자화 모델 다운로드
wget https://huggingface.co/google/gemma-3-27b-it/resolve/gguf/gemma-3-27b-it-q4_0.gguf -P models/
```

다른 옵션: 정확도와 메모리 요구사항 균형을 위해 다른 양자화 모델을 선택할 수 있습니다:
- `gemma-3-27b-it-q5_0.gguf`: 더 높은 정확도, 더 많은 메모리 사용
- `gemma-3-27b-it-q3_k_m.gguf`: 더 낮은 정확도, 더 적은 메모리 사용

### 5. Discord 봇 설정

1. [Discord 개발자 포털](https://discord.com/developers/applications)에 접속합니다.
2. "New Application"을 클릭하고 봇 이름을 입력합니다.
3. "Bot" 섹션으로 이동하여 "Add Bot"을 클릭합니다.
4. "Reset Token"을 클릭하여 새 토큰을 생성하고 복사합니다.
5. 이 토큰을 `.env` 파일의 `DISCORD_TOKEN` 변수에 붙여넣습니다.
6. "OAuth2" → "URL Generator"로 이동하여 다음 권한을 선택합니다:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `Attach Files`, `Embed Links`, `Use Slash Commands`
7. 생성된 URL을 사용하여 봇을 Discord 서버에 초대합니다.

## 실행 방법

### 배포 스크립트 사용

배포 스크립트를 실행 가능하게 만들고 시작합니다:

```bash
chmod +x deploy.sh
./deploy.sh start
```

스크립트는 설정을 확인하고 필요한 컨테이너를 시작합니다. LLM 제공자 설정에 따라 다음과 같이 작동합니다:

- `LLM_PROVIDER=local`: 로컬 Llama.cpp 서버를 포함한 모든 서비스 실행
- `LLM_PROVIDER=openai` 또는 `LLM_PROVIDER=anthropic`: Llama.cpp 서버를 제외한 서비스 실행

### 로그 확인

서비스 로그를 확인하여 정상 작동 여부를 모니터링할 수 있습니다:

```bash
# 모든 서비스의 로그 확인
./deploy.sh logs

# 특정 서비스의 로그만 확인 (예: Discord 봇)
./deploy.sh logs discord-bot
```

### 서비스 중지

서비스를 중지하려면 다음 명령을 실행합니다:

```bash
./deploy.sh stop
```

## 사용 가이드

### Discord 명령어

Discord 서버에서 다음과 같은 방식으로 봇을 사용할 수 있습니다:

- **일반 질문**: 봇을 멘션하고 질문을 입력합니다.
  ```
  @LLM봇 파이썬으로 피보나치 수열을 계산하는 코드를 작성해줘
  ```

- **웹 검색 질문**: 사실 기반 정보나 최신 정보가 필요한 질문을 입력합니다.
  ```
  @LLM봇 오늘 날씨 어때?
  @LLM봇 최근 테슬라 주가는 얼마야?
  ```

### 웹 검색 활용

봇은 다음과 같은 패턴의 질문에서 자동으로 웹 검색을 수행합니다:
- 최신 뉴스나 정보에 대한 질문
- 사실 확인이 필요한 질문
- 특정 날짜, 시간, 가격 등에 대한 질문

검색 결과는 응답의 일부로 포함되며, 응답 끝에 출처 링크가 제공됩니다.

## LLM 제공자 변경

### 로컬 LLM 사용

로컬 LLM을 사용하려면 `.env` 파일에서 다음과 같이 설정합니다:

```
LLM_PROVIDER=local
MODEL_PATH=/models/gemma-3-27b-it-q4_0.gguf
```

이 모드에서는 모델 파일이 `models` 디렉토리에 있어야 합니다.

### OpenAI API 사용

OpenAI API를 사용하려면 `.env` 파일에서 다음과 같이 설정합니다:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # 또는 다른 모델
```

### Anthropic Claude API 사용

Anthropic Claude API를 사용하려면 `.env` 파일에서 다음과 같이 설정합니다:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229  # 또는 다른 모델
```

## 고급 설정

### 하드웨어 가속 설정

로컬 LLM 사용 시 하드웨어 가속을 최적화하려면:

- **NVIDIA GPU 사용 시**:
  ```
  GPU_LAYERS=33  # 모델 레이어 수에 맞게 조정
  ```

- **Apple Silicon Mac 사용 시**:
  ```
  METAL_LAYERS=32  # 모델 레이어 수에 맞게 조정
  ```

- **CPU 쓰레드 최적화**:
  ```
  THREADS=8  # 사용 가능한 물리적 코어 수로 설정
  ```

### 모델 변경

다른 모델을 사용하려면:

1. 모델 파일을 `models` 디렉토리에 다운로드합니다.
2. `.env` 파일에서 `MODEL_PATH` 변수를 업데이트합니다:
   ```
   MODEL_PATH=/models/your-new-model.gguf
   ```

### 시스템 리소스 제한

메모리 사용량을 제한하려면 `docker-compose.yml` 파일에서 `llama-server` 서비스의 리소스 제한을 조정할 수 있습니다:

```yaml
deploy:
  resources:
    limits:
      memory: 12G  # 메모리 제한 조정
```

## 문제 해결

### 일반적인 문제와 해결 방법

1. **Discord 봇이 응답하지 않는 경우**
   - `./deploy.sh logs discord-bot` 명령으로 로그를 확인합니다.
   - Discord 봇 토큰이 올바르게 설정되었는지 확인합니다.
   - 봇에 필요한 권한이 있는지 확인합니다.

2. **로컬 LLM 서버 오류**
   - `./deploy.sh logs llama-server` 명령으로 로그를 확인합니다.
   - 모델 파일이 올바른 위치에 있는지 확인합니다.
   - 시스템 메모리가 충분한지 확인합니다.
   - GPU/Metal 설정이 올바른지 확인합니다.

3. **API 키 오류**
   - `.env` 파일에서 API 키가 올바르게 설정되었는지 확인합니다.
   - API 키의 공백이나 따옴표가 없는지 확인합니다.

4. **메모리 부족 오류**
   - 더 낮은 양자화 모델(예: q3_k_m)을 사용해 보세요.
   - Docker 리소스 제한을 확인하고 조정하세요.
   - 불필요한 백그라운드 프로세스를 종료하세요.

5. **검색 기능 작동 안함**
   - `./deploy.sh logs searxng` 및 `./deploy.sh logs mcp-server`로 로그를 확인합니다.
   - 인터넷 연결을 확인합니다.

### 로그 확인 및 디버깅

문제가 발생한 경우 로그를 확인하는 것이 가장 좋은 방법입니다:

```bash
# 특정 서비스의 로그 확인
./deploy.sh logs service-name

# 실시간 로그 확인
./deploy.sh logs -f service-name
```

## 개발 정보

이 프로젝트는 다음 컴포넌트로 구성됩니다:

- **Discord Bot**: Discord.py를 사용한 Discord 인터페이스
- **MCP Server**: FastAPI 기반 API 서버
- **Llama.cpp Server**: C++로 작성된 고성능 추론 서버
- **Qdrant**: 벡터 데이터베이스 (RAG 기능용)
- **SearxNG**: 프라이빗 메타 검색 엔진

코드 기여나 개발에 참여하고 싶다면 각 디렉토리의 README와 소스 코드를 참조하세요.

## 라이선스

[Apache License](LICENSE)

---

문제가 있거나 도움이 필요하면 이슈를 등록하거나 프로젝트 관리자에게 연락하세요.