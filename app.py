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
    
# ★★★ テーマの定義 ★★★
THEMES = ["選択なし", "仕事・キャリア", "人間関係", "自己成長", "健康・メンタル"] 

# ----------------------------------------------------
# 履歴機能のためのセッションステートの初期化
# ----------------------------------------------------
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'current_review_entry' not in st.session_state:
    st.session_state['current_review_entry'] = None
if 'positive_streak' not in st.session_state:
    st.session_state['positive_streak'] = 0
if 'monthly_report' not in st.session_state:
    st.session_state['monthly_report'] = None 

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title="Reframe: 安心の一歩", layout="centered")

# カスタム画像表示（モバイルでの入力不具合を避けるため、固定表示CSSは削除済み）
try:
    st.image("unnamed.jpg", use_column_width=True)
except FileNotFoundError:
    st.warning("⚠️ 画像ファイルが見つかりません: unnamed.jpg。ファイル名とパスを確認してください。")

# キャッチフレーズの文字サイズを調整
st.markdown(
    "<p style='font-size: 1.1em; font-weight: bold;'>あなたの「心の重さ」を、成長と行動に変換する安全な場所。</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# 連続記録の表示
st.markdown(
    f"##### 🏆 ポジティブ連続記録: <span style='color: green; font-size: 1.5em;'>{st.session_state.positive_streak}日</span> 連続中！", 
    unsafe_allow_html=True
)
st.markdown("---")

# ----------------------------------------------------
# Gemini APIクライアントの初期化
# ----------------------------------------------------
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        st.error("APIクライアントの初期化に失敗しました。シークレット設定にGEMINI_API_KEYがありません。")
        st.stop()
        
    API_KEY = st.secrets["tool"]["GEMINI_API_KEY"] 
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"APIクライアントの初期化に失敗しました。エラー: {e}")
    st.stop()    

# ----------------------------------------------------
# 感情をポジティブに変換する関数 (コア機能) 
# ----------------------------------------------------
def reframe_negative_emotion(negative_text):
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
# 連続記録の計算ロジック
# ----------------------------------------------------
def calculate_streak(history_list):
    """保存された履歴に基づき、現在の連続記録日数を計算する"""
    if not history_list:
        return 0

    unique_dates = sorted(list(set(entry['date_only'] for entry in history_list if 'date_only' in entry)), reverse=True)
    
    if not unique_dates:
        return 0

    streak = 0
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst).date()
    current_date_to_check = today
    
    for date_str in unique_dates:
        try:
             entry_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError:
             continue
        
        if entry_date == current_date_to_check:
            streak += 1
            current_date_to_check -= datetime.timedelta(days=1)
        elif entry_date < current_date_to_check:
            break
        
    return streak

