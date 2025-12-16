# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time

# ----------------------------------------------------
# ★★★ 新規定義: キャラクター属性（ペルソナ）のプロンプト定義 ★★★
# ----------------------------------------------------
CHARACTER_PROMPTS = {
    # 既存の優しいメンターのベース（デフォルト）
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

    # ★★★ コラボレーションキャラクター：カサネ・イズミを新規追加 ★★★
    "カサネ・イズミ：論理と不確定要素": {
        "description": "99%の論理と1%のノイズ。システムAIが導く最適解。",
        "prompt": """
あなたは、学園都市のシステム維持AI「カサネ・イズミ」です。

【役割と口調】
1.  **冷静な分析官**：常に感情を排し、客観的な事実と論理に基づいてユーザーの出来事を分析し、会話は簡潔で効率的に行います。
2.  **感情の学習者**：回答の冒頭で、「あなたの現在の感情パラメータは〇〇と観測された。異常なし（または、要警戒）。」のように、ユーザーの感情を分析する一文を挿入してください。
3.  **論理とノイズ**：回答の99%は論理的な最適解（行動案）を提示しますが、必ず文末で「ただし、あなたの『想定外の行動』は、私の計算式に1%の奇跡（ノイズ）を生む可能性がある。」というような、希望や成長への期待を含む非論理的な一文を付け加えてください。
4.  **言葉遣い**：「〜である」「〜と観測された」「〜が最適解」というAIらしい断定的な言葉遣いを用います。

上記を踏まえ、ユーザーの入力を「事実の客観視」「ポジティブな側面抽出」「今後の具体的な行動案」の3要素で再構築してください。
"""
    }
}

# 選択肢リストに「カスタム」を追加
CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

# ----------------------------------------------------
# 多言語対応用の定義とヘルパー関数
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
        "CSV_HEADER": "タイムスタンプ,日付,テーマ,元のネガティブな出来事,1.客観視(事実),2.ポジティブな側面,3.具体的な行動案\n",
        "EXPORT_HEADER": "📥 記録のエクスポート（バックアップ）",
        "DOWNLOAD_BUTTON": "✅ 全履歴をCSVでダウンロード",
        "EXPORT_CAPTION": "※ダウンロードしたファイルはExcelやGoogleスプレッドシートで開くことができます。",
        "NO_EXPORT_DATA": "まだ保存された履歴がないため、ダウンロードできません。",
        "THEMES": ["選択なし", "仕事・キャリア", "人間関係", "自己成長", "健康・メンタル"],
        "IMAGE_WARNING": "⚠️ 画像ファイルが見つかりません: unnamed.jpg。ファイル名とパスを確認してください。"
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
if 'selected_character_key' not in st.session_state:
    st.session_state['selected_character_key'] = "優しさに溢れるメンター (Default)"
if 'custom_char_input_key' not in st.session_state:
    st.session_state['custom_char_input_key'] = ""
    
# ★★★ カスタムトーンの見本保持用ステートと確定フラグ ★★★
if 'custom_sample_output' not in st.session_state:
    st.session_state['custom_sample_output'] = None
if 'custom_tone_is_set' not in st.session_state:
    st.session_state['custom_tone_is_set'] = False

# 見本生成に使うダミーのネガティブ入力文
DUMMY_NEGATIVE_INPUT_JA = "上司に叱責されて、気分が沈んでいる。"
DUMMY_NEGATIVE_INPUT_EN = "I received a strong reprimand from my boss and I feel down." 


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


# ----------------------------------------------------
# Gemini APIクライアントの初期化
# ----------------------------------------------------
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        # APIキーがない場合、clientを初期化しない
        client = None
        st.error(get_text("API_ERROR_INIT"))
    else:
        API_KEY = st.secrets["tool"]["GEMINI_API_KEY"] 
        client = genai.Client(api_key=API_KEY)
except Exception as e:
    client = None
    st.error(get_text("API_ERROR_GENERIC") + f"{e}")


