# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time

# 画像ファイルをbase64エンコードするヘルパー関数 (今回は使用せず残す)
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
# 一時的なレビュー用エントリをNoneで初期化
if 'current_review_entry' not in st.session_state:
    st.session_state['current_review_entry'] = None

# ★★★ 連続記録を保持するための初期化を追加 ★★★
if 'positive_streak' not in st.session_state:
    st.session_state['positive_streak'] = 0
# ★★★ 'last_saved_date'は、calculate_streakで履歴から動的に計算するため不要 (今回はhistoryのみで計算) ★★★

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")

# カスタム画像表示（モバイルでの入力不具合を避けるため、固定表示CSSは削除済み）
try:
    st.image("unnamed.jpg", use_column_width=True)
except FileNotFoundError:
    st.warning("⚠️ 画像ファイルが見つかりません: unnamed.jpg。ファイル名とパスを確認してください。")

st.markdown("### **あなたの「心の重さ」を、成長と行動に変換する安全な場所。**")
st.markdown("---")

# ★★★ 連続記録の表示を追加 ★★★
st.markdown(
    f"##### 🏆 ポジティブ連続記録: <span style='color: green; font-size: 1.5em;'>{st.session_state.positive_streak}日</span> 連続中！", 
    unsafe_allow_html=True
)
st.markdown("---")

# ----------------------------------------------------
# Gemini APIクライアントの初期化
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
    # ★★★ 多言語対応プロンプト ★★★
    system_prompt = """
    あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。
    ユーザーが入力したネガティブな感情や出来事に対し、**入力された言語と同じ言語で**、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。

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
            
            positive_and_action = positive_and_action = fact_and_rest[1].split("3. ", 1)
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
# 連続記録の計算ロジック (新規関数)
# ----------------------------------------------------
def calculate_streak(history_list):
    """保存された履歴に基づき、現在の連続記録日数を計算する"""
    if not history_list:
        return 0

    # 履歴から重複のない日付（YYYY/MM/DD形式）のリストを作成し、降順にソート
    unique_dates = sorted(list(set(entry['date_only'] for entry in history_list if 'date_only' in entry)), reverse=True)
    
    if not unique_dates:
        return 0

    streak = 0
    
    # 日本時間で今日の日付を取得
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst).date()
    
    # 計算開始日を今日の日付（YYYY-MM-DD）とする
    current_date_to_check = today
    
    # 連続記録の計算
    for date_str in unique_dates:
        # date_only (YYYY/MM/DD) を datetime.date オブジェクトに変換
        try:
             entry_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError:
             continue # フォーマットエラーをスキップ
        
        # ログの日付が計算中の日付（今日、昨日、一昨日...）と同じ場合
        if entry_date == current_date_to_check:
            streak += 1
            # 次にチェックすべき日付を「昨日」に設定
            current_date_to_check -= datetime.timedelta(days=1)
        # ログの日付が計算中の日付より古い場合（日付が飛んでいる場合）
        elif entry_date < current_date_to_check:
            # 日付が飛んでいるため、連続記録は途切れる
            break
        # entry_date > current_date_to_check は、unique_datesが降順のため発生しないはず
        
    return streak

# ----------------------------------------------------
# リセット、保存、破棄処理用の関数を定義
# ----------------------------------------------------
def clear_input_only():
    st.session_state["negative_input_key"] = ""

def reset_input():
    clear_input_only()
    st.session_state.current_review_entry = None

def save_entry():
    if st.session_state.current_review_entry:
        
        # ★★★ save_entry関数を修正し、連続記録に必要な 'date_only' を追加 ★★★
        
        # タイムスタンプから日付のみ（YYYY/MM/DD）を抽出
        timestamp_full = st.session_state.current_review_entry['timestamp'] # 例: 2025/12/13 09:24
        date_only = timestamp_full.split(" ")[0] # 例: 2025/12/13
        
        # エントリに日付のみのデータ 'date_only' を追加
        st.session_state.current_review_entry['date_only'] = date_only
        
        # 履歴の先頭に保存
        st.session_state.history.insert(0, st.session_state.current_review_entry)
        
        # 連続記録を再計算して更新
        st.session_state.positive_streak = calculate_streak(st.session_state.history)
        
        st.session_state.current_review_entry = None
        st.toast("✅ 日記が保存されました！", icon='💾')

def discard_entry():
    st.session_state.current_review_entry = None
    st.toast("🗑️ 変換結果は破棄されました。新しい日記をどうぞ。", icon='✍️')

# 履歴の削除処理用の関数を定義
def delete_entry(timestamp_to_delete):
    """指定されたタイムスタンプを持つエントリを履歴から削除する"""
    # 削除対象以外のエントリを新しいリストとして保持する
    new_history = [
        entry for entry in st.session_state.history 
        if entry['timestamp'] != timestamp_to_delete
    ]
    st.session_state.history = new_history
    
    # ★★★ 削除後、連続記録を再計算 ★★★
    st.session_state.positive_streak = calculate_streak(st.session_state.history)
    
    st.toast("🗑️ 日記エントリを削除しました。", icon='🚮')
# ----------------------------------------------------

# 変換ボタンのコールバック関数
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
            # 'date_only'はsave_entryで追加されるため、ここでは不要
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
    placeholder="例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。\n\nまたは、'I failed my driving test today and I feel discouraged.'",
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
    for i, entry in enumerate(st.session_state.history): 
        
        # 削除ボタンと履歴内容を横並びにするためのカラム設定
        col_ts, col_del = st.columns([0.8, 0.2])
        
        # タイムスタンプの表示
        with col_ts:
            st.caption(f"🗓️ 変換日時: {entry['timestamp']}")
        
        # 削除ボタンの設置
        with col_del:
            # uniqueなキーを生成し、コールバック関数に削除対象のtimestampを渡す
            st.button(
                "削除", 
                key=f"delete_btn_{entry['timestamp']}", 
                on_click=delete_entry,
                args=[entry['timestamp']]
            )
        
        # 履歴の内容を表示
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
        # ★★★ 連続記録のため、ここに日付情報を含めておくのが親切です ★★★
        st.caption(f"元のネガティブ内容 ({entry.get('date_only', '日付不明')} 記録): {entry['negative']}")
        st.caption("✨ **コピーのヒント:** 上のエリアをクリックし、Ctrl+A → Ctrl+C で素早くコピーできます。")
        st.markdown("---")

else:
    st.write("まだ保存された記録はありません。最初の出来事を変換して、保存してみましょう！")
