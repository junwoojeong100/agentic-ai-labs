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
| Azure AI Foundry (AIServices) | Agent 서비스 + OpenAI 모델 통합 | $20-50 (사용량 기반) |
| Azure AI Search | RAG 검색 | $10-30 |
| Azure Container Apps | 컨테이너 호스팅 | $10-20 |
| Azure Container Registry | 이미지 저장 | $5 |
| Azure Key Vault | 비밀 관리 | $1 |
| Azure Storage Account | 데이터 저장 | $5 |
| **총 예상 비용** | | **$51-131** |

> 💡 **참고**: AI Foundry는 Azure OpenAI, Agents, Evaluations 등을 통합한 단일 리소스입니다.  
> 별도의 Azure OpenAI 리소스를 생성할 필요가 없으며, AI Foundry 내에서 모델이 자동 배포됩니다.

> 💡 **Tip**: 실습 완료 후 즉시 리소스 그룹을 삭제하면 비용을 최소화할 수 있습니다.

---

### 권장 설정: 구독 소유자 ⭐

> **� 실습 권장 사항**
>
> 이 실습은 **구독 소유자(`Owner`) 역할**로 진행하도록 설계되었습니다.
> 
> 개별 역할을 수동으로 구성하는 것은 복잡하고 시간이 많이 소요됩니다.  
> 아래 섹션의 개별 역할 설명은 **교육 목적 및 프로덕션 환경 참고용**입니다.

**실습 진행 방법:**

