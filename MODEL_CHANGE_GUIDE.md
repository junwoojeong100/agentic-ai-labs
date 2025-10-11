# 🔄 모델 변경 가이드 (Model Change Guide)

이 프로젝트는 **환경변수 중심 설계**로 구성되어 있어, 코드 변경 없이 모델을 쉽게 변경할 수 있습니다.

> **🎯 핵심 요약**  
> **모델 변경은 딱 1곳만!**  
> Lab 1 노트북의 `model_name`과 `model_version` 변수만 바꾸면 전체 프로젝트에 자동으로 반영됩니다.

---

## 🎯 권장 워크플로우: Lab 1 노트북 사용

**가장 쉬운 방법은 Lab 1 노트북에서 모델 설정을 변경하는 것입니다.**

### 파일: `01_deploy_azure_resources.ipynb`

**섹션 4: 모델 설정**에서 다음 변수만 수정:

```python
# 👇 이 2줄만 바꾸면 됩니다!
model_name = "gpt-5"           # 모델명 변경
model_version = "2025-08-07"   # 모델 버전 변경 (모델에 따라 다름)
model_capacity = 50            # TPM 용량 (선택적)

# 셀 실행하면 자동으로 azd 환경변수 설정
```

**이후 자동 처리:**
- ✅ Azure OpenAI에 모델 배포
- ✅ Lab 3, 4에서 `.env` 파일 자동 생성
- ✅ 모든 Agent가 동일 모델 사용

> **💡 중요:** 
> - GPT-5 패밀리(`gpt-5`, `gpt-5-chat`, `gpt-5-mini`, `gpt-5-nano`)는 모두 버전 `2025-08-07` 사용
> - 다른 모델 사용 시 해당 모델의 정확한 버전을 지정해야 함
> - 버전 확인: [Azure OpenAI Models 문서](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)
> - 다른 파일(`.env`, `main.bicep` 등)은 수정할 필요 없음!

---

## 🌍 리전(Region) 변경

Quota 부족이나 특정 리전 요구사항이 있을 때만 변경합니다.

### 변경 위치

**파일:** `01_deploy_azure_resources.ipynb` - 섹션 3

```python
# 👇 Quota 부족 시만 이 1줄 변경!
location = "eastus"  # 'eastus2', 'westus', 'swedencentral' 등으로 변경
```

### 권장 리전

| 리전 | 추천 상황 |
|------|----------|
| `eastus` | 기본값, 가장 많은 서비스 지원 |
| `eastus2` | eastus Quota 부족 시 |
| `westus` | 미국 서부 지역 선호 시 |
| `swedencentral` | 유럽 지역 필요 시 |
| `northeurope` | 유럽 대체 옵션 |

> **⚠️ 주의:** 일부 리전에서는 Azure OpenAI나 AI Foundry가 제한될 수 있습니다.  
> 배포 실패 시 에러 메시지를 확인하고 다른 리전을 시도하세요.

---

## 📋 상세 변경 위치 (Advanced)

### ✅ 인프라 레벨 (Azure 배포)

#### 파일: `infra/main.bicep`
```bicep
# 라인 34-40 파라미터 변경
param openAiModelName string = 'gpt-5'         # 👈 모델명
param openAiModelVersion string = '2025-08-07'  # 👈 버전
param openAiModelCapacity int = 50              # 👈 용량 (TPM)
```

**또는 배포 시 파라미터로 지정:**
```bash
azd up --parameter openAiModelName=gpt-4 --parameter openAiModelVersion=turbo-2024-04-09
```

---

### ✅ 애플리케이션 레벨 (런타임)

#### 파일: `src/foundry_agent/.env`
```bash
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5  # 👈 여기만 변경
```

#### 파일: `src/agent_framework/.env`
```bash
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5  # 👈 여기만 변경
```

---

## 🚀 빠른 변경 예시

### GPT-5 Chat으로 변경

**Lab 1 노트북 방법 (권장):**
```python
# 01_deploy_azure_resources.ipynb 섹션 4
model_name = "gpt-5-chat"      # 👈 대화형 모델로 변경
model_version = "2025-08-07"   # GPT-5 패밀리는 동일 버전
model_capacity = 50

# 셀 실행 후 배포
```

### 다른 모델 예시

```python
# GPT-5 Mini (경량, 저비용)
model_name = "gpt-5-mini"
model_version = "2025-08-07"

# GPT-5 Nano (저지연)
model_name = "gpt-5-nano"
model_version = "2025-08-07"
```

**수동 방법:**
```bash
# 1. azd 환경변수 설정
azd env set openAiModelName gpt-5-chat
azd env set openAiModelVersion 2025-08-07

# 2. 인프라 배포
azd provision

# 3. 환경변수 파일 수정 (foundry_agent)
sed -i 's/AZURE_AI_MODEL_DEPLOYMENT_NAME=.*/AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat/g' src/foundry_agent/.env

# 4. 환경변수 파일 수정 (agent_framework)
sed -i 's/AZURE_AI_MODEL_DEPLOYMENT_NAME=.*/AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat/g' src/agent_framework/.env

# 5. 컨테이너 재배포 (Lab 3, Lab 4 노트북 재실행)
```

---

## 🎯 변경하지 않아도 되는 파일들

### ✅ 자동 처리되는 파일 (코드 변경 불필요)
- **`src/foundry_agent/main_agent.py`** - 환경변수 자동 읽음
- **`src/foundry_agent/research_agent.py`** - 환경변수 자동 읽음
- **`src/foundry_agent/tool_agent.py`** - 환경변수 자동 읽음
- **`src/foundry_agent/api_server.py`** - 동적으로 모델명 가져옴
- **`src/agent_framework/*.py`** - 환경변수 우선 사용

