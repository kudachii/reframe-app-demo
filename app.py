# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime 
import pytz 
import base64 

# 画像ファイルをbase64エンコードするヘルパー関数
def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return ""
    return ""
    
# ----------------------------------------------------
# 履歴機能のためのセッションステートの初期化 
# ----------------------------------------------------
if 'history' not in st.session_state:
    st.session_state['history'] = [] 
if 'current_review_entry' not in st.session_state:
    st.session_state['current_review_entry'] = None 

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")

# ★★★ カスタム背景設定用の関数を定義 ★★★
def set_custom_background():
    BG_IMAGE = "kabegami_107dotpattern_pi.jpg"
    HEADER_IMG = "unnamed.jpg" 
    
    HEADER_HEIGHT = "320px" 
    
    encoded_bg = get_base64_image(BG_IMAGE)
    encoded_header = get_base64_image(HEADER_IMG)

    st.markdown(
        f"""
        <style>
        /* 1. アプリ全体の背景：ドット柄を適用 */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded_bg}");
            background-size: repeat; 
            background-attachment: fixed; 
            background-position: center; 
        }}
        
        /* 2. カスタム固定ヘッダーのCSS */
        #custom-fixed-header {{
            position: fixed;
            /* 例としてトップを20pxに設定（ご自身で調整した数値に置き換えてください） */
            top: 20px; 
            left: 50%; 
            transform: translateX(-50%); 
            width: 100%;
            max-width: 700px; /* メインコンテンツの幅に合わせる */
            height: {HEADER_HEIGHT}; /* 画像の高さ */
            z-index: 9999; 
            
            background-color: transparent; 
            background-image: url("data:image/jpeg;base64,{encoded_header}");
            background-size: contain; 
            background-repeat: no-repeat;
            background-position: center; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15); 
        }}
        
        /* 3. コンテンツエリアの背景を白くする（透け防止） */
        .main > div {{
            background-color: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
        }}
        
        /* 4. サイドバーの領域を完全に非表示にする */
        section[data-testid="stSidebar"] {{
            display: none !important;
        }}
        
        /* 5. テキストエリア自体の背景を白くする */
        .stTextArea textarea {{
            background-color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_custom_background() 
# ----------------------------------------------------

# ★★★ 固定ヘッダー用のカスタムDIVを挿入 ★★★
st.markdown('<div id="custom-fixed-header"></div>', unsafe_allow_html=True) 

# ★★★ 修正箇所：スペーサーの背景を白くするCSSを追加 ★★★
# height: 200px は、 (画像の高さ 180px) + (topで下げた距離 20px) の合計です。
# ご自身の環境で調整した高さに合わせてください。
st.markdown("<div style='height: 220px; background-color: white;'></div>", unsafe_allow_html=True) 

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
    st.error(f"APIクライアントの初期化に失敗しました: {e}")
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
    2. ポジティブな側面抽出: (この出来事からあなたが優しさや強さを得た点、成長できた点を抽出します。ユーザーの頑張りや努力を認め、共感し、励ますような、温かく寄り添う口調で前向きな言葉を使って表現してください。)
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
            fact_and_rest = raw_text.split("2. ", 1)
            fact = fact_and_rest[0].strip().replace("1. ", "").replace("**", "")
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
def clear_input_only():
    st.session_state["negative_input_key"] = ""

def reset_input():
    clear_input_only()
    st.session_state.current_review_entry = None

# ----------------------------------------------------
# 保存処理用の関数を定義
# ----------------------------------------------------
def save_entry():
    if st.session_state.current_review_entry:
        st.session_state.history.insert(0, st.session_state.current_review_entry)
        st.session_state.current_review_entry = None
        st.toast("✅ 日記が保存されました！", icon='💾')

# ----------------------------------------------------
# 破棄処理用の関数を定義
# ----------------------------------------------------
def discard_entry():
    st.session_state.current_review_entry = None
    st.toast("🗑️ 変換結果は破棄されました。新しい日記をどうぞ。", icon='✍️')

# ----------------------------------------------------
# 変換ボタンのコールバック関数
# ----------------------------------------------------
def on_convert_click(input_value):
    if not input_value:
        st.warning("⚠️ 何か出来事を入力してください。あなたの心が待っています。")
        return

    with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
        converted_result = reframe_negative_emotion(input_value)
        
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.datetime.now(jst)
        
        st.session_state.current_review_entry = {
            "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
            "negative": input_value,
            "positive_reframe": converted_result
        }
        
        clear_input_only() 

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------

st.markdown("#### 📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。")

negative_input = st.text_area(
    "（ここは誰にも見られません。心に浮かんだことを自由に。）", 
    height=200,
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。今日のCWのテストライティングは不採用だった。\n\nここはあなたの安全地帯です。",
    key="negative_input_key" 
)

col1, col2 = st.columns([0.7, 0.3]) 

with col1:
    st.button(
        "✨ **ポジティブに変換する！**", 
        on_click=on_convert_click, 
        args=[negative_input], 
        type="primary"
    )

with col2:
    st.button("↩️ もう一度書き直す", on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果レビューエリア (UIの続き)
# ----------------------------------------------------
st.markdown("---")
if st.session_state.current_review_entry:
    
    review_entry = st.session_state.current_review_entry
    
    st.subheader("🧐 変換結果のレビューと次のステップ")
    
    st.caption(f"🗓️ 変換日時: {review_entry['timestamp']}")
    st.code(f"元の出来事: {review_entry['negative']}", language='text') 
    
    st.markdown("#### **✅ 変換結果（あなたの学びと次の行動）:**")
    
    st.markdown("##### 🧊 1. 事実の客観視（クールダウン）")
    st.info(review_entry['positive_reframe']['fact'])
    
    st.markdown("##### 🌱 2. ポジティブな側面抽出（学びと成長）")
    st.success(review_entry['positive_reframe']['positive'])
    
    st.markdown("##### 👣 3. 今後の具体的な行動案（Next Step）")
    st.warning(review_entry['positive_reframe']['action']) 
    
    st.markdown("---")
    
    save_col, discard_col = st.columns([0.5, 0.5])
    
    with save_col:
        st.button(
            "✅ 日記を確定・保存する", 
            on_click=save_entry, 
            type="primary",
            key="save_button"
        )
    
    with discard_col:
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
    for entry in st.session_state.history: 
        
        st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        
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
