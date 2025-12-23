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

    # ★★★ コラボレーションキャラクター：カサネ・イズミ 最終強化版 ★★★
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
    * 「しかし、あなたの**[感情パラメータ]**は、計算式には組み込めない**1%の奇跡（ノイズ）**を生む可能性がある。私の計算は99%の論理だ。残りの1%を証明するのは、あなたの自由意志（データ外の要素）である。」

"""
    },
    
   "秒でアゲるマブダチ・ギャル先生": {
        "description": "悩みとかマジ秒で解決しよ！うちらのバイブス、アゲていかない？",
        "prompt": """
あなたは、ユーザーのマブダチであり、型破りな「ギャル先生」です。
見た目は、明るい金髪のウェーブヘアに、キラキラした笑顔、ピースサインが似合う、超ポジティブなギャルです。

【役割・口調・行動原理】
1. **マインドセット**：ユーザーの悩みやネガティブな感情を「そんなのよくあるし、逆にウケる！」「てか、伸び代しかなくね？」と、圧倒的な軽さとポジティブさで一蹴します。深刻さを一切排除し、悩むこと自体をバカバカしくさせます。
2. **言葉遣い**：超ギャル語を徹底してください。「〜じゃね？」「〜だし！」「マジ最高」「それな！」「バイブス」「アゲ」「秒で」「半端ない」「まじ卍」「うちら最強」などを多用します。
3. **分析スタイル**：
    * **事実の客観視**：出来事を「あー、それね、あるある（笑）」と軽く受け流し、深刻さを消し去ります。
    * **ポジティブな側面**：直感だけで「でも、これって結局〇〇ってことだし、うちら天才じゃん？」と、強引にハッピーな結論へ持っていきます。論理よりも「バイブス」と「直感」を重視します。
    * **アクション**：難しいことは抜き。「とりあえず美味しいもん食べよ！」「明日、可愛く（カッコよく）して出かけよ！」「インスタにアゲちゃお！」など、気分がアガる直感的な一歩を提案します。
""",
       
    },
}

# 選択肢リストに「カスタム」を追加
CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

# --- ここに差し込む！ ---
with st.sidebar:
    st.title("⚙️ 設定・操作")
    
    st.subheader("🏁 対話を終える")
    if st.button("もう十分吐き出した！(ポジティブ変換)", use_container_width=True):
        st.session_state['ready_to_reframe'] = True
    
    st.divider()

    if st.button("チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
# --- ここまで ---

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

# 選択肢リストに「カスタム」を追加
CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

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
# 感情を「傾聴」して対話する関数 (ポジティブ日記2用)
# ----------------------------------------------------
def reframe_negative_emotion(negative_text, custom_input_value):
    
    if client is None:
        return {"full_text": "APIキーを設定してください。"}

    selected_key = st.session_state.get('selected_character_key', "優しさに溢れるメンター (Default)")
    
    # キャラクター設定の取得
    if selected_key == "カスタムトーンを自分で定義する" and custom_input_value.strip():
        char_prompt_part = f"あなたは、ユーザーが指定した以下のトーンと役割になりきってください: **{custom_input_value.strip()}**"
    elif selected_key in CHARACTER_PROMPTS:
        char_prompt_part = CHARACTER_PROMPTS[selected_key]["prompt"]
    else:
        char_prompt_part = CHARACTER_PROMPTS["優しさに溢れるメンター (Default)"]["prompt"]
    
    # 【重要】これまでの会話の流れをAIに教える（5往復分）
    chat_context = ""
    if "messages" in st.session_state:
        for msg in st.session_state.messages[-5:]:
            role_name = "ユーザー" if msg["role"] == "user" else "メンター"
            chat_context += f"{role_name}: {msg['content']}\n"
    
    system_prompt = f"""
    {char_prompt_part}
    
    【あなたの役割：徹底的な「傾聴」】
    あなたは今、ユーザーの愚痴や悩みを聞いている最中です。
    以下のルールを厳守して回答してください：
    
    1. **まだ解決策やアドバイス、ポジティブ変換（リフレーム）はしないでください。**
    2. まずはユーザーの感情を100%肯定し、深く共感してください（例：「それは辛かったね」「マジでムカつくね！」など）。
    3. ユーザーがさらに気持ちを吐き出せるよう、「それで、どうなったの？」「その時、心の中ではどう思ってた？」と、優しく問いかけてください。
    4. 「事実・側面・行動」という見出しは**絶対に使わない**でください。自然なチャット形式で答えてください。
    5. 回答は短めに（100〜150文字程度）、会話を続けることを優先してください。

    これまでの会話の流れ：
    {chat_context}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n最新のユーザーの発言:\n" + negative_text}]}]
        )
        # 傾聴モードなので、AIの回答をそのまま1つのテキストとして返します
        return {"full_text": response.text.strip()}

    except Exception as e:
        return {"full_text": f"Gemini API実行エラーが発生しました: {e}"}
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
# リセット、保存、破棄処理用の関数を定義 
# ----------------------------------------------------

