import streamlit as st
import pandas as pd
import random
import json
import os
import datetime
import time
from streamlit_option_menu import option_menu
import gspread

st.set_page_config(page_title="모바일 단어장", layout="centered")

# =====================================================================
# 🔐 1. 안전한 구글 비밀 금고(Secrets) 및 시트 연결 세팅
# =====================================================================
# 회원님의 고유 스프레드시트 ID
SHEET_ID = "152SWrgVZSegRnQ6AnslqWTRLsLJ5F_F3"

@st.cache_resource
def init_connection():
    # Streamlit 금고에 넣어둔 JSON 신분증 코드를 안전하게 읽어옴
    creds_dict = json.loads(st.secrets["google_credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    return gc.open_by_key(SHEET_ID)

try:
    doc = init_connection()
    sheet_word = doc.worksheet("단어")
    sheet_expr = doc.worksheet("표현")
    sheet_users = doc.worksheet("회원명부")
    sheet_progress = doc.worksheet("진도기록")
except Exception as e:
    st.error(f"🚨 구글 시트 금고 연결 실패! Secrets 세팅이나 시트 공유를 확인해 주세요. 에러: {e}")
    st.stop()

# =====================================================================
# 📊 2. 구글 시트 실시간 데이터 처리 함수들
# =====================================================================
def load_users():
    records = sheet_users.get_all_records()
    users_db = {}
    for r in records:
        uid = str(r.get("아이디", "")).strip().lower()
        pw = str(r.get("비밀번호", "")).strip()
        if uid:
            users_db[uid] = pw
    return users_db

def load_progress(user_id):
    records = sheet_progress.get_all_records()
    user_prog = {}
    for r in records:
        if str(r.get("아이디", "")).strip().lower() == user_id:
            word = str(r.get("단어", "")).strip()
            is_memo = str(r.get("암기여부", "")).strip().lower() in ['true', '1', 'yes']
            user_prog[word] = is_memo
    return user_prog

# 실시간 유저 정보 로드
users_db = load_users()

# 주소창(URL) 파라미터로 자동 로그인 감지
saved_user = st.query_params.get("user")

if 'logged_in' not in st.session_state:
    if saved_user and saved_user in users_db:
        st.session_state.logged_in = True
        st.session_state.user_id = saved_user
    else:
        st.session_state.logged_in = False
        st.session_state.user_id = ""

# =====================================================================
# 3. 🔐 로그인 & 회원가입 화면 (구글 시트에 실시간 반영)
# =====================================================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 나만의 단어장</h1>", unsafe_allow_html=True)
    st.write("---")
    
    tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab_login:
        login_id_input = st.text_input("아이디 (ID)")
        login_pw = st.text_input("비밀번호 (Password)", type="password")
        keep_logged_in = st.checkbox("로그인 상태 유지", value=True)
        
        if st.button("로그인", use_container_width=True, type="primary"):
            clean_login_id = login_id_input.lower().strip() 
            
            if clean_login_id in users_db and users_db[clean_login_id] == login_pw:
                if keep_logged_in:
                    st.query_params["user"] = clean_login_id
                
                st.session_state.logged_in = True
                st.session_state.user_id = clean_login_id
                time.sleep(0.5) 
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
                # 💡 구글 시트 '회원명부' 탭 맨 아랫줄에 실시간 영구 기록!
                sheet_users.append_row([clean_new_id, new_pw])
                st.success(f"🎉 가입 완료! 이제 로그인해 주세요.")
                time.sleep(1)
                st.rerun()
                
    st.markdown("<br><br><div style='text-align: center; color: #bdc3c7; font-size: 13px;'>✨ Designed & Developed by <b>SK Lee</b></div>", unsafe_allow_html=True)
    st.stop() 

# =====================================================================
# 4. 메인 앱 세팅 (사이드바 메뉴 및 👑 실시간 관리자 대시보드)
# =====================================================================
current_user = st.session_state.user_id

with st.sidebar:
    st.markdown(f"### 👤 **{current_user}** 님 환영합니다!")
    
    # 💡 별 기호 중복 제거 완료
    menu = option_menu(
        menu_title="📚 메뉴", 
        options=["단어/표현 리스트", "플래시카드", "복습", "핵심정리"], 
        icons=["list-ul", "layer-backward", "arrow-repeat", "star-fill"], 
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#f8f9fa"},
            "icon": {"color": "#ff7f0e", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#1f77b4", "color": "white"},
        }
    )
    
    st.divider()
    
    if st.button("🚪 로그아웃", use_container_width=True):
        if "user" in st.query_params:
            del st.query_params["user"]
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.voca_data = None 
        time.sleep(0.5)
        st.rerun()
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # 👑 덮어쓰기 위험이 없는 진짜 실시간 관리자 기능 오픈!
    if current_user == "admin": 
        with st.sidebar.expander("👑 관리자 계정 마스터", expanded=False):
            st.write("👥 **현재 가입자 명부**")
            for u, p in users_db.items():
                if u == "admin": continue
                st.text(f"• {u} (비번: {p})")
                
            st.divider()
            st.write("🔧 **회원 정보 즉시 제어**")
            target_user = st.text_input("대상 ID 입력", key="adm_target").strip().lower()
            adm_action = st.selectbox("수행할 명령", ["선택하세요", "비밀번호 즉시 변경", "계정 영구 삭제"], key="adm_act")
            
            if adm_action == "비밀번호 즉시 변경":
                adm_new_pw = st.text_input("새 변경 비번", key="adm_pw")
                if st.button("변경 명령 실행", use_container_width=True):
                    if target_user in users_db:
                        user_records = sheet_users.get_all_records()
                        for idx, r in enumerate(user_records):
                            if str(r.get("아이디","")).strip().lower() == target_user:
                                sheet_users.update_cell(idx + 2, 2, adm_new_pw) # 2열(비밀번호) 수정
                                st.success(f"🔑 {target_user}님 비번 변경 완료!")
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.error("존재하지 않는 ID입니다.")
                        
            elif adm_action == "계정 영구 삭제":
                if st.button("❌ 선택 계정 추방", use_container_width=True, type="primary"):
                    if target_user in users_db:
                        user_records = sheet_users.get_all_records()
                        for idx, r in enumerate(user_records):
                            if str(r.get("아이디","")).strip().lower() == target_user:
                                sheet_users.delete_rows(idx + 2) # 구글 시트에서 행 강제 삭제
                                st.success(f"🗑️ {target_user} 계정이 영구 삭제되었습니다.")
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.error("존재하지 않는 ID입니다.")

    st.markdown("<br><div style='text-align: center; color: #bdc3c7; font-size: 13px;'>✨ Designed & Developed by<br><b>SK Lee</b></div>", unsafe_allow_html=True)

# =====================================================================
# 5. 구글 시트에서 실시간 데이터 로드
# =====================================================================
if 'voca_data' not in st.session_state or st.session_state.voca_data is None:
    data = []
    user_progress = load_progress(current_user) 
    last_updated_date = None 
    today = datetime.datetime.now() 
    
    try:
        word_records = sheet_word.get_all_records()
        expr_records = sheet_expr.get_all_records()
        
        word_records.reverse() 
        expr_records.reverse()
        
        for row in word_records:
            en_word = str(row.get('단어', '')).strip()
            if en_word == "": continue
            is_memo = user_progress.get(en_word, False) 
            
            is_new = False
            reg_date = row.get('등록일', '')
            if reg_date != "":
                try:
                    date_obj = pd.to_datetime(reg_date)
                    if (today - date_obj).days <= 7:
                        is_new = True
                    if last_updated_date is None or date_obj > last_updated_date:
                        last_updated_date = date_obj
                except:
                    pass
            data.append({"type": "단어", "en": en_word, "ko": str(row.get('뜻', '')), "note": str(row.get('비고', '')), "memorized": is_memo, "is_new": is_new})
            
        for row in expr_records:
            en_expr = str(row.get('표현', '')).strip()
            if en_expr == "": continue
            is_memo = user_progress.get(en_expr, False)
            
            is_new = False
            reg_date = row.get('등록일', '')
            if reg_date != "":
                try:
                    date_obj = pd.to_datetime(reg_date)
                    if (today - date_obj).days <= 7:
                        is_new = True
                    if last_updated_date is None or date_obj > last_updated_date:
                        last_updated_date = date_obj
                except:
                    pass
            data.append({"type": "표현", "en": en_expr, "ko": str(row.get('뜻', '')), "note": str(row.get('비고', '')), "memorized": is_memo, "is_new": is_new})
            
        st.session_state.voca_data = data
        st.session_state.fc_queue = []
        st.session_state.fc_index = 0
        st.session_state.is_flipped = False
        st.session_state.last_updated = last_updated_date.strftime("%Y년 %m월 %d일") if last_updated_date else "기록 없음"
        
    except Exception as e:
        st.error(f"🚨 구글 시트 데이터를 가져오는 데 실패했습니다. 에러: {e}")
        st.stop()

# 💡 구글 시트 '진도기록'에 실시간 업서트(Upsert)하는 최첨단 함수
def update_memorized(word_en, is_memorized):
    for item in st.session_state.voca_data:
        if item['en'] == word_en:
            item['memorized'] = is_memorized
            break
            
    records = sheet_progress.get_all_records()
    row_idx = -1
    for i, r in enumerate(records):
        if str(r.get("아이디", "")).strip().lower() == current_user and str(r.get("단어", "")).strip() == word_en:
            row_idx = i + 2 
            break
            
    if row_idx != -1:
        sheet_progress.update_cell(row_idx, 3, str(is_memorized))
    else:
        sheet_progress.append_row([current_user, word_en, str(is_memorized)])

# =====================================================================
# 6. 메인 화면 출력 파트
# =====================================================================
if menu == "단어/표현 리스트":
    st.title(f"📖 {current_user}님의 단어장")
    st.caption(f"🔄 마지막 업데이트: {st.session_state.get('last_updated', '기록 없음')}") 
    
    tab1, tab2, tab3 = st.tabs(["📚 단어 (미암기)", "💬 표현 (미암기)", "✅ 암기 완료"])
    
    with tab1:
        words = [item for item in st.session_state.voca_data if item['type'] == '단어' and not item['memorized']]
        for item in words:
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
    col_title, col_reset = st.columns([7, 3])
    with col_title:
        st.title("🗂️ 플래시카드")
    with col_reset:
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button("🔄 리셋 (처음부터)", use_container_width=True):
            st.session_state.fc_queue = []
            st.session_state.fc_index = 0
            st.session_state.is_flipped = False
            st.rerun()

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
            if st.button("🔄 다시 하기 (오답 위주)"):
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

elif menu == "핵심정리":
    st.title("핵심정리 (연상 암기 노트)")
    st.info("💡 플래시카드에서 '암기 완료'한 단어와 표현은 이 노트에서 자동으로 숨겨집니다!")
    
    html_file = "VOCA.HTML"
    
    if os.path.exists(html_file):
        memo_words = [item['en'].lower().strip() for item in st.session_state.voca_data if item['memorized']]
        
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                if tds:
                    word_in_html = tds[0].get_text().lower().strip()
                    is_memorized = any(m_word in word_in_html for m_word in memo_words if len(m_word) > 2)
                    
                    if is_memorized:
                        tr.decompose() 
            
            # 💡 2중 스크롤 완전 해결 (Native 변환 삽입)
            style_tag = soup.find('style')
            style_str = str(style_tag) if style_tag else ""
            
            body_tag = soup.find('body')
            body_str = "".join([str(tag) for tag in body_tag.contents]) if body_tag else str(soup)
            
            st.markdown(style_str + body_str, unsafe_allow_html=True)
            
        except ImportError:
            st.warning("🚨 HTML 자동 필터링을 위해 'beautifulsoup4'가 필요합니다.")
            st.markdown(html_content, unsafe_allow_html=True)
            
    else:
        st.error(f"🚨 '{html_file}' 파일을 찾을 수 없습니다. 깃허브 창고에 함께 업로드해 주세요!")
