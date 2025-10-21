# Prerequisites Guide

이 문서는 Azure AI Foundry Agent 실습을 진행하기 위한 사전 요구사항에 대한 상세 가이드입니다.

## 📋 Table of Contents

1. [실습 환경 선택](#실습-환경-선택)
2. [GitHub Codespace 환경](#github-codespace-환경)
3. [로컬 환경 설정](#로컬-환경-설정)
4. [Azure 구독 및 권한](#azure-구독-및-권한)
5. [권한 확인 방법](#권한-확인-방법)

---

## 실습 환경 선택

### 권장: GitHub Codespace ⭐

이 실습은 **GitHub Codespace**에서 진행하도록 설계되었습니다.

**Codespace 사용 장점:**
- ✅ 사전 구성된 개발 환경 (도구 자동 설치)
- ✅ 클라우드 기반으로 어디서나 접근 가능
- ✅ 일관된 실습 환경 제공
- ✅ 로컬 머신 리소스 절약
- ✅ OS별 설정 차이 없음

**Codespace 시작 방법:**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/junwoojeong100/agentic-ai-labs?quickstart=1)

---

## GitHub Codespace 환경

### 자동 설치되는 도구

Codespace가 시작되면 다음이 자동으로 설치됩니다:

#### 기본 도구 및 런타임

| 도구 | 버전 | 용도 |
|------|------|------|
| **Azure Developer CLI (azd)** | 최신 | 인프라 배포 |
| **Azure CLI (az)** | 최신 | Azure 리소스 관리 |
| **Python** | 3.12 | Agent 및 서버 개발 |
| **Docker** | 최신 | 컨테이너 빌드 |
| **Git** | 최신 | 버전 관리 |
| **Node.js** | 최신 | 도구 의존성 |

#### Python 가상환경

`.venv` 가상환경이 자동으로 생성되고 활성화됩니다:

```bash
# 가상환경 자동 활성화됨
source .venv/bin/activate

# Jupyter 커널도 자동 등록됨
jupyter kernelspec list
```

#### VS Code 확장 (자동 설치)

| 확장 | ID | 용도 |
|------|-----|------|
| **Python** | ms-python.python | Python 개발 |
| **Pylance** | ms-python.vscode-pylance | Python 언어 서버 |
| **Jupyter** | ms-toolsai.jupyter | 노트북 실행 |
| **Azure Developer CLI** | ms-azuretools.azure-dev | azd 통합 |
| **Azure Resources** | ms-azuretools.vscode-azureresourcegroups | Azure 리소스 관리 |
| **Bicep** | ms-azuretools.vscode-bicep | IaC 개발 |
| **GitHub Copilot** | GitHub.copilot | AI 코드 어시스턴트 |
| **GitHub Copilot Chat** | GitHub.copilot-chat | AI 채팅 |

### Python 패키지 (자동 설치)

다음 패키지들이 `.venv`에 자동으로 설치됩니다:

#### Azure AI 및 핵심 서비스

```txt
azure-identity>=1.17.0
azure-core>=1.30.0
azure-ai-projects>=1.0.0b5
azure-ai-evaluation>=1.0.0
azure-ai-inference>=1.0.0b6
azure-search-documents>=11.4.0
openai>=1.51.0
python-dotenv>=1.0.0
requests>=2.31.0
```

#### API 서버

```txt
fastapi>=0.110.0
uvicorn>=0.30.0
httpx>=0.27.0
```

#### Observability (관찰성)

```txt
azure-monitor-opentelemetry>=1.6.0
azure-monitor-opentelemetry-exporter>=1.0.0b27
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-fastapi>=0.45b0
```

#### Agent Framework (Lab 5) & MCP

```txt
agent-framework>=1.0.0b251016
mcp>=1.1.0
```

#### Jupyter Notebook

```txt
jupyter>=1.0.0
ipykernel>=6.29.0
```

### Codespace 리소스

**기본 제공 리소스:**
- CPU: 2-4 cores
- RAM: 8-16 GB
- Storage: 32 GB

**무료 사용량 (개인 계정):**
- 월 120 코어 시간
- 월 15 GB 스토리지

---

## 로컬 환경 설정

로컬에서 실습을 진행하려면 다음을 수동으로 설치해야 합니다.

> ⚠️ **경고**: 로컬 환경에서는 OS별 설정 차이, 방화벽, 네트워크 정책 등으로 인한 문제가 발생할 수 있습니다. **GitHub Codespace 사용을 강력히 권장합니다.**

### 필수 도구 설치

#### 1. Azure Developer CLI (azd)

**macOS/Linux:**
```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

**Windows (PowerShell):**
```powershell
powershell -ex AllSigned -c "Invoke-RestMethod 'https://aka.ms/install-azd.ps1' | Invoke-Expression"
```

**설치 확인:**
```bash
azd version
```

#### 2. Azure CLI

**macOS:**
```bash
brew install azure-cli
```

**Linux (Ubuntu/Debian):**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Windows:**
- [다운로드 페이지](https://learn.microsoft.com/cli/azure/install-azure-cli-windows)에서 MSI 설치 프로그램 다운로드

**설치 확인:**
```bash
az version
```

#### 3. Python 3.11+

**macOS:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Windows:**
- [python.org](https://www.python.org/downloads/)에서 다운로드

**설치 확인:**
```bash
python3 --version
```

#### 4. Docker Desktop

- [Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop)

**설치 확인:**
```bash
docker --version
docker compose version
```

#### 5. Visual Studio Code

- [VS Code 다운로드](https://code.visualstudio.com/)

**필수 확장 설치:**
```bash
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
code --install-extension ms-azuretools.azure-dev
code --install-extension ms-azuretools.vscode-azureresourcegroups
```

### 로컬 환경 설정

```bash
# 리포지토리 클론
git clone https://github.com/junwoojeong100/agentic-ai-labs.git
cd agentic-ai-labs

# Python 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Jupyter 커널 등록
python -m ipykernel install --user --name=agentic-ai-labs --display-name="Python 3.12 (agentic-ai-labs)"
```

---

## Azure 구독 및 권한

### 필요한 Azure 리소스

이 실습에서 다음 Azure 리소스를 생성합니다:

| 리소스 | 용도 | 예상 비용/월 |
|--------|------|-------------|
| Azure AI Foundry Project | Agent 서비스 | $0 (사용량 기반) |
| Azure OpenAI | GPT-5 모델 | $20-50 (실습 기준) |
| Azure AI Search | RAG 검색 | $10-30 |
| Azure Container Apps | 컨테이너 호스팅 | $10-20 |
| Azure Container Registry | 이미지 저장 | $5 |
| Azure Key Vault | 비밀 관리 | $1 |
| Azure Storage Account | 데이터 저장 | $5 |
| **총 예상 비용** | | **$51-131** |

> 💡 **Tip**: 실습 완료 후 즉시 리소스 그룹을 삭제하면 비용을 최소화할 수 있습니다.

### 필요한 최소 권한 (이론적)

#### RBAC 역할

| 역할 | 용도 | 범위 |
|------|------|------|
| **Contributor** | 리소스 생성 및 관리 | 구독 또는 리소스 그룹 |
| **User Access Administrator** | Managed Identity 역할 할당 | 구독 또는 리소스 그룹 |
| **Cognitive Services Contributor** | Azure OpenAI 관리 | 구독 또는 리소스 그룹 |
| **Search Service Contributor** | Azure AI Search 관리 | 구독 또는 리소스 그룹 |

#### 추가 필요 권한

- ✅ 리소스 그룹 생성 권한
- ✅ 서비스 주체(Service Principal) 생성 권한
- ✅ 역할 할당 권한
- ✅ 리소스 제공자 등록 권한
  - `Microsoft.App` (Container Apps)
  - `Microsoft.CognitiveServices` (OpenAI)
  - `Microsoft.Search` (AI Search)
  - `Microsoft.MachineLearningServices` (AI Foundry)

### 권장 설정: 구독 소유자 ⭐

> **💡 실습 권장 사항**
>
> 위의 개별 역할들을 모두 구성하는 것은 복잡하고 시간이 많이 소요됩니다.
>
> **다음 중 하나를 강력히 권장합니다:**

#### 옵션 1: 구독 소유자 역할 사용 (가장 권장)

**장점:**
- ✅ 모든 리소스 생성 및 역할 할당 자동 가능
- ✅ 권한 문제로 인한 실습 중단 없음
- ✅ 빠른 실습 진행

**필요 권한:**
- 구독 수준에서 `Owner` 역할

#### 옵션 2: 별도의 실습 전용 구독 생성

**장점:**
- ✅ 프로덕션 환경과 격리
- ✅ 비용 추적 용이
- ✅ 실습 완료 후 간단히 정리 가능

**방법:**
1. Azure Portal에서 새 구독 생성
2. 해당 구독의 소유자로 설정
3. 실습 완료 후 전체 구독 정리

#### 옵션 3: 프로덕션 환경 사용 금지

**주의사항:**
- ⚠️ 실습 중 잘못된 설정 가능성
- ⚠️ 예상치 못한 비용 발생 가능
- ⚠️ 기존 리소스에 영향 가능

**권장 조치:**
- 별도의 개발/학습 환경 사용
- 또는 새 구독 생성

---

## 권한 확인 방법

### 현재 사용자 역할 확인

```bash
# Azure 로그인
az login

# 현재 사용자 ID 확인
az ad signed-in-user show --query id -o tsv

# 현재 사용자의 모든 역할 확인
az role assignment list \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --all \
  -o table
```

### 구독 소유자 여부 확인

```bash
# 구독 Owner 역할 확인
az role assignment list \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role Owner \
  --scope /subscriptions/$(az account show --query id -o tsv) \
  -o table
```

**출력 예시:**
```
Principal                            Role    Scope
-----------------------------------  ------  --------------------------------------------------
user@example.com                     Owner   /subscriptions/12345678-1234-1234-1234-123456789012
```

### 필요한 리소스 제공자 확인

```bash
# 등록된 리소스 제공자 확인
az provider list --query "[?registrationState=='Registered'].namespace" -o table

# 특정 제공자 확인
az provider show --namespace Microsoft.App --query registrationState -o tsv
az provider show --namespace Microsoft.CognitiveServices --query registrationState -o tsv
az provider show --namespace Microsoft.Search --query registrationState -o tsv
az provider show --namespace Microsoft.MachineLearningServices --query registrationState -o tsv
```

### 리소스 제공자 등록 (필요 시)

```bash
# Container Apps 제공자 등록
az provider register --namespace Microsoft.App

# Azure OpenAI 제공자 등록
az provider register --namespace Microsoft.CognitiveServices

# AI Search 제공자 등록
az provider register --namespace Microsoft.Search

# AI Foundry 제공자 등록
az provider register --namespace Microsoft.MachineLearningServices

# 등록 완료까지 대기 (몇 분 소요)
az provider show --namespace Microsoft.App --query registrationState -o tsv
```

### 구독 쿼터 확인

```bash
# 현재 구독 ID 확인
az account show --query id -o tsv

# 리전별 쿼터 확인 (예: East US)
az vm list-usage --location eastus -o table

# OpenAI 모델 배포 가능 여부 확인
az cognitiveservices account list-skus --location eastus -o table
```

---

## 문제 해결

### "권한이 부족합니다" 오류

**증상:**
```
ERROR: (AuthorizationFailed) The client 'user@example.com' does not have authorization 
to perform action 'Microsoft.Resources/deployments/write'
```

**해결:**
1. 현재 역할 확인: `az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --all`
2. 구독 관리자에게 `Owner` 또는 `Contributor` 역할 요청
3. 또는 별도의 실습 전용 구독 생성

### "리소스 제공자가 등록되지 않음" 오류

**증상:**
```
ERROR: (MissingSubscriptionRegistration) The subscription is not registered to use 
namespace 'Microsoft.App'
```

**해결:**
```bash
# 필요한 제공자 등록
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Search
az provider register --namespace Microsoft.MachineLearningServices

# 등록 상태 확인 (2-5분 소요)
az provider list --query "[].{Provider:namespace, Status:registrationState}" -o table | grep -E "App|Cognitive|Search|MachineLearning"
```

### "쿼터 초과" 오류

**증상:**
```
ERROR: (QuotaExceeded) Operation could not be completed as it results in exceeding 
approved quota.
```

**해결:**
1. Azure Portal > Subscriptions > Usage + quotas에서 현재 쿼터 확인
2. 다른 리전 시도 (예: `eastus` → `westus2`)
3. Azure 지원팀에 쿼터 증가 요청

### Codespace 생성 실패

**증상:**
```
Failed to create codespace: Resource quota exceeded
```

**해결:**
1. GitHub 계정의 Codespace 사용량 확인
2. 사용하지 않는 Codespace 삭제
3. 필요시 GitHub 플랜 업그레이드

---

## 다음 단계

사전 요구사항을 모두 충족했다면 다음을 진행하세요:

1. ✅ [빠른 시작 가이드](./README.md#-빠른-시작-quick-start)
2. ✅ [Lab 1: Azure 리소스 배포](./01_deploy_azure_resources.ipynb)
3. ✅ [설정 가이드](./CONFIGURATION.md) (필요 시)

---

## 관련 문서

- [README.md](./README.md) - 프로젝트 개요
- [CONFIGURATION.md](./CONFIGURATION.md) - 환경 변수 가이드
- [OBSERVABILITY.md](./OBSERVABILITY.md) - 관찰성 가이드

---

**Built with ❤️ using Azure AI Foundry**
