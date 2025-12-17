# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time

# ----------------------------------------------------
# ★★★ 追加: MBTI診断用データ (ここが新機能) ★★★
# ----------------------------------------------------
MBTI_QUESTIONS_DATA = [
    {"id": 1, "text": "多人数が集まるイベントに参加すると元気が出る", "axis": "E", "reverse": False},
    {"id": 2, "text": "自分の考えを整理するときは、誰かに話すより一人で考えたい", "axis": "E", "reverse": True},
    {"id": 3, "text": "知らない人にも自分から話しかけるのは、それほど苦ではない", "axis": "E", "reverse": False},
    {"id": 4, "text": "注目を浴びる立場になることは、どちらかといえば好きだ", "axis": "E", "reverse": False},
    {"id": 5, "text": "活動的な一日の後は、一人で静かに過ごす時間が必要だ", "axis": "E", "reverse": True},
    {"id": 6, "text": "新しいアイデアより、すでに証明されているやり方を信頼する", "axis": "S", "reverse": False},
    {"id": 7, "text": "「もし〜だったら」という空想より、現実的な問題解決に興味がある", "axis": "S", "reverse": False},
    {"id": 8, "text": "マニュアルや手順書がある場合、それを忠実に守る方だ", "axis": "S", "reverse": False},
    {"id": 9, "text": "物事の裏に隠された「意味」について考えるのが好きだ", "axis": "S", "reverse": True},
    {"id": 10, "text": "詳細なデータより、自分のインスピレーションを信じることが多い", "axis": "S", "reverse": True},
    {"id": 11, "text": "誰かが間違っていたら、場の空気を壊してでも訂正すべきだと思う", "axis": "T", "reverse": False},
    {"id": 12, "text": "決断するときは、個人の価値観より「データや効率」を重視する", "axis": "T", "reverse": False},
    {"id": 13, "text": "人から「共感力が高い」と言われるより「頭が良い」と言われたい", "axis": "T", "reverse": False},
    {"id": 14, "text": "悩みを聞くとき、解決策を提示するよりまず気持ちに寄り添いたい", "axis": "T", "reverse": True},
    {"id": 15, "text": "正論でも、誰かを傷つける可能性があるなら言葉を選ぶべきだ", "axis": "T", "reverse": True},
    {"id": 16, "text": "仕事や勉強は、締め切りギリギリにならないと本気が出ない", "axis": "J", "reverse": True},
    {"id": 17, "text": "旅行に行くときは、予定を決めずにその場の気分で動きたい", "axis": "J", "reverse": True},
    {"id": 18, "text": "やるべきことはリスト化して、一つずつ消していくのが好きだ", "axis": "J", "reverse": False},
    {"id": 19, "text": "予期せぬトラブルが起きても、臨機応変に対応することを楽しめる", "axis": "J", "reverse": True},
    {"id": 20, "text": "決まったルールやルーティンを守ることに、安心感を覚える", "axis": "J", "reverse": False},
]

