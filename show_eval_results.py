#!/usr/bin/env python3
"""
Evaluation 결과 상세 출력 스크립트
"""
import json
from pathlib import Path

def main():
    eval_output_path = Path("evals/eval-output.json")
    
    print("=" * 80)
    print("📊 AGENT EVALUATION RESULTS (상세)")
    print("=" * 80 + "\n")
    
    if not eval_output_path.exists():
        print("❌ 평가 결과 파일이 없습니다.")
        print(f"   파일 경로: {eval_output_path.absolute()}")
        print("\n   먼저 06_evaluate_agents.ipynb의 셀 5를 실행하세요.\n")
        return
    
    try:
        with open(eval_output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metrics = data.get('metrics', {})
        rows = data.get('rows', [])
        
        # 1. 전체 평균 점수
        print("⭐ 전체 평균 성능 점수")
        print("-" * 80)
        scores = [
            ('Intent Resolution', 'intent_resolution.intent_resolution', '의도 파악'),
            ('Task Adherence', 'task_adherence.task_adherence', '작업 충실도'),
        ]
        
        for name, key, desc in scores:
            if key in metrics:
                score = metrics[key]
                stars = '★' * int(score) + '☆' * (5 - int(score))
                bar = '█' * int(score * 4) + '░' * (20 - int(score * 4))
                print(f"  {name:20} {score:.2f}/5.0  {stars}  [{bar}]")
                print(f"  {'':20} → {desc}")
        
        # 2. 운영 메트릭
        print("\n\n⚡ 운영 메트릭 (평균)")
        print("-" * 80)
        
        operational_keys = [
            ('operational_metrics.server-run-duration-in-seconds', '서버 실행 시간', 's'),
            ('operational_metrics.client-run-duration-in-seconds', '클라이언트 실행 시간', 's'),
            ('operational_metrics.prompt-tokens', '프롬프트 토큰', 'tokens'),
            ('operational_metrics.completion-tokens', '완성 토큰', 'tokens'),
        ]
        
        for key, desc, unit in operational_keys:
            if key in metrics:
                value = metrics[key]
                if unit == 'tokens':
                    print(f"  {desc:25} {int(value):>8,} {unit}")
                else:
                    print(f"  {desc:25} {value:>8.2f} {unit}")
        
        # 3. 개별 쿼리 결과
        if rows:
            print("\n\n📋 쿼리별 상세 결과")
            print("=" * 80)
            
            for idx, row in enumerate(rows, 1):
                # 쿼리 텍스트 추출
                query = ""
                query_input = row.get('inputs.query', [])
                if isinstance(query_input, list):
                    for item in query_input:
                        if isinstance(item, dict) and item.get('role') == 'user':
                            content = item.get('content', [])
                            if isinstance(content, list) and len(content) > 0:
                                query = content[0].get('text', '')
                            break
                
                print(f"\n[Query {idx}]")
                print(f"질문: {query[:100]}{'...' if len(query) > 100 else ''}")
                
                # 점수
                intent = row.get('outputs.intent_resolution.intent_resolution', 'N/A')
                task = row.get('outputs.task_adherence.task_adherence', 'N/A')
                tool = row.get('outputs.tool_call_accuracy.tool_call_accuracy', 'N/A')
                
                print(f"  Intent Resolution:  {intent if isinstance(intent, str) else f'{intent:.1f}/5.0'}")
                print(f"  Task Adherence:     {task if isinstance(task, str) else f'{task:.1f}/5.0'}")
                print(f"  Tool Call Accuracy: {tool}")
                
                # 운영 메트릭
                duration = row.get('outputs.operational_metrics.client-run-duration-in-seconds', 0)
                prompt_tokens = row.get('outputs.operational_metrics.prompt-tokens', 0)
                completion_tokens = row.get('outputs.operational_metrics.completion-tokens', 0)
                
                print(f"  실행 시간: {duration:.2f}s  |  토큰: {prompt_tokens} + {completion_tokens} = {prompt_tokens + completion_tokens}")
                
                # 평가 이유 (있는 경우)
                intent_reason = row.get('outputs.intent_resolution.intent_resolution_reason', '')
                if intent_reason and len(intent_reason) < 150:
                    print(f"  💬 평가: {intent_reason}")
                
                print("-" * 80)
            
            # 4. 통계 요약
            print("\n\n📈 통계 요약")
            print("=" * 80)
            
            intent_scores = []
            task_scores = []
            durations = []
            total_tokens = []
            
            for row in rows:
                intent = row.get('outputs.intent_resolution.intent_resolution')
                task = row.get('outputs.task_adherence.task_adherence')
                duration = row.get('outputs.operational_metrics.client-run-duration-in-seconds', 0)
                prompt = row.get('outputs.operational_metrics.prompt-tokens', 0)
                completion = row.get('outputs.operational_metrics.completion-tokens', 0)
                
                if isinstance(intent, (int, float)):
                    intent_scores.append(intent)
                if isinstance(task, (int, float)):
                    task_scores.append(task)
                if duration:
                    durations.append(duration)
                total_tokens.append(prompt + completion)
            
            if intent_scores:
                print(f"Intent Resolution 평균:  {sum(intent_scores)/len(intent_scores):.2f}/5.0")
                print(f"  최고: {max(intent_scores):.1f}  |  최저: {min(intent_scores):.1f}")
            
            if task_scores:
                print(f"\nTask Adherence 평균:     {sum(task_scores)/len(task_scores):.2f}/5.0")
                print(f"  최고: {max(task_scores):.1f}  |  최저: {min(task_scores):.1f}")
            
            if durations:
                print(f"\n실행 시간 평균:           {sum(durations)/len(durations):.2f}s")
                print(f"  최고: {max(durations):.2f}s  |  최저: {min(durations):.2f}s")
            
            if total_tokens:
                print(f"\n토큰 사용 평균:           {sum(total_tokens)/len(total_tokens):.0f} tokens")
                print(f"  최대: {max(total_tokens)}  |  최소: {min(total_tokens)}")
        
        print("\n\n" + "=" * 80)
        print(f"✅ 총 {len(rows)}개 쿼리 평가 완료")
        print(f"� 상세 JSON 파일: {eval_output_path.absolute()}")
        print("=" * 80 + "\n")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
