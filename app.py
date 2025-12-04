# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime 
import pytz 
from streamlit_extras.st_copy_to_clipboard import st_copy_to_clipboard # ★追加★

# ----------------------------------------------------
# 履歴機能のためのセッションステートの初期化 
# ----------------------------------------------------
if 'history' not in st.session_state:
    st.session_state['history'] = [] 
if 'converted_text' not in st.session_state:
    st.session_state['converted_text'] = "" 

# ... (中略：APIキー初期化、reframe_negative_emotion関数、reset_input関数は変更なし) ...

# ----------------------------------------------------
# リセット処理用の関数を定義
# ----------------------------------------------------
def reset_input():
    st.session_state.negative_input_key = ""
    st.session_state.converted_text = "" 

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------

# テキスト入力エリア
negative_input = st.text_area(
    "今日のネガティブな出来事を、そのままの気持ちで書き出してください。", 
    height=200,
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。今日のCWのテストライティングは不採用だった。",
    key="negative_input_key" 
)

# 変換ボタンとリセットボタンを横並びにする
col1, col2 = st.columns([0.7, 0.3]) 

with col1:
    # 変換ボタン
    if st.button("ポジティブに変換する！", type="primary"):
        if negative_input:
            with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
                converted_result = reframe_negative_emotion(negative_input)
                jst = pytz.timezone('Asia/Tokyo')
                now_jst = datetime.datetime.now(jst)
                
                new_entry = {
                    "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
                    "negative": negative_input,
                    "positive_reframe": converted_result
                }
                st.session_state.history.insert(0, new_entry) 
                
                st.session_state.converted_text = converted_result
        else:
            st.warning("何か出来事を入力してください。")

with col2:
    st.button("リセット", on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果とコピペエリア (UIの続き) ★コピーツール追加★
# ----------------------------------------------------
st.markdown("---")
if st.session_state.converted_text:
    st.subheader("🎉 Reframe 完了！安心の一歩")
    
    converted_result = st.session_state.converted_text
    st.text_area(
        "📝 変換結果",
        value=converted_result,
        height=300,
        label_visibility="collapsed" # ラベル非表示
    )
    
    # ワンクリックコピーボタン
    st_copy_to_clipboard(converted_result, "👆 変換結果をクリップボードにコピー") 
    
    st.markdown("---")


# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader("📚 過去のポジティブ変換日記")

if st.session_state.history:
    for entry in st.session_state.history:
        st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        st.code(f"ネガティブ: {entry['negative']}", language='text') 
        st.markdown("**変換結果:**")
        st.markdown(entry['positive_reframe']) 
        st.markdown("---")
else:
    st.write("まだ変換記録はありません。最初の出来事を書き込んでみましょう！")
