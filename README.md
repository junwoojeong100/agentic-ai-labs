# Azure AI Foundry Multi-Agent System Lab

Azure AI Foundry Agent Service를 활용한 Multi-Agent 시스템 구축 실습 프로젝트입니다.

## 🎯 실습 개요

이 실습에서는 다음 내용을 다룹니다:

1. **Azure 리소스 배포** - Bicep과 Azure Developer CLI를 사용한 인프라 배포
2. **AI Search RAG 구성** - 벡터 검색 기반 지식 베이스 구축
3. **Multi-## 🔧 주요 설정

### 배포 후 생성되는 리소스

| 리소스 | 용도 | 특징 |
|-------|------|------|
| Azure AI Foundry Project | Agent 및 AI 서비스 통합 | Hub + Project 구조 |
| Azure OpenAI | GPT-4o 모델, 텍스트 임베딩 | text-embedding-ada-002 포함 |
| Azure AI Search | RAG 지식 베이스 | 벡터 검색, 하이브리드 쿼리 |
| Azure Container Apps | MCP 서버 및 Agent API 호스팅 | 자동 스케일링, Managed Identity |
| Azure Container Registry | 컨테이너 이미지 저장 | Private registry |
| Azure Key Vault | 비밀 및 키 관리 | RBAC 통합 |
| Azure Storage Account | 데이터 및 로그 저장 | Blob, Table, Queue |

### 환경 변수 및 설정

배포 후 `config.json`에 자동 저장되는 설정:Main Agent, Tool Agent (MCP 연동), Research Agent (RAG) 구현 및 오케스트레이션

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
- **Tool Agent**: MCP 서버의 도구 활용 (날씨, 계산기, 시간, 랜덤 숫자)
- **Research Agent**: Azure AI Search를 통한 RAG 기반 지식 베이스 검색
- **MCP Server**: Azure Container Apps에 배포된 FastMCP 기반 도구 서버

## 📋 사전 요구사항

- Azure 구독
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) 설치
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) 설치
- Python 3.9 이상 (권장: Python 3.11+)
- Docker (Container 이미지 빌드용)
- Visual Studio Code (권장)
- Jupyter Notebook 지원 환경

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Azure 로그인
azd auth login
az login

# 리포지토리 디렉토리로 이동
cd agentic-ai-labs
```

### 2. 실습 노트북 실행

실습은 3개의 Jupyter 노트북으로 구성되어 있습니다:

#### 📓 Lab 1: [01_deploy_azure_resources.ipynb](./01_deploy_azure_resources.ipynb)
- Azure AI Foundry Project 생성
- Azure AI Search, Container Apps 등 인프라 배포
- Bicep 기반 Infrastructure as Code

#### 📓 Lab 2: [02_setup_ai_search_rag.ipynb](./02_setup_ai_search_rag.ipynb)
- AI Search 인덱스 생성 및 스키마 설계
- 지식 베이스 문서 임베딩 및 업로드
- 벡터 검색 및 하이브리드 검색 테스트

#### 📓 Lab 3: [03_deploy_foundry_agent.ipynb](./03_deploy_foundry_agent.ipynb)
- MCP Server를 Azure Container Apps에 배포
- Azure AI Foundry Agent Service로 Multi-Agent 생성
  - Main Agent: 오케스트레이터
  - Tool Agent: MCP 도구 연동
  - Research Agent: RAG 검색
- Connected Agent 패턴 구현
- Multi-Agent 오케스트레이션 및 협업 테스트

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
│   ├── agent/                              # Multi-Agent 구현
│   │   ├── main_agent.py                   # Main Agent (오케스트레이터)
│   │   ├── tool_agent.py                   # Tool Agent (MCP 연동)
│   │   ├── research_agent.py               # Research Agent (RAG)
│   │   ├── api_server.py                   # Agent API 서버
│   │   ├── requirements.txt
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
├── azure.yaml                              # azd 설정
├── config.json                             # 배포 설정 (자동 생성)
└── README.md                               # 이 파일
```

## 🔧 인프라 파라미터

`infra/main.parameters.json`에서 커스터마이즈 가능:

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `environmentName` | 환경 이름 | 자동 생성 |
| `location` | Azure 리전 | `eastus` |
| `principalId` | 사용자 Principal ID | 자동 감지 |

주요 리소스는 Bicep 템플릿에서 자동으로 생성되며, 리소스 이름은 고유성을 위해 해시가 추가됩니다.

## 🐛 문제 해결

### Agent 생성 실패
```bash
# Azure AI Foundry 프로젝트 연결 확인
az ml workspace show --name <project-name> --resource-group <rg-name>

# 권한 확인 (Azure AI User 또는 Contributor 필요)
az role assignment list --scope <project-resource-id>
```

**일반적인 원인:**
- Managed Identity에 Azure AI User 역할이 할당되지 않음
- 역할 전파 시간 부족 (최대 5-10분 소요)
- 잘못된 project_connection_string 형식

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
- 잘못된 벡터 차원 (1536이어야 함)
- 인덱스 스키마 불일치
- Embedding 모델 배포 안 됨 (text-embedding-ada-002)