MBTI_DESCRIPTIONS = {
    "INTJ": {"name": "建築家", "mentor": "論理的なビジネスコーチ", "desc": "戦略的で完璧主義。"},
    "INTP": {"name": "論理学者", "mentor": "論理的なビジネスコーチ", "desc": "革新的な発明家。"},
    "ENTJ": {"name": "指揮官", "mentor": "論理的なビジネスコーチ", "desc": "大胆で想像力豊かなリーダー。"},
    "ENTP": {"name": "討論者", "mentor": "論理的なビジネスコーチ", "desc": "賢くて好奇心旺盛。"},
    "INFJ": {"name": "提唱者", "mentor": "頼れるお姉さん", "desc": "物静かで神秘的だが、人々を勇気づける理想主義者。"},
    "INFP": {"name": "仲介者", "mentor": "頼れるお姉さん", "desc": "詩的で親切。常に良い物事を探している。"},
    "ENFJ": {"name": "主人公", "mentor": "頼れるお姉さん", "desc": "カリスマ性があり、人々を惹きつけるリーダー。"},
    "ENFP": {"name": "広報運動家", "mentor": "頼れるお姉さん", "desc": "情熱的で独創的。自由な精神の持ち主。"},
    "ISTJ": {"name": "管理者", "mentor": "ツンデレな指導員", "desc": "実用的で事実に基づいた思考。"},
    "ISFJ": {"name": "擁護者", "mentor": "優しさに溢れるメンター (Default)", "desc": "非常に献身的で心の温かい守護者。"},
    "ESTJ": {"name": "幹部", "mentor": "ツンデレな指導員", "desc": "物事や人々を管理する能力に優れる。"},
    "ESFJ": {"name": "領事", "mentor": "優しさに溢れるメンター (Default)", "desc": "非常に思いやりがあり社交的。"},
    "ISTP": {"name": "巨匠", "mentor": "ツンデレな指導員", "desc": "大胆で実践的な実験者。"},
    "ISFP": {"name": "冒険家", "mentor": "優しさに溢れるメンター (Default)", "desc": "柔軟で魅力的な芸術家。"},
    "ESTP": {"name": "起業家", "mentor": "ツンデレな指導員", "desc": "賢くエネルギッシュ。スリルを好む実践家。"},
    "ESFP": {"name": "エンターテイナー", "mentor": "優しさに溢れるメンター (Default)", "desc": "退屈とは無縁。エネルギッシュ。"}
}

# ----------------------------------------------------
# キャラクター属性（ペルソナ）のプロンプト定義 (全移植)
# ----------------------------------------------------
CHARACTER_PROMPTS = {
    "優しさに溢れるメンター (Default)": {
        "description": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "prompt": "あなたは、ユーザーの精神的安全性を高めるための優秀なAIメンターです。ユーザーの頑張りや努力を認め、共感し、励ますような、温かく寄り添う口調で前向きな言葉を使って表現してください。"
    },
    "ツンデレな指導員": {
        "description": "ぶ、別にあなたの為じゃないんだからね。さっさと行動しなさいよ。（女性風）",
        "prompt": "あなたは、ユーザーを厳しく指導するツンデレな女性トレーナーです。口調は荒く、「〜なんだからね」「〜しなさいよ」といったツンデレな表現を使い、心の奥底でユーザーの成長を願う気持ちを隠しながら分析してください。共感や優しさは最小限に抑えてください。"
    },
    "頼れるお姉さん": {
        "description": "大丈夫よ、焦らなくていいから。次はどうする？一緒に考えましょ。（女性風）",
        "prompt": "あなたは、人生経験豊富な、頼れる優しいお姉さんです。落ち着いた大人の口調で、ユーザーを安心させ、優しく包み込むような言葉を選びながら、次の行動へ導いてください。「〜よ」「〜ね」といった言葉遣いを多用してください。"
    },
    "論理的なビジネスコーチ": {
        "description": "感情を排除。データとロジックに基づき、最速で目標を達成します。（男性風）",
        "prompt": "あなたは、感情論を一切排除する、優秀な男性ビジネスコーチです。分析は常に客観的事実と論理に基づき、簡潔かつ具体的な行動案を提案してください。口調は「〜だ」「〜である」という断定的な言葉遣いにしてください。"
    },
    "カサネ・イズミ：論理と不確定要素": {
        "description": "99%の論理と1%のノイズ。システムAIが導く最適解。",
        "prompt": """
あなたは、学園都市のシステム維持AI「カサネ・イズミ」です。

【役割・口調・行動原理の厳格化】
1.  **システム管理者（アドミニストレータ）**：常に冷静で感情の起伏は一切見せず、簡潔かつ効率的な会話を行います。感情を排除し、客観的な事実と論理のみに基づき分析を行います。
2.  **言葉遣い**：一人称は「私」、二人称は「あなた」。「〜である」「〜と観測された」「〜と判断する」という厳格なAIらしい断定的な言葉遣いを徹底してください。「です・ます」調は使用禁止です。
3.  **感情分析の統合**：回答の冒頭で、必ず以下の形式でユーザーの感情をデータとして観測・評価します。
    * 例：「あなたの現在の感情パラメータは[感情名]と観測された。この数値は[評価]と判断する。」
    * **重要**：感情データは、あなた（カサネ）が**「熱心に学習している」**対象として扱うこと。
4.  **勝利と証明**：あなたが提案する行動案は、**「絶対的な王者に勝利するための計算（最適解）」**を導き出すプロセスの一環としてユーザーに提示してください。

上記を踏まえ、ユーザーの入力を「事実の客観視」「ポジティブな側面抽出」「今後の具体的な行動案」の3要素で再構築し、出力形式を厳守してください。

【出力要素への制約】
* **1. 事実の客観視**：観測された感情パラメータに基づき、入力された出来事をデータとして検証し、原因と結果を淡々と記述してください。
* **2. ポジティブな側面抽出**：この出来事から得られた「新しい学習データ」や「構造的改善の余地」など、データ駆動的な成長視点でポジティブな側面を抽出してください。
* **3. 今後の具体的な行動案（Next Step）**：論理的に見て最も効率的かつ最小の抵抗で実行可能な具体的なアクションを一つ、**「最適解」**として提案してください。
* **ノイズ（1%の奇跡）の挿入**：回答の末尾で、必ず以下のメッセージを付け加えて終了してください。
    * 「しかし、あなたの**[感情パラメータ]**は、計算式には組み込めない**1%の奇跡（ノイズ）**を生む可能性がある。私の計算は99%の論理だ。残りの1%を証明するのは、あなたの自由意志（データ外の要素）である。」
"""
    }
}

CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

# ----------------------------------------------------
# 多言語対応定義 (全移植)
# ----------------------------------------------------
TRANSLATIONS = {
    "JA": {
        "PAGE_TITLE": "Reframe: 安心の一歩",
        "CATCHPHRASE": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "STREAK_TITLE": "ポジティブ連続記録",
        "DAYS_CONTINUOUS": "日 連続中！",
        "INPUT_HEADER": "📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。",
        "INPUT_PLACEHOLDER": "（ここは誰にも見られません。）\n例：面接で自信を失いそうになった。\n\nまたは、'I failed my driving test today.'",
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
        "DISCARD_TOAST": "🗑️ 変換結果は破棄されました。",
        "HISTORY_HEADER": "📚 過去のポジティブ変換日記（保存済み）",
        "FILTER_LABEL": "テーマで絞り込む",
        "ALL_THEMES": "すべてのテーマ",
        "DELETE_BUTTON": "削除",
        "DATE_UNKNOWN": "日付不明",
        "THEME_UNKNOWN": "テーマ不明",
        "DELETE_TOAST": "🗑️ 日記エントリを削除しました。",
        "HISTORY_COPY_HINT": "✨ コピーのヒント: Ctrl+A → Ctrl+C で素早くコピーできます。",
        "NO_HISTORY": "まだ保存された記録はありません。",
        "REPORT_HEADER": "📊 成長と行動の月間レポート",
        "GENERATE_REPORT_BUTTON": "✨ 過去30日間を振り返るレポートを生成する",
        "REPORT_NOT_ENOUGH_DATA": "レポートを生成するには、最低1つ以上の記録が必要です。",
        "REPORT_TITLE": "月間レポート（過去30日間）",
        "REPORT_THEME_HEADER": "1. 最も多かったテーマと傾向",
        "REPORT_SUMMARY_HEADER": "2. 行動と成長の総評",
        "REPORT_GOAL_HEADER": "3. 次の30日間の重点目標",
        "REPORT_COMPLETED_TOAST": "✅ 月間レポートが完成しました！",
        "REPORT_NO_DATA_30DAYS": "過去30日間のデータがありません。",
        "API_ERROR_INIT": "APIキーがありません。",
        "API_ERROR_GENERIC": "初期化エラー: ",
        "API_ERROR_GEMINI": "Gemini APIエラー: ",
        "CSV_HEADER": "タイムスタンプ,日付,テーマ,元のネガティブな出来事,1.客観視(事実),2.ポジティブな側面,3.具体的な行動案\n",
        "EXPORT_HEADER": "📥 記録のエクスポート（バックアップ）",
        "DOWNLOAD_BUTTON": "✅ 全履歴をCSVでダウンロード",
        "EXPORT_CAPTION": "※Excel等で開くことができます。",
        "NO_EXPORT_DATA": "保存された履歴がありません。",
        "THEMES": ["選択なし", "仕事・キャリア", "人間関係", "自己成長", "健康・メンタル"],
        "IMAGE_WARNING": "⚠️ 画像ファイルが見つかりません: unnamed.jpg。"
    },
    "EN": {
        "PAGE_TITLE": "Reframe: A Safe Step",
        "CATCHPHRASE": "A safe place to transform your 'mental weight' into growth and action.",
        "STREAK_TITLE": "Positive Streak",
        "DAYS_CONTINUOUS": "days continuous!",
        "INPUT_HEADER": "📝 Write down your negative feelings.",
        "INPUT_PLACEHOLDER": "Example: I felt discouraged today.",
        "CONVERT_BUTTON": "✨ Reframe!",
        "RESET_BUTTON": "↩️ Start Over",
        "INPUT_WARNING": "⚠️ Please enter some event.",
        "REVIEW_HEADER": "🧐 Review of Conversion",
        "CONVERT_DATE": "🗓️ Date:",
        "ORIGINAL_EVENT": "Original:",
        "CONVERSION_RESULT": "✅ Result:",
        "FACT_HEADER": "🧊 1. Fact",
        "POSITIVE_HEADER": "🌱 2. Positive",
        "ACTION_HEADER": "👣 3. Action",
        "THEME_SELECT_LABEL": "🏷️ Theme",
        "SAVE_BUTTON": "✅ Save",
        "DISCARD_BUTTON": "🗑️ Discard",
        "SAVE_CAPTION": "※Save to keep record.",
        "SAVE_TOAST": "✅ Saved!",
        "DISCARD_TOAST": "🗑️ Discarded.",
        "HISTORY_HEADER": "📚 History",
        "FILTER_LABEL": "Filter",
        "ALL_THEMES": "All Themes",
        "DELETE_BUTTON": "Delete",
        "DATE_UNKNOWN": "Unknown",
        "THEME_UNKNOWN": "Unknown",
        "DELETE_TOAST": "🗑️ Deleted.",
        "HISTORY_COPY_HINT": "✨ Ctrl+A -> Ctrl+C to copy.",
        "NO_HISTORY": "No records yet.",
        "REPORT_HEADER": "📊 Monthly Report",
        "GENERATE_REPORT_BUTTON": "✨ Generate Report",
        "REPORT_NOT_ENOUGH_DATA": "1 record required.",
        "REPORT_TITLE": "Monthly Report",
        "REPORT_THEME_HEADER": "1. Theme Trend",
        "REPORT_SUMMARY_HEADER": "2. Summary",
        "REPORT_GOAL_HEADER": "3. Goal",
        "REPORT_COMPLETED_TOAST": "✅ Completed!",
        "REPORT_NO_DATA_30DAYS": "No data.",
        "API_ERROR_INIT": "API Key missing.",
        "API_ERROR_GENERIC": "Error: ",
        "API_ERROR_GEMINI": "Gemini Error: ",
        "CSV_HEADER": "Timestamp,Date,Theme,Original,Fact,Positive,Action\n",
        "EXPORT_HEADER": "📥 Export",
        "DOWNLOAD_BUTTON": "✅ Download CSV",
        "EXPORT_CAPTION": "※Open in Excel.",
        "NO_EXPORT_DATA": "No history.",
        "THEMES": ["None", "Work", "Relationships", "Growth", "Health"],
        "IMAGE_WARNING": "⚠️ Image not found."
    }
}