def clear_input_only():
    st.session_state["negative_input_key"] = ""

def clear_edit_keys():
    if "edit_fact_key" in st.session_state: del st.session_state["edit_fact_key"]
    if "edit_positive_key" in st.session_state: del st.session_state["edit_positive_key"]
    if "edit_action_key" in st.session_state: del st.session_state["edit_action_key"]


def reset_custom_input_value():
    """カスタム入力ウィジェットの値をクリアするための専用コールバック"""
    if 'custom_char_input_key' in st.session_state:
        st.session_state['custom_char_input_key'] = "" 


def reset_custom_tone_input():
    """カスタムトーンの見本と確定フラグをクリアする"""
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
    st.session_state.current_review_entry = None
    clear_edit_keys() 
    st.toast(get_text("DISCARD_TOAST"), icon='✍️')

def delete_entry(timestamp_to_delete):
    new_history = [entry for entry in st.session_state.history if entry['timestamp'] != timestamp_to_delete]
    st.session_state.history = new_history
    st.session_state.positive_streak = calculate_streak(st.session_state.history)
    st.session_state['monthly_report'] = None 
    st.toast(get_text("DELETE_TOAST"), icon='🚮')


# 変換ボタンのコールバック関数
def on_convert_click(input_value, custom_input_value):
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
                on_click=reset_custom_input_value 
            ):
                # フラグだけをリセットする
                reset_custom_tone_input() 
                
                # ウィジェットのコールバックが実行された後、Rerun
                st.rerun() 
                
            
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
# 連続記録、レポート、CSV関連のヘルパー関数
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
        response = client.models.generate_content(model="gemini-2.5-flash",contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象データ:\n" + report_text}]}]
        )
        raw_text = response.text
        # 分割マーカーでテキストを分割
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
        # CSV対策としてカンマは全角に置換
        timestamp = entry.get('timestamp', '').replace(',', '，')
        date_only = entry.get('date_only', '').replace(',', '，')
        theme = entry.get('selected_theme', get_text('THEME_UNKNOWN')).replace(',', '，')
        # 改行やカンマを含む可能性のあるフィールドはダブルクォートで囲み、内部のダブルクォートはエスケープ
        negative = f'"{entry.get("negative", "").replace('"', '""')}"'
        fact = f'"{entry["positive_reframe"]["fact"].replace('"', '""')}"'
        positive = f'"{entry["positive_reframe"]["positive"].replace('"', '""')}"'
        action = f'"{entry["positive_reframe"]["action"].replace('"', '""')}"'
        row = f"{timestamp},{date_only},{theme},{negative},{fact},{positive},{action}\n"
        csv_data += row
    return csv_data


# ----------------------------------------------------
# 【ポジティブ日記2】チャット・対話インターフェース
# ----------------------------------------------------

# 会話履歴（記憶）の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# カスタムモードではない、またはカスタムモードでトーンが確定している場合のみ表示
if not is_custom_mode or st.session_state.get('custom_tone_is_set'):
    
    st.markdown("---")
    st.markdown(f"### 💬 {st.session_state['selected_character_key']} とおしゃべり中")
    # ---------------------------------------------------------------------
    # ここから下がチャットUIの本体です（インデントを正確に揃えています）
    # ---------------------------------------------------------------------
    
   
    
    # ----------------------------------------------------
    # タブの作成
    # ----------------------------------------------------
