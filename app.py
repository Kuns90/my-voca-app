import streamlit as st
import pandas as pd
import random
import json
import os
import datetime
from streamlit_option_menu import option_menu

st.set_page_config(page_title="모바일 단어장", layout="centered")

# =====================================================================
# 1. 데이터베이스(JSON) 관리 (회원명부 & 진도장) -> 쉬운 방법으로 복구!
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

users_db = load_json(USERS_FILE)
progress_db = load_json(PROGRESS_FILE)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""

# =====================================================================
# 2. 🔐 로그인 & 회원가입 화면
# =====================================================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 나만의 단어장</h1>", unsafe_allow_html=True)
    st.write("---")
    
    tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab_login:
        login_id_input = st.text_input("아이디 (ID)")
        login_pw = st.text_input("비밀번호 (Password)", type="password")
        
        if st.button("로그인", use_container_width=True, type="primary"):
            clean_login_id = login_id_input.lower().strip() 
            
            if clean_login_id in users_db and users_db[clean_login_id] == login_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = clean_login_id
                st.rerun()
            else:
                st.error("🚨 아이디 또는 비밀번호가 틀렸습니다.")
                
    with tab_signup:
        new_id_input = st.text_input("새 아이디 만들기")
        new_pw = st.text_input("새 비밀번호 만들기", type="password")
        new_pw_check = st.text_input("비밀번호 확인", type="password")
        
        if st.button("회원가입 하기", use_container_width=True):
            clean_new_id = new_id_input.lower().strip()
            
            if clean_new_id in users_db:
                st.warning("이미 존재하는 아이디입니다.")
            elif new_pw != new_pw_check:
                st.warning("비밀번호가 서로 다릅니다.")
            elif len(clean_new_id) < 2 or len(new_pw) < 2:
                st.warning("아이디와 비밀번호는 2글자 이상이어야 합니다.")
            else:
                # 💡 JSON 파일에 가입 정보 저장
                users_db[clean_new_id] = new_pw
                save_json(USERS_FILE, users_db)
                progress_db[clean_new_id] = {}
                save_json(PROGRESS_FILE, progress_db)
                st.success(f"🎉 가입 완료! 이제 로그인해 주세요.")
    st.stop() 

# =====================================================================
# 3. 메인 앱 세팅 (메뉴바)
# =====================================================================
current_user = st.session_state.user_id

with st.sidebar:
    st.markdown(f"### 👤 **{current_user}** 님 환영합니다!")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.voca_data = None 
        st.rerun()
    st.divider()
    menu = option_menu(
        menu_title="📚 메뉴", 
        options=["단어/표현 리스트", "플래시카드", "복습"], 
        icons=["list-ul", "layer-backward", "arrow-repeat"], 
        default_index=0
    )

# =====================================================================
# 4. 구글 시트에서 '단어/표현' 데이터만 읽어오기
# =====================================================================
# 🚨 아래 "" 안에 회원님의 구글 시트 마법의 링크(/export?format=xlsx)를 넣어주세요!
excel_file = "https://docs.google.com/spreadsheets/d/152SWrgVZSegRnQ6AnslqWTRLsLJ5F_F3/export?format=xlsx"

if 'voca_data' not in st.session_state or st.session_state.voca_data is None:
    data = []
    user_progress = progress_db.get(current_user, {}) 
    last_updated_date = None 
    today = datetime.datetime.now() 
    
    try:
        df_word = pd.read_excel(excel_file, sheet_name="단어").fillna("")
        df_word = df_word.iloc[::-1] # 최신순
        
        for _, row in df_word.iterrows():
            en_word = str(row['단어'])
            if en_word == "": continue
            is_memo = user_progress.get(en_word, False) 
            
            is_new = False
            if '등록일' in row and row['등록일'] != "":
                try:
                    date_obj = pd.to_datetime(row['등록일'])
                    if (today - date_obj).days <= 7:
                        is_new = True
                    if last_updated_date is None or date_obj > last_updated_date:
                        last_updated_date = date_obj
                except:
                    pass
            data.append({"type": "단어", "en": en_word, "ko": str(row['뜻']), "note": str(row['비고']), "memorized": is_memo, "is_new": is_new})
            
        df_expr = pd.read_excel(excel_file, sheet_name="표현").fillna("")
        df_expr = df_expr.iloc[::-1] # 최신순
        
        for _, row in df_expr.iterrows():
            en_expr = str(row['표현'])
            if en_expr == "": continue
            is_memo = user_progress.get(en_expr, False)
            
            is_new = False
            if '등록일' in row and row['등록일'] != "":
                try:
                    date_obj = pd.to_datetime(row['등록일'])
                    if (today - date_obj).days <= 7:
                        is_new = True
                    if last_updated_date is None or date_obj > last_updated_date:
                        last_updated_date = date_obj
                except:
                    pass
            data.append({"type": "표현", "en": en_expr, "ko": str(row['뜻']), "note": str(row['비고']), "memorized": is_memo, "is_new": is_new})
            
        st.session_state.voca_data = data
        st.session_state.fc_queue = []
        st.session_state.fc_index = 0
        st.session_state.is_flipped = False
        st.session_state.last_updated = last_updated_date.strftime("%Y년 %m월 %d일") if last_updated_date else "기록 없음"
        
    except Exception as e:
        st.error(f"🚨 구글 시트 데이터를 불러오지 못했습니다. 링크를 다시 확인해 주세요. 에러: {e}")
        st.stop()

# 💡 JSON 파일에 암기 상태 기록
def update_memorized(word_en, is_memorized):
    for item in st.session_state.voca_data:
        if item['en'] == word_en:
            item['memorized'] = is_memorized
            break
    progress_db[current_user][word_en] = is_memorized
    save_json(PROGRESS_FILE, progress_db)

# =====================================================================
# 5. 메인 화면 구성 (화면 출력부)
# =====================================================================
if menu == "단어/표현 리스트":
    st.title(f"📖 {current_user}님의 단어장")
    st.caption(f"🔄 마지막 업데이트: {st.session_state.get('last_updated', '기록 없음')}") 
    
    tab1, tab2, tab3 = st.tabs(["📚 단어 (미암기)", "💬 표현 (미암기)", "✅ 암기 완료"])
    
    with tab1:
        words = [item for item in st.session_state.voca_data if item['type'] == '단어' and not item['memorized']]
        for item in words:
            # 💡 시인성을 극대화한 NEW 표시!
            title = f"🔴 [NEW] 🔤 {item['en']}" if item['is_new'] else f"🔤 {item['en']}"
            with st.expander(title):
                st.write(f"➡️ **뜻:** {item['ko']}")
                if item['note']: st.info(f"📝 {item['note']}")

    with tab2:
        exprs = [item for item in st.session_state.voca_data if item['type'] == '표현' and not item['memorized']]
        for item in exprs:
            title = f"🔴 [NEW] 🗣️ {item['en']}" if item['is_new'] else f"🗣️ {item['en']}"
            with st.expander(title):
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