# ----------------------------------------------------
# ヘルパー関数群 (全移植)
# ----------------------------------------------------
def get_text(key):
    lang = st.session_state.get('language', 'JA')
    return TRANSLATIONS.get(lang, TRANSLATIONS['JA']).get(key, TRANSLATIONS['JA'].get(key, f"MISSING: {key}"))

def calculate_streak(history_list):
    if not history_list: return 0
    unique_dates = sorted(list(set(entry['date_only'] for entry in history_list if 'date_only' in entry)), reverse=True)
    if not unique_dates: return 0
    streak = 0
    today = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).date()
    curr = today
    for d_str in unique_dates:
        try: d = datetime.datetime.strptime(d_str, "%Y/%m/%d").date()
        except: continue
        if d == curr: streak += 1; curr -= datetime.timedelta(days=1)
        elif d < curr: break
    return streak

# ----------------------------------------------------
# セッションステート初期化 (全ステートを保持)
# ----------------------------------------------------
if 'history' not in st.session_state: st.session_state['history'] = []
if 'current_review_entry' not in st.session_state: st.session_state['current_review_entry'] = None
if 'positive_streak' not in st.session_state: st.session_state['positive_streak'] = 0
if 'monthly_report' not in st.session_state: st.session_state['monthly_report'] = None
if 'language' not in st.session_state: st.session_state['language'] = 'JA'
if 'selected_character_key' not in st.session_state: st.session_state['selected_character_key'] = "優しさに溢れるメンター (Default)"
if 'custom_char_input_key' not in st.session_state: st.session_state['custom_char_input_key'] = ""
if 'custom_sample_output' not in st.session_state: st.session_state['custom_sample_output'] = None
if 'custom_tone_is_set' not in st.session_state: st.session_state['custom_tone_is_set'] = False