1. **구독 소유자 권한 확인** (필수)
   - 기존 구독에서 `Owner` 역할 보유 확인
   - 또는 별도의 실습 전용 구독 생성 ([구독 생성 가이드](https://learn.microsoft.com/azure/cost-management-billing/manage/create-subscription))

2. **권한 확인 명령어:**
   ```bash
   # Azure 로그인
   az login

   # 구독 Owner 역할 확인
   az role assignment list \
     --assignee $(az ad signed-in-user show --query id -o tsv) \
     --role Owner \
     --scope /subscriptions/$(az account show --query id -o tsv) \
     -o table
   ```

3. **출력 예시 (Owner인 경우):**
   ```
   Principal                            Role    Scope
   -----------------------------------  ------  --------------------------------------------------
   user@example.com                     Owner   /subscriptions/12345678-1234-1234-1234-123456789012
   ```

**장점:**
- ✅ 모든 리소스 생성 및 역할 할당 자동 가능
- ✅ 권한 문제로 인한 실습 중단 없음
- ✅ Bicep 템플릿이 자동으로 필요한 역할 할당
- ✅ 빠른 실습 진행 (권한 설정 불필요)

**⚠️ 주의사항:**
- 프로덕션 구독보다는 **별도의 학습/개발 전용 구독** 사용 권장
- 실습 완료 후 리소스 그룹을 즉시 삭제하여 비용 최소화
- 예상 비용: $50-130 (리소스 즉시 삭제 시)


---

## 권한 확인 방법

### ✅ 1단계: Azure 로그인 및 구독 확인

```bash
# Azure 로그인
az login

# 현재 구독 확인
az account show --query "{Name:name, ID:id, TenantID:tenantId}" -o table

# 여러 구독이 있는 경우 구독 변경
az account set --subscription "<구독-ID>"
```

---

### ✅ 2단계: 구독 소유자 권한 확인 (필수)

```bash
# 구독 Owner 역할 확인
az role assignment list \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role Owner \
  --scope /subscriptions/$(az account show --query id -o tsv) \
  -o table
```

**✅ Owner인 경우 (실습 가능):**
```
Principal                            Role    Scope
-----------------------------------  ------  --------------------------------------------------
user@example.com                     Owner   /subscriptions/12345678-1234-1234-1234-123456789012
```

**❌ Owner가 아닌 경우:**
```
(출력 없음 또는 다른 역할만 표시됨)
```

➡️ **조치:** 구독 관리자에게 Owner 역할 요청 또는 별도의 실습 전용 구독 생성

---

### ✅ 3단계: 리소스 제공자 등록 상태 확인

```bash
# 필수 리소스 제공자 등록 상태 확인
az provider list --query "[?namespace=='Microsoft.CognitiveServices' || namespace=='Microsoft.Search' || namespace=='Microsoft.App' || namespace=='Microsoft.Storage' || namespace=='Microsoft.KeyVault' || namespace=='Microsoft.ContainerRegistry'].{Provider:namespace, Status:registrationState}" -o table
```

**✅ 모두 등록된 경우:**
```
Provider                          Status
--------------------------------  ----------
Microsoft.CognitiveServices       Registered
Microsoft.Search                  Registered
Microsoft.App                     Registered
Microsoft.ContainerRegistry       Registered
Microsoft.Storage                 Registered
Microsoft.KeyVault                Registered
```

**❌ 미등록된 제공자가 있는 경우:**
```bash
# 필수 제공자 일괄 등록 (Owner 권한 필요)
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Search
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.OperationalInsights

# 등록 완료까지 대기 (2-5분 소요)
# 등록 상태 재확인
az provider list --query "[?namespace=='Microsoft.CognitiveServices' || namespace=='Microsoft.Search' || namespace=='Microsoft.App' || namespace=='Microsoft.Storage' || namespace=='Microsoft.KeyVault'].{Provider:namespace, Status:registrationState}" -o table
```


### ✅ 4단계: Azure 쿼터 확인 (선택사항)

```bash
# 현재 구독 ID 확인
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# 선호하는 리전 확인 (예: eastus, koreacentral)
LOCATION="eastus"

# AI Foundry/OpenAI 쿼터 확인 (SKU 목록)
az cognitiveservices account list-skus --location $LOCATION -o table
```

> **💡 Tip:** 쿼터 부족 오류 발생 시 다른 리전을 시도하거나 Azure 지원팀에 쿼터 증가 요청

---

### 📋 권한 확인 체크리스트

실습 시작 전 다음 사항을 모두 확인하세요:

- [ ] Azure 로그인 완료 (`az login`)
- [ ] 구독 Owner 역할 보유 확인
- [ ] 필수 리소스 제공자 등록 완료 (6개)
- [ ] (선택) 쿼터 확인 및 리전 선택

**모두 체크되었다면 실습을 시작할 준비가 완료되었습니다!** 🎉

---

## Notebook별 필요한 역할

각 Notebook에서 필요한 Azure RBAC 역할을 정리한 참고 자료입니다.

### Lab 01: Azure 리소스 배포 (`01_deploy_azure_resources.ipynb`)

**사용자 계정 (👤):**
- `Owner` (구독 수준) - 리소스 생성 및 역할 할당

**자동 할당되는 역할 (Bicep):**
- 사용자 계정: `Azure AI User`, `Cognitive Services User`, `Storage Blob Data Contributor`
- Managed Identity: `Azure AI User`, `Cognitive Services User`

> **💡 참고 - 최소 권한 원칙:**
> - Bicep은 최소 권한 원칙에 따라 `Azure AI User` 역할을 부여합니다.
> - `Azure AI User`는 AI Foundry Project에서 Agent 개발 및 빌드에 필요한 최소 권한을 제공합니다.
> - 더 많은 권한이 필요한 경우 (예: Hub 관리, ML workspace 작업) `Azure AI Developer` 역할로 변경할 수 있습니다.

---

### Lab 02: AI Search RAG 구성 (`02_setup_ai_search_rag.ipynb`)

**사용자 계정 (👤):**
- `Cognitive Services User` - OpenAI 임베딩 API 호출
- `Search Service Contributor` - 인덱스 스키마 생성
- `Search Index Data Contributor` - 문서 업로드
- `Storage Blob Data Contributor` - 데이터 파일 읽기

**Managed Identity (🤖):**
- 해당 없음

---

### Lab 03: Foundry Agent 배포 (`03_deploy_foundry_agent.ipynb`)

**사용자 계정 (👤):**
- `Azure AI User` - Agent 생성 및 관리
- `Cognitive Services User` - OpenAI 모델 호출

**Managed Identity (🤖) - Container Apps:**
- `Azure AI User` - Agent 런타임 실행
- `Cognitive Services User` - 모델 추론
- `Search Index Data Reader` - RAG 검색

---

### Lab 04: Foundry Agent with MAF 배포 (`04_deploy_foundry_agent_with_maf.ipynb`)

**사용자 계정 (👤):**
- `Azure AI User` - Agent 생성 및 관리
- `Cognitive Services User` - OpenAI 모델 호출

**Managed Identity (🤖) - Container Apps:**
- `Azure AI User` - Agent 런타임 실행
- `Cognitive Services User` - 모델 추론
- `Search Index Data Reader` - RAG 검색

---

### Lab 05: MAF Workflow 패턴 (`05_maf_workflow_patterns.ipynb`)

**사용자 계정 (👤):**
- `Azure AI User` - Workflow 실행, Agent 생성
- `Cognitive Services User` - 모델 추론 API 호출

**Managed Identity (🤖):**
- 해당 없음

---

### Lab 06: Agent 평가 (`06_evaluate_agents.ipynb`)

**사용자 계정 (👤):**
- `Azure AI User` - Evaluation 실행, 결과 저장
- `Cognitive Services User` - 평가용 모델 호출 (Judge LLM)

**Managed Identity (🤖):**
- 해당 없음

---

## 역할 요약

**👤 사용자 계정에 필요한 역할 (모든 Notebook):**
```
구독 수준:
- Owner (또는 Contributor + User Access Administrator)

리소스 수준 (Bicep 자동 할당):
- Azure AI User
- Cognitive Services User
- Search Service Contributor
- Search Index Data Contributor
- Storage Blob Data Contributor
```

**🤖 Managed Identity에 필요한 역할 (Lab 03-04 Container Apps):**
```
리소스 수준 (Bicep 자동 할당):
- Azure AI User
- Cognitive Services User
- Search Index Data Reader
```

> **💡 참고:** Lab 01에서 `azd up` 실행 시 Bicep이 자동으로 필요한 역할을 할당하므로 수동 설정이 필요 없습니다.

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
