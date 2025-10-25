# Dev Container Setup Guide

이 프로젝트는 Dev Container를 사용하여 일관된 개발 환경을 제공합니다.

## 🚀 빠른 시작

### 1. Dev Container 열기

**VS Code에서:**
1. 이 저장소를 VS Code로 엽니다
2. 왼쪽 하단의 원격 아이콘 클릭 (><)
3. "Reopen in Container" 선택
4. 컨테이너 빌드 및 설정이 자동으로 완료됩니다 (처음 실행 시 5-10분 소요)

**GitHub Codespaces에서:**
1. GitHub 저장소 페이지에서 "Code" 버튼 클릭
2. "Codespaces" 탭 선택
3. "Create codespace on main" 클릭

### 2. 설정 완료 확인

컨테이너가 시작되면 자동으로 다음 작업이 수행됩니다:

```bash
✅ Python 3.12 설치
✅ 가상환경 (.venv) 생성
✅ 필수 패키지 설치
✅ Jupyter 커널 등록
✅ Azure CLI, Azure Developer CLI 설치
```

터미널에서 확인:

```bash
# Python 버전 확인
python --version  # Python 3.12.x

# 가상환경 활성화 확인
which python  # /workspaces/agentic-ai-labs/.venv/bin/python

# 패키지 설치 확인
pip list | grep azure
```

### 3. 노트북 실행

1. VS Code에서 `.ipynb` 파일 열기
2. 오른쪽 상단 "커널 선택" 클릭
3. "Python 3.12 (agentic-ai-labs)" 선택
4. 셀 실행 시작!

## 📦 포함된 도구

- **Python 3.12**: 최신 Python 런타임
- **Azure CLI**: Azure 리소스 관리
- **Azure Developer CLI (azd)**: 인프라 배포
- **Docker**: 컨테이너 빌드 및 실행
- **Git**: 버전 관리

## 📚 설치된 Python 패키지

모든 필수 패키지는 `requirements.txt`에 정의되어 있습니다:

- **Azure SDK**: identity, core, ai-projects (1.0.0b5), ai-inference (1.0.0b6), ai-evaluation, search-documents
- **OpenAI SDK**: GPT 모델 및 임베딩 API
- **Agent Framework**: Microsoft Agent Framework (1.0.0b251016)
- **Agent Framework Dev UI**: agent-framework-devui (1.0.0b251007) - 워크플로우 시각화 도구
- **MCP**: Model Context Protocol
- **FastAPI & Uvicorn**: API 서버
- **OpenTelemetry**: 관찰성 및 모니터링
- **Jupyter**: 노트북 지원

## 🔧 수동 설정 (Dev Container 없이)

Dev Container를 사용하지 않는 경우:

```bash
# 1. Python 3.12 설치 확인
python --version

# 2. 가상환경 생성
python -m venv .venv

# 3. 가상환경 활성화
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 4. 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 5. Jupyter 커널 등록
python -m ipykernel install --user --name=agentic-ai-labs --display-name "Python 3.12 (agentic-ai-labs)"
```

## 🆘 문제 해결

### 패키지가 설치되지 않은 경우

```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# 수동으로 패키지 재설치
pip install -r requirements.txt
```

### Jupyter 커널이 보이지 않는 경우

```bash
# 커널 재등록
source .venv/bin/activate
python -m ipykernel install --user --name=agentic-ai-labs --display-name "Python 3.12 (agentic-ai-labs)"
```

### Dev Container 재빌드

1. VS Code 명령 팔레트 열기 (`Cmd+Shift+P` 또는 `Ctrl+Shift+P`)
2. "Dev Containers: Rebuild Container" 입력 및 선택
3. 컨테이너가 처음부터 재빌드됩니다

## 📝 추가 정보

- **가상환경 경로**: `.venv/`
- **Setup 스크립트**: `.devcontainer/setup.sh`
- **패키지 목록**: `requirements.txt`
- **Dev Container 설정**: `.devcontainer/devcontainer.json`

## 🎯 다음 단계

Dev Container 설정이 완료되었다면:

1. `01_deploy_azure_resources.ipynb` 실행
2. `02_setup_ai_search_rag.ipynb` 실행
3. `03_deploy_foundry_agent_without_maf.ipynb` 실행
4. `04_deploy_foundry_agent_with_maf.ipynb` 실행

각 노트북의 지침을 따라 진행하세요!

---

## 관련 문서

- [README.md](./README.md) - 프로젝트 개요 및 시작 가이드
- [PREREQUISITES.md](./PREREQUISITES.md) - 사전 요구사항 및 도구 설치
- [CONFIGURATION.md](./CONFIGURATION.md) - 환경 변수 및 설정 가이드
- [.github/codespaces.md](./.github/codespaces.md) - GitHub Codespaces 설정