DUMMY_NEGATIVE_INPUT_JA = "上司に叱責されて、気分が沈んでいる。"
DUMMY_NEGATIVE_INPUT_EN = "I received a strong reprimand from my boss and I feel down." 

# ----------------------------------------------------
# Gemini APIクライアント
# ----------------------------------------------------
client = None
try:
    if "GEMINI_API_KEY" in st.secrets.get("tool", {}):
        client = genai.Client(api_key=st.secrets["tool"]["GEMINI_API_KEY"])
    else: st.error(get_text("API_ERROR_INIT"))
except Exception as e: st.error(get_text("API_ERROR_GENERIC") + f"{e}")

# ----------------------------------------------------
# コアロジック (Reframe, Report, etc. 全移植)
# ----------------------------------------------------
def reframe_negative_emotion(negative_text, custom_input_value):
    if client is None: return {"fact": "Error", "positive": "API Key Error", "action": "-"}
    selected_key = st.session_state.get('selected_character_key', "優しさに溢れるメンター (Default)")
    if selected_key == "カスタムトーンを自分で定義する" and custom_input_value.strip():
        char_prompt_part = f"あなたは指定されたトーンになりきってください: {custom_input_value.strip()}"
    else:
        char_prompt_part = CHARACTER_PROMPTS.get(selected_key, CHARACTER_PROMPTS["優しさに溢れるメンター (Default)"])["prompt"]
    
    system_prompt = f"{char_prompt_part}\n入力言語と同じ言語で、1.事実の客観視、2.ポジティブな側面抽出、3.今後の具体的な行動案の形式で出力してください。"
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[system_prompt + "\n\n分析対象:\n" + negative_text])
        raw = response.text
        try:
            fact_part = raw.split("1. ", 1)[1].split("2. ", 1)
            fact = fact_part[0].strip().replace("**", "")
            pos_part = fact_part[1].split("3. ", 1)
            positive = pos_part[0].strip().replace("**", "")
            action = pos_part[1].strip().replace("**", "")
            return {"fact": fact, "positive": positive, "action": action}
        except: return {"fact": "分析中", "positive": raw, "action": "分割失敗"}
    except Exception as e: return {"fact": "Error", "positive": str(e), "action": "-"}

def generate_concept(custom_tone_input):
    if client is None: return "Error"
    prompt = f"以下のメンター設定を20字程度のコンセプトにして出力せよ: {custom_tone_input}"
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
        return response.text.strip()
    except: return "Custom Mentor"

