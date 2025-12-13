# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time

# ----------------------------------------------------
# ★★★ 多言語対応用の定義とヘルパー関数 ★★★
# ----------------------------------------------------

# 多言語対応用の静的テキスト定義 (日本語と英語)
TRANSLATIONS = {
    "JA": {
        "PAGE_TITLE": "Reframe: 安心の一歩",
        "CATCHPHRASE": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "STREAK_TITLE": "ポジティブ連続記録",
        "DAYS_CONTINUOUS": "日 連続中！",
        "INPUT_HEADER": "📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。",
        "INPUT_PLACEHOLDER": "（ここは誰にも見られません。心に浮かんだことを自由に。）\n例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。\n\nまたは、'I failed my driving test today and I feel discouraged.'",
        "CONVERT_BUTTON": "✨ ポジティブに変換する！",
        "RESET_BUTTON": "↩️ もう一度書き直す",
        "INPUT_WARNING": "⚠️ 何か出来事を入力してください。あなたの心が待っています。",
        "REVIEW_HEADER": "🧐 変換結果のレビューと次のステップ",
        "CONVERT_DATE": "🗓️ 変換日時:",
        "ORIGINAL_EVENT": "元の出来事:",
        "CONVERSION_RESULT": "✅ 変換結果（あなたの学びと次の行動）:",
        "FACT_HEADER": "🧊 1. 事実の客観視（クールダウン）",
        "POSITIVE_HEADER": "🌱 2. ポジティブな側面抽出（学びと成長）",
        "ACTION_HEADER": "👣 3. 今後の具体的な行動案（Next Step）",
        "THEME_SELECT_LABEL": "🏷️ この出来事を分類するテーマを選んでください。",
        "SAVE_BUTTON": "✅ 日記を確定・保存する",
        "DISCARD_BUTTON": "🗑️ 破棄して次へ",
        "SAVE_CAPTION": "※「保存」すると記録が残り、「破棄」するとこの結果は失われます。",
        "SAVE_TOAST": "✅ 日記が保存されました！",
        "DISCARD_TOAST": "🗑️ 変換結果は破棄されました。新しい日記をどうぞ。",
        "HISTORY_HEADER": "📚 過去のポジティブ変換日記（保存済み）",
        "FILTER_LABEL": "テーマで絞り込む",
        "ALL_THEMES": "すべてのテーマ",
        "DELETE_BUTTON": "削除",
        "DATE_UNKNOWN": "日付不明",
        "THEME_UNKNOWN": "テーマ不明",
        "DELETE_TOAST": "🗑️ 日記エントリを削除しました。",
        "HISTORY_COPY_HINT": "✨ コピーのヒント: 上のエリアをクリックし、Ctrl+A → Ctrl+C で素早くコピーできます。",
        "NO_HISTORY": "まだ保存された記録はありません。最初の出来事を変換して、保存してみましょう！",
        "REPORT_HEADER": "📊 成長と行動の月間レポート",
        "GENERATE_REPORT_BUTTON": "✨ 過去30日間を振り返るレポートを生成する",
        "REPORT_NOT_ENOUGH_DATA": "レポートを生成するには、最低1つ以上の記録が必要です。",
        "REPORT_TITLE": "月間レポート（過去30日間）",
        "REPORT_THEME_HEADER": "1. 最も多かったテーマと傾向",
        "REPORT_SUMMARY_HEADER": "2. 行動と成長の総評",
        "REPORT_GOAL_HEADER": "3. 次の30日間の重点目標",
        "REPORT_COMPLETED_TOAST": "✅ 月間レポートが完成しました！",
        "REPORT_NO_DATA_30DAYS": "過去30日間のデータがありません。もう少し記録を続けてみましょう。",
        "API_ERROR_INIT": "APIクライアントの初期化に失敗しました。シークレット設定にGEMINI_API_KEYがありません。",
        "API_ERROR_GENERIC": "APIクライアントの初期化に失敗しました。エラー: ",
        "API_ERROR_GEMINI": "Gemini API実行エラーが発生しました: ",
        "CSV_HEADER": "タイムスタンプ,日付,テーマ,元のネガティブな出来事,1.客観視(事実),2.ポジティブな側面,3.具体的な行動案\n",
        "EXPORT_HEADER": "📥 記録のエクスポート（バックアップ）",
        "DOWNLOAD_BUTTON": "✅ 全履歴をCSVでダウンロード",
        "EXPORT_CAPTION": "※ダウンロードしたファイルはExcelやGoogleスプレッドシートで開くことができます。",
        "NO_EXPORT_DATA": "まだ保存された履歴がないため、ダウンロードできません。",
        "THEMES": ["選択なし", "仕事・キャリア", "人間関係", "自己成長", "健康・メンタル"],
        "IMAGE_WARNING": "⚠️ 画像ファイルが見つかりません: unnamed.jpg。ファイル名とパスを確認してください。"
    },
    "EN": {
        "PAGE_TITLE": "Reframe: A Safe Step",
        "CATCHPHRASE": "A safe place to transform your 'mental weight' into growth and action.",
        "STREAK_TITLE": "Positive Streak",
        "DAYS_CONTINUOUS": "days continuous!",
        "INPUT_HEADER": "📝 Write down your negative feelings as they are, in a safe space.",
        "INPUT_PLACEHOLDER": "(This is for your eyes only. Feel free to write what comes to mind.)\nExample: I felt discouraged when my age was questioned during the interview.\n\nまたは、'I failed my driving test today and I feel discouraged.'",
        "CONVERT_BUTTON": "✨ Reframe to Positive!",
        "RESET_BUTTON": "↩️ Start Over",
        "INPUT_WARNING": "⚠️ Please enter some event. Your mind is waiting.",
        "REVIEW_HEADER": "🧐 Review of Conversion and Next Steps",
        "CONVERT_DATE": "🗓️ Conversion Date:",
        "ORIGINAL_EVENT": "Original Event:",
        "CONVERSION_RESULT": "✅ Conversion Result (Your Learning and Next Action):",
        "FACT_HEADER": "🧊 1. Objective Fact (Cool Down)",
        "POSITIVE_HEADER": "🌱 2. Positive Aspect Extraction (Learning and Growth)",
        "ACTION_HEADER": "👣 3. Concrete Action Plan (Next Step)",
        "THEME_SELECT_LABEL": "🏷️ Select a theme to classify this event.",
        "SAVE_BUTTON": "✅ Confirm and Save Diary",
        "DISCARD_BUTTON": "🗑️ Discard and Continue",
        "SAVE_CAPTION": "※'Save' will keep the record; 'Discard' will lose this result.",
        "SAVE_TOAST": "✅ Diary saved!",
        "DISCARD_TOAST": "🗑️ Conversion discarded. Write a new entry!",
        "HISTORY_HEADER": "📚 Past Positive Reframe Diaries (Saved)",
        "FILTER_LABEL": "Filter by Theme",
        "ALL_THEMES": "All Themes",
        "DELETE_BUTTON": "Delete",
        "DATE_UNKNOWN": "Date Unknown",
        "THEME_UNKNOWN": "Theme Unknown",
        "DELETE_TOAST": "🗑️ Diary entry deleted.",
        "HISTORY_COPY_HINT": "✨ Copy Hint: Click the area above, then Ctrl+A → Ctrl+C to quickly copy.",
        "NO_HISTORY": "No saved records yet. Convert and save your first event!",
        "REPORT_HEADER": "📊 Monthly Report on Growth and Action",
        "GENERATE_REPORT_BUTTON": "✨ Generate 30-Day Review Report",
        "REPORT_NOT_ENOUGH_DATA": "At least 1 record is required to generate a report.",
        "REPORT_TITLE": "Monthly Report (Last 30 Days)",
        "REPORT_THEME_HEADER": "1. Most Frequent Theme and Trend",
        "REPORT_SUMMARY_HEADER": "2. General Review of Action and Growth",
        "REPORT_GOAL_HEADER": "3. Key Goal for the Next 30 Days",
        "REPORT_COMPLETED_TOAST": "✅ Monthly report completed!",
        "REPORT_NO_DATA_30DAYS": "No data for the last 30 days. Let's continue recording.",
        "API_ERROR_INIT": "API client initialization failed. GEMINI_API_KEY is missing in secrets.",
        "API_ERROR_GENERIC": "API client initialization failed. Error: ",
        "API_ERROR_GEMINI": "Gemini API execution error occurred: ",
        "CSV_HEADER": "Timestamp,Date,Theme,Original_Negative_Event,1.Objective_Fact,2.Positive_Aspect,3.Action_Plan\n",
        "EXPORT_HEADER": "📥 Export Records (Backup)",
        "DOWNLOAD_BUTTON": "✅ Download All History as CSV",
        "EXPORT_CAPTION": "※The downloaded file can be opened with Excel or Google Sheets.",
        "NO_EXPORT_DATA": "Cannot download as there is no saved history yet.",
        "THEMES": ["None Selected", "Work/Career", "Relationships", "Self-Growth", "Health/Mental"],
        "IMAGE_WARNING": "⚠️ Image file not found: unnamed.jpg. Check the filename and path."
    }
}

