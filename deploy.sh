#!/bin/bash

# Discord-LLM 프로젝트 관리 스크립트
# 모든 서비스를 쉽게 시작, 중지, 모니터링할 수 있습니다

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로고 출력
echo -e "${BLUE}"
echo "  _____  _                       _   _     _     __  __ "
echo " |  __ \(_)                     | | | |   | |   |  \/  |"
echo " | |  | |_ ___  ___ ___  _ __ __| | | |   | |   | \  / |"
echo " | |  | | / __|/ __/ _ \| '__/ _\` | | |   | |   | |\/| |"
echo " | |__| | \__ \ (_| (_) | | | (_| | | |___| |___| |  | |"
echo " |_____/|_|___/\___\___/|_|  \__,_| |_____|_____|_|  |_|"
echo -e "${NC}"
echo -e "${GREEN}Discord LLM 프로젝트 관리 도구${NC}"
echo ""

# 환경 변수 파일 확인
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}오류: .env 파일을 찾을 수 없습니다.${NC}"
    echo "샘플 .env 파일을 생성합니다. 필요한 내용을 수정해주세요."
    cat > $ENV_FILE << EOL
# Discord Bot 설정
DISCORD_TOKEN=여기에_디스코드_토큰_입력

# LLM 선택 설정
LLM_PROVIDER=local      # local, openai, anthropic 중 선택
# local: 로컬 llama.cpp 서버 사용
# openai: OpenAI API 사용
# anthropic: Anthropic Claude API 사용

# 외부 LLM API 설정 (LLM_PROVIDER가 local이 아닐 경우 사용)
OPENAI_API_KEY=         # OpenAI API 키 (LLM_PROVIDER=openai 일 때 필요)
OPENAI_MODEL=gpt-4o     # 사용할 OpenAI 모델 (기본값: gpt-4o)

ANTHROPIC_API_KEY=      # Anthropic API 키 (LLM_PROVIDER=anthropic 일 때 필요)
ANTHROPIC_MODEL=claude-3-opus-20240229  # 사용할 Anthropic 모델

# 하드웨어 설정
THREADS=4
METAL_LAYERS=32

# Docker 내부 통신용 URL (기본값)
LLAMA_SERVER_URL=http://llama-server:5602
QDRANT_URL=http://qdrant:6333
SEARXNG_URL=http://searxng:8080
MCP_SERVER_URL=http://mcp-server:5601
EOL
    echo -e "${YELLOW}.env 파일이 생성되었습니다. DISCORD_TOKEN을 설정한 후 다시 시도해주세요.${NC}"
    exit 1
fi

# LLM 제공자 확인
LLM_PROVIDER=$(grep "LLM_PROVIDER" $ENV_FILE | cut -d'=' -f2 | sed 's/[[:space:]]//g' | tr -d '"' | tr -d "'")
if [ -z "$LLM_PROVIDER" ]; then
    LLM_PROVIDER="local"
fi

# 모델 파일 확인 (local 모드일 때만)
if [ "$LLM_PROVIDER" = "local" ]; then
    MODEL_DIR="./models"
    if [ ! -d "$MODEL_DIR" ]; then
        echo -e "${YELLOW}경고: models 디렉토리가 없습니다. 생성합니다.${NC}"
        mkdir -p "$MODEL_DIR"
    fi

    MODEL_PATH=$(grep "MODEL_PATH" $ENV_FILE | cut -d'=' -f2)
    MODEL_FILENAME=$(basename $MODEL_PATH)
    if [ ! -f "$MODEL_DIR/$MODEL_FILENAME" ]; then
        echo -e "${YELLOW}경고: 모델 파일($MODEL_FILENAME)을 찾을 수 없습니다.${NC}"
        echo "모델 파일을 models 디렉토리에 다운로드한 후 다시 시도해주세요."
        echo "기본 모델: gemma-3-27b-it-q4_0.gguf"
        echo -e "${YELLOW}계속 진행하시겠습니까? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^([nN][oO]|[nN])$ ]]; then
            exit 1
        fi
    fi
else
    # 외부 LLM 사용 시 API 키 확인
    if [ "$LLM_PROVIDER" = "openai" ]; then
        OPENAI_API_KEY=$(grep "OPENAI_API_KEY" $ENV_FILE | cut -d'=' -f2 | sed 's/[[:space:]]//g' | tr -d '"' | tr -d "'")
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${RED}오류: OPENAI_API_KEY가 설정되지 않았습니다.${NC}"
            echo "OpenAI API 키를 .env 파일에 설정해주세요."
            exit 1
        fi
        echo -e "${GREEN}OpenAI API를 LLM 제공자로 사용합니다.${NC}"
    elif [ "$LLM_PROVIDER" = "anthropic" ]; then
        ANTHROPIC_API_KEY=$(grep "ANTHROPIC_API_KEY" $ENV_FILE | cut -d'=' -f2 | sed 's/[[:space:]]//g' | tr -d '"' | tr -d "'")
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo -e "${RED}오류: ANTHROPIC_API_KEY가 설정되지 않았습니다.${NC}"
            echo "Anthropic API 키를 .env 파일에 설정해주세요."
            exit 1
        fi
        echo -e "${GREEN}Anthropic Claude API를 LLM 제공자로 사용합니다.${NC}"
    else
        echo -e "${RED}오류: 알 수 없는 LLM_PROVIDER 값입니다: $LLM_PROVIDER${NC}"
        echo "LLM_PROVIDER는 local, openai, anthropic 중 하나여야 합니다."
        exit 1
    fi