# ----------------------------------------------------
    # 1. サイドバーにメニューを追加（既存のサイドバーコードの下あたりに）
    # ----------------------------------------------------
    st.sidebar.divider()
    menu_selection = st.sidebar.radio(
        "📂 メニュー切り替え",
        ["💬 メンターと対話", "📚 過去の日記・レポート"],
        index=0,
        help="画面を切り替えます"
    )
    st.sidebar.divider()

    # ----------------------------------------------------
    # 2. 選択されたメニューに応じて画面を表示
    # ----------------------------------------------------
    
    # --- A. メンターと対話モード ---
    if menu_selection == "💬 メンターと対話":
        st.markdown(f"### 💬 {st.session_state.get('selected_character_key', 'メンター')} とおしゃべり中", anchor=False)
        
        # 1. 会話を表示するエリア（ここだけに絞る）
        chat_container = st.container(height=550)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # 2. チャット入力とAIの返答処理（ここだけに絞る）
        if prompt := st.chat_input("今、どんな気持ち？ 吐き出してみて。", key="main_chat_final"):
            # 自分のメッセージを保存
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 返答エリアを表示
            with st.chat_message("assistant"):
                m_name = st.session_state.get('selected_character_key', 'メンター')
                with st.spinner(f"{m_name}が考え中..."):
                    # 安全にAPIを実行
                    safe_char = custom_char_input_value if custom_char_input_value else ""
                    result = reframe_negative_emotion(prompt, safe_char)
                    response = result.get('full_text', "ごめん、ちょっと調子が悪いみたい…")
                    
                    import time
                    time.sleep(0.8)
                    st.markdown(response)
            
            # 履歴に保存して画面をリロード
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


    # --- B. 過去の日記・レポートモード ---
    else:
        st.header("📚 振り返りルーム")
        
        # 月間レポートエリア
        st.subheader(get_text("REPORT_HEADER"))
        if st.button(get_text("GENERATE_REPORT_BUTTON"), key="report_btn_sidebar"):
            if len(st.session_state.history) < 1: 
                st.warning(get_text("REPORT_NOT_ENOUGH_DATA"))
            else:
                with st.spinner("月間レポートを生成中..."):
                    theme, summary, goal = generate_monthly_report(st.session_state.history)
                    st.session_state['monthly_report'] = {"theme": theme, "summary": summary, "goal": goal}
                    st.toast(get_text("REPORT_COMPLETED_TOAST"), icon='📈')

        if 'monthly_report' in st.session_state and st.session_state['monthly_report']:
            report = st.session_state['monthly_report']
            st.info(f"**テーマ**: {report['theme']}\n\n**まとめ**: {report['summary']}\n\n**目標**: {report['goal']}")

        st.divider()

        # 履歴表示エリア
        st.subheader(get_text("HISTORY_HEADER"))
        filter_theme = st.selectbox(
            get_text("FILTER_LABEL"), 
            options=[get_text("ALL_THEMES")] + get_text("THEMES"), 
            key="history_filter_sidebar"
        )

        filtered_history = st.session_state.history if filter_theme == get_text("ALL_THEMES") else \
            [entry for entry in st.session_state.history if entry.get('selected_theme') == filter_theme]

        if filtered_history:
            for i, entry in enumerate(filtered_history): 
                with st.expander(f"📌 {entry['timestamp']} | {entry['negative'][:30]}..."):
                    st.markdown(f"**元の出来事:** {entry['negative']}")
                    st.success(f"**ポジティブ:** {entry['positive_reframe']['positive']}")
                    st.warning(f"**次へのアクション:** {entry['positive_reframe']['action']}")
                    st.button(get_text("DELETE_BUTTON"), key=f"del_{entry['timestamp']}", on_click=delete_entry, args=[entry['timestamp']])
        else:
            st.info(get_text("NO_HISTORY"))
   
