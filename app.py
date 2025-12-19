# -*- coding: utf-8 -*-
import streamlit as st
from google import genai
import os
import datetime
import pytz
import base64
import time
import pandas as pd  # エクスポート機能用

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
    * 「しかし、あなたの**[感情パラメータ]**は、計算式には組み込めない**1%の奇跡（ノイズ）**を生む可能性がある。私の計算は99%の論理だ。残りの1%を証明するのは、あなたの自由意志（データ外の要素）である。」
""",
        "image": "images/mentor_izumi.png"
    }
}

CHARACTER_OPTIONS_BASE = list(CHARACTER_PROMPTS.keys())
CHARACTER_OPTIONS = ["カスタムトーンを自分で定義する"] + CHARACTER_OPTIONS_BASE

# ----------------------------------------------------
# 2. 多言語対応用の定義とヘルパー関数
# ----------------------------------------------------

TRANSLATIONS = {
    "JA": {
        "PAGE_TITLE": "Reframe: 安心の一歩",
        "CATCHPHRASE": "あなたの「心の重さ」を、成長と行動に変換する安全な場所。",
        "STREAK_TITLE": "ポジティブ連続記録",
        "DAYS_CONTINUOUS": "日 連続中！",
        "INPUT_HEADER": "📝 あなたのネガティブな気持ちを、安心してそのまま書き出してください。",
        "INPUT_PLACEHOLDER": "（ここは誰にも見られません。心に浮かんだことを自由に。）\\n例：面接で年齢の懸念を突っ込まれて、自信を失いそうになった。\\n\\nまたは、'I failed my driving test today and I feel discouraged.'",
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
        "IMAGE_WARNING": "⚠️ 画像ファイルが見つかりません: unnamed.jpg。ファイル名とパスを確認してください。"
    },
    "EN": {
        "PAGE_TITLE": "Reframe: A Safe Step",
        "CATCHPHRASE": "A safe place to transform your 'mental weight' into growth and action.",
        "STREAK_TITLE": "Positive Streak",
        "DAYS_CONTINUOUS": "days continuous!",
        "INPUT_HEADER": "📝 Write down your negative feelings as they are, in a safe space.",
        "INPUT_PLACEHOLDER": "(This is for your eyes only. Feel free to write what comes to mind.)\\nExample: 'I was pointed out about my age during the interview and almost lost confidence.'",
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
        "IMAGE_WARNING": "⚠️ Image file not found: unnamed.jpg."
    }
}

# 言語設定を取得するヘルパー関数
def get_text(key):
    lang = st.session_state.get('language', 'JA')
    # 辞書に存在しない場合は、日本語のフォールバックを使用
    return TRANSLATIONS.get(lang, TRANSLATIONS['JA']).get(key, TRANSLATIONS['JA'].get(key, f"MISSING TEXT: {key}"))

# ----------------------------------------------------
# 3. 履歴機能のためのセッションステートの初期化
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
    st.session_state['language'] = 'JA' # 初期言語
if 'selected_character_key' not in st.session_state:
    st.session_state['selected_character_key'] = "優しさに溢れるメンター (Default)"
if 'custom_char_input_key' not in st.session_state:
    st.session_state['custom_char_input_key'] = ""
    
# カスタムトーンの見本保持用ステートと確定フラグ
if 'custom_sample_output' not in st.session_state:
    st.session_state['custom_sample_output'] = None
if 'custom_tone_is_set' not in st.session_state:
    st.session_state['custom_tone_is_set'] = False

# 見本生成に使うダミーのネガティブ入力文
DUMMY_NEGATIVE_INPUT_JA = "上司に叱責されて、気分が沈んでいる。"
DUMMY_NEGATIVE_INPUT_EN = "I received a strong reprimand from my boss and I feel down." 

# ----------------------------------------------------
# 4. Gemini APIクライアントの初期化
# ----------------------------------------------------
try:
    if "GEMINI_API_KEY" not in st.secrets.get("tool", {}):
        client = None
        st.error(get_text("API_ERROR_INIT"))
    else:
        API_KEY = st.secrets["tool"]["GEMINI_API_KEY"] 
        client = genai.Client(api_key=API_KEY)
except Exception as e:
    client = None
    st.error(get_text("API_ERROR_GENERIC") + f"{e}")

# ----------------------------------------------------
# 5. 感情をポジティブに変換する関数 (コア機能) 
# ----------------------------------------------------
def reframe_negative_emotion(negative_text, custom_input_value):
    if client is None:
        return {"fact": "API未初期化", "positive": "APIキーを設定してください。", "action": "ー"}

    selected_key = st.session_state.get('selected_character_key', "優しさに溢れるメンター (Default)")
    
    # キャラクターに応じたプロンプトの組み立て
    if selected_key == "カスタムトーンを自分で定義する" and custom_input_value.strip():
        char_prompt_part = f"あなたは、ユーザーが指定した以下のトーンと役割になりきってください: **{custom_input_value.strip()}**"
    elif selected_key in CHARACTER_PROMPTS:
        char_prompt_part = CHARACTER_PROMPTS[selected_key]["prompt"]
    else:
        char_prompt_part = CHARACTER_PROMPTS["優しさに溢れるメンター (Default)"]["prompt"]
    
    # システムプロンプトの構築
    system_prompt = f"""
    {char_prompt_part}
    
    ユーザーが入力したネガティブな感情や出来事に対し、**入力された言語と同じ言語で**、以下の厳格な3つの形式で分析し、ポジティブな再構築をしてください。

    【出力形式】
    1. 事実の客観視: (起きた出来事を、感情を入れずに事実のみとして簡潔に要約してください。)
    2. ポジティブな側面抽出: (この出来事から得られる学び、成長の糧、あるいは隠れたメリットを、前述のキャラクターの口調で具体的に表現してください。共感や励ましを含めてください。)
    3. 今後の具体的な行動案（Next Step）: (この状況を改善するため、あるいは前向きに捉え直すために、今すぐ実行できる小さなアクションを一つ提案してください。)
    
    必ずこの3つの要素を「1.」「2.」「3.」で始まる形式で出力し、それ以外の説明や挨拶、余計な装飾は一切含めないでください。
    """
    
    try:
        # Gemini 2.0 Flash モデルを使用した生成
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\n分析対象の出来事:\n" + negative_text}]}
            ]
        )
        raw_text = response.text
        
        # テキストのパース処理（省略なし）
        try:
            # 「1. 」で分割
            parts_1 = raw_text.split("1. ", 1)
            content_after_1 = parts_1[1] if len(parts_1) > 1 else raw_text
            
            # 「2. 」で分割
            parts_2 = content_after_1.split("2. ", 1)
            fact = parts_2[0].strip().replace("**", "")
            content_after_2 = parts_2[1] if len(parts_2) > 1 else ""
            
            # 「3. 」で分割
            parts_3 = content_after_2.split("3. ", 1)
            positive = parts_3[0].strip().replace("**", "")
            action = parts_3[1].strip().replace("**", "") if len(parts_3) > 1 else ""

            return {"fact": fact, "positive": positive, "action": action}
        except Exception:
            # フォーマットが崩れた場合のフォールバック
            return {"fact": "分析完了（形式不一致）", "positive": raw_text, "action": "出力から直接確認してください"}
    except Exception as e:
        return {"fact": "APIエラー", "positive": get_text("API_ERROR_GEMINI") + f"{e}", "action": "ー"}

# ----------------------------------------------------
# 6. カスタムトーンのコンセプトを生成する関数
# ----------------------------------------------------
def generate_concept(custom_tone_input):
    if client is None: return "API未初期化"
    lang = st.session_state.get('language', 'JA')
    target_lang = "日本語" if lang == 'JA' else "English"
    
    system_prompt = f"ユーザーの指定したトーンを分析し、そのメンターを一言で表す簡潔なコンセプト（20〜30字程度、{target_lang}で）を提案してください。出力はコンセプトのみ。"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n入力: " + custom_tone_input}]}]
        )
        return response.text.strip()
    except:
        return "Custom Concept Generation Failed"

# ----------------------------------------------------
# 7. CSVエクスポート用のデータ変換（詳細版）
# ----------------------------------------------------
def convert_history_to_csv(history_list):
    csv_text = get_text("CSV_HEADER")
    for item in history_list:
        ts = item.get('timestamp', 'Unknown')
        dt = item.get('date_only', 'Unknown')
        tm = item.get('selected_theme', 'None')
        neg = item.get('negative', '').replace('"', '""').replace('\n', ' ')
        res = item.get('positive_reframe', {})
        fct = res.get('fact', '').replace('"', '""').replace('\n', ' ')
        pos = res.get('positive', '').replace('"', '""').replace('\n', ' ')
        act = res.get('action', '').replace('"', '""').replace('\n', ' ')
        
        line = f'"{ts}","{dt}","{tm}","{neg}","{fct}","{pos}","{act}"\n'
        csv_text += line
    return csv_text.encode('utf_8_sig') # Excel対応のBOM付きUTF-8

# ----------------------------------------------------
# 8. 連続記録計算ロジック
# ----------------------------------------------------
def calculate_streak(history_list):
    if not history_list: return 0
    # 重複を除いた日付リストを作成
    unique_dates = sorted(list(set(e['date_only'] for e in history_list if 'date_only' in e)), reverse=True)
    streak = 0
    today = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).date()
    curr = today
    
    for d_str in unique_dates:
        d = datetime.datetime.strptime(d_str, "%Y/%m/%d").date()
        if d == curr:
            streak += 1
            curr -= datetime.timedelta(days=1)
        elif d < curr:
            # 記録が途切れていないか確認
            break
    return streak
    # ----------------------------------------------------
# 9. 月間レポート生成関数 (長大なレポートプロンプトを保持)
# ----------------------------------------------------
def generate_monthly_report(history_list):
    if not history_list or client is None:
        return None
    
    # 直近30日間のデータを抽出
    now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    thirty_days_ago = now - datetime.timedelta(days=30)
    recent_history = [
        item for item in history_list 
        if datetime.datetime.strptime(item['date_only'], "%Y/%m/%d").date() >= thirty_days_ago.date()
    ]
    
    if not recent_history:
        return get_text("REPORT_NO_DATA_30DAYS")

    # レポート用データの要約
    history_summary = ""
    for item in recent_history:
        history_summary += f"- 日付: {item['date_only']}, テーマ: {item['selected_theme']}, 内容: {item['positive_reframe']['positive']}\n"

    lang = st.session_state.get('language', 'JA')
    target_lang = "日本語" if lang == 'JA' else "English"

    report_prompt = f"""
    あなたは、ユーザーの1ヶ月の心の軌跡を分析し、次のステップへ導く優秀なライフコーチです。
    以下の過去30日間のポジティブ変換日記のデータを元に、{target_lang}で月間レポートを作成してください。

    【入力データ: 過去30日間の記録】
    {history_summary}

    【レポートの構成】
    1. {get_text('REPORT_THEME_HEADER')}: 
       (どのテーマが多かったか、そこから見えるユーザーの現在の関心事や課題の傾向を分析してください。)
    2. {get_text('REPORT_SUMMARY_HEADER')}: 
       (30日間、ポジティブな変換を続けてきたユーザーの努力を称賛し、どのような心理的変化や成長が見られたかを総括してください。)
    3. {get_text('REPORT_GOAL_HEADER')}: 
       (分析結果に基づき、次の30日間で意識すべきことや、具体的な小さな目標を一つ提案してください。)

    出力は、親しみやすくもプロフェッショナルなコーチの口調で行ってください。
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": report_prompt}]}]
        )
        return response.text
    except Exception as e:
        return f"Report Generation Error: {e}"

