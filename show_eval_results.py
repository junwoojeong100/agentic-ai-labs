#!/usr/bin/env python3
"""평가 결과 상세 출력"""
import json
from pathlib import Path

SEPARATOR = "─" * 100
LINE = "=" * 100

def get_score_color(score, threshold=3.0):
    if score >= 4.5:
        return "\033[92m"
    elif score >= threshold:
        return "\033[93m"
    else:
        return "\033[91m"

def reset_color():
    return "\033[0m"

def get_score_indicator(score, threshold=3.0):
    if score >= 4.5:
        return "✅"
    elif score >= threshold:
        return "⚠️"
    else:
        return "❌"

def extract_query_text(query_input):
    if isinstance(query_input, list):
        for item in query_input:
            if isinstance(item, dict) and item.get("role") == "user":
                content = item.get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get("text", "")
    return ""

def extract_response_text(response):
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict) and item.get("role") == "assistant":
                content = item.get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get("text", "")
    return ""

def main():
    eval_output_path = Path("evals/eval-output.json")
    
    print(LINE)
    print("📊 AGENT EVALUATION RESULTS - 상세 분석 리포트")
    print(LINE, "\n")
    
    if not eval_output_path.exists():
        print("❌ 평가 결과 파일이 없습니다.")
        print(f"   파일 경로: {eval_output_path.absolute()}")
        print("\n   먼저 06_evaluate_agents.ipynb의 셀 5를 실행하세요.\n")
        return
    
    with open(eval_output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    metrics = data.get("metrics", {})
    rows = data.get("rows", [])
    
    # 섹션 1: 전체 평균 점수
    print("⭐ 전체 평균 성능 점수")
    print(LINE)
    scores_config = [
        ("Intent Resolution", "intent_resolution.intent_resolution", "의도 파악", 3.0),
        ("Task Adherence", "task_adherence.task_adherence", "작업 충실도", 3.0),
    ]
    
    for name, key, desc, threshold in scores_config:
        if key in metrics:
            score = metrics[key]
            color = get_score_color(score, threshold)
            reset = reset_color()
            indicator = get_score_indicator(score, threshold)
            stars = "★" * int(score) + "☆" * (5 - int(score))
            bar = "█" * int(score * 4) + "░" * (20 - int(score * 4))
            
            print(f"{indicator} {name:20} {color}{score:.2f}/5.0{reset}  {stars}")
            print(f"     {desc:20} [{bar}]")
            if score < threshold:
                print(f"     {color}⚠️ 임계값 미달 (기준: {threshold:.1f}){reset}")
            print()
    
    # 섹션 2: 운영 메트릭
    print("\n⚡ 운영 메트릭 (평균)")
    print(LINE)
    
    operational_keys = [
        ("operational_metrics.server-run-duration-in-seconds", "서버 실행 시간", "s"),
        ("operational_metrics.client-run-duration-in-seconds", "클라이언트 실행 시간", "s"),
        ("operational_metrics.prompt-tokens", "프롬프트 토큰", "tokens"),
        ("operational_metrics.completion-tokens", "완성 토큰", "tokens"),
    ]
    
    total_tokens = 0
    for key, desc, unit in operational_keys:
        if key in metrics:
            value = metrics[key]
            if unit == "tokens":
                print(f"  {desc:30} {int(value):>10,} {unit}")
                total_tokens += value
            else:
                print(f"  {desc:30} {value:>10.2f} {unit}")
    
    if total_tokens > 0:
        print(f"  {'총 토큰 사용량':30} {int(total_tokens):>10,} tokens")
        cost = (total_tokens / 1000) * 0.0025
        print(f"  {'예상 비용 (GPT-4o)':30} ${cost:>9.4f}")
    print()
    
    # 섹션 3: 개별 쿼리 상세 결과
    if rows:
        print("\n📋 쿼리별 상세 결과")
        print(LINE)
        
        for idx, row in enumerate(rows, 1):
            query = extract_query_text(row.get("inputs.query", []))
            response = extract_response_text(row.get("inputs.response", []))
            ground_truth = row.get("inputs.metrics.ground-truth", "")
            
            print(f"\n{SEPARATOR}")
            print(f"🔍 Query #{idx}")
            print(SEPARATOR)
            
            print("\n💬 사용자 질문:")
            print(f"   {query}")
            
            if ground_truth:
                print("\n📌 예상 동작 (Ground Truth):")
                print(f"   {ground_truth}")
            
            if response:
                print("\n🤖 Agent 응답 (요약):")
                response_preview = response[:200] if len(response) > 200 else response
                lines_shown = 0
                for line in response_preview.split("\n"):
                    if line.strip() and lines_shown < 3:
                        print(f"   {line.strip()}")
                        lines_shown += 1
                if len(response) > 200:
                    print(f"   ... (총 {len(response):,}자)")
            
            print("\n📊 평가 점수:")
            
            intent = row.get("outputs.intent_resolution.intent_resolution", "N/A")
            task = row.get("outputs.task_adherence.task_adherence", "N/A")
            tool = row.get("outputs.tool_call_accuracy.tool_call_accuracy", "N/A")
            
            intent_threshold = row.get("outputs.intent_resolution.intent_resolution_threshold", 3)
            task_threshold = row.get("outputs.task_adherence.task_adherence_threshold", 3)
            
            if isinstance(intent, (int, float)):
                color = get_score_color(intent, intent_threshold)
                reset = reset_color()
                indicator = get_score_indicator(intent, intent_threshold)
                print(f"   {indicator} Intent Resolution:  {color}{intent:.1f}/5.0{reset} (임계값: {intent_threshold})")
            else:
                print(f"   • Intent Resolution:  {intent}")
            
            if isinstance(task, (int, float)):
                color = get_score_color(task, task_threshold)
                reset = reset_color()
                indicator = get_score_indicator(task, task_threshold)
                print(f"   {indicator} Task Adherence:     {color}{task:.1f}/5.0{reset} (임계값: {task_threshold})")
            else:
                print(f"   • Task Adherence:     {task}")
            
            print(f"   • Tool Call Accuracy: {tool}")
            
            # 평가 이유
            print("\n�� 평가 상세:")
            
            intent_reason = row.get("outputs.intent_resolution.intent_resolution_reason", "")
            task_reason = row.get("outputs.task_adherence.task_adherence_reason", "")
            tool_reason = row.get("outputs.tool_call_accuracy.tool_call_accuracy_reason", "")
            
            if intent_reason:
                print("\n   [Intent Resolution 평가 이유]")
                for sentence in intent_reason.split(". "):
                    if sentence.strip():
                        print(f"   • {sentence.strip()}.")
            
            if task_reason:
                print("\n   [Task Adherence 평가 이유]")
                for sentence in task_reason.split(". "):
                    if sentence.strip():
                        print(f"   • {sentence.strip()}.")
            
            if tool_reason:
                print("\n   [Tool Call Accuracy 평가 이유]")
                for sentence in tool_reason.split(". "):
                    if sentence.strip():
                        print(f"   • {sentence.strip()}.")
            
            duration = row.get("outputs.operational_metrics.client-run-duration-in-seconds", 0)
            prompt_tokens = row.get("outputs.operational_metrics.prompt-tokens", 0)
            completion_tokens = row.get("outputs.operational_metrics.completion-tokens", 0)
            
            print("\n⏱️  성능 메트릭:")
            print(f"   • 실행 시간: {duration:.2f}초")
            print(f"   • 토큰 사용: {prompt_tokens:,} (입력) + {completion_tokens:,} (출력) = {prompt_tokens + completion_tokens:,} (총)")
            
            issues = []
            if isinstance(intent, (int, float)) and intent < intent_threshold:
                issues.append(f"Intent Resolution 점수 낮음 ({intent:.1f} < {intent_threshold})")
            if isinstance(task, (int, float)) and task < task_threshold:
                issues.append(f"Task Adherence 점수 낮음 ({task:.1f} < {task_threshold})")
            
            if issues:
                print(f"\n{get_score_color(1.0, 3.0)}⚠️  발견된 문제:{reset_color()}")
                for issue in issues:
                    print(f"   • {issue}")
        
        # 섹션 4: 통계 요약
        print(f"\n{SEPARATOR}\n")
        print("\n📈 통계 요약 및 분석")
        print(LINE)
        
        intent_scores = []
        task_scores = []
        durations = []
        total_tokens_list = []
        failed_queries = []
        
        for idx, row in enumerate(rows, 1):
            intent = row.get("outputs.intent_resolution.intent_resolution")
            task = row.get("outputs.task_adherence.task_adherence")
            duration = row.get("outputs.operational_metrics.client-run-duration-in-seconds", 0)
            prompt = row.get("outputs.operational_metrics.prompt-tokens", 0)
            completion = row.get("outputs.operational_metrics.completion-tokens", 0)
            
            intent_threshold = row.get("outputs.intent_resolution.intent_resolution_threshold", 3)
            task_threshold = row.get("outputs.task_adherence.task_adherence_threshold", 3)
            
            if isinstance(intent, (int, float)):
                intent_scores.append(intent)
                if intent < intent_threshold:
                    query = extract_query_text(row.get("inputs.query", []))
                    failed_queries.append((idx, "Intent Resolution", intent, query[:50]))
            
            if isinstance(task, (int, float)):
                task_scores.append(task)
                if task < task_threshold:
                    query = extract_query_text(row.get("inputs.query", []))
                    failed_queries.append((idx, "Task Adherence", task, query[:50]))
            
            if duration:
                durations.append(duration)
            total_tokens_list.append(prompt + completion)
        
        if intent_scores:
            avg_intent = sum(intent_scores) / len(intent_scores)
            color = get_score_color(avg_intent, 3.0)
            reset = reset_color()
            pass_count = len([s for s in intent_scores if s >= 3.0])
            
            print("\n📊 Intent Resolution (의도 파악)")
            print(f"   평균: {color}{avg_intent:.2f}/5.0{reset}")
            print(f"   최고: {max(intent_scores):.1f}  |  최저: {min(intent_scores):.1f}")
            print(f"   합격률: {pass_count}/{len(intent_scores)} ({pass_count/len(intent_scores)*100:.1f}%)")
        
        if task_scores:
            avg_task = sum(task_scores) / len(task_scores)
            color = get_score_color(avg_task, 3.0)
            reset = reset_color()
            pass_count = len([s for s in task_scores if s >= 3.0])
            
            print("\n📊 Task Adherence (작업 충실도)")
            print(f"   평균: {color}{avg_task:.2f}/5.0{reset}")
            print(f"   최고: {max(task_scores):.1f}  |  최저: {min(task_scores):.1f}")
            print(f"   합격률: {pass_count}/{len(task_scores)} ({pass_count/len(task_scores)*100:.1f}%)")
        
        if durations:
            print("\n⏱️  실행 시간")
            print(f"   평균: {sum(durations)/len(durations):.2f}초")
            print(f"   최대: {max(durations):.2f}초  |  최소: {min(durations):.2f}초")
        
        if total_tokens_list:
            avg_tokens = sum(total_tokens_list) / len(total_tokens_list)
            total_all_tokens = sum(total_tokens_list)
            
            print("\n💰 토큰 사용량")
            print(f"   평균: {avg_tokens:,.0f} tokens/query")
            print(f"   총합: {total_all_tokens:,} tokens")
            print(f"   최대: {max(total_tokens_list):,}  |  최소: {min(total_tokens_list):,}")
            print(f"   예상 비용 (GPT-4o): ${(total_all_tokens / 1000) * 0.0025:.4f}")
        
        if failed_queries:
            print(f"\n{get_score_color(1.0, 3.0)}⚠️  개선이 필요한 쿼리 ({len(failed_queries)}개){reset_color()}")
            print(SEPARATOR)
            
            seen = set()
            for idx, metric, score, query in failed_queries:
                key = (idx, metric)
                if key not in seen:
                    seen.add(key)
                    print(f"   Query #{idx}: {metric} = {score:.1f}")
                    print(f"   └─ {query}...")
                    print()
        else:
            print("\n✅ 모든 쿼리가 임계값을 통과했습니다!")
    
    print(f"\n{LINE}")
    print(f"✅ 총 {len(rows)}개 쿼리 평가 완료")
    print(f"📁 상세 JSON: {eval_output_path.absolute()}")
    print(f"💡 노트북에서도 동일한 결과 확인 가능 (셀 6)")
    print(f"{LINE}\n")

if __name__ == "__main__":
    main()
