# Multi-Agent System Source Code

이 디렉토리는 Azure AI Foundry Agent Service 기반 Multi-Agent 시스템의 소스 코드를 포함합니다.

## 디렉토리 구조

```
src/
├── agents/          # Multi-Agent 시스템 구현
│   ├── multi_agent.py      # MultiAgentOrchestrator 클래스
│   ├── requirements.txt    # Python 의존성
│   └── Dockerfile          # 컨테이너 이미지 (선택사항)
│
└── mcp/             # Model Context Protocol 서버
    ├── server.py           # MCP 서버 구현
    ├── requirements.txt    # Python 의존성
    └── Dockerfile          # 컨테이너 이미지
```

## 주요 컴포넌트

### 1. Multi-Agent System (`agents/`)

**파일**: `multi_agent.py`

Azure AI Foundry Agent Service를 사용한 멀티 에이전트 오케스트레이션 시스템입니다.

**주요 클래스**:
- `MultiAgentOrchestrator`: 여러 Agent를 조율하는 메인 클래스

**Agent 구성**:
1. **Main Orchestrator Agent**: 사용자 요청 분석 및 라우팅
2. **MCP Tool Agent**: MCP 서버의 도구 활용 (Connected Agent)
3. **RAG Research Agent**: Azure AI Search를 통한 지식 베이스 검색

**주요 메서드**:
```python
# Agent 설정
await orchestrator.setup_agents()

# 쿼리 처리
result = await orchestrator.orchestrate_query("Your question here")

# 정리
await orchestrator.cleanup()
```

### 2. MCP Server (`mcp/`)

**파일**: `server.py`

Model Context Protocol을 구현한 도구 서버입니다.

**제공 도구**:
- `get_weather`: 도시별 날씨 정보 조회
- `calculate`: 수학 계산 수행
- `get_current_time`: 현재 시간 조회
- `generate_random_number`: 랜덤 숫자 생성

**실행 방법**:
```bash
# 로컬 실행
cd src/mcp
pip install -r requirements.txt
python server.py

# Docker로 실행
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
```

## 배포

### MCP Server 배포

Notebook 3 (`03_azure_foundry_multi_agent.ipynb`)를 참조하세요. 자동으로:
1. Docker 이미지 빌드
2. Azure Container Registry에 푸시
3. Azure Container Apps에 배포

### Multi-Agent 사용

Notebook에서 직접 사용하거나, 스크립트로 실행:

```python
import asyncio
from multi_agent import MultiAgentOrchestrator

async def main():
    orchestrator = MultiAgentOrchestrator(
        project_connection_string="your_connection_string",
        search_endpoint="your_search_endpoint",
        search_key="your_search_key",
        search_index="your_index_name",
        mcp_endpoint="https://your-mcp-server.azurecontainerapps.io"
    )
    
    # Setup
    await orchestrator.setup_agents()
    
    # Use
    result = await orchestrator.orchestrate_query("What is RAG?")
    print(result['final_response'])
    
    # Cleanup
    await orchestrator.cleanup()

asyncio.run(main())
```

## 의존성

### Multi-Agent System
- `azure-ai-projects>=1.0.0`: Azure AI Foundry Agent Service SDK
- `azure-identity>=1.17.0`: Azure 인증
- `azure-search-documents>=11.6.0`: Azure AI Search 클라이언트
- `openai>=1.40.0`: OpenAI/Azure OpenAI SDK

### MCP Server
- `mcp>=1.0.0`: Model Context Protocol SDK
- `python-dotenv>=1.0.0`: 환경 변수 관리

## 환경 변수

필요한 환경 변수:

```bash
# Multi-Agent System
SEARCH_KEY=your_azure_search_admin_key

# Optional for MCP Server
TZ=UTC  # 타임존 설정
```

## 개발 가이드

### Agent 추가하기

새로운 전문 Agent를 추가하려면:

```python
# 1. Agent 생성
new_agent = self.project_client.agents.create_agent(
    model="gpt-4o",
    name="New Specialized Agent",
    instructions="Your agent instructions...",
    tools=your_tools  # Optional
)

# 2. 오케스트레이션 로직에 통합
# orchestrate_query() 메서드에 라우팅 로직 추가
```

### MCP 도구 추가하기

`server.py`에서:

```python
# 1. list_tools()에 도구 스키마 추가
Tool(
    name="new_tool",
    description="Tool description",
    inputSchema={...}
)

# 2. call_tool()에 구현 추가
if name == "new_tool":
    # 도구 로직 구현
    result = your_tool_logic(arguments)
    return [TextContent(type="text", text=json.dumps(result))]
```

## 문제 해결

### Agent 생성 실패
- Azure AI Foundry 프로젝트 연결 문자열 확인
- 적절한 권한 확인 (Contributor 이상)

### MCP 서버 연결 실패
- Container Apps 엔드포인트 확인
- 네트워크 설정 및 방화벽 규칙 확인
- 컨테이너 로그 확인

### RAG 검색 실패
- Azure AI Search 인덱스 존재 확인
- 검색 키 권한 확인 (Admin 키 필요)
- 인덱스에 문서가 있는지 확인

## 참고 자료

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Agent Service Guide](https://learn.microsoft.com/azure/ai-foundry/concepts/agents)
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
