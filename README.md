# Agentic AI Labs

Azure AI Foundry Agent Service를 활용한 Multi-Agent 시스템 구축 실습 프로젝트입니다.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/junwoojeong100/agentic-ai-labs?quickstart=1)

---

## 📑 Table of Contents

1. [개요 (Overview)](#-개요-overview)
2. [빠른 시작 (Quick Start)](#-빠른-시작-quick-start)
3. [Lab 안내](#-lab-안내)
4. [아키텍처](#-아키텍처)
5. [핵심 기능](#-핵심-기능-요약)
6. [인프라 & 리소스](#-인프라--리소스-개요)
7. [프로젝트 구조](#-프로젝트-구조)
8. [사전 요구사항](#-사전-요구사항)
9. [환경 변수 & 설정](#-환경-변수--설정)
10. [관찰성 (Observability)](#-관찰성-observability)
11. [모델 변경하기](#-모델-변경하기)
12. [리소스 정리](#-리소스-정리-cleanup)
13. [참고 자료](#-참고-자료)

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

**요약 TL;DR**: "이 레포는 RAG + MCP + Multi-Agent + Observability(Tracing + Analytics)를 한 번에 실습하는 통합 패턴 모음입니다."

---

> **📋 시작하기 전에**: [PREREQUISITES.md](./PREREQUISITES.md)에서 사전 요구사항을 확인하세요.  
> Codespace 사용 시 대부분의 도구가 자동 설치되지만, Azure 구독 및 권한은 미리 준비가 필요합니다.

---

## 🚀 빠른 시작 (Quick Start)

### 1️⃣ GitHub Codespace 시작

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/junwoojeong100/agentic-ai-labs?quickstart=1)

**방법:**
- 위의 버튼 클릭, 또는
- GitHub 리포지토리 → **Code** → **Codespaces** → **Create codespace on main**
- 환경 구성 자동 완료 (2-3분)

### 2️⃣ 실습 진행

Codespace가 준비되면 Jupyter 노트북을 순서대로 실행하세요:

1. **Lab 1**: Azure 리소스 배포 (`01_deploy_azure_resources.ipynb`)
2. **Lab 2**: RAG 지식 베이스 구축 (`02_setup_ai_search_rag.ipynb`)
3. **Lab 3**: Foundry Agent without MAF 배포 (`03_deploy_foundry_agent_without_maf.ipynb`)
4. **Lab 4**: Foundry Agent with MAF 배포 (`04_deploy_foundry_agent_with_maf.ipynb`)
5. **Lab 5**: MAF Workflow 패턴 (`05_maf_workflow_patterns.ipynb`)
6. **Lab 6**: Agent 평가 (`06_evaluate_agents.ipynb`)

> 💡 **Tip**: 각 Lab은 이전 Lab 완료를 전제로 합니다. 순서대로 진행하세요!

---

## 📓 Lab 안내

실습은 6개의 Jupyter 노트북으로 구성되어 있습니다:

| Lab | 노트북 | 목표 | Agent 기반 | 워크플로우 패턴 | 주요 내용 |
|-----|--------|------|-----------|---------------|-----------|
| **1** | [01_deploy_azure_resources.ipynb](./01_deploy_azure_resources.ipynb) | Azure 인프라 배포 | - | Bicep IaC | AI Foundry, OpenAI, AI Search, Container Apps 생성 |
| **2** | [02_setup_ai_search_rag.ipynb](./02_setup_ai_search_rag.ipynb) | RAG 구축 | - | Azure AI Search SDK | 인덱스 생성, 50개 문서 임베딩 |
| **3** | [03_deploy_foundry_agent_without_maf.ipynb](./03_deploy_foundry_agent_without_maf.ipynb) | Foundry Agent without MAF | **Foundry Agent Service** | **Connected Agent (Handoff)** | Main/Tool/Research Agent, MCP Server 배포 |
| **4** | [04_deploy_foundry_agent_with_maf.ipynb](./04_deploy_foundry_agent_with_maf.ipynb) | Foundry Agent with MAF | **Foundry Agent Service** | **Workflow Pattern (Router+Executor)** | AI 기반 라우팅, 병렬 실행, 커스텀 OpenTelemetry |
| **5** | [05_maf_workflow_patterns.ipynb](./05_maf_workflow_patterns.ipynb) | MAF Workflow | Microsoft Agent Framework | WorkflowBuilder | 6가지 오케스트레이션 패턴 (Sequential, Concurrent, Conditional, Loop, Error Handling, Handoff) |
| **6** | [06_evaluate_agents.ipynb](./06_evaluate_agents.ipynb) | Agent 평가 | - | Azure AI Evaluation SDK | 성능 메트릭, 품질 평가, 개선 방향 |

### Lab 1: Azure 인프라 배포

**배포 리소스:**
- **Azure AI Foundry**: Multi-Agent 개발 플랫폼
- **Azure OpenAI Service**: GPT-4o (권장), text-embedding-3-large 모델
- **Azure AI Search**: 벡터 검색 및 RAG 지원
- **Azure Container Apps Environment**: Agent 서비스 호스팅 환경

**배포 방법:**
- `azd provision` 명령으로 Bicep 템플릿 기반 자동 배포
- 약 3-5분 소요, config.json 자동 생성
- 모든 후속 Lab에서 사용할 기본 인프라 구성

> **💡 Tip**: 배포 후 생성된 `config.json`에 모든 엔드포인트 정보가 저장됩니다.

### Lab 2: RAG 지식 베이스 구축

**구축 프로세스:**
1. **데이터 준비**: 50개 여행지 문서 (`data/knowledge-base.json`)
2. **임베딩 생성**: Azure OpenAI text-embedding-3-large (3072차원)
3. **인덱스 생성**: Azure AI Search에 벡터 인덱스 구성
4. **검색 테스트**: 하이브리드 검색 (벡터 + 키워드) 검증

**인덱스 스키마:**
- `id`, `title`, `content`: 문서 기본 정보
- `category`, `section`, `subsection`: 계층적 분류
- `contentVector`: 3072차원 벡터 (검색용)

> **💡 Tip**: HNSW 알고리즘으로 빠른 벡터 검색, Semantic Ranker로 정확도 향상

### Lab 3: Multi-Agent 시스템 배포

**Agent 구성:**
- **Main Agent**: 사용자 질의 분석 및 에이전트 라우팅
- **Tool Agent**: MCP 프로토콜로 외부 도구 호출
- **Research Agent**: RAG 기반 지식 검색

**배포 컴포넌트:**
1. **MCP Server**: Model Context Protocol 서버 (날씨 도구)
2. **Agent Service**: Foundry Agent 기반 Multi-Agent 서비스
3. **Container Apps**: 두 서비스를 Container Apps에 배포

**테스트 시나리오:**
- 단순 질문 → Research Agent (RAG)
- 도구 필요 → Tool Agent (MCP)
- 복합 질의 → 여러 Agent 협업

> **💡 Tip**: AI Foundry의 Tracing 기능으로 Agent 간 상호작용을 시각화할 수 있습니다.

### Lab 4: Agent Framework 배포

**프레임워크 패턴:**
- **Router Pattern**: 질의 유형에 따라 적절한 Agent로 라우팅
- **Executor Pattern**: Agent 실행 및 결과 통합
- **OpenTelemetry**: 분산 추적 및 모니터링

**주요 기능:**
1. **지능형 라우팅**: LLM 기반 질의 분류
2. **동적 실행**: 런타임에 Agent 선택 및 실행
3. **관찰성**: 전체 Agent 호출 체인 추적

**배포 및 테스트:**
- Container Apps에 Agent Framework 배포
- REST API 엔드포인트를 통한 테스트
- Azure Monitor + OpenTelemetry로 성능 모니터링

> **💡 Tip**: 프로덕션 환경에서는 Router Pattern으로 효율적인 Agent 오케스트레이션이 가능합니다.

### Lab 5: MAF Workflow 패턴 상세

**학습할 6가지 패턴:**
1. **Sequential**: 순차 실행 (A → B → C)
2. **Concurrent**: 병렬 실행 (동시 처리 후 통합)
3. **Conditional**: 조건 분기 (동적 라우팅)
4. **Loop**: 반복 개선 (피드백 기반)
5. **Error Handling**: 오류 처리 및 복구
6. **Handoff**: 동적 제어 이전 (에스컬레이션)

**실습 시나리오**: 여행 계획 시스템을 통한 Multi-Agent 협업

> **💡 MAF vs Foundry Agent**
> - **Foundry Agent**: 개별 에이전트 (LLM 추론, 도구 호출)
> - **MAF Workflow**: 에이전트 실행 흐름 제어 (오케스트레이션)

### Lab 6: Agent 평가 및 품질 측정

**평가 프레임워크:**
- **Azure AI Evaluation SDK**: 자동화된 품질 평가
- **평가 메트릭**: Groundedness, Relevance, Coherence, Fluency
- **성능 측정**: 응답 시간, 토큰 사용량, 성공률

**평가 프로세스:**
1. **테스트 데이터셋 준비**: `evals/eval-input.jsonl` (다양한 질의 시나리오)
2. **자동 평가 실행**: GPT-4를 evaluator로 활용한 품질 평가
3. **결과 분석**: 점수 분포, 개선 포인트 식별
4. **시각화**: `show_eval_results.py`로 평가 결과 대시보드 생성

**평가 항목:**
- **Groundedness (근거성)**: RAG 문서에 기반한 답변인가?
- **Relevance (관련성)**: 질문과 관련된 답변인가?
- **Coherence (일관성)**: 논리적으로 일관된 답변인가?
- **Fluency (유창성)**: 자연스러운 한국어 표현인가?

> **💡 평가 베스트 프랙티스**
> - 다양한 질의 유형 포함 (단순 질문, 복잡한 추론, 여러 에이전트 협업)
> - 정기적인 평가로 성능 변화 추적
> - 평가 결과를 Agent 개선에 피드백

---

## 🏗️ 아키텍처

### Lab 3: Foundry Agent Service - Connected Agent Pattern

**기반 기술:** Azure AI Foundry Agent Service

**오케스트레이션:** Connected Agent Pattern (Handoff 기반)

**주요 특징:**
- Foundry Agent Service SDK 사용
- `handoff_to_agent()` API로 Agent 간 연결
- Thread 기반 대화 컨텍스트 관리
- Main Agent가 Sub Agent로 작업 위임

**모니터링:**
- ✅ Application Insights (자동 수집)
- ✅ OpenTelemetry (SDK 자동 계측)
- ✅ Prompt/Completion 기록 (`AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true`)

```text
┌────────────────────────────────────────────────────────────┐
│         Multi-Agent System (Connected Agent)               │
│                                                            │
│  ┌─────────────────────────────────────────────┐          │
│  │          Main Agent                         │          │
│  │  (Task Analysis & Agent Routing)            │          │
│  │  → handoff_to_tool_agent()                  │          │
│  │  → handoff_to_research_agent()              │          │
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

### Lab 4: Foundry Agent Service - Workflow Pattern

**기반 기술:** Azure AI Foundry Agent Service (Lab 3과 동일)

**오케스트레이션:** Workflow Pattern (Router + Executor)

**주요 특징:**
- 동일한 Foundry Agent Service 사용
- Router Executor로 의도 분류 및 라우팅
- Workflow Context 기반 상태 관리
- 병렬 실행 및 복잡한 조건 분기 가능

**모니터링:**
- ✅ Application Insights (동일한 인프라 사용)
- ✅ OpenTelemetry (커스텀 계측 구현)
- ✅ Prompt/Completion 기록 (동일한 설정 변수 사용)

```text
┌────────────────────────────────────────────────────────────┐
│      Agent Service - Workflow Pattern                      │
│                                                            │
│  ┌──────────────────────────────────────────┐             │
│  │        Router Executor                   │             │
│  │   (AI-based Intent Classification)       │             │
│  └────┬──────┬────────┬────────────┬────────┘             │
│       │      │        │            │                      │
│   ┌───▼──┐ ┌▼───┐  ┌─▼────┐   ┌──▼────────┐             │
│   │ Tool │ │Research│ │General│ │Orchestrator│            │
│   │Exec  │ │Executor│ │Executor│ │Executor  │             │
│   └───┬──┘ └┬───┘  └─┬────┘   └──┬────────┘             │
│       │     │        │            │                      │
│   ┌───▼─────▼────────▼────────────▼──────┐               │
│   │      Workflow Context                │               │
│   │   (Message Passing & Output)         │               │
│   └──────────────────────────────────────┘               │
│                                                            │
│   External Resources:                                     │
│   ┌──────────────┐    ┌────────────────┐                 │
│   │  MCP Server  │    │  Azure AI      │                 │
│   │  (Tools)     │    │  Search (RAG)  │                 │
│   └──────────────┘    └────────────────┘                 │
└────────────────────────────────────────────────────────────┘
```

**Lab 3 vs Lab 4 핵심 차이:**

| 특성 | Lab 3 (Connected Agent) | Lab 4 (Workflow Pattern) |
|------|------------------------|-------------------------|
| **Agent 기반** | ✅ Foundry Agent Service | ✅ Foundry Agent Service |
| **워크플로우 패턴** | Connected Agent (Handoff) | Workflow Pattern (Router+Executor) |
| **라우팅 방식** | `handoff_to_agent()` API | Router Executor 함수 |
| **실행 흐름** | Main → Handoff → Sub Agent | Router → Executor → Output |
| **상태 관리** | Thread 기반 | Workflow Context 기반 |
| **병렬 실행** | 순차 Handoff | Orchestrator 병렬 가능 |

> **💡 공통점 (Agent 및 모니터링):**
> - ✅ 두 Lab 모두 **동일한 Azure AI Foundry Agent Service** 사용
> - ✅ 두 Lab 모두 **동일한 Application Insights** 사용
> - ✅ 두 Lab 모두 **동일한 OpenTelemetry 설정** 사용
> - ✅ 두 Lab 모두 **동일한 환경 변수**로 제어
> - ✅ MCP Server 및 Azure AI Search 연동도 동일
> 
> **🎯 차이점 (오케스트레이션):**
> - Lab 3: **Connected Agent Pattern** - Handoff API로 Agent 간 순차적 작업 위임
> - Lab 4: **Workflow Pattern** - Router와 Executor로 유연한 흐름 제어 및 병렬 실행

### Lab 5: MAF Workflow + Foundry Agent 통합 아키텍처

```text
┌──────────────────────────────────────────────────────────────────┐
│              MAF Workflow Orchestration Layer                    │
│             (Microsoft Agent Framework - WorkflowBuilder)        │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  Sequential    │  │  Concurrent    │  │  Conditional/  │   │
│  │  Pattern       │  │  Pattern       │  │  Loop/Handoff  │   │
│  │                │  │                │  │  Patterns      │   │
│  │  A → B → C     │  │  ┌→ A         │  │  [조건 분기]    │   │
│  │  (순차 실행)    │  │  ├→ B         │  │  A → B or C    │   │
│  │                │  │  └→ C → 통합   │  │  (동적 라우팅)  │   │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘   │
│          │                   │                    │            │
└──────────┼───────────────────┼────────────────────┼────────────┘
           │                   │                    │
┌──────────▼───────────────────▼────────────────────▼────────────┐
│           Azure AI Foundry Agents (Agent Layer)                │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │  Validator      │  │  Transformer    │  │  Summarizer    │ │
│  │  Agent          │  │  Agent          │  │  Agent         │ │
│  │  (Foundry)      │  │  (Foundry)      │  │  (Foundry)     │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│                                                                 │
│  ✅ Thread-based State Management                              │
│  ✅ LLM Integration (GPT-4o)                                    │
│  ✅ Tool/MCP Server Integration                                │
└─────────────────────────────────────────────────────────────────┘
```

**MAF Workflow 주요 기능:**
- **그래프 기반 실행**: `WorkflowBuilder`로 노드와 엣지 정의
- **@executor 데코레이터**: 각 노드를 함수로 간단히 정의
- **WorkflowContext**: 노드 간 타입 안전한 데이터 전달
- **동적 라우팅**: 런타임에 조건부로 다음 노드 선택
- **병렬 실행**: 여러 노드를 동시에 실행 (asyncio.gather)
- **상태 관리**: 전체 워크플로우 실행 상태 추적

### 주요 컴포넌트

- **Main Agent**: 사용자 요청 분석 및 Connected Agent를 통한 하위 Agent 라우팅
- **Tool Agent**: MCP 서버의 도구 활용 (실시간 날씨 정보)
- **Research Agent**: Azure AI Search를 통한 RAG 기반 지식 베이스 검색
- **MCP Server**: Azure Container Apps에 배포된 FastMCP 기반 도구 서버

## ⚙️ 핵심 기능 요약

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

### Microsoft Agent Framework (MAF) - Lab 5
- **WorkflowBuilder 패턴**: 그래프 기반 워크플로우 오케스트레이션
- **@executor 데코레이터**: 각 워크플로우 노드를 함수로 간단히 정의
- **WorkflowContext**: 노드 간 타입 안전한 데이터 전달 및 상태 관리
- **6가지 워크플로우 패턴 구현**:
  - **Sequential**: 순차 실행 (A → B → C)
  - **Concurrent**: 병렬 실행 (A, B, C 동시 실행 → 통합)
  - **Conditional**: 조건 분기 (조건에 따라 A or B or C 실행)
  - **Loop**: 반복 개선 (피드백 기반 최대 N회 반복)
  - **Error Handling**: 오류 감지 및 복구 (재시도, 대체 경로)
  - **Handoff**: 동적 제어 이전 (복잡도에 따라 전문가 에이전트로 에스컬레이션)
- **Foundry Agent 통합**: Azure AI Foundry Agent를 MAF Workflow 노드로 사용
- **비동기 실행**: asyncio 기반 고성능 병렬 처리
- **타입 안전성**: dataclass 기반 메시지 타입 정의

### RAG (Retrieval-Augmented Generation)
- **Azure AI Search 통합**: 벡터 + 키워드 하이브리드 검색
- **Embedding 모델**: Azure OpenAI text-embedding-3-large (3072차원)
- **지식 베이스**: 50개 AI Agent 관련 문서 (카테고리별 청킹)
- **검색 최적화**: HNSW 알고리즘, Top-K=5, Semantic Ranker

> **� 상세 스키마**: Lab 2에서 id, title, content, category, contentVector (3072차원) 필드로 구성된 인덱스를 생성합니다. 자세한 내용은 [`02_setup_ai_search_rag.ipynb`](./02_setup_ai_search_rag.ipynb) 참조.

## 🧩 인프라 & 리소스 개요

### 배포 후 생성되는 리소스

| 리소스 | 용도 | 특징 |
|--------|------|------|
| Azure AI Foundry Project | Agent 및 AI 서비스 통합 | **Hub-less 독립형 프로젝트 (GA)** |
| Azure OpenAI | LLM 모델, 텍스트 임베딩 | text-embedding-3-large 포함 |
| Azure AI Search | RAG 지식 베이스 | 벡터 검색, 하이브리드 쿼리 |
| Azure Container Apps | MCP 서버 및 Agent API 호스팅 | 자동 스케일링, Managed Identity |
| Azure Container Registry | 컨테이너 이미지 저장 | Private registry |
| Azure Key Vault | 비밀 및 키 관리 | RBAC 통합 |
| Azure Storage Account | 데이터 및 로그 저장 | Blob, Table, Queue |

> **💡 아키텍처 특징**  
> - **Hub-less AI Foundry Project**: 독립형 프로젝트로 OpenAI, AI Search 등을 직접 연결
> - **Key Vault & Storage**: 인프라로 배포되지만 이번 실습에서는 미사용 (프로덕션 확장 시 활용 가능)



## 📁 프로젝트 구조

```text
agentic-ai-labs/
├── infra/                                      # Bicep 인프라 코드
│   ├── main.bicep                              # 메인 Bicep 템플릿
│   ├── main.parameters.json                    # 파라미터 파일
│   └── core/                                   # 모듈화된 Bicep 리소스
│       ├── ai/                                 # AI Foundry, OpenAI
│       ├── host/                               # Container Apps
│       ├── search/                             # AI Search
│       └── security/                           # Key Vault, RBAC
│
├── src/                                        # 소스 코드
│   ├── foundry_agent/                          # Multi-Agent 구현 (Foundry Agent Service)
│   │   ├── main_agent.py                       # Main Agent (오케스트레이터)
│   │   ├── tool_agent.py                       # Tool Agent (MCP 연동)
│   │   ├── research_agent.py                   # Research Agent (RAG)
│   │   ├── api_server.py                       # Agent API 서버
│   │   ├── masking.py                          # PII 마스킹 유틸리티
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── agent_framework/                        # Agent Framework Workflow
│   │   ├── main_agent_workflow.py              # Workflow Router & Orchestrator
│   │   ├── tool_agent.py                       # Tool Executor (MCP)
│   │   ├── research_agent.py                   # Research Executor (RAG)
│   │   ├── api_server.py                       # Workflow API 서버
│   │   ├── test_workflow.py                    # Workflow 테스트
│   │   ├── masking.py                          # PII 마스킹 유틸리티
│   │   ├── requirements.txt                    # OpenTelemetry 패키지 포함
│   │   └── Dockerfile
│   └── mcp/                                    # MCP 서버
│       ├── server.py                           # FastMCP 도구 서버
│       ├── requirements.txt
│       └── Dockerfile
│
├── data/                                       # 지식 베이스
│   └── knowledge-base.json                     # AI Search 인덱싱용 문서
│
├── scripts/                                    # 유틸리티 스크립트
│   └── generate_knowledge_base.py
│
├── 01_deploy_azure_resources.ipynb             # Lab 1 노트북
├── 02_setup_ai_search_rag.ipynb                # Lab 2 노트북
├── 03_deploy_foundry_agent_without_maf.ipynb   # Lab 3 노트북
├── 04_deploy_foundry_agent_with_maf.ipynb      # Lab 4 노트북
├── 05_maf_workflow_patterns.ipynb              # Lab 5 노트북
├── 06_evaluate_agents.ipynb                    # Lab 6 노트북 (Agent 평가)
├── azure.yaml                                  # azd 설정
├── config.json                                 # 배포 설정 (자동 생성)
├── evals/                                      # Evaluation 결과 (Lab 6)
│   ├── eval-queries.json                       # 테스트 쿼리
│   ├── eval-input.jsonl                        # Agent 실행 결과
│   └── eval-output.json                        # 평가 점수
├── OBSERVABILITY.md                            # 관찰성(Tracing/Analytics) 심화 가이드
└── README.md                                   # 이 파일
```

### 인프라 파라미터

`infra/main.parameters.json`에서 커스터마이즈 가능:

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `environmentName` | 환경 이름 | 자동 생성 |
| `location` | Azure 리전 | `eastus` |
| `principalId` | 사용자 Principal ID | 자동 감지 |

주요 리소스는 Bicep 템플릿에서 자동으로 생성되며, 리소스 이름은 고유성을 위해 해시가 추가됩니다.

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

## ✅ 사전 요구사항

### 🚀 빠른 시작: GitHub Codespace (권장)

이 실습은 **GitHub Codespace**에서 진행하도록 설계되었습니다.

**Codespace 사용 시 자동 구성:**
- ✅ Azure CLI, Azure Developer CLI (azd)
- ✅ Python 3.12 + 가상환경 (`.venv`)
- ✅ Docker, Git, VS Code 확장
- ✅ 모든 필수 Python 패키지 자동 설치

**Azure 구독 요구사항:**
- Azure 구독 (무료 체험 가능)
- 구독 소유자(Owner) 역할 필수
- 별도의 실습 전용 구독 사용 권장

> **💡 상세 가이드**: [PREREQUISITES.md](./PREREQUISITES.md)에서 로컬 환경 설정, Azure 권한 요구사항, 상세 구성 정보를 확인하세요.

---

## 🌐 환경 변수 & 설정

### Config.json (자동 생성)

Lab 1 배포 후 `config.json`이 자동 생성되며 다음 정보를 포함합니다:

```json
{
  "project_connection_string": "https://xxx.services.ai.azure.com/api/projects/yyy",
  "search_endpoint": "https://srch-xxx.search.windows.net/",
  "search_index": "ai-agent-knowledge-base",
  "mcp_endpoint": "https://mcp-server.xxx.azurecontainerapps.io",
  "agent_endpoint": "https://agent-service.xxx.azurecontainerapps.io"
}
```

### Agent 환경 변수

Lab 3 실행 시 `src/foundry_agent/.env` 파일이 자동 생성됩니다.

**핵심 설정:**
- Azure AI Foundry 연결 정보
- Azure AI Search (RAG)
- MCP Server 엔드포인트
- Application Insights (Observability)
- OpenTelemetry 설정

> **📘 상세 가이드**: [CONFIGURATION.md](./CONFIGURATION.md)
> - 전체 환경 변수 목록
> - 필수 vs 선택 변수
> - Content Recording 운영 전략
> - 샘플링 및 PII 마스킹 설정
> - 변경 적용 절차

---

## 📊 관찰성 (Observability)

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

실습 완료 후 비용 절감을 위해 리소스를 정리하세요:

```bash
# config.json에서 리소스 그룹 이름 확인
cat config.json | grep resource_group

# 리소스 그룹 전체 삭제 (권장)
az group delete --name <resource-group-name> --yes --no-wait
```

> ⚠️ 리소스 그룹 삭제 시 모든 리소스가 영구 삭제됩니다. 복구 불가능합니다.



## 🔄 모델 변경하기

프로젝트는 **환경변수 중심 설계**로 코드 수정 없이 모델을 변경할 수 있습니다.

> **🎯 핵심: 모델 변경은 딱 1곳만!**  
> **Lab 1 노트북**의 `model_name`과 `model_version` 변수만 수정하면 전체 프로젝트에 자동 반영됩니다.  
> 다른 파일 수정 불필요!

### 변경 방법

**Lab 1 노트북**에서 모델명과 버전을 변경하여 배포하세요:

```python
# 01_deploy_azure_resources.ipynb 에서
model_name = "gpt-4o"          # 👈 원하는 모델로 변경
model_version = "2024-11-20"   # 👈 모델 버전 (모델에 따라 다름)
model_capacity = 50            # TPM 용량
```

배포 후에는 `.env` 파일의 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 환경변수만 변경하면 됩니다.

### 지원 모델 예시

| 모델명 | 버전 | 특징 |
|--------|------|------|
| `gpt-4o` | `2024-11-20` | 멀티모달, 빠른 응답, 비용 효율적 (권장) |
| `gpt-4o-mini` | `2024-07-18` | 경량 버전, 저비용 |

**주요 기능:**
- Context Length: 128,000 토큰
- 멀티모달 입력 지원 (텍스트, 이미지)
- 실시간 스트리밍 및 완전한 도구 지원
- 빠른 응답 속도 및 비용 효율성
- 멀티모달 입력 지원 (텍스트, 이미지)
- 실시간 스트리밍 및 완전한 도구 지원
- 빠른 응답 속도 및 비용 효율성
- 향상된 안전성 (Jailbreak 방어 84/100)

> **📘 상세 가이드**: [MODEL_CHANGE_GUIDE.md](./MODEL_CHANGE_GUIDE.md) 참조

---

## 📚 참고 자료

### 공식 문서
- [Azure AI Foundry Agent Service](https://learn.microsoft.com/azure/ai-foundry/concepts/agents)
- [Azure AI Search RAG](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)

### 추가 가이드 📘
- [PREREQUISITES.md](./PREREQUISITES.md) - 사전 요구사항 상세
- [DEVCONTAINER.md](./DEVCONTAINER.md) - Dev Container 설정 가이드
- [CONFIGURATION.md](./CONFIGURATION.md) - 환경 변수 설정 가이드
- [OBSERVABILITY.md](./OBSERVABILITY.md) - 관찰성 심화 가이드
- [MODEL_CHANGE_GUIDE.md](./MODEL_CHANGE_GUIDE.md) - 모델 변경 방법

---

**Built with ❤️ using Azure AI Foundry** | MIT License | [Issues](https://github.com/junwoojeong100/agentic-ai-labs/issues)