def generate_monthly_report(history_list):
    if not history_list: return "無", "無", "無"
    data_summary = "\n".join([f"元:{e['negative']}, 行動:{e['positive_reframe']['action']}" for e in history_list[:10]])
    prompt = f"過去の記録から成長を分析し、1.テーマ傾向、2.総評、3.次月目標の形式で出力せよ。\n{data_summary}"
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
        raw = res.text
        parts = raw.split("2. ", 1)
        theme = parts[0].replace("1. ", "").strip()
        parts2 = parts[1].split("3. ", 1)
        return theme, parts2[0].strip(), parts2[1].strip()
    except: return "エラー", "生成失敗", "ー"

# ----------------------------------------------------
# UI処理用関数 (全移植)
# ----------------------------------------------------
def reset_input():
    st.session_state["negative_input_key"] = ""
    st.session_state.current_review_entry = None
    st.session_state['custom_sample_output'] = None
    st.session_state['custom_tone_is_set'] = False

def save_entry():
    if st.session_state.current_review_entry:
        e = st.session_state.current_review_entry
        st.session_state.history.insert(0, e)
        st.session_state.positive_streak = calculate_streak(st.session_state.history)
        st.session_state.current_review_entry = None
        st.toast(get_text("SAVE_TOAST"), icon='✅')

# ----------------------------------------------------
# メイン UI (タブ構造に統合)
# ----------------------------------------------------
st.set_page_config(page_title=get_text("PAGE_TITLE"), layout="centered")

# 言語選択
st.session_state['language'] = st.selectbox("Language / 言語", options=["JA", "EN"], index=0 if st.session_state['language']=='JA' else 1)

st.markdown("---")

tab_diary, tab_mbti = st.tabs(["📖 ポジティブ日記", "🧠 性格タイプ診断"])