fi

# Docker와 Docker Compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}오류: Docker가 설치되어 있지 않습니다.${NC}"
    echo "Docker를 설치하고 다시 시도해주세요."
    echo "설치 방법: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}오류: Docker Compose를 찾을 수 없습니다.${NC}"
    echo "Docker Compose를 설치하고 다시 시도해주세요."
    echo "설치 방법: https://docs.docker.com/compose/install/"
    exit 1
fi

# 함수 정의
show_help() {
    echo -e "${GREEN}사용법:${NC} ./deploy.sh [명령]"
    echo ""
    echo "명령:"
    echo "  start       - 모든 서비스 시작"
    echo "  stop        - 모든 서비스 중지"
    echo "  restart     - 모든 서비스 재시작"
    echo "  status      - 서비스 상태 확인"
    echo "  logs [서비스]  - 서비스 로그 확인 (예: ./deploy.sh logs discord-bot)"
    echo "  build       - 모든 도커 이미지 빌드"
    echo "  update      - 도커 이미지 업데이트 및 재시작"
    echo "  help        - 도움말 표시"
    echo ""
    echo "현재 LLM 제공자: $LLM_PROVIDER"
    if [ "$LLM_PROVIDER" = "local" ]; then
        echo -e "로컬 llama.cpp 서버를 사용합니다. 모델: ${YELLOW}$MODEL_FILENAME${NC}"
    elif [ "$LLM_PROVIDER" = "openai" ]; then
        OPENAI_MODEL=$(grep "OPENAI_MODEL" $ENV_FILE | cut -d'=' -f2 | sed 's/[[:space:]]//g' | tr -d '"' | tr -d "'")
        echo -e "OpenAI API를 사용합니다. 모델: ${YELLOW}$OPENAI_MODEL${NC}"
    elif [ "$LLM_PROVIDER" = "anthropic" ]; then
        ANTHROPIC_MODEL=$(grep "ANTHROPIC_MODEL" $ENV_FILE | cut -d'=' -f2 | sed 's/[[:space:]]//g' | tr -d '"' | tr -d "'")
        echo -e "Anthropic API를 사용합니다. 모델: ${YELLOW}$ANTHROPIC_MODEL${NC}"
    fi
    echo ""
    echo "예시:"
    echo "  ./deploy.sh start          # 모든 서비스 시작"
    echo "  ./deploy.sh logs mcp-server # MCP 서버 로그 확인"
}

start_services() {
    echo -e "${BLUE}서비스를 시작합니다 (LLM 제공자: $LLM_PROVIDER)...${NC}"
    
    if [ "$LLM_PROVIDER" = "local" ]; then
        # 로컬 LLM을 사용하는 경우 모든 서비스 시작
        echo "로컬 llama.cpp 서버와 함께 모든 서비스를 시작합니다..."
        docker compose --profile local up -d
    else
        # 외부 LLM을 사용하는 경우 llama-server를 제외하고 시작
        echo "외부 LLM API를 사용하여 서비스를 시작합니다 (llama-server 제외)..."
        docker compose up -d --scale llama-server=0 qdrant mcp-server discord-bot searxng nginx
    fi
    
    echo -e "${GREEN}서비스가 백그라운드에서 실행 중입니다. 상태를 확인하려면 './deploy.sh status'를 실행하세요.${NC}"
}

stop_services() {
    echo -e "${BLUE}모든 서비스를 중지합니다...${NC}"
    docker compose down
    echo -e "${GREEN}모든 서비스가 중지되었습니다.${NC}"
}

restart_services() {
    stop_services
    start_services
}

build_services() {
    echo -e "${BLUE}모든 서비스를 빌드합니다...${NC}"
    if [ "$LLM_PROVIDER" = "local" ]; then
        docker compose build
    else
        # llama-server를 제외하고 빌드
        docker compose build qdrant mcp-server discord-bot nginx
    fi
    echo -e "${GREEN}빌드가 완료되었습니다.${NC}"
}

check_status() {
    echo -e "${BLUE}서비스 상태 확인 중...${NC}"
    docker compose ps
}

show_logs() {
    if [ -z "$1" ]; then
        echo -e "${BLUE}모든 서비스의 로그를 확인합니다. 중단하려면 Ctrl+C를 누르세요...${NC}"
        docker compose logs -f
    else
        echo -e "${BLUE}$1 서비스의 로그를 확인합니다. 중단하려면 Ctrl+C를 누르세요...${NC}"
        docker compose logs -f "$1"
    fi
}

update_services() {
    echo -e "${BLUE}서비스를 업데이트합니다...${NC}"
    docker compose pull
    build_services
    restart_services
    echo -e "${GREEN}모든 서비스가 업데이트되었습니다.${NC}"
}

# 명령 처리
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs "$2"
        ;;
    build)
        build_services
        ;;
    update)
        update_services
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac