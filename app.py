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
# 一時的なレビュー用エントリをNoneで初期化
if 'current_review_entry' not in st.session_state:
    st.session_state['current_review_entry'] = None 

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
# 感情をポジティブに変換する関数 (コア機能) 
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
            return {"fact": "分析エラー", "positive": raw_text, "action": "分割失敗: AIの出力形式をご確認ください"}

    except Exception as e:
        return {"fact": "APIエラー", "positive": f"Gemini API実行エラーが発生しました: {e}", "action": "ー"}

# ----------------------------------------------------
# リセット処理用の関数を定義
# ----------------------------------------------------
def reset_input():
    # 入力エリアのクリア
    st.session_state.negative_input_key = ""
    # レビューエリアのクリア
    st.session_state.current_review_entry = None

# ----------------------------------------------------
# 保存処理用の関数を定義
# ----------------------------------------------------
def save_entry():
    if st.session_state.current_review_entry:
        # 履歴の先頭に保存
        st.session_state.history.insert(0, st.session_state.current_review_entry)
        # 一時レビューエリアをクリア
        st.session_state.current_review_entry = None
        # ユーザーに保存が完了したことを伝える
        st.toast("✅ 日記が保存されました！", icon='💾')

# ----------------------------------------------------
# ★新規追加: 破棄処理用の関数を定義★
# ----------------------------------------------------
def discard_entry():
    # 一時レビューエリアをクリア
    st.session_state.current_review_entry = None
    # ユーザーに破棄が完了したことを伝える
    st.toast("🗑️ 変換結果は破棄されました。新しい日記をどうぞ。", icon='✍️')

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
    # 変換ボタン 
    if st.button("✨ **ポジティブに変換する！**", type="primary"):
        if negative_input:
            with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
                converted_result = reframe_negative_emotion(negative_input)
                
                jst = pytz.timezone('Asia/Tokyo')
                now_jst = datetime.datetime.now(jst)
                
                # 結果を一時変数に格納
                st.session_state.current_review_entry = {
                    "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
                    "negative": negative_input,
                    "positive_reframe": converted_result
                }
                
                # エラー回避のため、キーの値を直接空文字列に設定して入力エリアをクリア
                st.session_state["negative_input_key"] = "" 

        else:
            st.warning("⚠️ 何か出来事を入力してください。あなたの心が待っています。")

with col2:
    # リセットボタン 
    st.button("↩️ もう一度書き直す", on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果レビューエリア (UIの続き)
# ----------------------------------------------------
st.markdown("---")
# 一時レビューエントリがある場合にのみ表示
if st.session_state.current_review_entry:
    
    review_entry = st.session_state.current_review_entry
    
    st.subheader("🧐 変換結果のレビューと次のステップ")
    
    # 変換結果を構造化表示
    st.caption(f"🗓️ 変換日時: {review_entry['timestamp']}")
    st.code(f"元の出来事: {review_entry['negative']}", language='text') 
    
    st.markdown("#### **✅ 変換結果（あなたの学びと次の行動）:**")
    
    # 1. 事実の客観視 (クールダウン) 
    st.markdown("##### 🧊 1. 事実の客観視（クールダウン）")
    st.info(review_entry['positive_reframe']['fact'])
    
    # 2. ポジティブな側面抽出 (学びと成長) 
    st.markdown("##### 🌱 2. ポジティブな側面抽出（学びと成長）")
    st.success(review_entry['positive_reframe']['positive'])
    
    # 3. 今後の具体的な行動案 (ネクストステップ) 
    st.markdown("##### 👣 3. 今後の具体的な行動案（Next Step）")
    st.warning(review_entry['positive_reframe']['action']) 
    
    # --- 保存/破棄ボタンの設置 (修正) ---
    st.markdown("---")
    
    # 2つのボタンを横並びにする
    save_col, discard_col = st.columns([0.5, 0.5])
    
    with save_col:
        # 保存ボタン (メインアクションとして強調)
        st.button(
            "✅ 日記を確定・保存する", 
            on_click=save_entry, 
            type="primary",
            key="save_button"
        )
    
    with discard_col:
        # 破棄ボタン 
        st.button(
            "🗑️ 破棄して次へ", 
            on_click=discard_entry, 
            type="secondary",
            key="discard_button"
        )
        
    st.caption("※「保存」すると記録が残り、「破棄」するとこの結果は失われます。")
    st.markdown("---")


# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader("📚 過去のポジティブ変換日記（保存済み）")

if st.session_state.history:
    # 保存された履歴全体をループ
    for entry in st.session_state.history: 
        
        st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        
        # 履歴表示エリアは、構造化された辞書の内容を結合して表示
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
    st.write("まだ保存された記録はありません。最初の出来事を変換して、保存してみましょう！")
