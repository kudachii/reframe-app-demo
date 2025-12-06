# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime 
import pytz 

# ----------------------------------------------------
# 履歴機能のためのセッションステートの初期化 
# ----------------------------------------------------
if 'history' not in st.session_state:
    st.session_state['history'] = [] 
if 'converted_text' not in st.session_state:
    st.session_state['converted_text'] = "" 

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")
st.title("💡 Reframe: ポジティブ変換日記")
st.markdown("### **あなたの「心の重さ」を、成長と行動に変換する安全な場所。**")
st.markdown("---")

# ----------------------------------------------------
# Gemini APIクライアントの初期化 (元のコードを使用)
# ----------------------------------------------------
try:
    API_KEY = st.secrets["tool"]["GEMINI_API_KEY"] 
    client = genai.Client(api_key=API_KEY)
except KeyError:
    st.error("APIクライアントの初期化に失敗しました。シークレット設定を確認してください。")
    st.stop()
except Exception as e:
    st.error(f"APIクライアントの初期化に失敗しました。エラー: {e}")
    st.stop()    

# ----------------------------------------------------
# 感情をポジティブに変換する関数 (コア機能) ★出力形式を辞書に変更★
# ----------------------------------------------------
def reframe_negative_emotion(negative_text):
    system_prompt = """
    あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。
    ユーザーが入力したネガティブな感情や出来事に対し、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。
    
    【出力形式】
    1. 事実の客観視: (事実のみを簡潔に要約)
    2. ポジティブな側面抽出: (この出来事から得られた成長、学び、改善点を抽出)
    3. 今後の具体的な行動案（Next Step）: (小さく、すぐ実行できる次のアクションを一つ提案)
    
    必ずこの3つの要素を「1.」「2.」「3.」で始まる形式で出力し、それ以外の説明や挨拶は一切含めないでください。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象の出来事:\n" + negative_text}]}
            ]
        )
        raw_text = response.text
        
        # --- AIの出力文字列を3つの要素に分割し、辞書で返す ---
        try:
            # 1. '2.' で分割し、前半を 'fact'、後半を 'positive' と 'action' に分ける
            fact_and_rest = raw_text.split("2. ", 1)
            fact = fact_and_rest[0].strip().replace("1. ", "").replace("**", "")
            
            # 2. '3.' で分割し、'positive' と 'action' に分ける
            positive_and_action = fact_and_rest[1].split("3. ", 1)
            positive = positive_and_action[0].strip().replace("**", "")
            action = positive_and_action[1].strip().replace("**", "")

            return {
                "fact": fact,
                "positive": positive,
                "action": action
            }

        except Exception:
            # 分割に失敗した場合は、エラーとして処理
            return {"fact": "分析エラー", "positive": raw_text, "action": "分割失敗: AIの出力形式をご確認ください"}

    except Exception as e:
        return {"fact": "APIエラー", "positive": f"Gemini API実行エラーが発生しました: {e}", "action": "ー"}

# ----------------------------------------------------
# リセット処理用の関数を定義
# ----------------------------------------------------
def reset_input():
    st.session_state.negative_input_key = ""
    st.session_state.converted_text = "" 

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------

# 日記入力エリアのタイトル
st.markdown("#### 📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。")

# テキスト入力エリア
negative_input = st.text_area(
    "（ここは誰にも見られません。心に浮かんだことを自由に。）", 
    height=200,
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。今日のCWのテストライティングは不採用だった。\n\nここはあなたの安全地帯です。",
    key="negative_input_key" 
)

# 変換ボタンとリセットボタンを横並びにする
col1, col2 = st.columns([0.7, 0.3]) 

with col1:
    # 変換ボタン (メインアクションとして強調)
    if st.button("✨ **ポジティブに変換する！**", type="primary"):
        if negative_input:
            with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
                converted_result = reframe_negative_emotion(negative_input)
                
                jst = pytz.timezone('Asia/Tokyo')
                now_jst = datetime.datetime.now(jst)
                
                # 履歴には元のnegativeと、構造化されたpositive_reframe（辞書）を保存
                new_entry = {
                    "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
                    "negative": negative_input,
                    "positive_reframe": converted_result
                }
                st.session_state.history.insert(0, new_entry) 
                
                st.session_state.converted_text = converted_result
        else:
            st.warning("⚠️ 何か出来事を入力してください。あなたの心が待っています。")

with col2:
    # リセットボタン 
    st.button("↩️ もう一度書き直す", on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果とコピペエリア (UIの続き) ★3要素を構造化表示★
# ----------------------------------------------------
st.markdown("---")
# 辞書型（dict）の結果が返っていることを確認
if st.session_state.converted_text and isinstance(st.session_state.converted_text, dict):
    st.subheader("🎉 Reframe 完了！安心の一歩")
    
    latest_entry = st.session_state.history[0] 
    
    st.caption(f"🗓️ 変換日時: {latest_entry['timestamp']}")
    st.code(f"元の出来事: {latest_entry['negative']}", language='text') 
    
    # --- 3要素の構造化表示 ---

    # 1. 事実の客観視 (クールダウン)
    st.markdown("##### 🧊 1. 事実の客観視（クールダウン）")
    st.info(latest_entry['positive_reframe']['fact'])
    
    # 2. ポジティブな側面抽出 (学びと成長)
    st.markdown("##### 🌱 2. ポジティブな側面抽出（学びと成長）")
    st.success(latest_entry['positive_reframe']['positive'])
    
    # 3. 今後の具体的な行動案 (ネクストステップ)
    st.markdown("##### 👣 3. 今後の具体的な行動案（Next Step）")
    st.warning(latest_entry['positive_reframe']['action']) 
    
    # --- 構造化表示ここまで ---
    
    st.caption("✨ **ヒント:** 結果をコピーしたい場合は、各ボックスのテキストを選択してコピーしてください。")
    st.markdown("---")


# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader("📚 過去のポジティブ変換日記")

if st.session_state.history:
    for entry in st.session_state.history[1:]: 
        
        st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        
        # 履歴表示エリアは、構造化された辞書の内容を結合して表示する必要がある
        history_value = (
            f"🧊 1. 事実の客観視: {entry['positive_reframe']['fact']}\n\n"
            f"🌱 2. ポジティブな側面抽出: {entry['positive_reframe']['positive']}\n\n"
            f"👣 3. 行動案: {entry['positive_reframe']['action']}"
        )
        
        st.text_area(
            f"過去の変換 ({entry['timestamp']})",
            value=history_value,
            height=300,
            label_visibility="collapsed",
            key=f"history_area_{entry['timestamp']}"
        )
        st.caption(f"元のネガティブ内容: {entry['negative']}")
        st.caption("✨ **コピーのヒント:** 上のエリアをクリックし、Ctrl+A → Ctrl+C で素早くコピーできます。")
        st.markdown("---")

else:
    st.write("まだ変換記録はありません。最初の出来事を書き込んでみましょう！")