### 📝 선택적 업데이트
- **`src/foundry_agent/.env.example`** - 예제 파일 (문서화 목적)
- **`src/agent_framework/.env.example`** - 예제 파일 (문서화 목적)
- **`README.md`** - 프로젝트 문서 (선택적)
- **`MODEL_CHANGE_GUIDE.md`** - 이 파일 (선택적)

---

## 📊 지원 모델 목록

## 지원 모델

| 모델명 | 버전 | 특징 |
|--------|------|------|
| `gpt-5` | `2025-08-07` | 논리 중심 및 다단계 작업 최적화 (기본값) |
| `gpt-5-chat` | `2025-08-07` | 고급 대화형, 멀티모달, 컨텍스트 인식 |
| `gpt-5-mini` | `2025-08-07` | 경량 버전, 비용 효율적 |
| `gpt-5-nano` | `2025-08-07` | 속도 최적화, 저지연 애플리케이션 |

**GPT-5 패밀리 주요 특징:**
- **Context Window**: 200,000 토큰
- **멀티모달**: 텍스트 및 이미지 입력 지원
- **Advanced Reasoning**: 논리적 추론 및 다단계 작업에 최적화
- **Tool Support**: "allowed tools" 및 "preamble" 지원
- **Safety**: 향상된 안전성 메커니즘 (Jailbreak 방어 84/100)
- **Training Data**: 2024년 10월까지의 데이터

> **참고**: 모델 버전은 Azure OpenAI Service에서 지원하는 버전을 사용하세요.  
> [Azure OpenAI Models Documentation](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)

---

## 🔍 환경변수 우선순위

프로젝트는 다음 우선순위로 모델을 선택합니다:

```
1. 생성자 파라미터 (코드에서 직접 지정)
   ↓ (없으면)
2. 환경변수 (AZURE_AI_MODEL_DEPLOYMENT_NAME)
   ↓ (없으면)
3. 기본값 (gpt-5) + 경고 로그
```

**예시:**
```python
# foundry_agent/main_agent.py
self.model = model or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5")
#           ↑ 1순위    ↑ 2순위 환경변수                           ↑ 3순위 기본값
```

---

## ✅ 체크리스트

모델 변경 시 다음 항목을 확인하세요:

### Lab 노트북 사용 시
- [ ] **Lab 1**: `01_deploy_azure_resources.ipynb` 섹션 4에서 모델 설정 변경
- [ ] **배포**: 노트북 셀 실행하여 azd 환경변수 설정
- [ ] **인프라**: `azd provision` 실행 (또는 Lab 1 전체 재실행)
- [ ] **확인**: Azure Portal에서 OpenAI 모델 배포 확인
- [ ] **Agent 배포**: Lab 3, Lab 4 노트북에서 .env 파일 자동 생성 및 컨테이너 재배포
- [ ] **테스트**: Agent 정상 작동 확인

### 수동 변경 시
- [ ] **인프라**: `azd env set` 명령어로 환경변수 설정
- [ ] **Foundry Agent**: `src/foundry_agent/.env` 파일의 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 변경
- [ ] **Agent Framework**: `src/agent_framework/.env` 파일의 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 변경
- [ ] **배포**: `azd provision` 실행하여 새 모델 배포
- [ ] **컨테이너**: Docker 이미지 재빌드 및 Container Apps 재배포
- [ ] **테스트**: Agent API 테스트

---

## 💡 팁

### 노트북 vs 수동 변경

**노트북 사용 (권장):**
- ✅ 간편한 설정 변경
- ✅ 자동 검증
- ✅ 단계별 가이드
- ✅ 실습 목적에 최적화

**수동 변경:**
- 🔧 CI/CD 파이프라인 구축 시
- 🔧 프로덕션 환경 자동화
- 🔧 스크립트 기반 배포

### 로컬 개발 vs 배포 환경

```bash
# 로컬 개발: .env 파일만 수정
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat

# Azure Container Apps 환경변수 직접 업데이트
az containerapp update \
  --name agent-service \
  --resource-group <rg-name> \
  --set-env-vars AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-chat

# 또는 Lab 3/4 노트북에서 .env 재생성 후 재배포 (권장)
```

### 여러 모델 동시 사용

각 Agent마다 다른 GPT-5 패밀리 모델을 사용할 수 있습니다:

```python
# Main Agent는 gpt-5 (논리 중심)
main_agent = MainAgent(client, model="gpt-5")

# Research Agent는 gpt-5-chat (대화형, 컨텍스트 인식)
research_agent = ResearchAgent(client, ..., model="gpt-5-chat")

# Tool Agent는 gpt-5-mini (비용 절감)
tool_agent = ToolAgent(client, model="gpt-5-mini")

# 고속 응답이 필요한 경우 gpt-5-nano
quick_agent = QuickAgent(client, model="gpt-5-nano")
```

### 배포 후 모델 확인

```bash
# Azure OpenAI 배포 확인
az cognitiveservices account deployment list \
  --name <openai-account-name> \
  --resource-group <rg-name> \
  --query "[].{Name:name, Model:properties.model.name, Version:properties.model.version}" \
  --output table

# Container Apps 환경변수 확인
az containerapp show \
  --name agent-service \
  --resource-group <rg-name> \
  --query "properties.template.containers[0].env" \
  --output table
```

---

## 📚 참고 자료

- [Azure AI Foundry - GPT-5 모델](https://ai.azure.com/catalog/models/gpt-5)
- [Azure OpenAI Service Models](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)
- [README.md - 모델 변경 섹션](./README.md#-모델-변경하기)
- [Lab 1 Notebook](./01_deploy_azure_resources.ipynb)

---

**Built with ❤️ for easy model switching**
