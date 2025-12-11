# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime 
import pytz 
import base64 

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
    BACKGROUND_IMAGE = "kabegami_107dotpattern_pi.jpg"
    
    st.markdown(
        f"""
        <style>
        /* 1. アプリ全体の背景：ドット柄を適用 */
        .stApp {{
            background-image: none; /* 全体背景を無効化 */
        }}

        /* メインコンテンツエリアの親要素にドット柄を適用 */
        .main {{
            background-image: url("data:image/jpeg;base64,{get_base64_image(BACKGROUND_IMAGE)}");
            background-size: repeat; 
            background-attachment: fixed; 
            background-position: center; 
        }}

        /* 2. メインコンテンツエリアの背景を白くし、読みやすくする */
        .main > div {{
            background-color: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
        }}
        
        /* テキストエリア自体の背景を白くする */
        .stTextArea textarea {{
            background-color: white;
        }}
        
        /* ★★★ 3. サイドバー固定のデザインを調整するCSS ★★★ */
        section[data-testid="stSidebar"] {{
            /* サイドバーの幅を非常に狭くし、左側の固定領域を最小限にする */
            width: 10px !important; 
            padding: 0;
            overflow: visible; /* 画像がサイドバーの外に出るのを許可 */
        }}

        /* st.sidebar内の画像コンポーネントの親要素に対してネガティブマージンを適用 */
        /* これにより、画像がメインコンテンツ側に押し出され、中央寄りに固定されます */
        section[data-testid="stSidebar"] div[data-testid="stImage"] {{
            /* 画像を左端から外側（メインコンテンツ側）へ押し出す */
            margin-left: -280px !important; /* ★★★ この値で調整します ★★★ */
            margin-top: 10px !important;
            width: 700px; /* 画像の元の幅または最大幅を設定 */
            position: relative; 
            z-index: 10000;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 画像ファイルをbase64エンコードするヘルパー関数
def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return ""
    return ""

set_custom_background() 
# ----------------------------------------------------

# ******** ★★★ 修正箇所：ヘッダー画像をサイドバーに移動（固定） ★★★ ********
IMAGE_PATH = "2025-12-09 9.44の画像.jpg" # 正しいファイル名に修正

try:
    if os.path.exists(IMAGE_PATH):
        # st.sidebar を使用し、画像を固定された領域に配置
        with st.sidebar:
            # st.sidebar の中は自動的に固定されます
            st.image(IMAGE_PATH, use_column_width=False) # width指定はCSSで行うためFalseに
            
    else:
        st.sidebar.warning(f"⚠️ 警告: ヘッダー画像ファイル '{IMAGE_PATH}' が見つかりませんでした。")

except Exception as e:
    st.sidebar.error(f"画像表示中にエラーが発生しました: {e}")
# ***************************************************************

# ★★★ 修正点：固定ヘッダーで隠れるコンテンツを下にずらすためのスペーサーは削除 ★★★
# サイドバー固定はコンテンツを隠さないため、スペーサーは不要。

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
