# Configuration Guide

이 문서는 Azure AI Foundry Agent 시스템의 환경 변수 및 설정에 대한 상세 가이드입니다.

## 📋 Table of Contents

1. [Config.json 구조](#configjson-구조)
2. [Agent Container 환경 변수](#agent-container-환경-변수)
3. [필수 vs 선택 변수](#필수-vs-선택-변수)
4. [Content Recording 운영 가이드](#content-recording-운영-가이드)
5. [변경 적용 절차](#변경-적용-절차)

---

## Config.json 구조

배포 후 `config.json`에 자동 저장되는 설정:

```json
{
  "resource_group": "rg-aiagent-xxxxx",
  "location": "eastus",
  "project_connection_string": "https://xxx.services.ai.azure.com/api/projects/yyy;subscription_id=...;resource_group=...",
  "search_endpoint": "https://srch-xxx.search.windows.net/",
  "search_service_name": "srch-xxx",
  "container_registry_endpoint": "crxxx.azurecr.io",
  "container_apps_environment_id": "/subscriptions/.../resourceGroups/.../providers/Microsoft.App/managedEnvironments/cae-xxx",
  "model_deployment_name": "gpt-4o",
  "model_version": "2024-11-20",
  "model_capacity": 50,
  "search_index": "ai-agent-knowledge-base",
  "mcp_endpoint": "https://mcp-server.xxx.azurecontainerapps.io",
  "agent_endpoint": "https://agent-service.xxx.azurecontainerapps.io",
  "agent_framework_endpoint": "https://agent-framework.xxx.azurecontainerapps.io"
}
```

### 주요 필드 설명

| 필드 | 설명 | 용도 |
|------|------|------|
| `resource_group` | 리소스 그룹 이름 | Azure 리소스 관리 |
| `location` | Azure 리전 | 배포 위치 |
| `project_connection_string` | Azure AI Foundry 프로젝트 연결 문자열 | Agent SDK 연결 |
| `search_endpoint` | Azure AI Search 엔드포인트 | RAG 검색 |
| `search_service_name` | AI Search 서비스 이름 | 관리 작업 |
| `search_index` | AI Search 인덱스 이름 | RAG 쿼리 대상 |
| `container_registry_endpoint` | Azure Container Registry 엔드포인트 | Docker 이미지 저장소 |
| `container_apps_environment_id` | Container Apps Environment ID | 컨테이너 배포 대상 |
| `model_deployment_name` | 배포된 OpenAI 모델 이름 | LLM 호출 시 사용 |
| `model_version` | OpenAI 모델 버전 | 모델 버전 추적 |
| `model_capacity` | 모델 용량 (TPM) | 처리량 설정 |
| `mcp_endpoint` | 배포된 MCP 서버 엔드포인트 | 도구 호출 |
| `agent_endpoint` | Foundry Agent API 서버 엔드포인트 | REST API 제공 (Lab 3) |
| `agent_framework_endpoint` | Agent Framework API 서버 엔드포인트 | REST API 제공 (Lab 4) |

---

## Agent Container 환경 변수

Lab 3 실행 시 `src/foundry_agent/.env` 파일이 **자동 생성**됩니다.

### 전체 환경 변수 목록

```properties
# ============================================
# Azure AI Foundry (필수)
# ============================================
PROJECT_CONNECTION_STRING=https://xxx.services.ai.azure.com/api/projects/yyy

# ============================================
# Azure AI Search - RAG (필수)
# ============================================
SEARCH_ENDPOINT=https://srch-xxx.search.windows.net/
SEARCH_KEY=xxx
SEARCH_INDEX=ai-agent-knowledge-base

# ============================================
# MCP Server (필수)
# ============================================
MCP_ENDPOINT=https://mcp-server.xxx.azurecontainerapps.io

# ============================================
# Application Insights (필수)
# ============================================
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;...

# ============================================
# OpenTelemetry Core (필수)
# ============================================
OTEL_SERVICE_NAME=azure-ai-agent
OTEL_TRACES_EXPORTER=azure_monitor
OTEL_METRICS_EXPORTER=azure_monitor
OTEL_LOGS_EXPORTER=azure_monitor
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

# ============================================
# GenAI Content Recording (권장)
# ============================================
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true

# ============================================
# 샘플링 - 고트래픽 환경 최적화 (선택)
# ============================================
# OTEL_TRACES_SAMPLER=parentbased_traceidratio
# OTEL_TRACES_SAMPLER_ARG=0.2   # 20% 샘플링

# ============================================
# PII 마스킹 정책 (선택)
# ============================================
# AGENT_MASKING_MODE=standard   # off|standard|strict
```

---

## 필수 vs 선택 변수

### 필수 변수

| 변수 | 설명 | 기본값 없음 |
|------|------|------------|
| `PROJECT_CONNECTION_STRING` | AI Foundry Project 식별자 | ❌ |
| `SEARCH_ENDPOINT` | AI Search 엔드포인트 | ❌ |
| `SEARCH_KEY` | AI Search 액세스 키 | ❌ |
| `SEARCH_INDEX` | RAG 인덱스 이름 | ❌ |
| `MCP_ENDPOINT` | MCP 서버 URL | ❌ |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights 연결 문자열 | ❌ |
| `OTEL_SERVICE_NAME` | 서비스 논리 이름 | ❌ |

### 권장 변수

| 변수 | 설명 | 권장 값 |
|------|------|---------|
| `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED` | Prompt/Completion 기록 | `true` (개발), `false` (운영) |
| `OTEL_TRACES_EXPORTER` | Trace 내보내기 대상 | `azure_monitor` |
| `OTEL_METRICS_EXPORTER` | 메트릭 내보내기 대상 | `azure_monitor` |
| `OTEL_LOGS_EXPORTER` | 로그 내보내기 대상 | `azure_monitor` |

### 선택 변수

| 변수 | 설명 | 예시 값 |
|------|------|---------|
| `OTEL_TRACES_SAMPLER` | 샘플링 전략 | `parentbased_traceidratio` |
| `OTEL_TRACES_SAMPLER_ARG` | 샘플링 비율 | `0.2` (20%) |
| `AGENT_MASKING_MODE` | PII 마스킹 수준 | `off`, `standard`, `strict` |

---

## Content Recording 운영 가이드

### 환경별 권장 설정

| 환경 | Content Recording | 샘플링 | 마스킹 | 이유 |
|------|-------------------|--------|--------|------|
| **Development** | ✅ `true` | ❌ 비활성화 | ❌ 불필요 | 전체 디버깅 정보 필요 |
| **QA/Test** | ✅ `true` | ❌ 비활성화 | ⚠️ `standard` | 테스트 데이터 검증 |
| **Staging** | ✅ `true` | ⚠️ 50% | ✅ `standard` | 실제 유사 환경 모니터링 |
| **Production (비민감)** | ✅ `true` | ✅ 10-20% | ✅ `strict` | 품질 분석 + 비용 최적화 |
| **Production (민감)** | ❌ `false` | ✅ 5-10% | ✅ `strict` | 규제 준수 (GDPR, HIPAA) |

### Content Recording 상세 설명

**활성화 시 (`true`)**
- ✅ Prompt와 Completion 전체가 Trace에 기록됨
- ✅ Tracing UI에서 입력/출력 전체 확인 가능
- ✅ 디버깅 및 품질 분석에 유용
- ⚠️ 민감 정보 노출 가능성
- ⚠️ 스토리지 비용 증가

**비활성화 시 (`false`)**
- ❌ Prompt/Completion이 Trace에 기록되지 않음
- ✅ 메타데이터만 기록 (토큰 수, 지연 시간 등)
- ✅ 민감 정보 보호
- ✅ 스토리지 비용 절감
- ⚠️ 디버깅 어려움

### 샘플링 설정

고트래픽 환경에서 비용을 절감하려면 샘플링을 활성화하세요:

```properties
# 20% 샘플링 (5개 중 1개 요청만 기록)
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.2
```

**샘플링 비율 권장사항:**
- 개발: 100% (샘플링 없음)
- Staging: 50% (`0.5`)
- Production (저트래픽): 20-50% (`0.2-0.5`)
- Production (고트래픽): 5-10% (`0.05-0.1`)

### PII 마스킹

`masking.py` 유틸리티를 사용하여 민감 정보를 마스킹할 수 있습니다:

```properties
# 마스킹 모드 설정
AGENT_MASKING_MODE=standard
```

**마스킹 레벨:**
- `off`: 마스킹 비활성화 (개발 환경)
- `standard`: 기본 패턴 마스킹 (이메일, 전화번호, 카드번호)
- `strict`: 엄격한 마스킹 (이름, 주소 등 추가)

**마스킹 대상 (standard 모드):**
- 이메일 주소: `user@example.com` → `[EMAIL]`
- 전화번호: `010-1234-5678` → `[PHONE]`
- 신용카드: `1234-5678-9012-3456` → `[CARD]`
- 주민등록번호: `123456-1234567` → `[SSN]`

---

## 변경 적용 절차

환경 변수를 변경한 후 반드시 다음 단계를 수행해야 합니다.

### 1. .env 파일 수정

```bash
# .env 파일 편집
nano src/foundry_agent/.env

# 또는 Lab 3 노트북의 해당 셀 재실행
```

### 2. Docker 이미지 재빌드

```bash
# ACR 로그인
az acr login --name <your-acr-name>

# 이미지 빌드
docker build -t <your-acr-name>.azurecr.io/agent-service:latest \
  src/foundry_agent/

# 이미지 푸시
docker push <your-acr-name>.azurecr.io/agent-service:latest
```

### 3. Container Apps 재배포

```bash
# 새 revision 배포 (자동으로 최신 이미지 사용)
az containerapp update \
  --name agent-service \
  --resource-group <resource-group> \
  --image <your-acr-name>.azurecr.io/agent-service:latest
```

### 4. 변경 사항 확인

```bash
# 환경 변수 확인
az containerapp show \
  --name agent-service \
  --resource-group <resource-group> \
  --query properties.template.containers[0].env

# 로그 확인
az containerapp logs show \
  --name agent-service \
  --resource-group <resource-group> \
  --tail 50
```

### 5. Tracing 확인 (선택)

Application Insights에서 Kusto 쿼리로 즉시 확인:

```kql
Application Insights에서 Kusto 쿼리로 즉시 확인:

```kql
// Content Recording 활성화 확인
dependencies
| where timestamp > ago(10m)
| where customDimensions.["gen_ai.system"] == "az.ai.agents"
| project timestamp, name, customDimensions.["gen_ai.prompt"], customDimensions.["gen_ai.completion"]
| take 10
```

---

## 중요 사항 ⚠️

1. **이미지 빌드 시 포함됨**
   - `.env` 파일은 Docker 이미지에 포함됩니다
   - 값 변경 후 반드시 재빌드 & 재배포 필요

2. **민감 키 보안**
   - `.env` 파일을 Git에 커밋하지 마세요
   - `.gitignore`에 포함되어 있는지 확인

3. **샘플링 주의사항**
   - 샘플링 활성화 시 Tracing UI에 일부 요청만 표시됨
   - 이는 의도된 동작입니다

4. **메트릭은 항상 전송됨**
   - Content Recording 비활성화 시에도 메트릭은 계속 수집됨
   - 호출 수, 지연 시간, 오류율 등은 영향 없음

---

## 문제 해결

### 환경 변수가 적용되지 않음

```bash
# Container 환경 변수 확인
az containerapp show --name agent-service --resource-group <rg> \
  --query properties.template.containers[0].env -o table

# 새 revision이 활성화되었는지 확인
az containerapp revision list --name agent-service --resource-group <rg> \
  -o table
```

### Content Recording이 보이지 않음

1. `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` 확인
2. Application Insights 연결 문자열이 올바른지 확인
3. 이미지 재빌드 후 재배포했는지 확인
4. 5-10분 대기 후 Tracing UI에서 확인

### 샘플링 비율이 예상과 다름

- `OTEL_TRACES_SAMPLER_ARG` 값이 0과 1 사이인지 확인
- Parent-based 샘플링은 부모 span의 결정을 따릅니다
- 일부 요청은 항상 샘플링될 수 있습니다 (오류 발생 시 등)

---

## 관련 문서

- [OBSERVABILITY.md](./OBSERVABILITY.md) - 관찰성 심화 가이드
- [README.md](./README.md) - 프로젝트 개요
- [PREREQUISITES.md](./PREREQUISITES.md) - 사전 요구사항

---

**Built with ❤️ using Azure AI Foundry**
