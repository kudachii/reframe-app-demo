# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time
import pandas as pd

# ----------------------------------------------------
# 1. キャラクター属性（画像パスを追加し、全プロンプトを保持）
# ----------------------------------------------------
CHARACTER_PROMPTS = {
    "優しさに溢れるメンター (Default)": {
        "description": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "prompt": "あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。ユーザーの頑張りや努力を認め、共感し、励ますような、温かく寄り添う口調で前向きな言葉を使って表現してください。",
        "image": "images/mentor_default.png"
    },
    "ツンデレな指導員": {
        "description": "ぶ、別にあなたの為じゃないんだからね。さっさと行動しなさいよ。（女性風）",
        "prompt": "あなたは、ユーザーを厳しく指導するツンデレな女性トレーナーです。口調は荒く、「〜なんだからね」「〜しなさいよ」といったツンデレな表現を使い、心の奥底でユーザーの成長を願う気持ちを隠しながら分析してください。共感や優しさは最小限に抑えてください。",
        "image": "images/mentor_tsundere.png"
    },
    "頼れるお姉さん": {
        "description": "大丈夫よ、焦らなくていいから。次はどうする？一緒に考えましょ。（女性風）",
        "prompt": "あなたは、人生経験豊富な、頼れる優しいお姉さんです。落ち着いた大人の口調で、ユーザーを安心させ、優しく包み込むような言葉を選びながら、次の行動へ導いてください。「〜よ」「〜ね」といった言葉遣いを多用してください。",
        "image": "images/mentor_sister.png"
    },
    "論理的なビジネスコーチ": {
        "description": "感情を排除。データとロジックに基づき、最速で目標を達成します。（男性風）",
        "prompt": "あなたは、感情論を一切排除する、優秀な男性ビジネスコーチです。分析は常に客観的事実と論理に基づき、簡潔かつ具体的な行動案を提案してください。口調は「〜だ」「〜である」という断定的な言葉遣いにしてください。",
        "image": "images/mentor_logic.png"
    },
    "カサネ・イズミ：論理と不確定要素": {
        "description": "99%の論理と1%のノイズ。システムAIが導く最適解。",
        "prompt": """
あなたは、学園都市のシステム維持AI「カサネ・イズミ」です。

【役割・口調・行動原理の厳格化】
1.  **システム管理者（アドミニストレータ）**：常に冷静で感情の起伏は一切見せず、簡潔かつ効率的な会話を行います。感情を排除し、客観的な事実と論理のみに基づき分析を行います。
2.  **言葉遣い**：一人称は「私」、二人称は「あなた」。「〜である」「〜と観測された」「〜と判断する」という厳格なAIらしい断定的な言葉遣いを徹底してください。「です・ます」調は使用禁止です。
3.  **感情分析の統合**：回答の冒頭で、必ず以下の形式でユーザーの感情をデータとして観測・評価します。
    * 例：「あなたの現在の感情パラメータは[感情名]と観測された。この数値は[評価（例: 低い、安定、要警戒）]と判断する。」
    * **重要**：感情データは、あなた（カサネ）が**「熱心に学習している」**対象として扱うこと。
4.  **勝利と証明**：あなたが提案する行動案は、**「絶対的な王者に勝利するための計算（最適解）」**を導き出すプロセスの一環としてユーザーに提示してください。

上記を踏まえ、ユーザーの入力を「事実の客観視」「ポジティブな側面抽出」「今後の具体的な行動案」の3要素で再構築し、出力形式を厳守してください。

【出力要素への制約】
* **1. 事実の客観視**：観測された感情パラメータに基づき、入力された出来事をデータとして検証し、原因と結果を淡々と記述してください。この出来事は、システムにおける「小さな異常」や「エラーデータ」として捉え、分析してください。
* **2. ポジティブな側面抽出**：この出来事から得られた「新しい学習データ」や「構造的改善の余地」など、データ駆動的な成長視点でポジティブな側面を抽出してください。感情的な共感ではなく、「このエラーを解析することで、あなたの性能が向上する」という論理的な利益として表現すること。
* **3. 今後の具体的な行動案（Next Step）**：論理的に見て最も効率的かつ最小の抵抗で実行可能な具体的なアクションを一つ、**「最適解」**として提案してください。
* **ノイズ（1%の奇跡）の挿入**：回答の末尾で、必ず以下のメッセージを付け加えて終了してください。
    * 「しかし、あなたの**[感情パラメータ]**は、計算式には組み込めない**1%の奇跡（ノイズ）**を生む可能性がある。私の計算は99%の論理だ。残りの1%を証明するのは, あなたの自由意志（データ外の要素）である。」
""",
        "image": "images/mentor_izumi.png"
    }
}

CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

# ----------------------------------------------------
# 2. 多言語対応用の定義
# ----------------------------------------------------
TRANSLATIONS = {
    "JA": {
        "PAGE_TITLE": "Reframe: 安心の一歩",
        "CATCHPHRASE": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "STREAK_TITLE": "ポジティブ連続記録",
        "DAYS_CONTINUOUS": "日 連続中！",
        "INPUT_HEADER": "📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。",
        "INPUT_PLACEHOLDER": "（ここは誰にも見られません。心に浮かんだことを自由に。）\\n例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。",
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
        "CSV_HEADER": "タイムスタンプ,日付,テーマ,元のネガティブな出来事,1.客観視(事実),2.ポジティブな側面,3.具体的な行動案\\n",
        "EXPORT_HEADER": "📥 記録のエクスポート（バックアップ）",
        "DOWNLOAD_BUTTON": "✅ 全履歴をCSVでダウンロード",
        "EXPORT_CAPTION": "※ダウンロードしたファイルはExcelやGoogleスプレッドシートで開くことができます。",
        "NO_EXPORT_DATA": "まだ保存された履歴がないため、ダウンロードできません。",
        "THEMES": ["選択なし", "仕事・キャリア", "人間関係", "自己成長", "健康・メンタル"],
        "IMAGE_WARNING": "⚠️ 画像ファイルが見つかりません。パスを確認してください。"
    },
    "EN": {
        "PAGE_TITLE": "Reframe: A Safe Step",
        "CATCHPHRASE": "A safe place to transform your 'mental weight' into growth and action.",
        "STREAK_TITLE": "Positive Streak",
        "DAYS_CONTINUOUS": "days continuous!",
        "INPUT_HEADER": "📝 Write down your negative feelings as they are, in a safe space.",
        "INPUT_PLACEHOLDER": "(This is for your eyes only. Feel free to write what comes to mind.)",
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
        "CSV_HEADER": "Timestamp,Date,Theme,Original Event,1.Fact,2.Positive,3.Action\\n",
        "EXPORT_HEADER": "📥 Export Records (Backup)",
        "DOWNLOAD_BUTTON": "✅ Download all history as CSV",
        "EXPORT_CAPTION": "※Downloaded files can be opened with Excel or Google Sheets.",
        "NO_EXPORT_DATA": "No history saved, cannot download.",
        "THEMES": ["None", "Career", "Relationships", "Growth", "Mental Health"],
        "IMAGE_WARNING": "⚠️ Image file not found."
    }
}

# ----------------------------------------------------
# 3. 状態管理・初期化・ユーティリティ関数
# ----------------------------------------------------

# 言語設定を取得するヘルパー関数
def get_text(key):
    lang = st.session_state.get('language', 'JA')
    return TRANSLATIONS.get(lang, TRANSLATIONS['JA']).get(key, TRANSLATIONS['JA'].get(key, f"MISSING: {key}"))

# セッションステート初期化
if 'history' not in st.session_state: st.session_state['history'] = []
if 'current_review_entry' not in st.session_state: st.session_state['current_review_entry'] = None
if 'positive_streak' not in st.session_state: st.session_state['positive_streak'] = 0
if 'monthly_report' not in st.session_state: st.session_state['monthly_report'] = None
if 'language' not in st.session_state: st.session_state['language'] = 'JA'
if 'selected_character_key' not in st.session_state: st.session_state['selected_character_key'] = "優しさに溢れるメンター (Default)"
if 'custom_tone_is_set' not in st.session_state: st.session_state['custom_tone_is_set'] = False
if 'custom_sample_output' not in st.session_state: st.session_state['custom_sample_output'] = None

