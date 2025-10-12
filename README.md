# Agentic AI Labs

Azure AI Foundry Agent Service를 활용한 Multi-Agent 시스템 구축 실습 프로젝트입니다. 본 README는 빠른 이해 후 Labs 순서대로 진행하도록 구성되었습니다.

---
📑 Table of Content

Azure AI Foundry Agent Service를 활용한 Multi-Agent 시스템 구축 실습 프로젝트입니다. 본 README는 빠른 이해 후 Labs 순서대로 진행하도록 구성되었습니다.

1. [개요 (Overview)](#개요-overview)
2. [아키텍처](#-아키텍처)
3. [핵심 기능 요약](#핵심-기능-요약)
4. [사전 요구사항](#-사전-요구사항)
5. [빠른 시작 (Quick Start)](#-빠른-시작)
6. [Lab 안내](#lab-안내)
7. [프로젝트 구조](#-프로젝트-구조)
8. [인프라 & 파라미터](#-인프라-파라미터)
9. [환경 변수 & 설정](#환경-변수--설정)
10. [Knowledge Base 관리](#-knowledge-base-관리)
11. [Troubleshooting (요약)](#-문제-해결)
12. [Cleanup](#-리소스-정리-cleanup)
13. [참고 자료](#-참고-자료)
14. [기여하기](#-기여하기)
15. [라이선스](#-라이선스)

> 상세 관찰성(Tracing, Analytics) 심화는 별도 문서: `OBSERVABILITY.md`

---
## 🎯 개요 (Overview)

이 실습은 **GitHub Codespace** 환경에서 진행되도록 설계되었으며, 다음 Core Pillars를 다룹니다:

| Pillar | 설명 | 핵심 요소 |
|--------|------|-----------|
| Multi-Agent Orchestration | Main / Tool / Research Agent 연결 및 라우팅 | Connected Agents, MCP, RAG | 
| Retrieval-Augmented Generation | Azure AI Search 기반 지식 검색 결합 | Hybrid (Vector + BM25), Embeddings |
| Tool & Protocol Integration | MCP(Model Context Protocol) 도구 호출 | FastMCP, External Utilities |
| Observability & Tracing | Prompt/Completion 포함 실행 추적 | OpenTelemetry, Application Insights |

> **💡 실습 환경**  
> GitHub Codespace에 최적화되어 사전 도구(Azure CLI, azd, Python, Docker)가 준비되어 별도 설치가 최소화됩니다.

**학습 후 할 수 있는 것 (Learning Outcomes)**
- Azure AI Foundry Project 기반 Multi-Agent 시스템 아키텍처 이해 및 배포
- RAG + MCP + Orchestration 결합 패턴 구현
- Application Analytics vs Tracing 차이와 활용 전략 수립
- Prompt/Completion(Content Recording) 포함 추적 및 운영 시 마스킹/샘플링 고려 적용

**요약 TL;DR**: “이 레포는 RAG + MCP + Multi-Agent + Observability(Tracing + Analytics)를 한 번에 실습하는 통합 패턴 모음입니다.”

## 🏗️ 아키텍처

```
┌────────────────────────────────────────────────────────────┐
│                 Multi-Agent System                         │
│                                                            │
│  ┌─────────────────────────────────────────────┐          │
│  │          Main Agent                         │          │
│  │  (Task Analysis & Agent Routing)            │          │
│  └────────────┬────────────────┬────────────────┘          │
│               │                │                           │
│       ┌───────▼──────┐  ┌──────▼──────────┐               │
│       │  Tool Agent  │  │  Research       │               │
│       │  (MCP)       │  │  Agent (RAG)    │               │
│       └──────┬───────┘  └────────┬────────┘               │
│              │                   │                         │
│       ┌──────▼───────┐    ┌──────▼─────────┐              │
│       │  MCP Server  │    │  Azure AI      │              │
│       │  (ACA)       │    │  Search (RAG)  │              │
│       └──────────────┘    └────────────────┘              │
└────────────────────────────────────────────────────────────┘
```

### 주요 컴포넌트

- **Main Agent**: 사용자 요청 분석 및 Connected Agent를 통한 하위 Agent 라우팅
- **Tool Agent**: MCP 서버의 도구 활용 (실시간 날씨 정보)
- **Research Agent**: Azure AI Search를 통한 RAG 기반 지식 베이스 검색
- **MCP Server**: Azure Container Apps에 배포된 FastMCP 기반 도구 서버

## ⚙️ 핵심 기능 요약

### Azure AI Foundry Agent Service
- **Agent 생성 및 관리**: GPT-5 기반 전문화된 Agent
- **Connected Agent Pattern**: Agent 간 연결을 통한 협업
- **Tool Integration**: Azure AI Search, MCP Tools, Function Calling
- **Thread 관리**: 대화 컨텍스트 유지

### Multi-Agent 시스템 구성
- **Main Agent (Orchestrator)**: 
  - 사용자 요청 분석 및 적절한 Agent 선택
  - Connected Agent를 통한 하위 Agent 호출
  - 여러 Agent 응답 통합 및 최종 답변 생성
  
- **Tool Agent**:
  - MCP 서버와 연동하여 외부 도구 활용
  - **실시간 날씨 정보**: 전 세계 도시의 정확한 날씨 데이터 제공
  - HTTP 기반 MCP 클라이언트 구현
  
- **Research Agent**:
  - Azure AI Search를 통한 RAG 구현
  - 하이브리드 검색 (벡터 + 키워드)
  - 지식 베이스 기반 답변 생성
  - **자동 Citation 기능**: 
    - Azure AI Foundry SDK가 자동으로 출처 표시 (예: `【3:0†source】`)
    - Tracing UI에서 각 citation 클릭 시 원본 문서 확인 가능
    - 코드 구현 없이 SDK 내장 기능으로 자동 생성

### MCP (Model Context Protocol) Server
- **실시간 날씨 정보 서비스**:
  - `get_weather(location)`: 전 세계 도시의 정확한 실시간 날씨 정보
  - **데이터 소스**: wttr.in API (무료, API 키 불필요)
  - **지원 언어**: 한글/영어 도시명 모두 지원 (예: 'Seoul', '서울')
  - **제공 정보**: 
    - 현재 온도 및 체감 온도
    - 날씨 상태 (맑음, 흐림, 비 등)
    - 습도 및 풍속/풍향
    - 관측 시간
- **FastMCP 프레임워크**: Python 기반 간편한 MCP 서버 구현
- **Azure Container Apps 배포**: 확장 가능한 서버리스 호스팅
- **HTTP/SSE 엔드포인트**: `/mcp` 경로로 MCP 프로토콜 제공

### RAG (Retrieval-Augmented Generation)
- **Azure AI Search 통합**: 벡터 + 키워드 하이브리드 검색
- **Embedding 모델**: Azure OpenAI text-embedding-3-large (3072차원)
- **지식 베이스**: 54개 AI Agent 관련 문서 (카테고리별 청킹)
- **검색 최적화**: Top-K=5, Semantic Ranker 적용

#### 📐 RAG 인덱스 스키마

**Lab 2에서 실제로 생성하는 인덱스 스키마는 다음과 같습니다:**

| 필드 | 타입 | 용도 | 벡터 설정 |
|------|------|------|----------|
| **id** | Edm.String | 문서 고유 식별자 (key) | - |
| **title** | Edm.String | 문서 제목 (searchable, filterable) | - |
| **content** | Edm.String | 본문 전체 텍스트 (searchable) | - |
| **category** | Edm.String | 문서 분류 (filterable, facetable) | - |
| **section** | Edm.String | 섹션 이름 (filterable) | - |
| **contentVector** | Collection(Single) | 텍스트 임베딩 벡터 | dimensions=**3072** (text-embedding-3-large) |

**중요 구성 사항:**

1. **벡터 검색 알고리즘**: HNSW (Hierarchical Navigable Small World)
   - `m`: 4 (연결 수)
   - `efConstruction`: 400 (인덱싱 품질)
   - `metric`: cosine (코사인 유사도)

2. **하이브리드 검색**: 
   - Vector Search (contentVector 필드, 3072차원)
   - Keyword Search (title, content 필드, BM25 알고리즘)

3. **필수 일치 사항**:
   - ⚠️ `contentVector` 차원은 **반드시 3072**이어야 합니다 (text-embedding-3-large 모델 출력)
   - 3072차원(text-embedding-3-small)과 호환되지 않음

> **상세 구현**: 스키마 생성 코드는 [`02_setup_ai_search_rag.ipynb`](./02_setup_ai_search_rag.ipynb) 섹션 6 "Azure AI Search 인덱스 생성"을 참조하세요.

## 🧩 인프라 & 리소스 개요

### 배포 후 생성되는 리소스

| 리소스 | 용도 | 특징 |
|--------|------|------|
| Azure AI Foundry Project | Agent 및 AI 서비스 통합 | **Hub-less 독립형 프로젝트 (GA)** |
| Azure OpenAI | GPT-5 모델, 텍스트 임베딩 | text-embedding-3-large 포함 |
| Azure AI Search | RAG 지식 베이스 | 벡터 검색, 하이브리드 쿼리 |
| Azure Container Apps | MCP 서버 및 Agent API 호스팅 | 자동 스케일링, Managed Identity |
| Azure Container Registry | 컨테이너 이미지 저장 | Private registry |
| Azure Key Vault | 비밀 및 키 관리 | RBAC 통합 |
| Azure Storage Account | 데이터 및 로그 저장 | Blob, Table, Queue |

> **Azure AI Foundry Project 구조**  
> 이 실습에서는 **Hub 없이 Standalone AI Foundry Project**를 직접 생성하여 사용합니다. 이전의 Hub + Project 구조 대신, 프로젝트 단독으로 필요한 모든 리소스(OpenAI, AI Search 등)를 연결하여 더 간단하고 경량화된 아키텍처를 구현합니다.

> **Key Vault 사용 안내**  
> Azure Key Vault는 Bicep 템플릿을 통해 배포되지만, 현재 이 실습에서는 직접 사용하지 않습니다. Azure AI Search API 키는 Azure CLI를 통해 직접 조회하여 사용합니다. 향후 프로덕션 환경에서는 Key Vault를 활용하여 다음과 같은 시크릿을 안전하게 관리할 수 있습니다:
> - Azure AI Search Admin Key
> - OpenAI API Key  
> - Database Connection Strings
> - Container Apps에서 Key Vault Reference를 통한 시크릿 주입
> - Managed Identity 기반 접근 제어

> **Storage Account 사용 안내**  
> Azure Storage Account도 인프라 배포 시 생성되지만, 이번 실습에서는 직접 사용하지 않습니다. 현재 실습에서는 JSON 파일 기반으로 AI Search 인덱스를 생성하므로 Blob Storage가 필요하지 않습니다. 향후 확장 시나리오에서는 Storage Account를 다음과 같이 활용할 수 있습니다:
> - AI Search의 데이터 소스로 Blob Storage 연결 (문서, PDF 등)
> - Agent 실행 로그 및 대화 기록 저장
> - 대용량 파일 업로드/다운로드 처리
> - Queue Storage를 통한 비동기 작업 처리
> - Table Storage를 활용한 메타데이터 관리

## ✅ 사전 요구사항

### 실습 환경: GitHub Codespace

이 실습은 **GitHub Codespace**에서 진행하도록 설계되었습니다.

#### Codespace 환경 구성 (자동 설정됨)
Codespace가 시작되면 다음 도구들이 자동으로 설치되어 있습니다:

**기본 도구 및 런타임:**
- ✅ Azure Developer CLI (azd)
- ✅ Azure CLI (az)
- ✅ Python 3.11+
- ✅ Docker
- ✅ Git
- ✅ Visual Studio Code (Web/Desktop)

**VS Code 확장:**
- ✅ Python 확장 (ms-python.python)
- ✅ Pylance (ms-python.vscode-pylance)
- ✅ Jupyter Notebook (ms-toolsai.jupyter)
- ✅ Azure Developer CLI (ms-azuretools.azure-dev)
- ✅ Azure Resources (ms-azuretools.vscode-azureresourcegroups)
- ✅ Bicep (ms-azuretools.vscode-bicep)
- ✅ GitHub Copilot (GitHub.copilot)

**Python 패키지 (자동 설치됨):**

Codespace 시작 시 다음 패키지들이 자동으로 설치됩니다:
- `azure-identity`, `azure-ai-projects`, `azure-ai-inference` - Azure AI 서비스
- `azure-search-documents` - Azure AI Search
- `openai`, `python-dotenv`, `requests` - 기본 유틸리티
- `fastapi`, `uvicorn`, `httpx` - API 서버
- `azure-monitor-opentelemetry`, `azure-monitor-opentelemetry-exporter` - Observability
- `opentelemetry-api`, `opentelemetry-sdk` - OpenTelemetry 코어
- `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-requests`, `opentelemetry-instrumentation-httpx` - 계측
- `agent-framework[azure-ai]>=1.0.0b251007` - Microsoft Agent Framework
- `fastmcp>=0.2.0`, `mcp>=1.1.0` - Model Context Protocol

> **💡 참고**: 패키지들은 시스템 전역에 설치되므로, 별도의 가상환경 설정 없이 바로 노트북을 실행할 수 있습니다. 설치 내용은 `.devcontainer/devcontainer.json`의 `postCreateCommand`에 정의되어 있습니다.

#### 로컬 환경에서 실습하는 경우
로컬에서 실습을 진행하려면 다음을 수동으로 설치해야 합니다:
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- Python 3.9 이상 (권장: Python 3.11+)
- Docker Desktop
- Visual Studio Code + Jupyter 확장

> **⚠️ 권장 사항**: GitHub Codespace 사용을 강력히 권장합니다. 로컬 환경에서는 OS별 설정 차이, 방화벽, 네트워크 정책 등으로 인한 문제가 발생할 수 있습니다.

### Azure 구독 및 권한 요구사항

#### 필요한 최소 권한 (이론적)
이 실습을 완료하기 위해 이론적으로 필요한 Azure RBAC 역할:

| 역할 | 용도 | 범위 |
|------|------|------|
| **Contributor** | 리소스 생성 및 관리 (Azure AI Foundry, OpenAI, AI Search, Container Apps 등) | 구독 또는 리소스 그룹 |
| **User Access Administrator** | Managed Identity에 역할 할당 (Container Apps → AI Foundry Project) | 구독 또는 리소스 그룹 |
| **Cognitive Services Contributor** | Azure OpenAI 서비스 배포 및 모델 관리 | 구독 또는 리소스 그룹 |
| **Search Service Contributor** | Azure AI Search 인덱스 생성 및 관리 | 구독 또는 리소스 그룹 |
| **Key Vault Administrator** | Key Vault 생성 및 비밀 관리 (선택사항) | 구독 또는 리소스 그룹 |

추가로 필요한 작업 권한:
- 리소스 그룹 생성 권한
- 서비스 주체(Service Principal) 생성 권한 (azd 배포 시)
- 역할 할당 권한 (Managed Identity 설정)
- Azure AI Foundry 리소스 제공자 등록 권한

#### 권장 설정: 구독 소유자

> **⚠️ 실습 권장 사항**  
> 
> 위의 개별 역할들을 모두 구성하는 것은 복잡하고 시간이 많이 소요됩니다. **실습을 원활하게 진행하기 위해 다음 중 하나를 권장합니다:**
>
> 1. **구독 소유자(Owner) 역할 사용** (가장 권장)
>    - 모든 리소스 생성 및 역할 할당이 자동으로 가능
>    - 권한 문제로 인한 실습 중단 없음
>    - 구독 수준에서 `Owner` 역할 필요
>
> 2. **별도의 실습 전용 구독 사용**
>    - 개인 또는 팀 학습용 Azure 구독 생성
>    - 해당 구독의 소유자로 설정
>    - 실습 완료 후 전체 리소스 그룹 삭제로 정리
>
> 3. **프로덕션 환경에서 실습하지 않기**
>    - 실습 중 잘못된 설정이나 비용 발생 가능
>    - 별도의 개발/학습 환경 사용 권장

**권한 확인 방법:**

```bash
# 현재 사용자의 역할 확인
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --all

# 구독 소유자 여부 확인
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role Owner --scope /subscriptions/$(az account show --query id -o tsv)
```

## 🚀 빠른 시작 (Quick Start)

### 1. GitHub Codespace 시작

#### 방법 1: GitHub 웹사이트에서
1. 이 리포지토리 페이지에서 **Code** 버튼 클릭
2. **Codespaces** 탭 선택
3. **Create codespace on main** 클릭
4. Codespace 환경이 자동으로 구성됩니다 (2-3분 소요)

#### 방법 2: VS Code Desktop에서
1. VS Code에서 Command Palette 열기 (`Cmd+Shift+P` 또는 `Ctrl+Shift+P`)
2. "Codespaces: Create New Codespace" 입력
3. 리포지토리 선택: `junwoojeong100/agentic-ai-labs`
4. Branch 선택: `main`

### 2. 실습 노트북 실행

실습은 3개의 Jupyter 노트북으로 구성되어 있습니다:

#### 📓 Lab 1: [01_deploy_azure_resources.ipynb](./01_deploy_azure_resources.ipynb)
**섹션 구조:**
1. 사전 요구 사항 확인 (Prerequisites Check)
2. Azure 인증 (Azure Authentication)
3. 환경 변수 설정 (Environment Configuration)
4. 모델 설정 (Configure Model)
5. 인프라 배포 (Deploy Infrastructure)
6. 배포 결과 확인 (Verify Deployment)
7. 주요 리소스 연결 정보 저장 (Save Configuration)
8. Azure Portal에서 확인 (Verify in Azure Portal)
9. 배포 완료 및 요약 (Deployment Summary)

**주요 내용:**
- Azure Developer CLI (azd)를 사용한 인프라 배포
- Azure AI Foundry Project 생성 (Hub-less)
- Azure OpenAI, AI Search, Container Apps 등 필수 리소스 프로비저닝
- config.json 파일 자동 생성 및 저장

> **💡 설정 변경 포인트:**
> - **모델 변경**: 섹션 4의 `model_name`, `model_version` 변수만 수정
> - **리전 변경**: 섹션 3의 `location` 변수만 수정 (Quota 부족 시)

#### 📓 Lab 2: [02_setup_ai_search_rag.ipynb](./02_setup_ai_search_rag.ipynb)
**섹션 구조:**
1. 사전 요구 사항 확인 (Prerequisites Check)
2. 패키지 설치 및 설정 로드 (Install Packages & Load Configuration)
3. Azure 인증 (Azure Authentication)
4. 지식 베이스 데이터 로드 (Load Knowledge Base Data)
5. Azure AI Search 인덱스 생성 (Create Search Index)
6. 문서 임베딩 및 업로드 (Generate Embeddings & Upload)
7. 하이브리드 검색 테스트 (Hybrid Search Test)

**주요 내용:**
- AI Search 인덱스 스키마 설계 (벡터 + 키워드)
- Azure OpenAI로 텍스트 임베딩 생성 (text-embedding-3-large)
- 54개 AI Agent 관련 문서 인덱싱
- 하이브리드 검색 (Vector + BM25) 실행 및 검증

#### 📓 Lab 3: [03_deploy_foundry_agent.ipynb](./03_deploy_foundry_agent.ipynb)
**섹션 구조:**
1. 환경 설정 및 인증 (Setup & Authentication)
2. Azure AI Search 키 가져오기 (Get Search Key)
3. Azure AI Search 연결 추가 (Add Azure AI Search Connection)
4. MCP Server 배포 (Deploy MCP Server)
5. Agent Container 빌드 및 배포 (Build & Deploy Agent Container)
   - 5.1. Azure 리소스 확인 (Verify Azure Resources)
   - 5.2. Agent Service 배포 및 권한 설정 (Deploy with Permissions)
   - 5.2.1. Agent Service 시작 (Start Agent Service)
6. 배포된 Agent 테스트 (Test Deployed Agent via HTTP)

**주요 내용:**
- MCP Server를 Azure Container Apps에 배포 (날씨, 계산기 등 도구)
- Multi-Agent 시스템 구축 (Main, Tool, Research Agent)
- Managed Identity 기반 RBAC 권한 설정
- Connected Agent 패턴으로 Agent 간 협업 구현
- **자동 환경 변수 설정**: Application Insights + OpenTelemetry 설정이 `.env` 파일에 자동 생성
- **10개의 다양한 테스트 케이스**: Tool Agent(5), Research Agent(3), 복합 질의(2)
- 실제 질의를 통한 Multi-Agent 오케스트레이션 검증

#### 📓 Lab 4: [04_deploy_agent_framework.ipynb](./04_deploy_agent_framework.ipynb)
**섹션 구조:**
1. 환경 설정 및 인증 (Setup & Authentication)
2. Azure AI Search 키 가져오기 (Get Search Key)
3. Agent Framework Container 빌드 및 배포 (Build & Deploy Container)
4. Azure 리소스 확인 및 Agent Framework Service 배포 (Deploy with Permissions)
5. Agent Framework Service 시작 (Start Service)
6. 배포된 Agent Framework 테스트 (Test Deployed Workflow)
   - 6.1. Workflow Pattern 테스트 (다양한 질문)
7. 정리 및 비교 (Summary & Comparison)

**주요 내용:**
- Microsoft Agent Framework의 Workflow Pattern 구현
- Router Executor 기반 AI 의도 분류 (rule-based / ai-based)
- Tool, Research, General, Orchestrator Executor 구성
- Workflow Context를 통한 메시지 라우팅
- **OpenTelemetry 트레이싱 완전 구현**
  - Azure Monitor + Application Insights 통합
  - FastAPI 자동 계측 (HTTP 요청 추적)
  - Azure AI Inference 자동 계측 (LLM 호출 추적)
  - 커스텀 Span 구현 (Router, Executor, MCP, RAG)
  - PII 마스킹 유틸리티 (Standard/Strict 모드)
- Connected Agent vs Workflow Pattern 아키텍처 비교
- **10개 테스트 케이스**: Tool(4), Research(3), Orchestrator(2), General(1)


## 📁 프로젝트 구조

```
agentic-ai-labs/
├── infra/                                  # Bicep 인프라 코드
│   ├── main.bicep                          # 메인 Bicep 템플릿
│   ├── main.parameters.json                # 파라미터 파일
│   └── core/                               # 모듈화된 Bicep 리소스
│       ├── ai/                             # AI Foundry, OpenAI
│       ├── host/                           # Container Apps
│       ├── search/                         # AI Search
│       └── security/                       # Key Vault, RBAC
│
├── src/                                    # 소스 코드
│   ├── foundry_agent/                      # Multi-Agent 구현 (Foundry Agent Service)
│   │   ├── main_agent.py                   # Main Agent (오케스트레이터)
│   │   ├── tool_agent.py                   # Tool Agent (MCP 연동)
│   │   ├── research_agent.py               # Research Agent (RAG)
│   │   ├── api_server.py                   # Agent API 서버
│   │   ├── masking.py                      # PII 마스킹 유틸리티
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── agent_framework/                    # Agent Framework Workflow
│   │   ├── main_agent_workflow.py          # Workflow Router & Orchestrator
│   │   ├── tool_agent.py                   # Tool Executor (MCP)
│   │   ├── research_agent.py               # Research Executor (RAG)
│   │   ├── api_server.py                   # Workflow API 서버
│   │   ├── test_workflow.py                # Workflow 테스트
│   │   ├── masking.py                      # PII 마스킹 유틸리티
│   │   ├── requirements.txt                # OpenTelemetry 패키지 포함
│   │   └── Dockerfile
│   └── mcp/                                # MCP 서버
│       ├── server.py                       # FastMCP 도구 서버
│       ├── requirements.txt
│       └── Dockerfile
│
├── data/                                   # 지식 베이스
│   └── knowledge-base.json                 # AI Search 인덱싱용 문서
│
├── scripts/                                # 유틸리티 스크립트
│   └── generate_knowledge_base.py
│
├── 01_deploy_azure_resources.ipynb        # Lab 1 노트북
├── 02_setup_ai_search_rag.ipynb           # Lab 2 노트북
├── 03_deploy_foundry_agent.ipynb          # Lab 3 노트북
├── 04_deploy_agent_framework.ipynb        # Lab 4 노트북
├── azure.yaml                              # azd 설정
├── config.json                             # 배포 설정 (자동 생성)
├── OBSERVABILITY.md                        # 관찰성(Tracing/Analytics) 심화 가이드
└── README.md                               # 이 파일
```

## �️ 인프라 파라미터

`infra/main.parameters.json`에서 커스터마이즈 가능:

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `environmentName` | 환경 이름 | 자동 생성 |
| `location` | Azure 리전 | `eastus` |
| `principalId` | 사용자 Principal ID | 자동 감지 |

주요 리소스는 Bicep 템플릿에서 자동으로 생성되며, 리소스 이름은 고유성을 위해 해시가 추가됩니다.

## 🌐 환경 변수 & 설정

배포 후 `config.json`에 자동 저장되는 설정:

```json
{
  "resource_group": "rg-aiagent-xxxxx",
  "location": "eastus",
  "project_connection_string": "https://xxx.services.ai.azure.com/api/projects/yyy",
  "search_endpoint": "https://srch-xxx.search.windows.net/",
  "search_service_name": "srch-xxx",
  "search_index": "ai-agent-knowledge-base",
  "container_registry_endpoint": "crxxx.azurecr.io",
  "container_apps_environment_id": "/subscriptions/.../managedEnvironments/...",
  "mcp_endpoint": "https://mcp-server.xxx.azurecontainerapps.io",
  "agent_endpoint": "https://agent-service.xxx.azurecontainerapps.io"
}
```

**주요 필드 설명:**
- `project_connection_string`: Azure AI Foundry 프로젝트 연결 문자열
- `search_index`: AI Search 인덱스 이름 (RAG용)
- `mcp_endpoint`: 배포된 MCP 서버 엔드포인트
- `agent_endpoint`: Agent API 서버 엔드포인트 (향후 REST API 제공)

### Agent Container 환경 변수 (현행화)

Lab 3 실행 시 `src/foundry_agent/.env` 파일이 **자동 생성**되며 아래 구조를 기본 포함합니다. 일부 선택 변수는 목적에 따라 추가됩니다.

```properties
# Azure AI Foundry
PROJECT_CONNECTION_STRING=https://xxx.services.ai.azure.com/api/projects/yyy

# Azure AI Search (RAG)
SEARCH_ENDPOINT=https://srch-xxx.search.windows.net/
SEARCH_KEY=xxx
SEARCH_INDEX=ai-agent-knowledge-base

# MCP Server
MCP_ENDPOINT=https://mcp-server.xxx.azurecontainerapps.io

# Application Insights (Metrics / Logs / Traces Export)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;...

# OpenTelemetry Core
OTEL_SERVICE_NAME=azure-ai-agent
OTEL_TRACES_EXPORTER=azure_monitor
OTEL_METRICS_EXPORTER=azure_monitor
OTEL_LOGS_EXPORTER=azure_monitor
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

# GenAI Content Recording (Prompt/Completion 표시; Dev/Debug 권장)
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true

# (선택) PII 마스킹 / 운영 모드 전략
AGENT_MASKING_MODE=standard  # standard|strict|off (코드에서 선택적으로 활용)

# (선택) 샘플링 – 고트래픽 환경에서 비용/저장 최적화
# OTEL_TRACES_SAMPLER=parentbased_traceidratio
# OTEL_TRACES_SAMPLER_ARG=0.2   # 20% 샘플링 예시

# (선택) PII 마스킹 정책 커스텀 플래그 (코드에서 해석 구현 가능)
# AGENT_MASKING_MODE=standard   # standard|strict|off
```

#### 필수 / 선택 구분
| 분류 | 변수 | 설명 |
|------|------|------|
| 필수 | PROJECT_CONNECTION_STRING | AI Foundry Project 식별자 |
| 필수 | SEARCH_ENDPOINT / SEARCH_KEY / SEARCH_INDEX | RAG 인덱스 접근 |
| 필수 | MCP_ENDPOINT | MCP 도구 호출 경로 |
| 필수 | APPLICATIONINSIGHTS_CONNECTION_STRING | App Insights Export 대상 |
| 필수 | OTEL_SERVICE_NAME | 서비스 논리 이름(Trace Grouping) |
| 권장 | AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED | Tracing UI Input/Output 표시 |
| 선택 | OTEL_TRACES_SAMPLER / ARG | 트레이스 비율 조절 |
| 선택 | AGENT_MASKING_MODE | 프롬프트/응답 마스킹 전략 선택 |

> - `AGENT_MASKING_MODE` → off / standard / strict (기본: off)

> `AGENT_MASKING_MODE` 는 제공되는 샘플 마스킹 유틸(`src/foundry_agent/masking.py`)과 연동하여 prompt/completion 기록 전 민감정보 기본 정규식 마스킹을 적용할 때 사용할 수 있습니다. (없으면 무시)

---

#### Content Recording 운영 가이드
| 환경 | 권장 값 | 비고 |
|------|---------|------|
| Dev / QA | true | 디버깅/튜닝 편의 |
| Staging | true + 마스킹 | 실제 유사 데이터 검증 |
| Prod (민감) | false (또는 요약 후 저장) | 규제/보안 고려 |
| Prod (비민감) | true + 샘플링 | 품질/행동 분석 |

#### 중요 사항
- 이 `.env` 는 **이미지 빌드 시 포함** → 값 변경 후 반드시 재빌드 & 재배포 필요
- 민감 키는 Git에 커밋 금지 (`.gitignore` 유지)
- 샘플링 활성화 시 Tracing UI 일부 요청만 표시될 수 있음(의도된 동작)
- Content Recording 비활성화 시에도 메트릭은 계속 전송됨

#### 변경 적용 절차 (요약)
1. `.env` 수정 (또는 Lab 3 재생성 셀 실행)
2. Docker 이미지 재빌드
3. Container Apps 새 revision 배포
4. (선택) Kusto Logs로 반영 여부 즉시 확인

---

## 📊 Observability: Monitoring & Tracing

Azure AI Foundry Agent 시스템의 운영 관찰성을 위한 **Monitoring**과 **Tracing** 기능을 제공합니다.

### 핵심 개념

| 기능 | 목적 | 데이터 타입 |
|------|------|------------|
| **Monitoring** | 시스템 헬스, SLA, 성능 추세 | 집계 메트릭 (호출 수, 지연, 오류율, 토큰) |
| **Tracing** | 실행 흐름, 디버깅, 품질 분석 | Span Tree, Prompt/Completion |

### 이 실습에서 구현된 내용

- ✅ **Lab 3 (Foundry Agent)**: Azure Agent Service 자동 계측
- ✅ **Lab 4 (Agent Framework)**: 커스텀 OpenTelemetry 완전 구현

### 상세 가이드

Monitoring과 Tracing의 차이, 설정 방법, 운영 전략 등 모든 내용은 **[OBSERVABILITY.md](./OBSERVABILITY.md)** 문서를 참조하세요:

- 🎯 Monitoring vs Tracing 상세 비교
- ⚙️ 단계별 설정 가이드 (환경 변수, 코드 구현)
- 🔍 Span 구조와 커스텀 계측
- 📋 Content Recording 운영 전략
- 🔧 샘플링, PII 마스킹, Troubleshooting
- 📊 Kusto 쿼리 예제

---
## 🧹 리소스 정리 (Cleanup)
학습 완료 후 비용을 줄이기 위해 전체 리소스를 제거하려면 **리소스 그룹 삭제**가 가장 간단합니다.

```bash
# config.json 에서 resource_group 값 확인
cat config.json | grep resource_group

# 리소스 그룹 삭제 (복구 불가 주의)
az group delete --name <resource-group-name> --yes --no-wait
```

세부적으로 선택 삭제를 원할 경우:
```bash
# Container Apps 환경 & 앱 목록
az containerapp list --resource-group <rg> -o table

# AI Search 인덱스 삭제
az search index delete --name ai-agent-knowledge-base \
  --service-name <search-service-name> \
  --resource-group <rg>

# ACR 이미지 목록/삭제
az acr repository list --name <acrName> -o table
az acr repository delete --name <acrName> --image agent-service:latest --yes
az acr repository delete --name <acrName> --image mcp-server:latest --yes
```

> 삭제 전 비용 추적은 Azure Portal > Cost Management 또는 `az costmanagement query` 사용.

---

### Azure Developer CLI (azd) 설정

`azure.yaml` 파일은 azd 배포를 위한 메타데이터를 정의합니다:

```yaml
name: ai-foundry-agent-lab
infra:
  path: ./infra
  module: main
```

**azd 사용 범위:**
- **Lab 1**: `azd provision` 명령으로 Azure 인프라 배포 (Bicep 템플릿 기반)
  - Azure AI Foundry Project, OpenAI, AI Search, Container Apps Environment 등 생성
  - Container Apps는 생성하지 않고 인프라만 프로비저닝 (약 3-5분 소요)
- **Lab 3**: Container 배포는 `az containerapp create` 명령으로 수동 진행
  - MCP Server 및 Agent Service 배포
  - 더 세밀한 제어와 학습 목적으로 수동 배포 방식 사용

**참고:** 
- azd는 인프라 프로비저닝(Lab 1)에 주로 사용됩니다
- 애플리케이션 배포(Lab 3)는 학습 목적상 단계별로 수동 실행합니다
- `azd up` 대신 `azd provision`을 사용하여 인프라만 빠르게 구성합니다

## 📚 Knowledge Base 관리

지식 베이스 문서를 수정하려면:

```bash
# 1. data/knowledge-base.json 직접 편집

# 2. 또는 스크립트로 생성 (커스텀 마크다운에서)
python3 scripts/generate_knowledge_base.py
```

현재 지식 베이스 내용:
- AI Agent 개발 패턴
- RAG 구현 방법
- Model Context Protocol (MCP)
- 배포 전략
- 아키텍처 패턴

## 🐛 문제 해결 (요약 Troubleshooting)

### Agent 생성 실패
```bash
# Azure AI Foundry 프로젝트 확인 (Hub-less Project)
# Azure Portal에서 프로젝트 연결 문자열 및 리소스 ID 확인:
# https://ai.azure.com > 프로젝트 선택 > Settings > Project properties

# config.json에서 프로젝트 연결 문자열 확인
cat config.json | grep project_connection_string

# Managed Identity 권한 확인
az role assignment list \
  --assignee <managed-identity-principal-id> \
  --scope <project-resource-id>
```

**일반적인 원인:**
- Container App의 Managed Identity에 Azure AI User 역할 미할당
- 역할 전파 시간 부족 (최대 5-10분 소요)
- project_connection_string 형식 오류 (형식: `https://<region>.services.ai.azure.com/api/projects/<project-id>`)
- Azure AI Foundry Project 리소스가 제대로 생성되지 않음

### MCP 서버 배포 실패
```bash
# Container App 로그 확인
az containerapp logs show \
  --name mcp-server \
  --resource-group <rg-name> \
  --follow

# Container Registry 인증 확인
az acr login --name <registry-name>

# Container App 상태 확인
az containerapp show \
  --name mcp-server \
  --resource-group <rg-name> \
  --query properties.runningStatus
```

**일반적인 원인:**
- Docker 이미지 빌드 실패 (플랫폼 불일치: linux/amd64 필요)
- Container Registry 접근 권한 부족
- 포트 설정 오류 (target-port는 8000이어야 함)

### AI Search 인덱싱 실패
```bash
# 인덱스 존재 확인
az search index show \
  --service-name <search-name> \
  --name ai-agent-knowledge-base

# 관리 키 확인
az search admin-key show \
  --service-name <search-name> \
  --resource-group <rg-name>

# 인덱서 상태 확인 (있는 경우)
az search indexer show-status \
  --service-name <search-name> \
  --name <indexer-name>
```

**일반적인 원인:**
- 잘못된 벡터 차원 (3072이어야 함)
- 인덱스 스키마 불일치
- Embedding 모델 배포 안 됨 (text-embedding-3-large)

### Python 패키지 버전 충돌
```bash
# 가상 환경 재생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r src/foundry_agent/requirements.txt
pip install -r src/mcp/requirements.txt
```

**참고:** Azure AI SDK는 빠르게 업데이트되므로 최신 버전 사용을 권장합니다.


**참고:** Azure AI SDK는 빠르게 업데이트되므로 최신 버전 사용을 권장합니다.

---

## 🔄 모델 변경하기

프로젝트는 **환경변수 중심 설계**로 코드 수정 없이 모델을 변경할 수 있습니다.

> **🎯 핵심: 모델 변경은 딱 1곳만!**  
> **Lab 1 노트북**의 `model_name`과 `model_version` 변수만 수정하면 전체 프로젝트에 자동 반영됩니다.  
> 다른 파일 수정 불필요!

### 변경 방법

**Lab 1 노트북**에서 모델명과 버전을 변경하여 배포하세요:

```python
# 01_deploy_azure_resources.ipynb 에서
model_name = "gpt-5"           # 👈 원하는 모델로 변경
model_version = "2025-08-07"   # 👈 모델 버전 (모델에 따라 다름)
model_capacity = 50            # TPM 용량
```

배포 후에는 `.env` 파일의 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 환경변수만 변경하면 됩니다.

### 지원 모델 예시

| 모델명 | 버전 | 특징 |
|--------|------|------|
| `gpt-5` | `2025-08-07` | 논리 중심 및 다단계 작업 최적화 (기본값) |
| `gpt-5-chat` | `2025-08-07` | 고급 대화형, 멀티모달, 컨텍스트 인식 |
| `gpt-5-mini` | `2025-08-07` | 경량 버전, 비용 효율적 |
| `gpt-5-nano` | `2025-08-07` | 속도 최적화, 저지연 애플리케이션 |

**주요 기능:**
- Context Length: 200,000 토큰
- 멀티모달 입력 지원 (텍스트, 이미지)
- 실시간 스트리밍 및 완전한 도구 지원
- Minimal reasoning 모드 및 "customs" 도구
- 향상된 안전성 (Jailbreak 방어 84/100)

> **📘 상세 가이드**: [MODEL_CHANGE_GUIDE.md](./MODEL_CHANGE_GUIDE.md) 참조

---

## 📚 참고 자료
- [Agent Service Guide](https://learn.microsoft.com/azure/ai-foundry/concepts/agents)
- [Azure AI Search RAG](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)

### 학습 리소스
- [Multi-Agent Systems](https://learn.microsoft.com/azure/ai-foundry/concepts/multi-agent)
- [RAG Patterns](https://learn.microsoft.com/azure/search/search-what-is-azure-search#rag-in-azure-ai-search)
- [Bicep Templates](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)

## 🤝 기여하기

이슈나 개선 사항이 있으시면 GitHub Issues를 통해 알려주세요.

## 📄 라이선스

MIT License

---

**Built with ❤️ using Azure AI Foundry**

💡 **Tip**: 각 노트북을 순서대로 실행하면서 Azure AI Agent 개발의 전체 과정을 경험해보세요!
