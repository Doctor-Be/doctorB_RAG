import streamlit as st
from strands import Agent
from strands_tools import retrieve
import os

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="닥터B - 전문의 추천 시스템",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS 스타일링
# ============================================================
st.markdown("""
<style>
    /* 메인 컨테이너 */
    .main {
        padding: 2rem;
    }
    
    /* 헤더 스타일 */
    .header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .header h1 {
        color: white;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
    }
    
    /* 검색창 스타일 */
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #ddd !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 2px solid #667eea !important;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.2rem;
        padding: 0.8rem 2rem;
        border-radius: 10px;
        border: none;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 의사 카드 스타일 */
    .doctor-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        transition: all 0.3s;
    }
    
    .doctor-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .doctor-name {
        font-size: 1.8rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .doctor-hospital {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 0.3rem;
    }
    
    .doctor-dept {
        font-size: 1.1rem;
        color: #777;
        margin-bottom: 1rem;
    }
    
    .info-section {
        margin: 1rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    
    .info-label {
        font-weight: bold;
        color: #667eea;
        margin-right: 0.5rem;
    }
    
    /* 로딩 스피너 */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* 경고/정보 박스 */
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        background: #e8f4f8;
        border-left: 4px solid #2196F3;
        color: #000 !important;
    }
    
    .info-box strong {
        color: #000 !important;
    }
    
    .warning-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #000 !important;
    }
    
    .warning-box strong {
        color: #000 !important;
    }
    
    /* 다크모드 대응 */
    @media (prefers-color-scheme: dark) {
        .info-box {
            background: #1e3a5f;
            color: #fff !important;
        }
        
        .info-box strong {
            color: #4db8ff !important;
        }
        
        .warning-box {
            background: #5c4d2c;
            color: #fff !important;
        }
        
        .warning-box strong {
            color: #ffd54f !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Agent 초기화
# ============================================================

MEDICAL_AGENT_PROMPT = """
의료 정보 AI 어시스턴트입니다.

**순서:**
1. 증상 분석 → 진료과 파악
2. retrieve(text="검색어", numberOfResults=6) 호출
3. 다른 병원 의사 2명만 선택
4. 각 의사당 10줄 이내 출력

**형식:**
==========
{이름} 교수
==========
이름: {이름}
병원: {병원}
진료과: {진료과}
전문분야: {전문분야}
진료시간: {시간}
예약: {예약방법}
홈페이지: {URL}

추천이유: {한줄}

---

**규칙:**
- KB 데이터만 사용
- 없는 정보 생성 금지
- 중복 금지
- 못 찾으면: "해당 증상에 대한 전문의 정보를 찾지 못했습니다."
"""

def get_agent():
    """Agent 초기화 (매번 새로 생성)"""
    os.environ.setdefault("AWS_REGION", "us-east-1")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ["KNOWLEDGE_BASE_ID"] = "ZEDWEUWXP6"
    
    return Agent(
        model="us.amazon.nova-lite-v1:0",
        system_prompt=MEDICAL_AGENT_PROMPT,
        tools=[retrieve],
    )

# ============================================================
# 메인 UI
# ============================================================

def main():
    # 헤더
    st.markdown("""
    <div class="header">
        <h1>🏥 닥터B</h1>
        <p>AI 기반 전문의 추천 시스템</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 안내 메시지
    st.markdown("""
    <div class="info-box">
        <strong>💡 사용 방법</strong><br>
        증상이나 질병명을 자유롭게 입력하세요!<br>
        예시: '심장이 아파요', '기침이 심해요', '소화가 안돼요', '두통이 있어요'
    </div>
    """, unsafe_allow_html=True)
    
    # 검색창
    col1, col2 = st.columns([4, 1])
    
    with col1:
        symptom = st.text_input(
            "🩺 증상을 입력하세요",
            placeholder="예: 심장이 아파요",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 전문의 찾기", use_container_width=True)
    
    # 지원 질병 안내
    with st.expander("📋 지원 질병 및 진료과"):
        st.markdown("""
        **주요 지원 질병:**
        - 🫀 심장병, 고혈압 (순환기내과)
        - 🫁 폐암, 호흡기 질환 (호흡기내과)
        - 🏥 위암, 대장암 (소화기내과/외과)
        - 🩺 간암, 간경화 (간담췌내과)
        - 🎀 유방암 (유방외과)
        - 💉 당뇨병 (내분비내과)
        
        **주요 대학병원:**
        - 서울대학교병원
        - 서울아산병원
        - 세브란스병원
        - 삼성서울병원
        - 이대서울병원
        """)
    
    # 검색 실행
    if search_button and symptom:
        with st.spinner("🔍 전문의를 검색하고 있습니다..."):
            try:
                agent = get_agent()
                
                # Agent 호출
                result = agent(symptom)
                
                # AgentResult를 문자열로 변환
                response = str(result)
                
                # 결과 표시
                st.markdown("---")
                st.markdown("## 📋 추천 전문의")
                
                # 디버깅: 응답 확인
                st.write("**응답 받음!**")
                
                # 응답이 "찾지 못했습니다"인 경우
                if "찾지 못했습니다" in response:
                    st.markdown("""
                    <div class="warning-box">
                        <strong>⚠️ 검색 결과 없음</strong><br>
                        해당 증상에 대한 전문의 정보를 찾지 못했습니다.<br>
                        다른 키워드로 다시 검색해보세요.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # 텍스트를 그대로 표시 (박스 없이)
                    st.text(response)
                
                # 면책 공지
                st.markdown("---")
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ 주의사항</strong><br>
                    - 이 시스템은 참고용 정보 제공만을 목적으로 합니다<br>
                    - 의학적 조언이나 진단을 대체하지 않습니다<br>
                    - 정확한 진단은 반드시 의료기관에서 받으시기 바랍니다
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                st.info("💡 다시 시도하거나 다른 증상으로 검색해보세요.")
    
    elif search_button and not symptom:
        st.warning("💬 증상이나 질병명을 입력해주세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 2rem 0;">
        <p>🏥 닥터B - RAG 기반 전문의 추천 시스템</p>
        <p style="font-size: 0.9rem;">Powered by AWS Bedrock & Strands Agent</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()