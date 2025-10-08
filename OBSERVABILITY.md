# Observability (Monitoring & Tracing)

> 메인 가이드로 돌아가기: [README.md](./README.md)

이 문서는 메인 README에서 분리된 **모니터링 / 트레이싱 / 운영 관찰성** 심화 가이드입니다. 실습 초반에는 README의 요약만 참고하고, 상세 튜닝/운영 시 본 문서를 활용하세요.

---
## 📑 Quick Index
1. [개요 & 계층](#1-개요)
2. [Metrics vs Tracing 비교](#2-metrics-vs-tracing)
3. [Prompt/Completion 표시 조건](#3-promptcompletion-표시-조건)
4. [계측 순서 (필수 순서도)](#4-계측-순서-order-matters)
5. [핵심 환경 변수 요약](#5-핵심-환경-변수-요약)
6. [운영 전략: Content Recording](#6-content-recording-운영-전략)
7. [샘플링 설정](#7-샘플링)
8. [Kusto Quick Queries](#8-kusto-quick-queries)
9. [Troubleshooting Top 6](#9-troubleshooting-top-6)
10. [Quick Checklist](#10-quick-checklist)
11. [Ultra-Short Recap (EN)](#11-english-ultra-short-recap)
12. [확장 아이디어](#12-향후-확장-아이디어)
13. [Application Analytics 0 데이터 케이스](#13-application-analytics-메트릭이-보이지-않는-경우)
14. [Appendix A: Tracing 활성화 상세](#appendix-a-tracing-활성화-상세-가이드-원래-readme-내용)

---
## 1. 개요
| 층 | 목적 | 도구/UI |
|----|------|---------|
| Metrics (Application Analytics) | 총 호출 수, 평균 지연, 오류율 | Project > Monitoring > Application Analytics |
| Tracing (Execution) | 단계 흐름 + Prompt/Completion(옵션) | Project > Tracing |
| Logs | 런타임 예외/상태 | Container Apps, App Insights Logs |

## 2. Metrics vs Tracing
| 구분 | Application Analytics | Tracing |
|------|----------------------|---------|
| 데이터 형태 | 집계 메트릭 | 세부 실행 Span 트리 |
| Prompt/Completion | 미지원 | Content Recording ON 시 표시 |
| 사용 목적 | 헬스 / SLA / 추세 | 디버깅 / 품질 / 프롬프트 최적화 |
| 수집 전제 | App Insights 연결 문자열 | + OpenTelemetry 계측 + Span 속성 |

## 3. Prompt/Completion 표시 조건
Prompt/Completion이 Tracing UI에 나오려면 모두 충족:
1. `APPLICATIONINSIGHTS_CONNECTION_STRING` 설정
2. `configure_azure_monitor()`가 **AIProjectClient 생성 이전** 호출
3. `AIProjectClient(logging_enable=True)`
4. `AIInferenceInstrumentor().instrument()` 호출
5. Span에 `gen_ai.prompt`, `gen_ai.completion` 속성 설정 (커스텀 span 또는 자동 계측)
6. `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true`
7. 컨테이너 재배포 (이미지에 `.env` baked)

## 4. 계측 순서 (Order Matters)
```text
configure_azure_monitor() → (optional) AIAgentsInstrumentor() → AIProjectClient(logging_enable=True)
→ AIInferenceInstrumentor().instrument() → custom span(gen_ai.*) → (content recording flag) → redeploy
```

## 5. 핵심 환경 변수 요약
| 변수 | 분류 | 설명 |
|------|------|------|
| APPLICATIONINSIGHTS_CONNECTION_STRING | 필수 | Export 대상 App Insights 연결 문자열 |
| OTEL_SERVICE_NAME | 필수 | 서비스 논리 이름(Trace 그룹) |
| PROJECT_CONNECTION_STRING | 필수 | Azure AI Foundry Project 연결 |
| AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED | 권장 | Prompt/Completion 표시 (Dev/튜닝) |
| OTEL_TRACES_SAMPLER / OTEL_TRACES_SAMPLER_ARG | 선택 | 샘플링 비율 제어 |
| SEARCH_ENDPOINT / SEARCH_KEY / SEARCH_INDEX | 필수(RAG) | Search 인덱스 접근 |
| MCP_ENDPOINT | 필수(툴) | MCP 도구 호출 엔드포인트 |

## 6. Content Recording 운영 전략
| 환경 | Recording | 추가 권장 |
|------|----------|-----------|
| Dev | ON | 상세 튜닝/디버깅 |
| Staging | ON + 마스킹 | 실제 검증 |
| Prod (민감) | OFF | 요약/통계만 저장 |
| Prod (비민감) | ON + 샘플링(≤20%) | 비용·가시성 균형 |

### 마스킹 헬퍼 (간단 예시)
```python
import re
MAX_LEN = 2000
EMAIL_RE = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"

def mask(text: str) -> str:
    t = re.sub(EMAIL_RE, "[EMAIL]", text)
    return t[:MAX_LEN] + ("...[TRUNC]" if len(t) > MAX_LEN else "")

span.set_attribute("gen_ai.prompt", mask(prompt))
span.set_attribute("gen_ai.completion", mask(output))
```

## 7. 샘플링
고트래픽 시 비용/저장 최적화:
```bash
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.2  # 20%
```
주의: 낮은 비율은 드문 오류 재현을 어렵게 할 수 있음 → 문제 조사 중엔 1.0 임시 사용.

## 8. Kusto Quick Queries

**Content Recording & 샘플링 확인:**

```kusto
dependencies
| where timestamp > ago(30m)
| where name contains "ChatCompletions" or customDimensions has "gen_ai.prompt"
| summarize count() by bin(timestamp, 5m)
```

**최근 Prompt/Completion 10건 조회:**

```kusto
dependencies
| where timestamp > ago(30m)
| where customDimensions has "gen_ai.prompt"
| project timestamp, name, customDimensions["gen_ai.prompt"], customDimensions["gen_ai.completion"], duration
| take 10
```

**분 단위 호출 수 집계:**

```kusto
dependencies
| where timestamp > ago(1h)
| summarize calls = count() by bin(timestamp, 5m)
| order by timestamp desc
```

**오류 추적 (Severity Level 3 이상):**

```kusto
traces
| where timestamp > ago(1h)
| where severityLevel >= 3
| project timestamp, message, customDimensions
| take 20
```

## 9. Troubleshooting Top 6
| 증상 | 원인 | 해결 |
|------|------|------|
| 메트릭 0 | 컨테이너 미배포 / 연결 문자열 누락 | App Insights 변수 재확인 후 재배포 |
| Tracing 비어있음 | `configure_azure_monitor()` 순서 오류 | 앱 시작 최상단에서 호출 |
| Input/Output 없음 | Recording flag 꺼짐 / span 속성 미설정 | env true + `gen_ai.*` 설정 |
| 모델 span 없음 | Inference 계측 누락 | `AIInferenceInstrumentor().instrument()` 호출 |
| Agent 구조 span 없음 | AIAgentsInstrumentor 미설치/미호출 | 패키지 업데이트 + instrument() |
| completion 속성 누락 | 예외로 span 종료 | finally 블록에서 set_attribute |

## 10. Quick Checklist
```text
[ ] configure_azure_monitor() 선실행
[ ] AIProjectClient(logging_enable=True)
[ ] AIInferenceInstrumentor() 호출
[ ] gen_ai.prompt / gen_ai.completion 설정
[ ] (옵션) AIAgentsInstrumentor / Recording / Sampling
[ ] 재빌드 & 재배포
```

## 11. English Ultra-Short Recap
Configure early → (Agents) → Create client → Inference instrument → Add gen_ai.* attrs → (Enable content) → Redeploy.

## 12. 향후 확장 아이디어
- Token usage span 속성 (`gen_ai.usage.prompt_tokens`, `gen_ai.usage.completion_tokens`)
- 중앙 마스킹 유틸 모듈화 & config 기반 모드 전환
- Trace 기반 품질 지표(응답 길이, RAG 히트율) 커스텀 이벤트화
- CI 파이프라인에 Kusto lint(쿼리 smoke test) 추가

## 13. Application Analytics 메트릭이 보이지 않는 경우

메트릭 화면(Application Analytics)에 호출 수/지연 등이 0으로만 표시되는 경우 아래를 점검하세요.

### 증상
- Azure AI Foundry Portal의 Application Analytics에서 모든 메트릭이 0으로 표시
- Agent 정상 응답에도 Total inference calls / Average duration / Error rate 미집계

### 원인 (정확한 설명)
#### 📖 주요 원인 및 설명

Notebook 기반 기본 흐름은 API 서버(`src/foundry_agent/api_server.py`)를 **지속 실행**하지 않거나 OpenTelemetry 초기화를 수행하지 않으므로 **Application Insights로 전송되는 메트릭/트레이스가 생성되지 않아** 0으로 보입니다. 플랫폼 제한이 아니라 계측 미실행 & 환경 변수 누락이 핵심입니다. Portal의 Analytics는 지속 서비스 패턴을 가정하므로 짧은 단발 실행 호출만으로는 집계가 지연/생략될 수 있습니다.

### 해결 방법 (권장 순서)
1. 컨테이너(ACA)에 Agent 배포 (Lab 3 섹션 5.2)
2. 배포된 HTTP 엔드포인트를 통한 반복 호출 (Lab 3 섹션 6)
3. (선택) 로컬에서 동일 계측을 적용해 테스트

### 실행 환경별 비교
| 실행 환경 | OpenTelemetry 초기화 | .env 주입 | 지속성 | 결과 |
|-----------|--------------------|----------|--------|------|
| 로컬 Notebook | ❌ (미호출) | ❌ | 단발 | 0 (데이터 없음) |
| 로컬 서버(직접 실행) | ✅ 가능 | ✅ 수동 | 지속 | 메트릭/트레이스 생성 가능 |
| Container (ACA) | ✅ 자동(코드 포함) | ✅ Lab 3 `.env` | 지속/스케일 | 안정 수집 |

### 주요 원인 Top 5
1. OpenTelemetry 미초기화 (`configure_azure_monitor` 누락)
2. 환경 변수 미설정 (`APPLICATIONINSIGHTS_CONNECTION_STRING`, `OTEL_SERVICE_NAME` 등)
3. 프로세스 수명 짧음 (집계 전 종료)
4. 호출량 부족 (UI 집계 지연 5–10분)
5. 네트워크/권한 차이 (Notebook 자격 이슈 등)

### 필수 코드 스니펫 (Notebook 테스트 시)
```python
from azure.monitor.opentelemetry import configure_azure_monitor
import os
configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
```

### 필수 환경 변수 예시
```properties
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;...
OTEL_SERVICE_NAME=azure-ai-agent
OTEL_TRACES_EXPORTER=azure_monitor
OTEL_METRICS_EXPORTER=azure_monitor
OTEL_LOGS_EXPORTER=azure_monitor
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
```

### 빠른 검증 절차
```bash
curl -X POST https://<agent-endpoint>/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is the weather in Seoul?"}'
```
Portal 경로: https://ai.azure.com > Project > Monitoring > Application Analytics (5–10분 대기)

### 추가 팁

- 초기엔 Tracing(Kusto)에서 raw span 존재 여부 먼저 확인
- 메트릭 0 + Tracing OK → 집계 지연 가능성 높음

---

---
**참고:** 구현 참조 파일: `src/agent/api_server.py`

---
## Appendix A. Tracing 활성화 상세 가이드 (README 원본 보관용)

> **⚠️ 동기화 주의**: 이 섹션은 README.md에서 OBSERVABILITY.md로 이동한 원본 내용을 참고용으로 보관합니다. README.md가 업데이트되면 이 섹션도 함께 동기화해야 합니다. 최신 간소화된 내용은 README.md를 참고하세요.

Application Analytics는 메트릭(숫자)만 제공하지만, **Tracing**은 Agent의 상세 실행 흐름 + (선택적) 프롬프트/응답을 시각화합니다.

### A.1 표시 가능한 정보
- Agent 실행 흐름 (Tool 호출 순서, LLM 요청)
- 단계별 소요 시간
- 오류 지점 식별
- (향후) 토큰 사용량 세부 분석

### A.2 Input/Output 표시 조건 (요약)
```
OTEL_* 환경 변수 세팅
configure_azure_monitor() 선 호출 (클라이언트 생성 전)
AIProjectClient(logging_enable=True)
AIInferenceInstrumentor().instrument()
Span: gen_ai.prompt / gen_ai.completion
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
컨테이너 재배포 (새 revision)
```

### A.3 단계별 활성화
1. Lab 3 실행 → `.env` 자동 생성
2. 컨테이너 시작 → `configure_azure_monitor()` 호출
3. `AIInferenceInstrumentor()` / (옵션) `AIAgentsInstrumentor()`
4. 커스텀 span에서 `gen_ai.prompt` / `gen_ai.completion` 설정
5. Content Recording 활성화 → Tracing UI Input/Output 표시

### A.4 코드 스니펫 (실제 구현 기반)

**실제 `api_server.py` 초기화 순서:**

```python
# 1. Application Insights 연결 문자열 획득 (환경 변수)
app_insights_conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

# 2. OpenTelemetry 계측 (AIProjectClient 생성 전에 필수)
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor(
    connection_string=app_insights_conn_str,
    enable_live_metrics=True,
    instrumentation_options={
        "azure_sdk": {"enabled": True},
        "fastapi": {"enabled": True},
        "requests": {"enabled": True},
    }
)

# 3. (선택) Agent 구조 자동 계측
try:
    from azure.ai.agents.telemetry import AIAgentsInstrumentor
    AIAgentsInstrumentor().instrument()
except ImportError:
    pass  # 패키지 없으면 생략

# 4. AIProjectClient 생성 (logging_enable=True)
project_client = AIProjectClient(
    credential=credential,
    endpoint=project_endpoint,
    logging_enable=True  # 필수
)

# 5. AI Inference 계측 (모델 호출 추적)
from azure.ai.inference.tracing import AIInferenceInstrumentor
AIInferenceInstrumentor().instrument()

# 6. (선택) 커스텀 span에서 prompt/completion 속성 설정
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("agent_chat") as span:
    span.set_attribute("gen_ai.prompt", user_message)
    # ... Agent 실행 ...
    span.set_attribute("gen_ai.completion", agent_response)
```

```

> **교육 목적 참고**: 위 코드는 실제 `src/foundry_agent/api_server.py`의 초기화 흐름을 단순화한 것입니다. 전체 컨텍스트는 소스 파일을 직접 참고하세요.

#### 2.2 메트릭 계측

### A.5 대안 검증 (Input/Output 미표시 시)
Kusto:
```kusto
dependencies
| where timestamp > ago(1h)
| where name contains "ChatCompletions" or customDimensions has "gen_ai.prompt"
| project timestamp, name, customDimensions["gen_ai.prompt"], customDimensions["gen_ai.completion"], duration
| take 20
```
Container Logs:
```bash
az containerapp logs show \
    --name agent-service \
    --resource-group <rg> \
    --tail 100 --follow
```

### A.6 Application Analytics vs Tracing 비교 (간단)
| 기능 | Analytics | Tracing |
|------|----------|---------|
| 데이터 | 집계 숫자 | 실행 단계 + 속성 |
| Prompt/Completion | ❌ | ✅ (Recording ON) |
| 용도 | 헬스/추세 | 디버깅/튜닝 |

### A.7 Troubleshooting (추가)
| 증상 | 원인 | 해결 |
|------|------|------|
| Input/Output 없음 | Recording OFF / span 속성 누락 | flag true + gen_ai.* 설정 |
| Tracing 전무 | 순서 오류(`configure_azure_monitor` 늦음) | 초기화 위치 상단 이동 |
| 모델 span 없음 | Inference 계측 누락 | AIInferenceInstrumentor 추가 |
| Agent 구조 미표시 | AIAgentsInstrumentor 미적용 | 패키지 업그레이드 후 enable |
| 오래된 값 유지 | 재배포 미실시 | 새 이미지 + 새 revision 배포 |

---