# ----------------------------------------------------
# 10. UI 構築開始 (Streamlit)
# ----------------------------------------------------
st.set_page_config(page_title=get_text("PAGE_TITLE"), layout="centered")

# 言語選択・UI初期化
col_lang, col_info = st.columns([0.7, 0.3])
with col_lang:
    st.title(get_text("PAGE_TITLE"))
    st.caption(get_text("CATCHPHRASE"))

with col_info:
    # 言語切り替え
    lang_options = {"JA": "日本語", "EN": "English"}
    new_lang = st.selectbox(
        "Language", 
        options=list(lang_options.keys()), 
        format_func=lambda x: lang_options[x],
        key="lang_selector",
        index=0 if st.session_state['language'] == 'JA' else 1
    )
    if new_lang != st.session_state['language']:
        st.session_state['language'] = new_lang
        st.rerun()

st.markdown("---")

# キャラクター選択
st.session_state['selected_character_key'] = st.selectbox(
    "🎭 あなたのメンター属性を選択", 
    options=CHARACTER_OPTIONS,
    index=CHARACTER_OPTIONS.index(st.session_state['selected_character_key'])
)

# カスタムトーン処理
is_custom_mode = st.session_state['selected_character_key'] == "カスタムトーンを自分で定義する"
if is_custom_mode:
    st.text_input(
        "✨ メンターの口調や役割を入力してください",
        placeholder="例: 博多弁で励ましてくれる、情熱的な個人塾の先生",
        key='custom_char_input_key'
    )
    if not st.session_state.get('custom_tone_is_set'):
        if st.button("💬 このトーンの見本を生成する"):
            c_input = st.session_state.get('custom_char_input_key', '')
            if c_input.strip():
                with st.spinner("Generating..."):
                    sample_q = DUMMY_NEGATIVE_INPUT_JA if st.session_state['language'] == 'JA' else DUMMY_NEGATIVE_INPUT_EN
                    concept = generate_concept(c_input)
                    res = reframe_negative_emotion(sample_q, c_input)
                    st.session_state['custom_sample_output'] = {"result": res, "concept": concept}
                    st.rerun()
    
    if st.session_state['custom_sample_output']:
        st.info(f"**Concept:** {st.session_state['custom_sample_output']['concept']}")
        if st.button("✨ このトーンを使用する (確定)"):
            st.session_state['custom_tone_is_set'] = True
            st.rerun()