# ----------------------------------------------------
# 月間レポートを生成する関数
# ----------------------------------------------------
def generate_monthly_report(history_list):
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst)
    
    start_date = today - datetime.timedelta(days=30)
    
    recent_entries = []
    for entry in history_list:
        try:
            entry_date_str = entry.get('date_only', entry['timestamp'].split(" ")[0])
            entry_date = datetime.datetime.strptime(entry_date_str, "%Y/%m/%d").date()
            
            if entry_date >= start_date.date():
                recent_entries.append(entry)
        except Exception:
            continue
            
    if not recent_entries:
        return "履歴が不足しています。", "過去30日間のデータがありません。もう少し記録を続けてみましょう。", "ー"

    report_text = f"【過去30日間のポジティブ日記（合計{len(recent_entries)}件）】\n\n"
    
    for i, entry in enumerate(recent_entries):
        report_text += f"--- 記録 {i+1} ({entry.get('selected_theme', 'テーマ不明')}) ---\n"
        report_text += f"元の出来事: {entry['negative']}\n"
        report_text += f"変換後の行動案: {entry['positive_reframe']['action']}\n"
        report_text += f"変換後のポジティブ側面: {entry['positive_reframe']['positive'][:50]}...\n\n" 

    system_prompt = f"""
    あなたは、ユーザーの行動と成長を分析する専門家です。
    ユーザーの過去30日間の日記データから、以下の3つの視点で分析した「月間レポート」を生成してください。

    【レポートの形式】
    1. 最も多かったテーマと傾向: (どのテーマの記録が多かったか、その記録から共通する傾向や課題を簡潔に要約)
    2. 行動と成長の総評: (ユーザーが頑張っていた点、行動案を通して達成したと思われる小さな進歩、成長した側面を温かい言葉で総評)
    3. 次の30日間の重点目標: (抽出された傾向に基づき、次の30日で意識すべき具体的な目標を一つ提案)

    必ずこの3つの要素を「1.」「2.」「3.」で始まる形式で出力し、それ以外の説明や挨拶は一切含めないでください。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象データ:\n" + report_text}]}
            ]
        )
        raw_text = response.text
        
        try:
            theme_and_rest = raw_text.split("2. ", 1)
            theme = theme_and_rest[0].strip().replace("1. ", "").replace("**", "")
            
            summary_and_goal = theme_and_rest[1].split("3. ", 1)
            summary = summary_and_goal[0].strip().replace("**", "")
            goal = summary_and_goal[1].strip().replace("**", "")

            return theme, summary, goal

        except Exception:
            return "解析エラー", "AIの出力形式が予期せぬものでした。", raw_text

    except Exception as e:
        return "APIエラー", f"Gemini API実行エラーが発生しました: {e}", "ー"
# ----------------------------------------------------

# ----------------------------------------------------
# 履歴をCSV形式に変換する関数 (Ver. 4.4 新規追加)
# ----------------------------------------------------
def convert_history_to_csv(history_list):
    """セッション履歴をCSV形式の文字列に変換する"""
    if not history_list:
        return ""

    # ヘッダー行
    header = "タイムスタンプ,日付,テーマ,元のネガティブな出来事,1.客観視(事実),2.ポジティブな側面,3.具体的な行動案\n"
    csv_data = header

    for entry in history_list:
        # CSVのセル内でカンマや改行が含まれないよう、ダブルクォーテーションで囲む
        timestamp = entry.get('timestamp', '').replace(',', '，')
        date_only = entry.get('date_only', '').replace(',', '，')
        theme = entry.get('selected_theme', 'テーマ不明').replace(',', '，')
        
        # 複数行のテキストデータはダブルクォーテーションで囲み、内部のダブルクォーテーションはエスケープ（""）
        negative = f'"{entry.get("negative", "").replace('"', '""')}"'
        fact = f'"{entry["positive_reframe"]["fact"].replace('"', '""')}"'
        positive = f'"{entry["positive_reframe"]["positive"].replace('"', '""')}"'
        action = f'"{entry["positive_reframe"]["action"].replace('"', '""')}"'
        
        row = f"{timestamp},{date_only},{theme},{negative},{fact},{positive},{action}\n"
        csv_data += row

    return csv_data
# ----------------------------------------------------

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
        
        timestamp_full = st.session_state.current_review_entry['timestamp'] 
        date_only = timestamp_full.split(" ")[0]
        
        st.session_state.current_review_entry['date_only'] = date_only
        
        st.session_state.history.insert(0, st.session_state.current_review_entry)
        
        st.session_state.positive_streak = calculate_streak(st.session_state.history)
        
        st.session_state.current_review_entry = None
        st.session_state['monthly_report'] = None 
        st.toast("✅ 日記が保存されました！", icon='💾')

def discard_entry():
    st.session_state.current_review_entry = None
    st.toast("🗑️ 変換結果は破棄されました。新しい日記をどうぞ。", icon='✍️')

def delete_entry(timestamp_to_delete):
    """指定されたタイムスタンプを持つエントリを履歴から削除する"""
    new_history = [
        entry for entry in st.session_state.history 
        if entry['timestamp'] != timestamp_to_delete
    ]
    st.session_state.history = new_history
    
    st.session_state.positive_streak = calculate_streak(st.session_state.history)
    st.session_state['monthly_report'] = None 
    
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
            "negative": input_value,
            "positive_reframe": converted_result,
            "selected_theme": THEMES[0] 
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
    
    # テーマ選択 UI
    selected_theme = st.selectbox(
        "🏷️ この出来事を分類するテーマを選んでください。", 
        options=THEMES, 
        key="theme_selector_key"
    )
    st.session_state.current_review_entry['selected_theme'] = selected_theme
    
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
# 月間レポートエリア 
# ----------------------------------------------------
st.subheader("📊 成長と行動の月間レポート")

if st.button("✨ 過去30日間を振り返るレポートを生成する"):
    if len(st.session_state.history) < 1: 
        st.warning("レポートを生成するには、最低1つ以上の記録が必要です。")
    else:
        with st.spinner("過去の記録を分析し、レポートを作成中..."):
            theme, summary, goal = generate_monthly_report(st.session_state.history)
            
            st.session_state['monthly_report'] = {
                "theme": theme,
                "summary": summary,
                "goal": goal
            }
            st.toast("✅ 月間レポートが完成しました！", icon='📈')

# レポート表示エリア
if 'monthly_report' in st.session_state and st.session_state['monthly_report']:
    report = st.session_state['monthly_report']
    st.markdown("#### **月間レポート（過去30日間）**")
    
    st.markdown("##### 1. 最も多かったテーマと傾向")
    st.info(report['theme'])
    
    st.markdown("##### 2. 行動と成長の総評")
    st.success(report['summary'])
    
    st.markdown("##### 3. 次の30日間の重点目標")
    st.warning(report['goal'])
    
    st.markdown("---")
# ----------------------------------------------------

# ★★★ 履歴データのエクスポート機能 (Ver. 4.4 新規追加) ★★★
st.markdown("#### 📥 記録のエクスポート（バックアップ）")

if st.session_state.history:
    csv_string = convert_history_to_csv(st.session_state.history)
    
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.datetime.now(jst).strftime("%Y%m%d_%H%M")
    file_name = f"Reframe_PositiveDiary_{now_jst}.csv"
    
    st.download_button(
        label="✅ 全履歴をCSVでダウンロード",
        data=csv_string,
        file_name=file_name,
        mime="text/csv",
        type="secondary"
    )
    st.caption("※ダウンロードしたファイルはExcelやGoogleスプレッドシートで開くことができます。")
else:
    st.info("まだ保存された履歴がないため、ダウンロードできません。")
st.markdown("---")
# ----------------------------------------------------

# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader("📚 過去のポジティブ変換日記（保存済み）")

# 履歴フィルタリング UI
filter_theme = st.selectbox(
    "テーマで絞り込む", 
    options=["すべてのテーマ"] + THEMES, 
    index=0,
    key="history_filter_key"
)

# フィルタリング処理
if filter_theme == "すべてのテーマ":
    filtered_history = st.session_state.history
else:
    filtered_history = [
        entry for entry in st.session_state.history 
        if entry.get('selected_theme') == filter_theme
    ]

if filtered_history:
    for i, entry in enumerate(filtered_history): 
        
        col_ts, col_del = st.columns([0.8, 0.2])
        
        with col_ts:
            theme_display = entry.get('selected_theme', 'テーマ不明')
            st.caption(f"🗓️ 変換日時: {entry['timestamp']} | 🏷️ テーマ: **{theme_display}**")
        
        with col_del:
            st.button(
                "削除", 
                key=f"delete_btn_{entry['timestamp']}", 
                on_click=delete_entry,
                args=[entry['timestamp']]
            )
        
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
        st.caption(f"元のネガティブ内容 ({entry.get('date_only', '日付不明')} 記録): {entry['negative']}")
        st.caption("✨ **コピーのヒント:** 上のエリアをクリックし、Ctrl+A → Ctrl+C で素早くコピーできます。")
        st.markdown("---")

else:
    st.write("まだ保存された記録はありません。最初の出来事を変換して、保存してみましょう！")