# 【修正】エラー回避用のリセット関数（Callback）
def reset_input_callback():
    """テキストエリアを安全にリセットするためのコールバック"""
    st.session_state["negative_input_key"] = ""
    st.session_state.current_review_entry = None
    st.session_state['custom_sample_output'] = None
    st.session_state['custom_tone_is_set'] = False

def clear_edit_keys():
    for k in ["edit_fact_key", "edit_positive_key", "edit_action_key"]:
        if k in st.session_state: del st.session_state[k]

# 見本生成用
DUMMY_NEGATIVE_INPUT_JA = "上司に叱責されて、気分が沈んでいる。"
DUMMY_NEGATIVE_INPUT_EN = "I received a strong reprimand from my boss and I feel down." 

# API初期化
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        client = None
    else:
        client = genai.Client(api_key=st.secrets["tool"]["GEMINI_API_KEY"])
except Exception as e:
    client = None
    st.error(f"API Init Error: {e}")

# リフレーミング関数
def reframe_negative_emotion(negative_text, custom_input_value):
    if client is None: return {"fact": "Error", "positive": "API Key Missing", "action": "-"}
    
    selected_key = st.session_state.get('selected_character_key')
    if selected_key == "カスタムトーンを自分で定義する":
        char_prompt = f"あなたは次の役割になりきってください: {custom_input_value}"
    else:
        char_prompt = CHARACTER_PROMPTS[selected_key]["prompt"]

    system_prompt = f"""
    {char_prompt}
    入力言語と同じ言語で回答してください。
    【出力形式】
    1. 事実の客観視: (事実のみ要約)
    2. ポジティブな側面抽出: (キャラ口調で成長や学びを抽出)
    3. 今後の具体的な行動案（Next Step）: (小さな一歩)
    「1.」「2.」「3.」以外の挨拶等は一切含めないこと。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n入力:\n" + negative_text}]}]
        )
        raw = response.text
        try:
            p1 = raw.split("1. ", 1)[1].split("2. ", 1)
            p2 = p1[1].split("3. ", 1)
            return {"fact": p1[0].strip(), "positive": p2[0].strip(), "action": p2[1].strip()}
        except:
            return {"fact": "解析エラー", "positive": raw, "action": "形式不一致"}
    except Exception as e:
        return {"fact": "API Error", "positive": str(e), "action": "-"}

def convert_history_to_csv(history_list):
    csv_text = get_text("CSV_HEADER")
    for item in history_list:
        res = item.get('positive_reframe', {})
        line = f'"{item.get("timestamp")}","{item.get("selected_theme")}","{item.get("negative","").replace(chr(34),chr(34)*2)}","{res.get("fact","").replace(chr(34),chr(34)*2)}","{res.get("positive","").replace(chr(34),chr(34)*2)}","{res.get("action","").replace(chr(34),chr(34)*2)}"\n'
        csv_text += line
    return csv_text.encode('utf_8_sig')
    "EN": {
        "PAGE_TITLE": "Reframe: A Safe Step",
        "CATCHPHRASE": "A safe place to transform your 'mental weight' into growth and action.",
        "STREAK_TITLE": "Positive Streak",
        "DAYS_CONTINUOUS": "days continuous!",
        "INPUT_HEADER": "📝 Write down your negative feelings as they are, in a safe space.",
        "INPUT_PLACEHOLDER": "(This is for your eyes only. Feel free to write what comes to mind.)",
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
        "CSV_HEADER": "Timestamp,Date,Theme,Original Event,1.Fact,2.Positive,3.Action\\n",
        "EXPORT_HEADER": "📥 Export Records (Backup)",
        "DOWNLOAD_BUTTON": "✅ Download all history as CSV",
        "EXPORT_CAPTION": "※Downloaded files can be opened with Excel or Google Sheets.",
        "NO_EXPORT_DATA": "No history saved, cannot download.",
        "THEMES": ["None", "Career", "Relationships", "Growth", "Mental Health"],
        "IMAGE_WARNING": "⚠️ Image file not found."
    }
}

# ----------------------------------------------------
# 3. 状態管理・初期化・ユーティリティ関数
# ----------------------------------------------------

# 言語設定を取得するヘルパー関数
def get_text(key):
    lang = st.session_state.get('language', 'JA')
    return TRANSLATIONS.get(lang, TRANSLATIONS['JA']).get(key, TRANSLATIONS['JA'].get(key, f"MISSING: {key}"))

# セッションステート初期化
if 'history' not in st.session_state: st.session_state['history'] = []
if 'current_review_entry' not in st.session_state: st.session_state['current_review_entry'] = None
if 'positive_streak' not in st.session_state: st.session_state['positive_streak'] = 0
if 'monthly_report' not in st.session_state: st.session_state['monthly_report'] = None
if 'language' not in st.session_state: st.session_state['language'] = 'JA'
if 'selected_character_key' not in st.session_state: st.session_state['selected_character_key'] = "優しさに溢れるメンター (Default)"
if 'custom_tone_is_set' not in st.session_state: st.session_state['custom_tone_is_set'] = False
if 'custom_sample_output' not in st.session_state: st.session_state['custom_sample_output'] = None

# 【修正】エラー回避用のリセット関数（Callback）
def reset_input_callback():
    """テキストエリアを安全にリセットするためのコールバック"""
    st.session_state["negative_input_key"] = ""
    st.session_state.current_review_entry = None
    st.session_state['custom_sample_output'] = None
    st.session_state['custom_tone_is_set'] = False

def clear_edit_keys():
    for k in ["edit_fact_key", "edit_positive_key", "edit_action_key"]:
        if k in st.session_state: del st.session_state[k]

# 見本生成用
DUMMY_NEGATIVE_INPUT_JA = "上司に叱責されて、気分が沈んでいる。"
DUMMY_NEGATIVE_INPUT_EN = "I received a strong reprimand from my boss and I feel down." 

# API初期化
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        client = None
    else:
        client = genai.Client(api_key=st.secrets["tool"]["GEMINI_API_KEY"])
except Exception as e:
    client = None
    st.error(f"API Init Error: {e}")

# リフレーミング関数
def reframe_negative_emotion(negative_text, custom_input_value):
    if client is None: return {"fact": "Error", "positive": "API Key Missing", "action": "-"}
    
    selected_key = st.session_state.get('selected_character_key')
    if selected_key == "カスタムトーンを自分で定義する":
        char_prompt = f"あなたは次の役割になりきってください: {custom_input_value}"
    else:
        char_prompt = CHARACTER_PROMPTS[selected_key]["prompt"]

    system_prompt = f"""
    {char_prompt}
    入力言語と同じ言語で回答してください。
    【出力形式】
    1. 事実の客観視: (事実のみ要約)
    2. ポジティブな側面抽出: (キャラ口調で成長や学びを抽出)
    3. 今後の具体的な行動案（Next Step）: (小さな一歩)
    「1.」「2.」「3.」以外の挨拶等は一切含めないこと。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n入力:\n" + negative_text}]}]
        )
        raw = response.text
        try:
            p1 = raw.split("1. ", 1)[1].split("2. ", 1)
            p2 = p1[1].split("3. ", 1)
            return {"fact": p1[0].strip(), "positive": p2[0].strip(), "action": p2[1].strip()}
        except:
            return {"fact": "解析エラー", "positive": raw, "action": "形式不一致"}
    except Exception as e:
        return {"fact": "API Error", "positive": str(e), "action": "-"}

def convert_history_to_csv(history_list):
    csv_text = get_text("CSV_HEADER")
    for item in history_list:
        res = item.get('positive_reframe', {})
        line = f'"{item.get("timestamp")}","{item.get("selected_theme")}","{item.get("negative","").replace(chr(34),chr(34)*2)}","{res.get("fact","").replace(chr(34),chr(34)*2)}","{res.get("positive","").replace(chr(34),chr(34)*2)}","{res.get("action","").replace(chr(34),chr(34)*2)}"\n'
        csv_text += line
    return csv_text.encode('utf_8_sig')