# 言語設定を取得するヘルパー関数
def get_text(key):
    lang = st.session_state.get('language', 'JA')
    # 辞書に存在しない場合は、日本語のフォールバックを使用
    return TRANSLATIONS.get(lang, TRANSLATIONS['JA']).get(key, TRANSLATIONS['JA'].get(key, f"MISSING TEXT: {key}"))

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
if 'language' not in st.session_state:
    st.session_state['language'] = 'JA' # 初期言語は日本語

# ----------------------------------------------------
# 画面デザインとタイトル設定
# ----------------------------------------------------
st.set_page_config(page_title=get_text("PAGE_TITLE"), layout="centered")

# ★★★ 言語選択 UI (最上部に配置) ★★★
LANGUAGES = {"JA": "日本語", "EN": "English"}
st.session_state['language'] = st.selectbox(
    "Select Language / 言語を選択", 
    options=list(LANGUAGES.keys()), 
    format_func=lambda x: LANGUAGES[x],
    key='language_selector',
    index=list(LANGUAGES.keys()).index(st.session_state['language'])
)
st.markdown("---")

# カスタム画像表示
try:
    st.image("unnamed.jpg", use_column_width=True)
except FileNotFoundError:
    st.warning(get_text("IMAGE_WARNING"))

# キャッチフレーズの文字サイズを調整
st.markdown(
    f"<p style='font-size: 1.1em; font-weight: bold;'>{get_text('CATCHPHRASE')}</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# 連続記録の表示
st.markdown(
    f"##### 🏆 {get_text('STREAK_TITLE')}: <span style='color: green; font-size: 1.5em;'>{st.session_state.positive_streak}</span> {get_text('DAYS_CONTINUOUS')}", 
    unsafe_allow_html=True
)
st.markdown("---")

# ----------------------------------------------------
# Gemini APIクライアントの初期化
# ----------------------------------------------------
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        st.error(get_text("API_ERROR_INIT"))
        st.stop()
        
    API_KEY = st.secrets["tool"]["GEMINI_API_KEY"] 
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(get_text("API_ERROR_GENERIC") + f"{e}")
    st.stop()    

# ----------------------------------------------------
# 感情をポジティブに変換する関数 (コア機能) 
# ----------------------------------------------------
def reframe_negative_emotion(negative_text):
    # ★★★ プロンプトは「入力言語と同じ言語で出力を返す」指示を保持 (多言語対応済) ★★★
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
        return {"fact": "APIエラー", "positive": get_text("API_ERROR_GEMINI") + f"{e}", "action": "ー"}

# ----------------------------------------------------
# 連続記録の計算ロジック (変更なし)
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
# 月間レポートを生成する関数 (変更なし)
# ----------------------------------------------------
def generate_monthly_report(history_list):
    # ... (レポート生成のロジックは変更なし) ...
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
        # ★★★ UIテキストを多言語化 ★★★
        return get_text("REPORT_API_ERROR"), get_text("REPORT_NO_DATA_30DAYS"), "ー"

    report_text = f"【過去30日間のポジティブ日記（合計{len(recent_entries)}件）】\n\n"
    
    for i, entry in enumerate(recent_entries):
        report_text += f"--- 記録 {i+1} ({entry.get('selected_theme', get_text('THEME_UNKNOWN'))}) ---\n"
        report_text += f"元の出来事: {entry['negative']}\n"
        report_text += f"変換後の行動案: {entry['positive_reframe']['action']}\n"
        report_text += f"変換後のポジティブ側面: {entry['positive_reframe']['positive'][:50]}...\n\n" 

    # ★★★ プロンプトは日本語/英語の区別なく通用するよう設計 ★★★
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
            return get_text("REPORT_API_ERROR"), "AIの出力形式が予期せぬものでした。", raw_text

    except Exception as e:
        return get_text("REPORT_API_ERROR"), get_text("API_ERROR_GEMINI") + f"{e}", "ー"
# ----------------------------------------------------

# ----------------------------------------------------
# 履歴をCSV形式に変換する関数
# ----------------------------------------------------
def convert_history_to_csv(history_list):
    """セッション履歴をCSV形式の文字列に変換する"""
    if not history_list:
        return ""

    # ★★★ ヘッダー行を多言語対応させる ★★★
    header = get_text("CSV_HEADER")
    csv_data = header

    for entry in history_list:
        timestamp = entry.get('timestamp', '').replace(',', '，')
        date_only = entry.get('date_only', '').replace(',', '，')
        theme = entry.get('selected_theme', get_text('THEME_UNKNOWN')).replace(',', '，')
        
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
        # ★★★ UIテキストを多言語化 ★★★
        st.toast(get_text("SAVE_TOAST"), icon='💾')

def discard_entry():
    st.session_state.current_review_entry = None
    # ★★★ UIテキストを多言語化 ★★★
    st.toast(get_text("DISCARD_TOAST"), icon='✍️')

def delete_entry(timestamp_to_delete):
    """指定されたタイムスタンプを持つエントリを履歴から削除する"""
    new_history = [
        entry for entry in st.session_state.history 
        if entry['timestamp'] != timestamp_to_delete
    ]
    st.session_state.history = new_history
    
    st.session_state.positive_streak = calculate_streak(st.session_state.history)
    st.session_state['monthly_report'] = None 
    
    # ★★★ UIテキストを多言語化 ★★★
    st.toast(get_text("DELETE_TOAST"), icon='🚮')
# ----------------------------------------------------

# 変換ボタンのコールバック関数
def on_convert_click(input_value):
    if not input_value:
        # ★★★ UIテキストを多言語化 ★★★
        st.warning(get_text("INPUT_WARNING"))
        return

    with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
        converted_result = reframe_negative_emotion(input_value)
        
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.datetime.now(jst)
        
        st.session_state.current_review_entry = {
            "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
            "negative": input_value,
            "positive_reframe": converted_result,
            "selected_theme": get_text("THEMES")[0] # 「選択なし」または「None Selected」
        }
        
        clear_input_only() 

# ----------------------------------------------------
# ユーザーインターフェース (UI)
# ----------------------------------------------------
st.markdown(f"#### {get_text('INPUT_HEADER')}")

negative_input = st.text_area(
    get_text("INPUT_PLACEHOLDER"), # ラベルとして利用 (スペース節約のため通常は空だが、今回はプレースホルダーをラベルとして使用)
    height=200,
    placeholder=get_text("INPUT_PLACEHOLDER"),
    key="negative_input_key",
    label_visibility="collapsed" # ラベルを非表示にし、プレースホルダーのみを表示
)

col1, col2 = st.columns([0.7, 0.3]) 

with col1:
    st.button(
        get_text("CONVERT_BUTTON"), 
        on_click=on_convert_click, 
        args=[negative_input], 
        type="primary"
    )

with col2:
    st.button(get_text("RESET_BUTTON"), on_click=reset_input, key="reset_button") 

# ----------------------------------------------------
# 変換結果レビューエリア (UIの続き)
# ----------------------------------------------------
st.markdown("---")
if st.session_state.current_review_entry:
    
    review_entry = st.session_state.current_review_entry
    
    st.subheader(get_text("REVIEW_HEADER"))
    
    st.caption(f"{get_text('CONVERT_DATE')} {review_entry['timestamp']}")
    st.code(f"{get_text('ORIGINAL_EVENT')} {review_entry['negative']}", language='text') 
    
    st.markdown(f"#### **{get_text('CONVERSION_RESULT')}**")
    
    st.markdown(f"##### {get_text('FACT_HEADER')}")
    st.info(review_entry['positive_reframe']['fact'])
    
    st.markdown(f"##### {get_text('POSITIVE_HEADER')}")
    st.success(review_entry['positive_reframe']['positive'])
    
    st.markdown(f"##### {get_text('ACTION_HEADER')}")
    st.warning(review_entry['positive_reframe']['action']) 
    
    st.markdown("---")
    
    # テーマ選択 UI
    selected_theme = st.selectbox(
        get_text("THEME_SELECT_LABEL"), 
        options=get_text("THEMES"), 
        key="theme_selector_key"
    )
    st.session_state.current_review_entry['selected_theme'] = selected_theme
    
    st.markdown("---")
    
    save_col, discard_col = st.columns([0.5, 0.5])
    
    with save_col:
        st.button(
            get_text("SAVE_BUTTON"), 
            on_click=save_entry, 
            type="primary",
            key="save_button"
        )
    
    with discard_col:
        st.button(
            get_text("DISCARD_BUTTON"), 
            on_click=discard_entry, 
            type="secondary",
            key="discard_button"
        )
        
    st.caption(get_text("SAVE_CAPTION"))
    st.markdown("---")


# ----------------------------------------------------
# 月間レポートエリア 
# ----------------------------------------------------
st.subheader(get_text("REPORT_HEADER"))

if st.button(get_text("GENERATE_REPORT_BUTTON")):
    if len(st.session_state.history) < 1: 
        st.warning(get_text("REPORT_NOT_ENOUGH_DATA"))
    else:
        with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
            theme, summary, goal = generate_monthly_report(st.session_state.history)
            
            st.session_state['monthly_report'] = {
                "theme": theme,
                "summary": summary,
                "goal": goal
            }
            st.toast(get_text("REPORT_COMPLETED_TOAST"), icon='📈')

# レポート表示エリア
if 'monthly_report' in st.session_state and st.session_state['monthly_report']:
    report = st.session_state['monthly_report']
    st.markdown(f"#### **{get_text('REPORT_TITLE')}**")
    
    st.markdown(f"##### {get_text('REPORT_THEME_HEADER')}")
    st.info(report['theme'])
    
    st.markdown(f"##### {get_text('REPORT_SUMMARY_HEADER')}")
    st.success(report['summary'])
    
    st.markdown(f"##### {get_text('REPORT_GOAL_HEADER')}")
    st.warning(report['goal'])
    
    st.markdown("---")
# ----------------------------------------------------

# ----------------------------------------------------
# 履歴データのエクスポート機能 
# ----------------------------------------------------
st.markdown(f"#### {get_text('EXPORT_HEADER')}")

if st.session_state.history:
    csv_string = convert_history_to_csv(st.session_state.history)
    
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.datetime.now(jst).strftime("%Y%m%d_%H%M")
    file_name = f"Reframe_PositiveDiary_{now_jst}.csv"
    
    st.download_button(
        label=get_text("DOWNLOAD_BUTTON"),
        data=csv_string,
        file_name=file_name,
        mime="text/csv",
        type="secondary"
    )
    st.caption(get_text("EXPORT_CAPTION"))
else:
    st.info(get_text("NO_EXPORT_DATA"))
st.markdown("---")
# ----------------------------------------------------

# ----------------------------------------------------
# 履歴の表示エリア (UIの最後)
# ----------------------------------------------------
st.subheader(get_text("HISTORY_HEADER"))

# 履歴フィルタリング UI
filter_theme = st.selectbox(
    get_text("FILTER_LABEL"), 
    options=[get_text("ALL_THEMES")] + get_text("THEMES"), 
    index=0,
    key="history_filter_key"
)

# フィルタリング処理
if filter_theme == get_text("ALL_THEMES"):
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
            theme_display = entry.get('selected_theme', get_text('THEME_UNKNOWN'))
            # ★★★ 日付とテーマの表示も多言語化されたテキストを使用 ★★★
            st.caption(f"{get_text('CONVERT_DATE')} {entry['timestamp']} | 🏷️ {get_text('THEME_SELECT_LABEL').split(' ')[0]}: **{theme_display}**")
        
        with col_del:
            st.button(
                get_text("DELETE_BUTTON"), 
                key=f"delete_btn_{entry['timestamp']}", 
                on_click=delete_entry,
                args=[entry['timestamp']]
            )
        
        # 履歴の内容を表示 (AIの出力は入力言語に依存するため、そのまま表示)
        history_value = (
            f"🧊 1. {get_text('FACT_HEADER').split(' ')[-1]}: {entry['positive_reframe']['fact']}\n\n"
            f"🌱 2. {get_text('POSITIVE_HEADER').split(' ')[-1]}: {entry['positive_reframe']['positive']}\n\n"
            f"👣 3. {get_text('ACTION_HEADER').split(' ')[-1]}: {entry['positive_reframe']['action']}"
        )
        
        st.text_area(
            f"過去の変換 ({entry['timestamp']})",
            value=history_value,
            height=300,
            label_visibility="collapsed",
            key=f"history_area_{entry['timestamp']}"
        )
        st.caption(f"元のネガティブ内容 ({entry.get('date_only', get_text('DATE_UNKNOWN'))} 記録): {entry['negative']}")
        st.caption(get_text("HISTORY_COPY_HINT"))
        st.markdown("---")

else:
    st.write(get_text("NO_HISTORY"))
