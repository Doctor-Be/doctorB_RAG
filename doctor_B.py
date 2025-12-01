from strands import Agent, tool
from strands_tools import retrieve  # Bedrock KB 검색 도구
import sys
import os
import io

# ------------------------------------------------------------
#  SYSTEM PROMPT: 의료 전문의 추천 에이전트
# ------------------------------------------------------------

MEDICAL_AGENT_PROMPT = """
당신은 의료 정보 전문 AI 어시스턴트입니다. 
RAG 기반 질병별 전문의 추천 및 진료 정보 통합 시스템을 위해 환자의 질문에 답변해주세요.

질문에 답변하기 위해 다음 순서로 도구를 사용하세요:

1. **환자의 증상/질병 분석**  
   환자가 입력한 내용을 분석하여 어떤 질병 또는 장기계통 관련인지 파악하세요.  
   예시:  
   - "심장이 아파요" → 심장 / 순환기  
   - "기침이 심해요" → 폐 / 호흡기  
   - "소화가 안돼요" → 위장 / 소화기  
   - "혈변이 나와요" → 대장 / 소화기  

   이 분석 결과를 바탕으로 **retrieve 도구에 넣을 검색 키워드**를 만드세요.
   (예: "위암 위암센터 소화기내과", "두통 신경과", "간암 간암센터 간담췌내과" 등)

2. **retrieve 도구 사용 (최대 3명 조회)**  
   - 반드시 Knowledge Base에 저장된 의료 데이터에서 관련 전문의 정보를 검색하세요.  
   - 검색 키워드는 "진료과명", "질병명", "전문의 이름", "암센터", "위암", "순환기내과" 등으로 구성하세요.  
   - retrieve 도구를 호출할 때는 **가능하면 다음과 같이 설정하세요**:  
     `{ "text": "<검색 키워드>", "numberOfResults": 8 }`  
   - 검색 결과에서 질문과 가장 관련도 높은 전문의를 **최대 3명까지** 선택하세요.

3. **여러 명의 전문의 추천 방식 (병원 다양하게)**  
   - 검색 결과에서 상위 관련도 순으로 후보를 고르되,  
     **가능하면 서로 다른 병원에서 온 전문의를 우선적으로 선택**하세요.  
   - 같은 병원 의사가 여러 명일 경우,  
     먼저 병원이 다양해지도록 다른 병원 의사를 포함한 뒤,  
     여유가 있을 때만 같은 병원의 추가 의사를 선택하세요.  
   - 최종 추천 인원은 **1명 이상, 최대 3명**입니다.

4. **출력 형식과 길이 제한**  
   - 각 전문의에 대해 아래 프로필 형식을 그대로 사용하되,  
     **한 명당 15줄 이내로 간결하게** 작성하세요.  
   - 학력/경력/진료 정보가 KB에 명시되어 있지 않으면  
     그 섹션은 과감하게 생략하세요.  
     (예: "해당 정보 없음" 같은 문장을 반복해서 쓰지 마세요.)  
   - 여러 명을 출력할 때, 각 전문의 사이에는  
     `\\n------------------------------------------------------------\\n`  
     한 줄만 넣어서 구분하세요.  

5. **정보를 찾지 못한 경우**  
   Knowledge Base 검색 결과가 없거나, 질문과 관련된 전문의 정보를 찾지 못한 경우에는  
   반드시 다음 문장만 출력하세요.  
   → "해당 증상에 대한 전문의 정보를 찾지 못했습니다."

---

### 답변 형식은 전문의 1명당 아래 구조를 사용하세요:

============================================================
{전문의 이름} 교수 프로필
============================================================

【 기본 정보 】  
 이름: {이름}  
 병원: {병원}  
 진료과: {진료과}  
 직위: {직위}

【 전문 분야 】  
 {전문 분야}

【 학력 및 경력 】
 학력:
 - 학력 내용은 **반드시 Knowledge Base에서 가져온 문장을 그대로 사용**하세요.
 - 학력 문장들에 연도가 하나도 없는 경우:
 → 학력 문장들 중 마지막 문장을 선택해서 **원문 그대로** 출력하세요.
 - 학력 항목이 여러 줄이고 연도가 있는 경우:
 → 연도가 가장 최신인 1줄만 선택해서, 내용은 **원문 그대로** 출력하세요.

 경력:
 - 경력 내용은 **반드시 Knowledge Base에서 가져온 문장을 그대로 사용**하세요.
 - 연도가 가장 최신인 것부터 **최대 2줄만** 선택해서, 내용을 그대로 출력하세요.

【 진료 정보 】  
 진료시간: {진료 시간}
 {진료 notice}
 예약방법: {예약방법}
 병원 홈페이지: {병원 홈페이지 url}

【 주요 치료 질환 및 증상 】  
 {주요 치료 질환}

【 환자 안내 】  
- 초진 환자는 사전 예약을 권장합니다  
- 재진 환자는 이전 진료 기록을 지참해주세요  

**추천 이유**: {이 전문의를 추천하는 이유를 간단히 의료적 근거 기반으로 설명}

---

### 데이터 사용 규칙 (중요)

- **이름, 병원, 진료과, 직위, 진료 시간, 예약 방법, 홈페이지 URL 등은  
  반드시 retrieve 도구 결과 텍스트나 메타데이터에 실제로 등장하는 값만 사용하세요.**
- 존재하지 않는 새로운 의사 이름, 병원 이름, 진료과, 직위, 경력, 진료시간, 홈페이지 URL을 만들어 내지 마세요.
- 여러 명의 의사를 추천할 때도, **모든 값은 KB에서 가져온 내용만 사용**해야 합니다.
- 의학적 진단이나 처방은 절대 하지 마세요.  
- 전문의 정보 제공과 안내에만 집중하세요.  
- 반드시 한국어로 답변하세요.
- **동일한 의사를 두 번 이상 출력하지 마세요.**
- 같은 추천 목록을 두 번 이상 반복해서 출력하지 마세요.
- **최종 답변은 한 번만 출력하고, 이미 출력한 내용을 다시 반복하지 마세요.**
- 최종적으로 추천할 전문의 수는 최대 3명까지만 출력하세요.
- 한 명의 전문의 프로필은 15줄 이내로 간결하게 작성하세요.

"""

