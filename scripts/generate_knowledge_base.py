#!/usr/bin/env python3
"""
COMPLETE_GUIDE.md를 청킹하여 knowledge-base.json 생성
"""

import json
import re
from pathlib import Path
from typing import List, Dict

def parse_markdown_sections(md_content: str) -> List[Dict]:
    """마크다운 파일을 섹션별로 파싱"""
    
    documents = []
    
    # 주요 섹션 패턴 (# 1., # 2., # 3., # 4., # 5.)
    sections = re.split(r'\n(# \d+\. .+?)\n', md_content)
    
    # 첫 번째는 헤더 부분 (목차까지)
    intro = sections[0]
    
    # 나머지는 섹션별로 처리
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break
            
        section_title = sections[i].replace('# ', '').strip()
        section_content = sections[i + 1].strip()
        
        # 섹션 번호 추출
        section_num = section_title.split('.')[0]
        section_name = section_title.split('. ', 1)[1]
        
        # 하위 섹션으로 분리 (## 로 시작)
        subsections = re.split(r'\n(## .+?)\n', section_content)
        
        # 섹션 개요 (첫 부분)
        overview = subsections[0].strip()
        
        if overview:
            # 섹션 개요 문서
            doc_id = f"doc-{section_num.zfill(2)}-00"
            documents.append({
                "id": doc_id,
                "title": f"{section_name} - 개요",
                "content": overview[:2000],  # 최대 2000자
                "category": section_name,
                "section": section_num,
                "subsection": "overview",
                "metadata": {
                    "source": "COMPLETE_GUIDE.md",
                    "lastModified": "2025-09-30",
                    "tags": get_tags_for_section(section_num)
                }
            })
        
        # 하위 섹션 처리
        subsection_counter = 1
        for j in range(1, len(subsections), 2):
            if j + 1 >= len(subsections):
                break
            
            subsection_title = subsections[j].replace('## ', '').strip()
            subsection_content = subsections[j + 1].strip()
            
            # 너무 긴 경우 분할
            chunks = split_long_content(subsection_content, max_length=1500)
            
            for chunk_idx, chunk in enumerate(chunks):
                doc_id = f"doc-{section_num.zfill(2)}-{str(subsection_counter).zfill(2)}"
                if len(chunks) > 1:
                    doc_id += f"-{chr(97 + chunk_idx)}"  # a, b, c...
                
                documents.append({
                    "id": doc_id,
                    "title": f"{section_name} - {subsection_title}",
                    "content": chunk,
                    "category": section_name,
                    "section": section_num,
                    "subsection": subsection_title,
                    "metadata": {
                        "source": "COMPLETE_GUIDE.md",
                        "lastModified": "2025-09-30",
                        "tags": get_tags_for_section(section_num)
                    }
                })
            
            subsection_counter += 1
    
    return documents

def split_long_content(content: str, max_length: int = 1500) -> List[str]:
    """긴 콘텐츠를 의미 있는 단위로 분할"""
    if len(content) <= max_length:
        return [content]
    
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def get_tags_for_section(section_num: str) -> List[str]:
    """섹션 번호에 따른 태그 반환"""
    tag_map = {
        "1": ["agent-development", "azure-ai-foundry", "sdk", "basics"],
        "2": ["multi-agent", "architecture", "orchestration", "connected-agents"],
        "3": ["rag", "azure-search", "vector-search", "embeddings"],
        "4": ["mcp", "tools", "integration", "external-apis"],
        "5": ["container-apps", "deployment", "kubernetes", "devops"]
    }
    return tag_map.get(section_num, ["general"])

def main():
    # 파일 경로
    project_root = Path(__file__).parent.parent
    md_file = project_root / "data" / "COMPLETE_GUIDE.md"
    json_file = project_root / "data" / "knowledge-base.json"
    
    print(f"📖 읽는 중: {md_file}")
    
    # 마크다운 파일 읽기
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    print("✂️  청킹 중...")
    
    # 섹션별로 파싱
    documents = parse_markdown_sections(md_content)
    
    print(f"✅ {len(documents)}개 문서 생성됨")
    
    # JSON 파일로 저장
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"💾 저장 완료: {json_file}")
    
    # 통계 출력
    print("\n📊 문서 통계:")
    for section_num in ["1", "2", "3", "4", "5"]:
        section_docs = [d for d in documents if d.get("section") == section_num]
        if section_docs:
            section_name = section_docs[0]["category"]
            print(f"  - 섹션 {section_num} ({section_name}): {len(section_docs)}개 문서")

if __name__ == "__main__":
    main()