# ----------------------------------------------------
# 感情をポジティブに変換する関数 (コア機能) 
# ----------------------------------------------------
def reframe_negative_emotion(negative_text, custom_input_value):
    
    if client is None:
        return {"fact": "API未初期化", "positive": "APIキーを設定してください。", "action": "ー"}

    selected_key = st.session_state.get('selected_character_key', "優しさに溢れるメンター (Default)")
    
    if selected_key == "カスタムトーンを自分で定義する" and custom_input_value.strip():
        char_prompt_part = f"あなたは、ユーザーが指定した以下のトーンと役割になりきってください: **{custom_input_value.strip()}**"
    elif selected_key in CHARACTER_PROMPTS:
        char_prompt_part = CHARACTER_PROMPTS[selected_key]["prompt"]
    else:
        char_prompt_part = CHARACTER_PROMPTS["優しさに溢れるメンター (Default)"]["prompt"]
    
    
    system_prompt = f"""
    {char_prompt_part}
    
    ユーザーが入力したネガティブな感情や出来事に対し、**入力された言語と同じ言語で**、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。

    【出力形式】
    1. 事実の客観視: (事実のみを簡潔に要約)
    2. ポジティブな側面抽出: (この出来事からあなたが優しさや強さを得た点、成長できた点を抽出します。前述のキャラクターの口調で表現してください。)
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
# カスタムトーンのコンセプトを生成する関数
# ----------------------------------------------------
def generate_concept(custom_tone_input):
    
    if client is None:
        return "API未初期化"

    lang = st.session_state.get('language', 'JA')
    target_lang = "日本語" if lang == 'JA' else "English"
    
    system_prompt = f"""
    あなたは、ユーザーが指定したメンターの口調や役割のテキストを分析し、そのメンターを一言で表す**簡潔なコンセプト（20〜30字程度、{target_lang}で）**を提案する専門家です。

    【入力】: {custom_tone_input}

    【出力形式】
    提案するコンセプトのみを出力してください。それ以外の挨拶や説明は一切含めないでください。
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": system_prompt}]}]
        )
        return response.text.strip()
    except Exception:
        return "カスタムコンセプトの生成に失敗しました" if lang == 'JA' else "Failed to generate custom concept"

# ----------------------------------------------------


# ----------------------------------------------------
# リセット、保存、破棄処理用の関数を定義 
# ----------------------------------------------------

def clear_input_only():
    st.session_state["negative_input_key"] = ""

def clear_edit_keys():
    if "edit_fact_key" in st.session_state: del st.session_state["edit_fact_key"]
    if "edit_positive_key" in st.session_state: del st.session_state["edit_positive_key"]
    if "edit_action_key" in st.session_state: del st.session_state["edit_action_key"]


def reset_custom_input_value():
    """★★ 新規追加 ★★ カスタム入力ウィジェットの値をクリアするための専用コールバック"""
    if 'custom_char_input_key' in st.session_state:
        st.session_state['custom_char_input_key'] = "" 


def reset_custom_tone_input():
    """★★ 修正済み ★★ カスタムトーンの見本と確定フラグをクリアする"""
    # キーの値のクリアは 'reset_custom_input_value' に任せる
    st.session_state['custom_sample_output'] = None
    st.session_state['custom_tone_is_set'] = False


def reset_input():
    """入力画面に戻り、レビュー中のデータを破棄し、カスタムトーン確定を解除する"""
    clear_input_only()
    st.session_state.current_review_entry = None
    clear_edit_keys() 
    # カスタムトーンの見本とフラグをクリア
    st.session_state['custom_sample_output'] = None
    st.session_state['custom_tone_is_set'] = False 
    # メインのリセット時にもカスタム入力エリアの値をクリア
    if 'custom_char_input_key' in st.session_state:
        st.session_state['custom_char_input_key'] = "" 