else:
    desc = CHARACTER_PROMPTS[st.session_state['selected_character_key']]["description"]
    st.info(f"**Concept:** {desc}")

st.markdown("---")

# 入力セクション
st.markdown(f"#### {get_text('INPUT_HEADER')}")
neg_input = st.text_area(
    label="Negative Input Area",
    placeholder=get_text("INPUT_PLACEHOLDER"),
    height=150,
    key="negative_input_key",
    label_visibility="collapsed"
)

btn_c1, btn_c2 = st.columns([0.7, 0.3])
with btn_c1:
    if st.button(get_text("CONVERT_BUTTON"), type="primary"):
        if neg_input.strip():
            with st.spinner("Analyzing..."):
                res = reframe_negative_emotion(neg_input, st.session_state.get('custom_char_input_key', ''))
                now_ts = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M")
                st.session_state.current_review_entry = {
                    "timestamp": now_ts,
                    "date_only": now_ts.split(" ")[0],
                    "negative": neg_input,
                    "positive_reframe": res,
                    "selected_theme": get_text("THEMES")[0]
                }
                st.session_state["negative_input_key"] = ""
                st.rerun()
        else:
            st.warning(get_text("INPUT_WARNING"))

with btn_c2:
    if st.button(get_text("RESET_BUTTON")):
        st.session_state["negative_input_key"] = ""
        st.session_state.current_review_entry = None
        st.rerun()

