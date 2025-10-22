# Observability (Monitoring & Tracing) 완벽 가이드

> 🏠 메인 가이드로 돌아가기: [README.md](./README.md)

Azure AI Foundry Agent 시스템의 **운영 관찰성(Observability)**을 위한 완벽 가이드입니다. Monitoring과 Tracing의 개념부터 실전 구현, 운영 전략까지 단계별로 다룹니다.

---

## 📑 목차

### 🎯 시작하기
1. [Observability 개요](#1-observability-개요)
2. [Monitoring vs Tracing 핵심 차이](#2-monitoring-vs-tracing-핵심-차이)

### 📊 Monitoring 구현
3. [Monitoring 설정 가이드](#3-monitoring-설정-가이드)
4. [수집되는 메트릭 상세](#4-수집되는-메트릭-상세)
5. [Portal에서 확인하기](#5-portal에서-monitoring-확인)

### 🔍 Tracing 구현
6. [Tracing 설정 가이드](#6-tracing-설정-가이드)
7. [Span 구조와 커스텀 계측](#7-span-구조와-커스텀-계측)
8. [Content Recording (Prompt/Completion)](#8-content-recording-promptcompletion)

### ⚙️ 고급 설정
9. [계측 순서 (Order Matters)](#9-계측-순서-order-matters)
10. [환경 변수 완벽 가이드](#10-환경-변수-완벽-가이드)
11. [운영 전략](#11-운영-전략)
12. [샘플링 설정](#12-샘플링-설정)

### 🛠️ 실전 운영
13. [Kusto 쿼리 예제](#13-kusto-쿼리-예제)
14. [Troubleshooting 가이드](#14-troubleshooting-가이드)
15. [체크리스트](#15-체크리스트)

### 📚 부록
16. [FAQ](#16-faq)
17. [참고 자료](#17-참고-자료)

---

## 1. Observability 개요

### 1.1. 3가지 관찰성 계층

Azure AI Foundry에서 Agent 시스템을 관찰하는 계층:

| 계층 | 목적 | 데이터 타입 | Portal 위치 |
|------|------|------------|-------------|
| **Monitoring** | 시스템 헬스, SLA, 성능 추세 | 집계 메트릭 (숫자) | Monitoring > Application Analytics |
| **Tracing** | 실행 흐름, 디버깅, 품질 분석 | Span Tree, Attributes | Tracing 탭 |
| **Logging** | 런타임 예외, 상태 메시지 | 텍스트 로그 | Container Apps Logs |

### 1.2. 이 실습에서 구현된 패턴

| 구분 | Lab 3 | Lab 4 |
|------|-------|-------|
| **Notebook** | 03_deploy_foundry_agent.ipynb | 04_deploy_agent_framework.ipynb |
| **Agent 기반** | ✅ Azure AI Foundry Agent Service | ✅ Azure AI Foundry Agent Service |
| **워크플로우 패턴** | Connected Agent (Handoff) | Workflow Pattern (Router+Executor) |
| **Monitoring** | ✅ Application Insights + OpenTelemetry | ✅ Application Insights + OpenTelemetry |
| **Tracing** | ✅ Content Recording 지원 | ✅ Content Recording 지원 |
| **환경 변수** | 동일한 OTEL 설정 | 동일한 OTEL 설정 |

> **💡 핵심 포인트**  
> - 두 Lab 모두 **동일한 Azure AI Foundry Agent Service**를 사용합니다
> - **Observability 설정 (Monitoring & Tracing)도 동일**합니다
> - 차이점은 **워크플로우 오케스트레이션 패턴**입니다 (Connected Agent vs Workflow Pattern)

---

## 2. Monitoring vs Tracing 핵심 차이

### 2.1. 빠른 비교표

| 구분 | Monitoring (Application Analytics) | Tracing |
|------|-----------------------------------|---------|
| **목적** | 시스템 헬스, SLA, 성능 추세 분석 | 개별 요청의 실행 흐름 및 디버깅 |
| **데이터** | 집계 메트릭<br>(호출 수, 평균 지연, 오류율) | 세부 Span Tree<br>(단계별 실행, Prompt/Completion) |
| **사용 시나리오** | • 일일 호출량 추세 파악<br>• SLA 위반 알림<br>• 성능 저하 탐지<br>• 비용 모니터링 | • 느린 요청 원인 분석<br>• 프롬프트 최적화<br>• 오류 디버깅<br>• Agent 라우팅 검증 |
| **Portal** | Monitoring > Application Analytics | Tracing 탭 |
| **Prompt/Completion** | ❌ 미지원 | ✅ Content Recording 활성화 시 |
| **필수 조건** | Container App + 환경 변수 | Monitoring + 추가 계측 |
| **데이터 지연** | 5-10분 | 실시간 (1-2분) |

### 2.2. 언제 무엇을 사용할까?

**📊 Monitoring을 사용하는 경우:**
- ✅ "이번 주 평균 응답 시간이 늘어났나?"
- ✅ "하루에 LLM 호출이 몇 번 발생했나?"
- ✅ "오류율이 5%를 넘으면 알림을 받고 싶다"
- ✅ "토큰 사용량 추세를 보고 비용을 예측하고 싶다"

**🔍 Tracing을 사용하는 경우:**
- ✅ "특정 질문에 왜 Research Agent가 아닌 Tool Agent가 선택되었나?"
- ✅ "프롬프트가 어떻게 전달되고 응답이 어떻게 생성되었나?"
- ✅ "MCP 호출이 왜 5초나 걸렸나?"
- ✅ "RAG 검색 결과가 왜 이렇게 나왔나?"

---

## 3. Monitoring 설정 가이드

### 3.1. 목적

Monitoring은 **시스템 전체의 건강 상태**를 집계 메트릭으로 파악합니다:
- 총 호출 횟수 (Total Calls)
- 평균/P50/P95/P99 응답 시간
- 오류 발생 비율
- 토큰 사용량 (입력/출력 토큰)

### 3.2. 필수 환경 변수

```bash
# Application Insights 연결
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...

# 서비스 식별자 (Tracing에서 필터링에 사용)
OTEL_SERVICE_NAME=foundry-agent-service  # 또는 agent-framework-workflow

# Metrics Exporter 지정
OTEL_METRICS_EXPORTER=azure_monitor
```

> **📍 CONNECTION_STRING 확인 방법**  
> Azure Portal > Application Insights 리소스 > Properties > Connection String 복사

### 3.3. 코드 구현 - Foundry Agent

`src/foundry_agent/api_server.py`:

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.ai.projects import AIProjectClient
import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # ✅ 1단계: Azure Monitor 설정 (가장 먼저!)
    app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if app_insights_conn:
        configure_azure_monitor(
            connection_string=app_insights_conn,
            enable_live_metrics=True,  # 실시간 메트릭 활성화
            instrumentation_options={
                "azure_sdk": {"enabled": True},
                "fastapi": {"enabled": True},
                "requests": {"enabled": True},
            }
        )
        logger.info("✅ Azure Monitor configured for Monitoring")
        
        # ✅ 2단계: AI Inference 계측 (LLM 호출 자동 추적)
        AIInferenceInstrumentor().instrument()
        logger.info("✅ AI Inference instrumentation enabled")
    else:
        logger.warning("⚠️ APPLICATIONINSIGHTS_CONNECTION_STRING not set")
    
    # ✅ 3단계: AIProjectClient 생성 (logging_enable=True 필수!)
    project_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=project_endpoint,
        logging_enable=True  # ⭐ 매우 중요!
    )
```

### 3.4. 코드 구현 - Agent Framework

`src/agent_framework/main_agent_workflow.py`:

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.inference.tracing import AIInferenceInstrumentor

def _initialize_agents(self):
    # ✅ 1단계: Azure Monitor 설정
    app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if app_insights_conn:
        configure_azure_monitor(
            connection_string=app_insights_conn
        )
        logger.info("✅ Azure Monitor configured")
        
        # ✅ 2단계: AI Inference 계측
        AIInferenceInstrumentor().instrument()
        logger.info("✅ AI Inference instrumentation enabled")
    
    # ✅ 3단계: AIProjectClient 생성
    self.project_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=project_endpoint,
        logging_enable=True  # ⭐ 필수!
    )
```

### 3.5. 필수 조건 (중요!)

| 조건 | 이유 | 확인 방법 |
|------|------|-----------|
| **Container App 배포** | Notebook 실행은 메트릭 수집 안됨 | `az containerapp show` |
| **지속 실행 서비스** | 단발성 스크립트는 집계 불가 | Container App Running 상태 확인 |
| **충분한 호출량** | 최소 10개 이상 요청 권장 | 테스트 스크립트 실행 |
| **5-10분 대기** | 첫 메트릭 표시 지연 | Portal 새로고침 |

> **⚠️ 주의: Notebook에서 Agent를 직접 실행하면 메트릭이 수집되지 않습니다!**  
> 반드시 Container App으로 배포 후 HTTP 요청을 통해 호출해야 메트릭이 집계됩니다.

---

## 4. 수집되는 메트릭 상세

### 4.1. Application Analytics 메트릭 카테고리

| 카테고리 | 메트릭 | 설명 | 활용 사례 |
|---------|--------|------|----------|
| **Volume** | Total Calls | 총 LLM 호출 횟수 | 일일/주간 트래픽 추세 분석 |
| | Requests/sec | 초당 요청 수 | 부하 패턴 파악 |
| **Performance** | Average Duration | 평균 응답 시간 (ms) | 성능 기준선 설정 |
| | P50/P95/P99 | 백분위수 지연 시간 | SLA 모니터링 (예: P95 < 3초) |
| **Reliability** | Error Rate | 오류 발생 비율 (%) | 안정성 추적 |
| | Success Rate | 성공률 (%) | 품질 지표 |
| **Cost** | Prompt Tokens | 입력 토큰 총량 | 비용 예측 |
| | Completion Tokens | 출력 토큰 총량 | 비용 최적화 전략 |

---

## 5. Portal에서 Monitoring 확인

### 5.1. 접근 경로

1. **Azure AI Foundry Portal** 접속 (https://ai.azure.com)
2. 프로젝트 선택
3. 좌측 메뉴: **Monitoring** > **Application Analytics**
4. 시간 범위 선택 (예: Last 24 hours)

### 5.2. 메트릭 화면 구성

- **Overview**: 전체 요약 (호출 수, 평균 시간, 오류율)
- **Performance**: 응답 시간 분포 및 추세 그래프
- **Reliability**: 성공/실패 비율 및 오류 유형
- **Usage**: 토큰 사용량 통계 및 비용 분석

### 5.3. 메트릭이 보이지 않는 경우

**체크리스트:**

- [ ] Container App이 Running 상태인가?
- [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING`이 올바른가?
- [ ] `logging_enable=True`로 AIProjectClient를 생성했나?
- [ ] 최소 10개 이상의 요청을 실행했나?
- [ ] 첫 요청 후 5-10분이 경과했나?
- [ ] Portal에서 올바른 시간 범위를 선택했나?

**디버깅 명령:**

```bash
# Container App 로그 확인
az containerapp logs show \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --follow

# Application Insights 메트릭 확인
az monitor app-insights metrics show \
  --app <app-insights-name> \
  --resource-group <rg-name> \
  --metrics requests/count
```

---

## 6. Tracing 설정 가이드

### 6.1. 목적

Tracing은 **개별 요청의 실행 흐름**을 세밀하게 추적합니다:
- Router → Executor → Tool/RAG 실행 흐름
- 각 단계의 소요 시간
- Prompt와 Completion (Content Recording 활성화 시)
- 오류 발생 위치 및 스택 트레이스

### 6.2. 추가 환경 변수

```bash
# ✅ Monitoring 필수 변수 (섹션 3과 동일)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
OTEL_SERVICE_NAME=foundry-agent-service

# ✅ Tracing 추가 변수
OTEL_TRACES_EXPORTER=azure_monitor
OTEL_LOGS_EXPORTER=azure_monitor
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

# ✅ Prompt/Completion 표시 (Dev/Staging 권장)
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

> **📍 중요:** Monitoring이 먼저 설정되어야 Tracing도 작동합니다!

### 6.3. Foundry Agent - 자동 계측

Azure Agent Service는 기본적으로 자동 계측을 제공합니다:

```python
# ✅ Monitoring 설정 (섹션 3) 완료 후

# (선택) Agent 구조 자동 계측
try:
    from azure.ai.agents.telemetry import AIAgentsInstrumentor
    AIAgentsInstrumentor().instrument()
    logger.info("✅ AIAgentsInstrumentor enabled")
except ImportError:
    logger.warning("⚠️ AIAgentsInstrumentor not available (optional)")
```

### 6.4. Agent Framework - 커스텀 계측

Agent Framework는 수동으로 OpenTelemetry를 구현합니다:

**FastAPI 계측 (`api_server.py`):**

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

@app.on_event("startup")
async def startup_event():
    # ... Monitoring 설정 (섹션 3) ...
    
    # ✅ FastAPI HTTP 요청 추적
    FastAPIInstrumentor.instrument_app(app)
    logger.info("✅ FastAPI instrumentation enabled")
```

---

## 7. Span 구조와 커스텀 계측

### 7.1. Span이란?

Span은 **실행의 한 단위**를 나타냅니다:
- HTTP 요청 처리
- Agent 라우팅 결정
- MCP 도구 호출
- RAG 검색 실행
- LLM 호출

Span들이 부모-자식 관계로 연결되어 **Span Tree**를 형성합니다.

### 7.2. Agent Framework의 Span 구조 예시

```
POST /chat (FastAPI Span)
├── workflow.router (AI 의도 분류)
│   └── gen_ai.chat.completions (GPT-4o 호출)
├── workflow.executor.tool (Tool Executor)
│   └── tool_agent.mcp_call (MCP 호출)
│       └── http.client.request (HTTP 요청)
└── workflow.executor.research (Research Executor)
    └── research_agent.rag_search (RAG 검색)
        ├── gen_ai.embeddings.create (임베딩 생성)
        └── azure.search.documents.query (AI Search 쿼리)
```

### 7.3. 커스텀 Span 구현

**기본 패턴:**

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("operation_name") as span:
    # Span 속성 설정
    span.set_attribute("custom.key", "value")
    
    # 작업 수행
    result = do_something()
    
    # 결과 기록
    span.set_attribute("result.status", "success")
```

**Router Span (AI 기반 의도 분류):**

```python
with tracer.start_as_current_span("workflow.router") as span:
    span.set_attribute("router.method", "ai_based")
    span.set_attribute("router.user_message", user_message[:100])
    
    # LLM으로 의도 분류
    intent = await self._classify_intent(user_message)
    
    span.set_attribute("router.intent", intent)
    span.set_attribute("router.executor", executor_name)
```

**Tool Executor Span:**

```python
with tracer.start_as_current_span("workflow.executor.tool") as span:
    span.set_attribute("executor.type", "tool")
    span.set_attribute("tool.name", "weather")
    span.set_attribute("tool.location", location)
    
    # MCP 호출
    result = await tool_agent.execute(message)
    
    span.set_attribute("tool.result.length", len(result))
```

### 7.4. GenAI Semantic Conventions

OpenTelemetry GenAI 표준 속성:

| 속성 | 설명 | 예시 값 |
|------|------|---------|
| `gen_ai.system` | AI 시스템 종류 | `azure_openai` |
| `gen_ai.request.model` | 모델 이름 | `gpt-4o` |
| `gen_ai.request.temperature` | 온도 설정 | `0.7` |
| `gen_ai.prompt` | 입력 프롬프트 | `"What is RAG?"` |
| `gen_ai.completion` | LLM 응답 | `"RAG is..."` |
| `gen_ai.usage.prompt_tokens` | 입력 토큰 수 | `15` |
| `gen_ai.usage.completion_tokens` | 출력 토큰 수 | `120` |

---

## 8. Content Recording (Prompt/Completion)

### 8.1. Content Recording이란?

Content Recording은 **Prompt(입력)와 Completion(출력)을 Tracing에 포함**시키는 기능입니다.

**활성화 시:**
- ✅ Tracing UI에서 정확한 Prompt 확인 가능
- ✅ LLM 응답 전체 내용 확인 가능
- ✅ 프롬프트 엔지니어링 최적화
- ✅ 품질 분석 및 디버깅

**비활성화 시:**
- ❌ Prompt/Completion 내용 미표시
- ✅ 메타데이터만 수집 (모델명, 토큰 수, 소요 시간)
- ✅ 민감 정보 보호
- ✅ 저장 공간 절약

### 8.2. 활성화 방법

```bash
# 환경 변수 설정
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

### 8.3. 운영 환경별 권장 설정

| 환경 | Recording | 샘플링 | 마스킹 | 비고 |
|------|----------|--------|--------|------|
| **Dev** | ✅ ON | 100% | 선택 | 상세 디버깅 |
| **Staging** | ✅ ON | 50% | ✅ 권장 | 실제 데이터 검증 |
| **Prod (비민감)** | ✅ ON | 10-20% | ✅ 권장 | 품질 분석 |
| **Prod (민감)** | ❌ OFF | N/A | N/A | 규제 준수 |

### 8.4. PII 마스킹 구현

민감 정보 보호를 위한 마스킹 유틸리티:

**`src/foundry_agent/masking.py` 또는 `src/agent_framework/masking.py`:**

```python
import re

def mask_text(text: str, mode: str = "standard") -> str:
    """
    PII 마스킹 유틸리티
    
    Args:
        text: 원본 텍스트
        mode: "standard" | "strict" | "off"
    """
    if mode == "off":
        return text
    
    # 이메일 마스킹
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        text
    )
    
    # 전화번호 마스킹
    text = re.sub(
        r'\b\d{2,3}-\d{3,4}-\d{4}\b',
        '[PHONE]',
        text
    )
    
    if mode == "strict":
        # 카드번호 마스킹
        text = re.sub(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            '[CARD]',
            text
        )
        
        # 주민등록번호 마스킹
        text = re.sub(
            r'\b\d{6}-[1-4]\d{6}\b',
            '[SSN]',
            text
        )
    
    return text
```

**사용 예시:**

```python
from masking import mask_text

masking_mode = os.getenv("AGENT_MASKING_MODE", "standard")

with tracer.start_as_current_span("llm_call") as span:
    span.set_attribute("gen_ai.prompt", mask_text(user_message, masking_mode))
    
    response = await llm_call()
    
    span.set_attribute("gen_ai.completion", mask_text(response, masking_mode))
```

---

## 9. 계측 순서 (Order Matters!)

OpenTelemetry 계측은 **순서가 매우 중요**합니다. 잘못된 순서로 초기화하면 일부 텔레메트리가 누락될 수 있습니다.

### 9.1. 올바른 초기화 순서

```python
# ✅ 1단계: configure_azure_monitor() 가장 먼저!
configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

# ✅ 2단계: 계측 라이브러리 활성화
AIInferenceInstrumentor().instrument()  # LLM 호출 추적
FastAPIInstrumentor.instrument_app(app)  # HTTP 요청 추적 (Agent Framework)

# ✅ 3단계: AIProjectClient 생성 (logging_enable=True)
project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=project_endpoint,
    logging_enable=True
)

# ✅ 4단계: Agent 생성 및 사용
agent = project_client.agents.create_agent(...)
```

### 9.2. 잘못된 순서 (안티패턴)

```python
# ❌ 잘못된 예: AIProjectClient를 먼저 생성
project_client = AIProjectClient(...)  # configure_azure_monitor() 전에 생성

configure_azure_monitor(...)  # 너무 늦음!
AIInferenceInstrumentor().instrument()  # 이미 생성된 client는 계측 안됨

# 결과: LLM 호출이 추적되지 않음
```

---

## 10. 환경 변수 완벽 가이드

### 10.1. 필수 환경 변수

| 변수 | 분류 | 설명 |
|------|------|------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | 필수 | Application Insights 연결 문자열 |
| `OTEL_SERVICE_NAME` | 필수 | 서비스 이름 (Tracing 필터링용) |
| `PROJECT_CONNECTION_STRING` | 필수 | Azure AI Foundry Project 연결 |

### 10.2. Monitoring 관련 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OTEL_METRICS_EXPORTER` | `azure_monitor` | 메트릭 exporter 지정 |
| `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED` | `true` | 자동 로깅 활성화 |

### 10.3. Tracing 관련 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OTEL_TRACES_EXPORTER` | `azure_monitor` | Trace exporter 지정 |
| `OTEL_LOGS_EXPORTER` | `azure_monitor` | Log exporter 지정 |
| `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED` | `false` | Prompt/Completion 표시 |

### 10.4. 샘플링 관련 변수 (선택)

| 변수 | 예시 값 | 설명 |
|------|---------|------|
| `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` | 샘플링 전략 |
| `OTEL_TRACES_SAMPLER_ARG` | `0.2` | 샘플링 비율 (20%) |

### 10.5. 기타 변수

| 변수 | 예시 값 | 설명 |
|------|---------|------|
| `SEARCH_ENDPOINT` | `https://xxx.search.windows.net/` | AI Search 엔드포인트 (RAG용) |
| `SEARCH_KEY` | `...` | AI Search 관리 키 |
| `MCP_ENDPOINT` | `https://mcp-xxx.azurecontainerapps.io` | MCP 서버 엔드포인트 |
| `AGENT_MASKING_MODE` | `standard` | PII 마스킹 모드 (`standard`/`strict`/`off`) |

---

## 11. 운영 전략

### 11.1. Content Recording 전략

| 환경 | Recording | 추가 권장 | 비고 |
|------|----------|-----------|------|
| **Development** | ✅ ON | 상세 디버깅 | 모든 요청 기록 |
| **Staging** | ✅ ON + 마스킹 | 실제 데이터 검증 | PII 마스킹 필수 |
| **Production (비민감)** | ✅ ON + 샘플링 (10-20%) | 비용 최적화 | 품질 분석용 |
| **Production (민감)** | ❌ OFF | 규제 준수 | 메타데이터만 수집 |

### 11.2. 비용 최적화 전략

**1. 샘플링 적용** (섹션 12 참조)
- 고트래픽 환경에서 10-20% 샘플링
- 중요 요청은 100% 수집 (에러, 느린 요청)

**2. 데이터 보존 기간 조정**
- Application Insights 보존 기간 설정 (30-90일)
- 오래된 데이터는 Archive Storage로 이동

**3. Content Recording 선택적 사용**
- Prod 환경에서는 OFF 또는 샘플링
- 문제 조사 시에만 임시 활성화

---

## 12. 샘플링 설정

### 12.1. 샘플링이란?

샘플링은 **모든 요청이 아닌 일부만 추적**하여 비용과 저장 공간을 절약하는 기법입니다.

### 12.2. 샘플링 설정 방법

```bash
# 환경 변수 설정
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.2  # 20% 샘플링
```

### 12.3. 샘플링 전략

| 트래픽 규모 | 샘플링 비율 | 설명 |
|-----------|-----------|------|
| 낮음 (< 1000/일) | 100% (1.0) | 모든 요청 추적 |
| 중간 (1000-10000/일) | 50% (0.5) | 절반 샘플링 |
| 높음 (> 10000/일) | 10-20% (0.1-0.2) | 비용 최적화 |

### 12.4. 주의사항

- 🔴 낮은 샘플링 비율은 드문 오류를 놓칠 수 있음
- 🟡 문제 조사 중에는 임시로 100% 샘플링 권장
- 🟢 샘플링은 Tracing에만 영향 (Monitoring 메트릭은 항상 100%)

---

## 13. Kusto 쿼리 예제

### 13.1. Content Recording 확인

```kusto
dependencies
| where timestamp > ago(30m)
| where name contains "ChatCompletions" or customDimensions has "gen_ai.prompt"
| summarize count() by bin(timestamp, 5m)
```

### 13.2. 최근 Prompt/Completion 조회

```kusto
dependencies
| where timestamp > ago(30m)
| where customDimensions has "gen_ai.prompt"
| project 
    timestamp, 
    name, 
    prompt = customDimensions["gen_ai.prompt"],
    completion = customDimensions["gen_ai.completion"],
    duration
| take 10
```

### 13.3. 분 단위 호출 수 집계

```kusto
dependencies
| where timestamp > ago(1h)
| summarize calls = count() by bin(timestamp, 5m)
| order by timestamp desc
```

### 13.4. 오류 추적

```kusto
traces
| where timestamp > ago(1h)
| where severityLevel >= 3  // Error 이상
| project timestamp, message, customDimensions
| take 20
```

### 13.5. 느린 요청 분석

```kusto
dependencies
| where timestamp > ago(1h)
| where duration > 3000  // 3초 이상
| project timestamp, name, duration, customDimensions
| order by duration desc
| take 20
```

---

## 14. Troubleshooting 가이드

### 14.1. 메트릭이 0으로 표시되는 경우

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| Application Analytics가 0 | Container App 미배포 | Container App 배포 확인 |
| | CONNECTION_STRING 누락 | 환경 변수 확인 및 재배포 |
| | 호출량 부족 | 최소 10개 요청 실행 |
| | 시간 범위 오류 | Portal에서 시간 범위 조정 |

### 14.2. Tracing이 비어있는 경우

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| Tracing 데이터 없음 | `configure_azure_monitor()` 순서 오류 | 초기화 순서 확인 (섹션 9) |
| | TRACES_EXPORTER 미설정 | `OTEL_TRACES_EXPORTER=azure_monitor` 설정 |
| | Instrumentation 누락 | `AIInferenceInstrumentor().instrument()` 호출 확인 |

### 14.3. Prompt/Completion이 표시되지 않는 경우

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| Input/Output 없음 | Recording 플래그 OFF | `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` |
| | Span 속성 미설정 | `gen_ai.prompt`, `gen_ai.completion` 속성 추가 |
| | 재배포 안됨 | 새 이미지 빌드 및 재배포 |

### 14.4. 일반 디버깅 절차

1. **Container App 로그 확인:**
   ```bash
   az containerapp logs show \
     --name <app-name> \
     --resource-group <rg> \
     --follow
   ```

2. **환경 변수 확인:**
   ```bash
   az containerapp show \
     --name <app-name> \
     --resource-group <rg> \
     --query properties.template.containers[0].env
   ```

3. **Application Insights 연결 테스트:**
   ```bash
   az monitor app-insights component show \
     --app <app-name> \
     --resource-group <rg>
   ```

---

## 15. 체크리스트

### 15.1. Monitoring 활성화 체크리스트

- [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING` 환경 변수 설정
- [ ] `configure_azure_monitor()` 호출 (AIProjectClient 생성 전)
- [ ] `AIInferenceInstrumentor().instrument()` 호출
- [ ] `AIProjectClient(logging_enable=True)` 생성
- [ ] Container App으로 배포
- [ ] 10개 이상 테스트 요청 실행
- [ ] 5-10분 후 Portal에서 메트릭 확인

### 15.2. Tracing 활성화 체크리스트

- [ ] Monitoring 체크리스트 모두 완료
- [ ] `OTEL_TRACES_EXPORTER=azure_monitor` 설정
- [ ] `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` 설정
- [ ] (Agent Framework) FastAPI 계측 추가
- [ ] (Agent Framework) 커스텀 Span 구현
- [ ] Container App 재배포
- [ ] Portal Tracing 탭에서 Span Tree 확인

### 15.3. 운영 준비 체크리스트

- [ ] PII 마스킹 구현 (Prod 환경)
- [ ] 샘플링 설정 (고트래픽 환경)
- [ ] 알림 설정 (오류율, 응답 시간)
- [ ] 데이터 보존 기간 설정
- [ ] 비용 모니터링 대시보드 구성

---

## 16. FAQ

**Q1: Notebook에서 실행해도 메트릭이 수집되나요?**  
A: 아니요. Monitoring은 Container App으로 배포된 서비스만 지원합니다. Notebook 실행은 단발성이므로 집계되지 않습니다.

**Q2: Content Recording을 운영 환경에서 사용해도 되나요?**  
A: 민감 정보가 없다면 가능하지만, 샘플링 (10-20%)과 PII 마스킹을 함께 적용하는 것을 권장합니다.

**Q3: Tracing과 Monitoring 중 하나만 활성화할 수 있나요?**  
A: Tracing은 Monitoring이 먼저 설정되어야 작동합니다. Monitoring만 단독 사용은 가능합니다.

**Q4: 샘플링을 적용하면 메트릭도 영향을 받나요?**  
A: 아니요. 샘플링은 Tracing에만 영향을 주며, Monitoring 메트릭은 항상 100% 수집됩니다.

**Q5: Portal에서 메트릭이 바로 안 보이는 이유는?**  
A: Application Insights는 5-10분의 데이터 지연이 있습니다. 충분한 요청 (10개 이상) 실행 후 대기하세요.

---

## 17. 참고 자료

### 공식 문서
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-enable)
- [Azure AI Foundry Tracing](https://learn.microsoft.com/azure/ai-foundry/concepts/tracing)
- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/)
- [GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

### 관련 실습
- [Lab 3: Foundry Agent 배포](./03_deploy_foundry_agent.ipynb)
- [Lab 4: Agent Framework 배포](./04_deploy_agent_framework.ipynb)

### 추가 리소스
- [Azure Monitor 가격 정책](https://azure.microsoft.com/pricing/details/monitor/)
- [Application Insights 샘플링](https://learn.microsoft.com/azure/azure-monitor/app/sampling)
- [PII 데이터 보호 모범 사례](https://learn.microsoft.com/azure/architecture/framework/security/design-storage)

---

**✅ 완료!** 이 가이드를 통해 Azure AI Foundry Agent 시스템의 완벽한 관찰성을 구현할 수 있습니다.

💡 **Tip:** 실습 초반에는 README의 간단한 요약을 참고하고, 상세 튜닝이나 운영 시 이 문서를 활용하세요!

🏠 [README.md로 돌아가기](./README.md)