### Python 패키지 버전 충돌
```bash
# 가상 환경 재생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r src/agent/requirements.txt
pip install -r src/mcp/requirements.txt
```

**참고:** Azure AI SDK는 빠르게 업데이트되므로 최신 버전 사용을 권장합니다.

## 📚 참고 자료

### 공식 문서
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Agent Service Guide](https://learn.microsoft.com/azure/ai-foundry/concepts/agents)
- [Azure AI Search RAG](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)

### 학습 리소스
- [Multi-Agent Systems](https://learn.microsoft.com/azure/ai-foundry/concepts/multi-agent)
- [RAG Patterns](https://learn.microsoft.com/azure/search/search-what-is-azure-search#rag-in-azure-ai-search)
- [Bicep Templates](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)

## 💡 다음 단계

### 확장 아이디어
1. **더 많은 Agent 추가**
   - Code Generator Agent
   - Data Analyzer Agent
   - Translation Agent

2. **MCP 도구 확장**
   - 데이터베이스 쿼리 도구
   - API 통합 도구
   - 파일 처리 도구

3. **프로덕션 준비**
   - API Server를 통한 REST API 제공
   - 모니터링 및 로깅 추가 (Application Insights)
   - 비용 최적화 및 스케일링 전략
   - 보안 강화 (Managed Identity, Key Vault)

4. **고급 기능**
   - Agent 간 비동기 통신
   - 이벤트 기반 Agent 트리거
   - Multi-turn 대화 기록 관리
   - Custom Tools 개발 및 통합
   - 성능 튜닝
   - CI/CD 파이프라인 구성

### 추가 실습
- Agent 간 통신 패턴 고도화
- 프롬프트 엔지니어링 최적화
- RAG 검색 품질 향상
- 분산 추적(Tracing) 구현

## 🛠️ 주요 기능

### Azure AI Foundry Agent Service
- **Agent 생성 및 관리**: GPT-4o 기반 전문화된 Agent
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
  - 날씨, 계산, 시간, 랜덤 숫자 등 유틸리티 기능
  - HTTP 기반 MCP 클라이언트 구현
  
- **Research Agent**:
  - Azure AI Search를 통한 RAG 구현
  - 하이브리드 검색 (벡터 + 키워드)
  - 지식 베이스 기반 답변 생성

### MCP (Model Context Protocol) Server
- **제공 도구**:
  - `get_weather`: 도시별 날씨 정보
  - `calculate`: 수학 계산
  - `get_current_time`: 현재 시간
  - `generate_random_number`: 랜덤 숫자 생성
- **FastMCP 프레임워크**: Python 기반 간편한 MCP 서버 구현
- **Azure Container Apps 배포**: 확장 가능한 서버리스 호스팅
- **HTTP/SSE 엔드포인트**: `/mcp` 경로로 MCP 프로토콜 제공

### RAG (Retrieval-Augmented Generation)
- **Azure AI Search 통합**: 벡터 + 키워드 하이브리드 검색
- **Embedding 모델**: Azure OpenAI text-embedding-ada-002 (1536차원)
- **지식 베이스**: 54개 AI Agent 관련 문서 (카테고리별 청킹)
- **검색 최적화**: Top-K=5, Semantic Ranker 적용

## � 주요 설정

### 배포 후 생성되는 리소스

| 리소스 | 용도 |
|-------|------|
| Azure AI Foundry Project | Agent 및 AI 서비스 통합 |
| Azure OpenAI | GPT-4o 모델, 텍스트 임베딩 |
| Azure AI Search | RAG 지식 베이스 (벡터 검색) |
| Azure Container Apps | MCP 서버 호스팅 |
| Azure Container Registry | 컨테이너 이미지 저장 |
| Azure Key Vault | 비밀 및 키 관리 |
| Azure Storage Account | 데이터 저장 |

### 환경 변수

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

### Azure Developer CLI (azd) 설정

`azure.yaml` 파일은 azd 배포를 위한 메타데이터를 정의합니다:

```yaml
name: ai-foundry-agent-lab
services:
  mcp-server:
    project: ./src/mcp
    language: python
    host: containerapp
infra:
  path: ./infra
  module: main
```

**참고:** 
- 현재 `azure.yaml`에는 사용하지 않는 서비스 정의가 포함되어 있을 수 있습니다
- 실제 배포는 노트북(Lab 3)에서 `az containerapp create` 명령으로 수동 진행됩니다
- azd 기반 자동 배포는 향후 개선 예정입니다

## 📝 Knowledge Base 관리

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

## 🤝 기여하기

이슈나 개선 사항이 있으시면 GitHub Issues를 통해 알려주세요.

## 📄 라이선스

MIT License

---

**Built with ❤️ using Azure AI Foundry**

💡 **Tip**: 각 노트북을 순서대로 실행하면서 Azure AI Agent 개발의 전체 과정을 경험해보세요!