# ----------------------------------------------------
# ★ 変換結果表示エリア (画像 3 : テキスト 7 分割) ★
# ----------------------------------------------------
if st.session_state.current_review_entry:
    st.markdown("---")
    entry = st.session_state.current_review_entry
    char_key = st.session_state['selected_character_key']
    
    st.subheader(get_text("REVIEW_HEADER"))
    st.caption(f"{get_text('CONVERT_DATE')} {entry['timestamp']}")
    st.code(entry['negative'])

    # 3:7 カラムレイアウト
    col_img, col_main = st.columns([0.3, 0.7])
    
    with col_img:
        # 画像表示
        img_path = CHARACTER_PROMPTS.get(char_key, {}).get("image", "images/mentor_custom.png")
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning(f"Avatar Not Found: {img_path}")

    with col_main:
        # 編集可能なテキストエリア
        st.markdown(f"##### {get_text('FACT_HEADER')}")
        st.text_area("Fact Edit", value=entry['positive_reframe']['fact'], key="edit_fact_key", label_visibility="collapsed")
        
        st.markdown(f"##### {get_text('POSITIVE_HEADER')}")
        st.text_area("Positive Edit", value=entry['positive_reframe']['positive'], height=200, key="edit_positive_key", label_visibility="collapsed")
        
        st.markdown(f"##### {get_text('ACTION_HEADER')}")
        st.text_area("Action Edit", value=entry['positive_reframe']['action'], key="edit_action_key", label_visibility="collapsed")

    # 保存設定
    st.markdown("---")
    entry['selected_theme'] = st.selectbox(get_text("THEME_SELECT_LABEL"), options=get_text("THEMES"))
    
    save_col1, save_col2 = st.columns(2)
    with save_col1:
        if st.button(get_text("SAVE_BUTTON"), type="primary"):
            # 編集内容を反映して保存
            entry['positive_reframe']['fact'] = st.session_state.get("edit_fact_key", entry['positive_reframe']['fact'])
            entry['positive_reframe']['positive'] = st.session_state.get("edit_positive_key", entry['positive_reframe']['positive'])
            entry['positive_reframe']['action'] = st.session_state.get("edit_action_key", entry['positive_reframe']['action'])
            
            st.session_state.history.insert(0, entry)
            st.session_state.positive_streak = calculate_streak(st.session_state.history)
            st.session_state.current_review_entry = None
            st.toast(get_text("SAVE_TOAST"), icon='✅')
            st.rerun()

    with save_col2:
        if st.button(get_text("DISCARD_BUTTON")):
            st.session_state.current_review_entry = None
            st.toast(get_text("DISCARD_TOAST"))
            st.rerun()