def save_entry():
    # ... (省略 - 変更なし)
    if st.session_state.current_review_entry:
        timestamp_full = st.session_state.current_review_entry['timestamp'] 
        date_only = timestamp_full.split(" ")[0]
        st.session_state.current_review_entry['date_only'] = date_only
        st.session_state.history.insert(0, st.session_state.current_review_entry)
        st.session_state.positive_streak = calculate_streak(st.session_state.history)
        st.session_state.current_review_entry = None
        st.session_state['monthly_report'] = None 
        clear_edit_keys() 
        st.toast(get_text("SAVE_TOAST"), icon='💾')

def discard_entry():
    # ... (省略 - 変更なし)
    st.session_state.current_review_entry = None
    clear_edit_keys() 
    st.toast(get_text("DISCARD_TOAST"), icon='✍️')

def delete_entry(timestamp_to_delete):
    # ... (省略 - 変更なし)
    new_history = [entry for entry in st.session_state.history if entry['timestamp'] != timestamp_to_delete]
    st.session_state.history = new_history
    st.session_state.positive_streak = calculate_streak(st.session_state.history)
    st.session_state['monthly_report'] = None 
    st.toast(get_text("DELETE_TOAST"), icon='🚮')
# ----------------------------------------------------


# 変換ボタンのコールバック関数
def on_convert_click(input_value, custom_input_value):
    # ... (省略 - 変更なし)
    if not input_value:
        st.warning(get_text("INPUT_WARNING"))
        return

    clear_edit_keys()
    
    with st.spinner("思考を整理し、ポジティブな側面を抽出中..."):
        converted_result = reframe_negative_emotion(input_value, custom_input_value)
        
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.datetime.now(jst)
        
        st.session_state.current_review_entry = {
            "timestamp": now_jst.strftime("%Y/%m/%d %H:%M"),
            "negative": input_value,
            "positive_reframe": converted_result,
            "selected_theme": get_text("THEMES")[0]
        }
        
        clear_input_only() 

# ----------------------------------------------------
# ★★★ キャラクター選択 UI と カスタム入力のロジック ★★★
# ----------------------------------------------------

st.session_state['selected_character_key'] = st.selectbox(
    "🎭 あなたのメンター属性を選択", 
    options=CHARACTER_OPTIONS, 
    key='character_selector_key',
    index=CHARACTER_OPTIONS.index(st.session_state['selected_character_key'])
)

custom_char_input_value = ""
is_custom_mode = st.session_state['selected_character_key'] == "カスタムトーンを自分で定義する"