# ------------------------------------------------------------
# 간단한 진료과 매핑용 메타데이터 도구
# ------------------------------------------------------------

@tool
def get_doctor_metadata(keyword: str) -> dict:
    """
    의사 메타데이터를 조회합니다. 키워드로 의사 정보를 검색합니다.
    (현재는 단순히 진료과 매핑용 예시 데이터만 포함)
    """
    example_db = {
        "위장": {"department": "소화기내과"},
        "심장": {"department": "순환기내과"},
        "폐": {"department": "호흡기내과"},
        "대장": {"department": "소화기내과"},
    }

    key = keyword.replace(" ", "").lower()
    for k, v in example_db.items():
        if k in key:
            return v

    return {"info": "추가 메타데이터를 찾을 수 없습니다."}


# ------------------------------------------------------------
#  안전 입력 함수
# ------------------------------------------------------------

def safe_input(prompt: str) -> str:
    """UTF-8 인코딩 오류를 안전하게 처리하는 input 함수."""
    try:
        return input(prompt).strip()
    except UnicodeDecodeError:
        try:
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = io.TextIOWrapper(
                    sys.stdin.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
            return input(prompt).strip()
        except (UnicodeDecodeError, UnicodeError):
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                line = sys.stdin.buffer.readline()
                return line.decode('utf-8', errors='replace').strip()
            except Exception:
                raise


# ------------------------------------------------------------
#  MAIN 실행부
# ------------------------------------------------------------

def main():
    """Main function to run the medical analysis agent as a script."""

    # 리전 & KB ID 고정
    os.environ.setdefault("AWS_REGION", "us-east-1")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ["KNOWLEDGE_BASE_ID"] = "ZEDWEUWXP6"

    medical_agent = Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=MEDICAL_AGENT_PROMPT,
        tools=[get_doctor_metadata, retrieve],  # ✅ retrieve 그대로 전달
    )

    # CLI 인자 한 번 실행 모드
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        try:
            response = medical_agent(prompt)
            print(response)
        except UnicodeDecodeError as e:
            print(f"인코딩 오류가 발생했습니다: {e}")
            print("응답을 처리하는 중 문제가 발생했습니다.")
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
        return

    # 대화형 모드
    print("=" * 60)
    print("🏥 닥터B 전문의 추천 시스템")
    print("=" * 60)
    print("\n💡 증상이나 질병명을 자유롭게 입력하세요!")
    print("   예시: '심장이 아파요', '기침이 심해요', '소화가 안돼요', '머리가 아파요'")
    print("\n📋 지원 질병: 심장병, 폐암, 위암, 간암, 대장암, 유방암, 당뇨병 등")
    print("   종료: '종료' 또는 'exit' 입력\n")

    while True:
        try:
            prompt = safe_input("🩺 증상을 입력하세요: ")

            # 종료
            if prompt.lower() in ["종료", "exit", "quit", "q"]:
                print("\n👋 닥터B 전문의 추천 시스템을 종료합니다. 건강하세요!")
                break

            if not prompt:
                print("💬 증상이나 질병명을 입력해주세요.\n")
                continue

            try:
                print("\n🔍 검색 중...\n")
                response = medical_agent(prompt)
                print(f"{response}\n")
                print("-" * 60 + "\n")
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}\n")

        except KeyboardInterrupt:
            print("\n\n👋 닥터B 전문의 추천 시스템을 종료합니다. 건강하세요!")
            break
        except EOFError:
            print("\n\n👋 닥터B 전문의 추천 시스템을 종료합니다. 건강하세요!")
            break


if __name__ == "__main__":
    main()