# ----------------------------------------------------
# 11. 履歴・統計・レポート表示
# ----------------------------------------------------
st.markdown("---")
st.markdown(f"### 🏆 {get_text('STREAK_TITLE')}: {st.session_state.positive_streak} {get_text('DAYS_CONTINUOUS')}")

# 月間レポートセクション
with st.expander(f"📊 {get_text('REPORT_HEADER')}"):
    if st.button(get_text("GENERATE_REPORT_BUTTON")):
        if not st.session_state.history:
            st.warning(get_text("REPORT_NOT_ENOUGH_DATA"))
        else:
            with st.spinner("Generating Monthly Report..."):
                report = generate_monthly_report(st.session_state.history)
                st.session_state.monthly_report = report
                st.toast(get_text("REPORT_COMPLETED_TOAST"))
    
    if st.session_state.monthly_report:
        st.markdown(f"### {get_text('REPORT_TITLE')}")
        st.write(st.session_state.monthly_report)

# 履歴表示セクション
with st.expander(get_text("HISTORY_HEADER")):
    if st.session_state.history:
        theme_filter = st.selectbox(get_text("FILTER_LABEL"), [get_text("ALL_THEMES")] + get_text("THEMES"))
        for item in st.session_state.history:
            if theme_filter == get_text("ALL_THEMES") or item['selected_theme'] == theme_filter:
                with st.container():
                    st.write(f"**{item['timestamp']} [{item['selected_theme']}]**")
                    st.write(f"**Q:** {item['negative']}")
                    st.info(f"**A:** {item['positive_reframe']['positive']}")
                    if st.button(f"{get_text('DELETE_BUTTON')} {item['timestamp']}", key=f"del_{item['timestamp']}"):
                        st.session_state.history = [h for h in st.session_state.history if h['timestamp'] != item['timestamp']]
                        st.session_state.positive_streak = calculate_streak(st.session_state.history)
                        st.rerun()
                    st.markdown("---")
    else:
        st.write(get_text("NO_HISTORY"))

# CSVエクスポート
if st.session_state.history:
    st.markdown("---")
    st.markdown(f"#### {get_text('EXPORT_HEADER')}")
    csv_data = convert_history_to_csv(st.session_state.history)
    st.download_button(
        label=get_text("DOWNLOAD_BUTTON"),
        data=csv_data,
        file_name=f"reframe_diary_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    st.caption(get_text("EXPORT_CAPTION"))
