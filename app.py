import streamlit as st
import pandas as pd
import random
import json
import os
from streamlit_option_menu import option_menu

st.set_page_config(page_title="모바일 단어장", layout="centered")

# =====================================================================
# 1. 데이터베이스(JSON) 관리 (회원명부 & 진도장)
# =====================================================================
USERS_FILE = "users.json"
PROGRESS_FILE = "progress.json"

def load_json(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 파일 읽어오기
users_db = load_json(USERS_FILE)
progress_db = load_json(PROGRESS_FILE)

# 로그인 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

# =====================================================================
# 2. 🔐 로그인 & 회원가입 화면 (로그인 안 했을 때만 보임)
# =====================================================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 나만의 단어장</h1>", unsafe_allow_html=True)
    st.write("---")
    
    tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    # [로그인 탭]
    with tab_login:
        login_id = st.text_input("아이디 (ID)")
        login_pw = st.text_input("비밀번호 (Password)", type="password")
        
        if st.button("로그인", use_container_width=True, type="primary"):
            if login_id in users_db and users_db[login_id] == login_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = login_id
                st.success(f"환영합니다, {login_id}님!")
                st.rerun() # 로그인 성공 시 화면 새로고침하여 메인 앱으로 이동!
            else:
                st.error("🚨 아이디 또는 비밀번호가 틀렸습니다.")
                
    # [회원가입 탭]
    with tab_signup:
        new_id = st.text_input("새 아이디 만들기")
        new_pw = st.text_input("새 비밀번호 만들기", type="password")
        new_pw_check = st.text_input("비밀번호 확인", type="password")
        
        if st.button("회원가입 하기", use_container_width=True):
            if new_id in users_db:
                st.warning("이미 존재하는 아이디입니다. 다른 아이디를 입력해 주세요.")
            elif new_pw != new_pw_check:
                st.warning("비밀번호가 서로 다릅니다. 다시 확인해 주세요.")
            elif len(new_id) < 2 or len(new_pw) < 2:
                st.warning("아이디와 비밀번호는 2글자 이상이어야 합니다.")
            else:
                users_db[new_id] = new_pw
                save_json(USERS_FILE, users_db)
                # 진도장에도 이 사람의 공간을 미리 만들어줍니다.
                progress_db[new_id] = {}
                save_json(PROGRESS_FILE, progress_db)
                st.success(f"🎉 가입 완료! 이제 '{new_id}'로 로그인해 주세요.")
                
    # 로그인을 안 했으면 아래 코드(메인 앱)는 실행되지 않도록 여기서 멈춥니다!
    st.stop() 

# =====================================================================
# 3. 사이드바: 메뉴 및 로그아웃
# =====================================================================
current_user = st.session_state.user_id

with st.sidebar:
    st.markdown(f"### 👤 **{current_user}** 님 환영합니다!")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.voca_data = None # 데이터 초기화
        st.rerun()
        
    st.divider()

    menu = option_menu(
        menu_title="📚 메뉴", 
        options=["단어/표현 리스트", "플래시카드", "복습"], 
        icons=["list-ul", "layer-backward", "arrow-repeat"], 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#f8f9fa"},
            "icon": {"color": "#ff7f0e", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#1f77b4", "color": "white"},
        }
    )

# =====================================================================
# 4. 엑셀 데이터 불러오기 (현재 로그인한 사용자 기준)
# =====================================================================
excel_file = "voca.xlsx"

if 'voca_data' not in st.session_state or st.session_state.voca_data is None:
    data = []
    # 현재 로그인한 사용자의 진도 기록 가져오기
    user_progress = progress_db.get(current_user, {}) 
    
    try:
        df_word = pd.read_excel(excel_file, sheet_name="단어").fillna("")
        for _, row in df_word.iterrows():
            en_word = row['단어']
            is_memo = user_progress.get(en_word, False) 
            data.append({"type": "단어", "en": en_word, "ko": row['뜻'], "note": row['비고'], "memorized": is_memo})
            
        df_expr = pd.read_excel(excel_file, sheet_name="표현").fillna("")
        for _, row in df_expr.iterrows():
            en_expr = row['표현']
            is_memo = user_progress.get(en_expr, False)
            data.append({"type": "표현", "en": en_expr, "ko": row['뜻'], "note": row['비고'], "memorized": is_memo})
            
        st.session_state.voca_data = data
        st.session_state.fc_queue = []
        st.session_state.fc_index = 0
        st.session_state.is_flipped = False
        
    except Exception as e:
        st.error("🚨 엑셀 파일을 읽어올 수 없습니다. 'voca.xlsx' 파일을 확인해 주세요.")
        st.stop()

def update_memorized(word_en, is_memorized):
    for item in st.session_state.voca_data:
        if item['en'] == word_en:
            item['memorized'] = is_memorized
            break
    progress_db[current_user][word_en] = is_memorized
    save_json(PROGRESS_FILE, progress_db)

# =====================================================================
# 5. 메인 화면 구성 (리스트, 플래시카드, 복습)
# =====================================================================
if menu == "단어/표현 리스트":
    st.title(f"📖 {current_user}님의 단어장")
    tab1, tab2, tab3 = st.tabs(["📚 단어 (미암기)", "💬 표현 (미암기)", "✅ 암기 완료"])
    
    with tab1:
        words = [item for item in st.session_state.voca_data if item['type'] == '단어' and not item['memorized']]
        for item in words:
            with st.expander(f"🔤 {item['en']}"):
                st.write(f"➡️ **뜻:** {item['ko']}")
                if item['note']: st.info(f"📝 {item['note']}")

    with tab2:
        exprs = [item for item in st.session_state.voca_data if item['type'] == '표현' and not item['memorized']]
        for item in exprs:
            with st.expander(f"🗣️ {item['en']}"):
                st.write(f"➡️ **뜻:** {item['ko']}")
                if item['note']: st.info(f"📝 {item['note']}")
                
    with tab3:
        memorized = [item for item in st.session_state.voca_data if item['memorized']]
        for item in memorized:
            with st.expander(f"✅ {item['en']} ({item['type']})"):
                st.write(f"➡️ **뜻:** {item['ko']}")

elif menu == "플래시카드":
    st.title("🗂️ 플래시카드")
    unmemorized = [item for item in st.session_state.voca_data if not item['memorized']]
    
    if len(unmemorized) == 0:
        st.success("축하합니다! 모든 항목을 다 외우셨습니다! 🎉")
    else:
        if not st.session_state.fc_queue:
            random.shuffle(unmemorized)
            st.session_state.fc_queue = unmemorized
            st.session_state.fc_index = 0
            st.session_state.is_flipped = False

        if st.session_state.fc_index < len(st.session_state.fc_queue):
            current_card = st.session_state.fc_queue[st.session_state.fc_index]
            
            st.caption(f"진행 상황: {st.session_state.fc_index + 1} / {len(st.session_state.fc_queue)}")
            st.progress((st.session_state.fc_index) / len(st.session_state.fc_queue))

            st.markdown(f"<div style='background-color:#f0f2f6; padding: 30px; border-radius: 15px; text-align: center;'>"
                        f"<h1 style='color: #1f77b4; margin:0;'>{current_card['en']}</h1>"
                        f"</div><br>", unsafe_allow_html=True)

            if not st.session_state.is_flipped:
                if st.button("🔄 뜻 확인하기 (클릭!)", use_container_width=True):
                    st.session_state.is_flipped = True
                    st.rerun()
            else:
                st.markdown(f"<h3 style='text-align: center; color: #ff7f0e;'>{current_card['ko']}</h3>", unsafe_allow_html=True)
                if current_card['note']: st.info(f"📝 비고: {current_card['note']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❌ 틀렸어요", use_container_width=True):
                        st.session_state.fc_index += 1
                        st.session_state.is_flipped = False
                        st.rerun()
                with col2:
                    if st.button("⭕ 맞췄어요 (암기완료)", type="primary", use_container_width=True):
                        update_memorized(current_card['en'], True)
                        st.session_state.fc_index += 1
                        st.session_state.is_flipped = False
                        st.rerun()
        else:
            st.success("이번 세트의 플래시카드를 다 보셨습니다!")
            if st.button("🔄 다시 하기"):
                st.session_state.fc_queue = []
                st.rerun()

elif menu == "복습":
    st.title("♻️ 복습 (암기 완료 목록)")
    memorized = [item for item in st.session_state.voca_data if item['memorized']]
    
    if not memorized:
        st.info("아직 암기 완료된 항목이 없습니다.")
    else:
        for item in memorized:
            with st.expander(f"✅ {item['en']} ({item['type']})"):
                st.markdown(f"<h4 style='color:#ff7f0e;'>➡️ {item['ko']}</h4>", unsafe_allow_html=True)
                if st.button("🔙 이 단어 다시 암기할래요 (취소)", key=f"ret_{item['en']}", use_container_width=True):
                    update_memorized(item['en'], False)
                    st.session_state.fc_queue = [] 
                    st.rerun()
