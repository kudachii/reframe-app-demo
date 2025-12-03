import streamlit as st
from google import genai
import os

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")
st.title("💡 Reframe: ポジティブ変換日記")
st.markdown("---")
st.markdown("**ネガティブな出来事を書き込み、AIの力で学びと行動案に変換します。**")

# ----------------------------------------------------
# Gemini APIクライアントの初期化
# ----------------------------------------------------
# 環境変数からAPIキーを読み込む設定。デプロイ時に必要。
# Colabでのテスト実行時は、ここでキーを直接設定することも可能ですが、
# セキュリティ上、環境変数(st.secrets)を使うのがベストです。
try:
    # 環境変数 'GEMINI_API_KEY' が設定されていることを前提とします
    client = genai.Client()
except Exception as e:
    st.error("APIクライアントの初期化に失敗しました。Gemini APIキーが正しく設定されているか確認してください。")
    st.stop()
    
# ----------------------------------------------------
# 感情をポジティブに変換する関数 (コア機能)
# ----------------------------------------------------
def reframe_negative_emotion(negative_text):
    system_prompt = """
    あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。
    ユーザーが入力したネガティブな感情や出来事に対し、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。
    
    【出力形式】
    ### 1. 事実の客観視
    (事実のみを簡潔に要約)
    
    ### 2. ポジティブな側面抽出
    (この出来事から得られた成長、学び、改善点を抽出)
    
    ### 3. 今後の具体的な行動案（Next Step）
    (小さく、すぐ実行できる次のアクションを一つ提案)
    
    必ずこの3つのMarkdown形式の要素を出力し、それ以外の説明や挨拶は一切含めないでください。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象の出来事:\n" + negative_text}]}
            ]
        )
        return response.text
        
    except Exception as e:
        return f"Gemini API実行エラーが発生しました: {e}"

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------

# テキスト入力エリア
negative_input = st.text_area(
    "今日のネガティブな出来事を、そのままの気持ちで書き出してください。", 
    height=200,
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。今日のCWのテストライティングは不採用だった。"
)

# 変換ボタン
if st.button("ポジティブに変換する！", type="primary"):
    if negative_input:
        with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
            # コア関数を呼び出し
            converted_result = reframe_negative_emotion(negative_input)
            
            # 結果表示
            st.markdown("---")
            st.subheader("🎉 Reframe 完了！安心の一歩")
            st.markdown(converted_result)
    else:
        st.warning("何か出来事を入力してください。")

# (注: Colabでこのコードを実行する場合、ローカルでStreamlitを立ち上げる必要があります。)
