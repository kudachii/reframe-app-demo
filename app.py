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
# ★修正点: 全体のトーンを意識したタイトルと説明に調整★
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")

# Streamlitの標準機能では背景色の変更が難しいが、Markdownで区切ることで視覚的な区切りを設ける
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
    # (中略：API呼び出しのシステムプロンプトと処理は変更なし)
    system_prompt = """
    あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。
    ユーザーが入力したネガティブな感情や出来事に対し、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。
    
    【出力形式】
    **1. 事実の客観視**
    (事実のみを簡潔に要約)
    
    **2. ポジティブな側面抽出**
    (この出来事から得られた成長、学び、改善点を抽出)
    
    **3. 今後の具体的な行動案（Next Step）**
    (小さく、すぐ実行できる次のアクションを一つ提案)
    
    必ずこの3つのMarkdown形式の要素を出力し、それ以外の説明や挨拶は一切含めないでください。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象の出来事:\n" + negative_text}]}<
            ]
        )
        cleaned_text = response.text.replace("### ", "").replace("###", "").replace("**", "")
        return cleaned_text
        
    except Exception as e:
        return f"Gemini API実行エラーが発生しました: {e}"

# ----------------------------------------------------
# リセット処理用の関数を定義
# ★修正点: リセットボタンの心理的な抵抗を下げるため、ラベルを調整★
# ----------------------------------------------------
def reset_input():
    st.session_state.negative_input_key = ""
    st.session_state.converted_text = "" 

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------

# ★修正点: テキストエリアの上に心理的安全性を高めるコピーを追加★
st.markdown("#### 📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。")

# テキスト入力エリア
negative_input = st.text_area(
    "（ここは誰にも見られません。心に浮かんだことを自由に。）", # ラベルをヒントに変更
    height=200,
    # ★修正点: プレースホルダーで心理的安全性を高める一文を追加★
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。今日のCWのテストライティングは不採用だった。\n\nここはあなたの安全地帯です。",
    key="negative_input_key" 
)

# 変換ボタンとリセットボタンを横並びにする
col1, col2 = st.columns([0.7, 0.3]) 

with col1:
    # 変換ボタン
    # ★修正点: ポジティブなアクションを強調するため、ボタンの色をprimary (デフォルトでは青系)で維持★
    if st.button("✨ ポジティブに変換する！", type="primary"):
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
            # ★修正点: st.warningで警告（エラー時のフィードバック）★
            st.warning("⚠️ 何か出来事を入力してください。あなたの心が待っています。")

with col2:
    # リセットボタン
    # ★修正点: ラベルを「もう一度書き直す」に変更し、心理的抵抗を軽減★
    st.button("↩️ もう一度書き直す", on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果とコピペエリア (UIの続き)
# ----------------------------------------------------
st.markdown("---")
if st.session_state.converted_text:
    st.subheader("🎉 Reframe 完了！安心の一歩")
    
    latest_entry = st.session_state.history[0] 
    
    st.caption(f"🗓️ 変換日時: {latest_entry['timestamp']}")
    st.code(f"元の出来事: {latest_entry['negative']}", language='text') 
    st.markdown("#### **✅ 変換結果（あなたの学びと次の行動）:**")
    
    # ★修正点: 変換結果を強調表示するため、st.infoやst.successで囲むことが望ましいが、今回は元のコードのmarkdown表示を維持
    st.markdown(latest_entry['positive_reframe']) 
    
    st.caption("✨ **ヒント:** 結果をコピーしたい場合は、履歴エリアのテキストを選択してコピーしてください。")
    st.markdown("---")


# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader("📚 過去のポジティブ変換日記")

if st.session_state.history:
    # (中略：履歴表示部分は変更なし)
    for entry in st.session_state.history[1:]: 
        
        st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        
        st.text_area(
            f"過去の変換 ({entry['timestamp']})",
            value=entry['positive_reframe'],
            height=300,
            label_visibility="collapsed",
            key=f"history_area_{entry['timestamp']}"
        )
        st.caption(f"元のネガティブ内容: {entry['negative']}")
        st.caption("✨ **コピーのヒント:** 上のエリアをクリックし、Ctrl+A → Ctrl+C で素早くコピーできます。")
        st.markdown("---")

else:
    st.write("まだ変換記録はありません。最初の出来事を書き込んでみましょう！")