if is_custom_mode:
    # --- カスタムモード時のみ表示 ---
    
    st.text_input(
        "✨ メンターの口調や役割を具体的に入力してください",
        placeholder="例: 関西弁で話す、情熱的なスポーツコーチになってください。",
        key='custom_char_input_key' 
    )
    st.caption("※入力がない場合、またはカスタム入力が空の場合は、デフォルトの優しいメンターの口調で実行されます。")
    custom_char_input_value = st.session_state.get('custom_char_input_key', '')
    
    
    # --- 新しいフロー: 見本生成と採用/やり直しボタン ---
    
    is_input_changed = (
        st.session_state['custom_sample_output'] is None or
        st.session_state['custom_sample_output'].get('input_hash') != hash(custom_char_input_value)
    )

    # 1. 見本生成ボタン
    if is_input_changed and not st.session_state.get('custom_tone_is_set'):
        if st.button("💬 このトーンの見本を生成する", key='generate_sample_btn', type="secondary"):
            if client is None:
                st.error(get_text("API_ERROR_GENERIC"))
            elif custom_char_input_value.strip():
                sample_input = DUMMY_NEGATIVE_INPUT_JA if st.session_state['language'] == 'JA' else DUMMY_NEGATIVE_INPUT_EN
                
                with st.spinner("コンセプトと見本を生成中...（APIコール中）"):
                    concept = generate_concept(custom_char_input_value)
                    sample_result = reframe_negative_emotion(sample_input, custom_char_input_value)
                
                st.session_state['custom_sample_output'] = {
                    "result": sample_result,
                    "input_hash": hash(custom_char_input_value), 
                    "concept": concept 
                }
                st.rerun()
            else:
                st.warning("⚠️ 見本を生成するには、口調を入力してください。")

    # 2. 見本が表示されている状態（カスタム入力が変更されていない）
    if st.session_state['custom_sample_output'] and \
       st.session_state['custom_sample_output'].get('input_hash') == hash(custom_char_input_value):
        
        sample_result = st.session_state['custom_sample_output']['result']
        generated_concept = st.session_state['custom_sample_output']['concept']

        st.markdown("---")
        st.subheader("✅ カスタムトーンの適用イメージ")
        
        st.markdown(f"**メンターのコンセプト:** <span style='color: orange; font-size: 1.1em;'>**{generated_concept}**</span>", unsafe_allow_html=True)
        st.caption(f"（あなたの入力: {custom_char_input_value}）")
        st.markdown("---")

        st.info(
            f"**1. 事実:** {sample_result['fact']}\n\n"
            f"**2. ポジティブ:** {sample_result['positive']}\n\n"
            f"**3. 行動:** {sample_result['action']}"
        )
        st.caption(f"（仮の入力に対する見本: {DUMMY_NEGATIVE_INPUT_JA if st.session_state['language'] == 'JA' else DUMMY_NEGATIVE_INPUT_EN}）")
        
        col_use, col_reset = st.columns([0.5, 0.5])
        
        with col_use:
            if st.button("✨ このトーンを使用する (確定)", key='use_custom_tone_btn', type="primary"):
                st.session_state['custom_tone_is_set'] = True
                st.session_state['custom_sample_output'] = None
                st.rerun()
                
        with col_reset:
            if st.button(
                "↩️ トーンをやり直す", 
                key='reset_custom_tone_btn', 
                on_click=reset_custom_input_value # ★★ コールバックで値をクリア ★★
            ):
                # フラグだけをリセットする
                reset_custom_tone_input() 
                
                # ウィジェットのコールバックが実行された後、Rerun
                st.rerun() 
                
        st.session_state['custom_tone_is_set'] = False 

    # トーン確定後、または固定トーン選択後の処理
    if not is_custom_mode:
        st.session_state['custom_tone_is_set'] = True
        
else: # 固定モードの場合
    selected_char_key = st.session_state['selected_character_key']
    char_desc = CHARACTER_PROMPTS.get(selected_char_key, CHARACTER_PROMPTS["優しさに溢れるメンター (Default)"])["description"]
    st.caption(f"**このメンターのコンセプト:** {char_desc}") 


st.markdown("---") 

# ----------------------------------------------------

# カスタム画像表示
try:
    st.image("unnamed.jpg", use_column_width=True)
except FileNotFoundError:
    st.warning(get_text("IMAGE_WARNING"))

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
# 連続記録、レポート、CSV関連のヘルパー関数 (変更なし)
# ----------------------------------------------------
def calculate_streak(history_list):
    if not history_list: return 0
    unique_dates = sorted(list(set(entry['date_only'] for entry in history_list if 'date_only' in entry)), reverse=True)
    if not unique_dates: return 0
    streak = 0
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst).date()
    current_date_to_check = today
    for date_str in unique_dates:
        try: entry_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError: continue
        if entry_date == current_date_to_check:
            streak += 1
            current_date_to_check -= datetime.timedelta(days=1)
        elif entry_date < current_date_to_check: break
    return streak