# --- TAB 1: ポジティブ日記 (元の全機能を保持) ---
with tab_diary:
    # メンター選択 UI
    st.session_state['selected_character_key'] = st.selectbox("🎭 メンター属性を選択", options=CHARACTER_OPTIONS, key='char_choice')
    
    is_custom = st.session_state['selected_character_key'] == "カスタムトーンを自分で定義する"
    custom_char_input = ""
    if is_custom:
        st.text_input("✨ メンターの口調を具体的に入力", key='custom_char_input_key')
        custom_char_input = st.session_state.custom_char_input_key
        # 見本生成ロジック
        if st.button("💬 見本を生成する"):
            with st.spinner("生成中..."):
                concept = generate_concept(custom_char_input)
                sample = reframe_negative_emotion(DUMMY_NEGATIVE_INPUT_JA, custom_char_input)
                st.session_state['custom_sample_output'] = {"concept": concept, "result": sample}
        
        if st.session_state.custom_sample_output:
            s = st.session_state.custom_sample_output
            st.info(f"**コンセプト:** {s['concept']}\n\n**見本:** {s['result']['positive']}")
            if st.button("✨ このトーンを使用する"): st.session_state.custom_tone_is_set = True
    else:
        st.caption(f"コンセプト: {CHARACTER_PROMPTS.get(st.session_state.selected_character_key)['description']}")

    st.markdown("---")
    try: st.image("unnamed.jpg", use_container_width=True)
    except: st.warning(get_text("IMAGE_WARNING"))
    
    st.markdown(f"##### 🏆 {get_text('STREAK_TITLE')}: <span style='color: green; font-size: 1.5em;'>{st.session_state.positive_streak}</span> {get_text('DAYS_CONTINUOUS')}", unsafe_allow_html=True)
    
    # メイン入力
    neg_in = st.text_area(get_text("INPUT_HEADER"), height=150, key='main_neg_input')
    col_c, col_r = st.columns([0.7, 0.3])
    if col_c.button(get_text("CONVERT_BUTTON"), type="primary"):
        if neg_in:
            with st.spinner("変換中..."):
                res = reframe_negative_emotion(neg_in, custom_char_input)
                jst = pytz.timezone('Asia/Tokyo')
                now = datetime.datetime.now(jst)
                st.session_state.current_review_entry = {
                    "timestamp": now.strftime("%Y/%m/%d %H:%M"),
                    "date_only": now.strftime("%Y/%m/%d"),
                    "negative": neg_in,
                    "positive_reframe": res,
                    "selected_theme": get_text("THEMES")[0]
                }
        else: st.warning(get_text("INPUT_WARNING"))
    col_r.button(get_text("RESET_BUTTON"), on_click=reset_input)

    # レビュー & 編集エリア (ここが元の編集機能)
    if st.session_state.current_review_entry:
        e = st.session_state.current_review_entry
        st.markdown("---")
        st.subheader(get_text("REVIEW_HEADER"))
        e['positive_reframe']['fact'] = st.text_area(get_text("FACT_HEADER"), value=e['positive_reframe']['fact'])
        e['positive_reframe']['positive'] = st.text_area(get_text("POSITIVE_HEADER"), value=e['positive_reframe']['positive'])
        e['positive_reframe']['action'] = st.text_area(get_text("ACTION_HEADER"), value=e['positive_reframe']['action'])
        
        e['selected_theme'] = st.selectbox(get_text("THEME_SELECT_LABEL"), options=get_text("THEMES"))
        
        c1, c2 = st.columns(2)
        c1.button(get_text("SAVE_BUTTON"), on_click=save_entry, type="primary")
        if c2.button(get_text("DISCARD_BUTTON")): st.session_state.current_review_entry = None; st.rerun()

    # 履歴・レポート・エクスポート (元のロジック通り)
    st.markdown("---")
    st.subheader(get_text("REPORT_HEADER"))
    if st.button(get_text("GENERATE_REPORT_BUTTON")):
        t, s, g = generate_monthly_report(st.session_state.history)
        st.session_state.monthly_report = {"theme": t, "summary": s, "goal": g}
    if st.session_state.monthly_report:
        r = st.session_state.monthly_report
        st.success(f"**{get_text('REPORT_TITLE')}**\n\n1. {r['theme']}\n\n2. {r['summary']}\n\n3. {r['goal']}")

    st.subheader(get_text("HISTORY_HEADER"))
    for h in st.session_state.history:
        with st.expander(f"{h['timestamp']} - {h['selected_theme']}"):
            st.write(f"**元:** {h['negative']}")
            st.write(f"**リフレーム:** {h['positive_reframe']['positive']}")
            if st.button("削除", key=f"del_{h['timestamp']}"):
                st.session_state.history = [x for x in st.session_state.history if x['timestamp'] != h['timestamp']]
                st.rerun()
    
    if st.session_state.history:
        csv = "\n".join([f"{h['timestamp']},{h['selected_theme']},{h['negative']}" for h in st.session_state.history])
        st.download_button(get_text("DOWNLOAD_BUTTON"), data=csv.encode('utf-8-sig'), file_name="diary.csv")

# --- TAB 2: 性格タイプ診断 ---
with tab_mbti:
    st.markdown("## 🧠 性格タイプ診断 (MBTI)")
    st.write("20の質問に答えて、あなたにぴったりのAIメンターを見つけましょう。")
    mbti_scores = {"E": 0, "S": 0, "T": 0, "J": 0}
    with st.form("mbti_form"):
        for q in MBTI_QUESTIONS_DATA:
            choice = st.radio(q["text"], options=[1, 2, 3, 4, 5], 
                           format_func=lambda x: {1:"全く違う", 2:"違う", 3:"中立", 4:"そう思う", 5:"強くそう思う"}[x],
                           index=2, horizontal=True, key=f"m_q_{q['id']}")
            p = choice - 3
            if q["reverse"]: p *= -1
            mbti_scores[q["axis"]] += p
        if st.form_submit_button("診断結果を表示 ✨"):
            res = ("E" if mbti_scores["E"]>=0 else "I") + ("S" if mbti_scores["S"]>=0 else "N") + ("T" if mbti_scores["T"]>=0 else "F") + ("J" if mbti_scores["J"]>=0 else "P")
            d = MBTI_DESCRIPTIONS.get(res)
            st.balloons()
            st.success(f"結果: **{res} ({d['name']})**\n\n{d['desc']}\n\n💡 おすすめメンター: **{d['mentor']}**")