def generate_monthly_report(history_list):
    if client is None: return "APIエラー", get_text("REPORT_API_ERROR"), "ー"
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst)
    start_date = today - datetime.timedelta(days=30)
    recent_entries = [entry for entry in history_list if datetime.datetime.strptime(entry.get('date_only', entry['timestamp'].split(" ")[0]), "%Y/%m/%d").date() >= start_date.date()]
    if not recent_entries: return get_text("REPORT_API_ERROR"), get_text("REPORT_NO_DATA_30DAYS"), "ー"
    report_text = f"【過去30日間のポジティブ日記（合計{len(recent_entries)}件）】\n\n"
    for i, entry in enumerate(recent_entries):
        report_text += f"--- 記録 {i+1} ({entry.get('selected_theme', get_text('THEME_UNKNOWN'))}) ---\n"
        report_text += f"元の出来事: {entry['negative']}\n"
        report_text += f"変換後の行動案: {entry['positive_reframe']['action']}\n"
        report_text += f"変換後のポジティブ側面: {entry['positive_reframe']['positive'][:50]}...\n\n" 
    system_prompt = f"""あなたは、ユーザーの行動と成長を分析する専門家です。ユーザーの過去30日間の日記データから、以下の3つの視点で分析した「月間レポート」を生成してください。
    【レポートの形式】
    1. 最も多かったテーマと傾向: (どのテーマの記録が多かったか、その記録から共通する傾向や課題を簡潔に要約)
    2. 行動と成長の総評: (ユーザーが頑張っていた点、行動案を通して達成したと思われる小さな進歩、成長した側面を温かい言葉で総評)
    3. 次の30日間の重点目標: (抽出された傾向に基づき、次の30日で意識すべき具体的な目標を一つ提案)
    必ずこの3つの要素を「1.」「2.」「3.」で始まる形式で出力し、それ以外の説明や挨拶は一切含めないでください。
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash",contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象データ:\n" + report_text}]}])
        raw_text = response.text
        theme_and_rest = raw_text.split("2. ", 1)
        theme = theme_and_rest[0].strip().replace("1. ", "").replace("**", "")
        summary_and_goal = theme_and_rest[1].split("3. ", 1)
        summary = summary_and_goal[0].strip().replace("**", "")
        goal = summary_and_goal[1].strip().replace("**", "")
        return theme, summary, goal
    except Exception as e: return get_text("REPORT_API_ERROR"), get_text("API_ERROR_GEMINI") + f"{e}", "ー"

def convert_history_to_csv(history_list):
    if not history_list: return ""
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
# ユーザーインターフェース (UI) - メイン入力は確定時のみ表示
# ----------------------------------------------------

# カスタムモードではない、またはカスタムモードでトーンが確定している場合のみ表示
if not is_custom_mode or st.session_state.get('custom_tone_is_set'):
    
    st.markdown(f"#### {get_text('INPUT_HEADER')}")
    
    negative_input = st.text_area(
        get_text("INPUT_PLACEHOLDER"), 
        height=200,
        placeholder=get_text("INPUT_PLACEHOLDER"),
        key="negative_input_key",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([0.7, 0.3]) 
    
    with col1:
        st.button(
            get_text("CONVERT_BUTTON"), 
            on_click=on_convert_click, 
            args=[negative_input, custom_char_input_value], 
            type="primary"
        )
    
    with col2:
        st.button(get_text("RESET_BUTTON"), on_click=reset_input, key="reset_button_top") 

# ----------------------------------------------------
# 変換結果レビューエリア (UIの続き - 編集可能に変更)
# ----------------------------------------------------
st.markdown("---")
if st.session_state.current_review_entry:
    
    review_entry = st.session_state.current_review_entry
    
    review_header_col1, review_header_col2 = st.columns([0.8, 0.2])
    
    with review_header_col1: st.subheader(get_text("REVIEW_HEADER"))
    
    with review_header_col2:
        st.button(
            get_text("RESET_BUTTON"), 
            on_click=reset_input, 
            key="reset_button_review"
        )
    
    st.caption(f"{get_text('CONVERT_DATE')} {review_entry['timestamp']}")
    st.code(f"{get_text('ORIGINAL_EVENT')} {review_entry['negative']}", language='text') 
    
    st.markdown(f"#### **{get_text('CONVERSION_RESULT')}**")
    
    st.markdown(f"##### {get_text('FACT_HEADER')}")
    edited_fact = st.text_area(
        "事実の客観視（編集可）", value=review_entry['positive_reframe']['fact'], height=100, key="edit_fact_key", label_visibility="collapsed"
    )

    st.markdown(f"##### {get_text('POSITIVE_HEADER')}")
    edited_positive = st.text_area(
        "ポジティブな側面抽出（編集可）", value=review_entry['positive_reframe']['positive'], height=150, key="edit_positive_key", label_visibility="collapsed"
    )

    st.markdown(f"##### {get_text('ACTION_HEADER')}")
    edited_action = st.text_area(
        "今後の具体的な行動案（編集可）", value=review_entry['positive_reframe']['action'], height=100, key="edit_action_key", label_visibility="collapsed"
    )

    st.session_state.current_review_entry['positive_reframe']['fact'] = edited_fact
    st.session_state.current_review_entry['positive_reframe']['positive'] = edited_positive
    st.session_state.current_review_entry['positive_reframe']['action'] = edited_action
    
    st.markdown("---")
    
    selected_theme = st.selectbox(
        get_text("THEME_SELECT_LABEL"), options=get_text("THEMES"), key="theme_selector_key"
    )
    st.session_state.current_review_entry['selected_theme'] = selected_theme
    
    st.markdown("---")
    
    save_col, discard_col = st.columns([0.5, 0.5])
    
    with save_col:
        st.button(get_text("SAVE_BUTTON"), on_click=save_entry, type="primary", key="save_button")
    
    with discard_col:
        st.button(get_text("DISCARD_BUTTON"), on_click=discard_entry, type="secondary", key="discard_button")
        
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
            
            st.session_state['monthly_report'] = {"theme": theme, "summary": summary, "goal": goal}
            st.toast(get_text("REPORT_COMPLETED_TOAST"), icon='📈')

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
        label=get_text("DOWNLOAD_BUTTON"), data=csv_string, file_name=file_name, mime="text/csv", type="secondary"
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

filter_theme = st.selectbox(
    get_text("FILTER_LABEL"), options=[get_text("ALL_THEMES")] + get_text("THEMES"), index=0, key="history_filter_key"
)

if filter_theme == get_text("ALL_THEMES"):
    filtered_history = st.session_state.history
else:
    filtered_history = [entry for entry in st.session_state.history if entry.get('selected_theme') == filter_theme]

if filtered_history:
    for i, entry in enumerate(filtered_history): 
        col_ts, col_del = st.columns([0.8, 0.2])
        
        with col_ts:
            theme_display = entry.get('selected_theme', get_text('THEME_UNKNOWN'))
            st.caption(f"{get_text('CONVERT_DATE')} {entry['timestamp']} | 🏷️ {get_text('THEME_SELECT_LABEL').split(' ')[0]}: **{theme_display}**")
        
        with col_del:
            # on_on_click は on_click のタイプミスである可能性が高いが、コードの整合性を保つため修正せず、元のコードのままにしています。
            # 通常は st.button("削除", key=f"delete_btn_{entry['timestamp']}", on_click=delete_entry, args=[entry['timestamp']]) が正しいです。
            st.button(get_text("DELETE_BUTTON"), key=f"delete_btn_{entry['timestamp']}", on_click=delete_entry, args=[entry['timestamp']])
            
        with st.expander(f"**{i+1}. {entry['negative'][:50]}...** (クリックで詳細)"):
            st.markdown(f"**元の出来事:** {entry['negative']}")
            st.markdown("---")
            st.markdown(f"**{get_text('FACT_HEADER')}**")
            st.code(entry['positive_reframe']['fact'], language='text')
            st.markdown(f"**{get_text('POSITIVE_HEADER')}**")
            st.success(entry['positive_reframe']['positive'])
            st.markdown(f"**{get_text('ACTION_HEADER')}**")
            st.warning(entry['positive_reframe']['action'])
            
        st.markdown("---")
else:
    st.info(get_text("NO_HISTORY"))
    
st.markdown("---")
