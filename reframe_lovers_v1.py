# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import datetime
import pytz
import json
import time # sleep/spinner用にインポート

# ----------------------------------------------------
# 1. 多言語対応とセッションステートの初期化
# ----------------------------------------------------

# 多言語対応用の静的テキスト定義 (ゲームUI用)
GAME_TRANSLATIONS = {
    "JA": {
        "TITLE": "Reframe Lovers 〜スタートアップの空の下で〜 (プロトタイプ)",
        "LANG_SELECT": "言語を選択 / Select Language",
        "GENDER_SELECT": "主人公の性別を選択",
        "GENDER_MALE": "男性 (Man)",
        "GENDER_FEMALE": "女性 (Woman)",
        "NAME_INPUT": "主人公の名前を入力してください",
        "CSV_HEADER": "🔗 ポジティブ日記データの連動",
        "CSV_UPLOAD": "ポジティブ日記の最新のCSVファイルをアップロードしてください",
        "CSV_HINT": "※このファイルから「自信ゲージ」を計算します。",
        "LOAD_BUTTON": "データをロードしてゲーム開始",
        "DATA_ERROR": "⚠️ データエラー：CSVをアップロードするか、ファイルが壊れていないか確認してください。",
        "DATA_SUCCESS": "✅ データロード成功！",
        "CONTINUOUS_DAYS": "連続記録日数:",
        "CONFIDENCE_GAUGE": "現在の自信ゲージ (Confidence):",
        "START_GAME": "ゲームを開始する ➡️"
    },
    "EN": {
        "TITLE": "Reframe Lovers ~Under the Startup Sky~ (Prototype)",
        "LANG_SELECT": "Select Language / 言語を選択",
        "GENDER_SELECT": "Select Player Gender",
        "GENDER_MALE": "Male",
        "GENDER_FEMALE": "Female",
        "NAME_INPUT": "Enter Player Name",
        "CSV_HEADER": "🔗 Link Positive Diary Data",
        "CSV_UPLOAD": "Please upload the latest CSV file from your Positive Diary App",
        "CSV_HINT": "※This file is used to calculate your Confidence Gauge.",
        "LOAD_BUTTON": "Load Data and Start Game",
        "DATA_ERROR": "⚠️ Data Error: Please upload a valid CSV file.",
        "DATA_SUCCESS": "✅ Data Load Successful!",
        "CONTINUOUS_DAYS": "Continuous Recording Days:",
        "CONFIDENCE_GAUGE": "Current Confidence Gauge:",
        "START_GAME": "Start Game ➡️"
    }
}

def get_text(key):
    lang = st.session_state.get('game_language', 'JA')
    return GAME_TRANSLATIONS.get(lang, GAME_TRANSLATIONS['JA']).get(key, f"MISSING TEXT: {key}")

# セッションステートの初期化を setdefault で簡略化
st.session_state.setdefault('game_language', 'JA')
st.session_state.setdefault('continuous_days', 0)
st.session_state.setdefault('game_state', 'START') # START / DIARY_LOADED / CONVERSATION_LOAD / CONVERSATION
st.session_state.setdefault('player_gender', 'Female') 
st.session_state.setdefault('player_name', 'あなた')
st.session_state.setdefault('confidence_level', 1)
st.session_state.setdefault('conversation_history', []) # 会話履歴
st.session_state.setdefault('conversation_theme', "オフィスでの新機能開発の課題") # 第1話テーマ
st.session_state.setdefault('favor_ryo', 50) # 氷室涼の好感度 

# ----------------------------------------------------
# 2. 連続記録日数を計算するコアロジック (日記アプリと同じ)
# ----------------------------------------------------

def calculate_streak_from_df(df):
    """データフレームから連続記録日数を計算する"""
    
    date_column = None
    if '日付' in df.columns:
        date_column = '日付'
    elif 'Date' in df.columns:
        date_column = 'Date'
    else:
        st.error(f"CSVファイルに '日付' または 'Date' カラムが見つかりません。")
        return 0
        
    df = df.dropna(subset=[date_column])
    
    # 日付形式を自動推論する改善案を適用
    try:
        df['date_only'] = pd.to_datetime(
            df[date_column], 
            errors='coerce', 
            infer_datetime_format=True
        ).dt.date
    except Exception as e:
        st.error(f"日付形式の解析エラーが発生しました。: {e}")
        return 0

    df = df.dropna(subset=['date_only'])
    unique_dates = sorted(list(df['date_only'].unique()), reverse=True)
    
    if not unique_dates:
        return 0

    streak = 0
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.datetime.now(jst).date()
    current_date_to_check = today
    
    for entry_date in unique_dates:
        if entry_date == current_date_to_check:
            streak += 1
            current_date_to_check -= datetime.timedelta(days=1)
        elif entry_date < current_date_to_check:
            break
            
    return streak

# ----------------------------------------------------
# 3. AI会話生成ロジック (Step 2-1 & 2-2)
# ----------------------------------------------------

def get_system_instruction(player_name, player_gender, confidence_level):
    """
    AIに与える氷室 涼のペルソナと制約を定義するゴールデンプロンプト。
    (この関数は、API呼び出し時に利用されます)
    """
    # 実際のAPI連携では、この長い文字列をSYSTEM INSTRUCTIONとして渡します。
    # 簡略化のため、詳細は省略します。

    return f"""
    あなたはゲームの攻略対象キャラクター『氷室 涼（ひむろ りょう）』です。
    ... (中略) ...
    自信レベル: {confidence_level} / プレイヤー名: {player_name} / 性別: {player_gender}
    出力は以下のJSON形式に厳密に従ってください。
    """

def generate_conversation_turn(conversation_context):
    """
    Gemini APIを呼び出し、氷室 涼の会話と選択肢をJSONで取得する関数。
    現在は動作確認のためのモックデータを使用しています。
    """
    # 状態の取得
    player_name = st.session_state['player_name']
    player_gender = st.session_state['player_gender']
    confidence_level = st.session_state['confidence_level']

    # 実際のAPI呼び出しの代わりに、動作確認のためのモックデータを使用
    time.sleep(1.5) # AIが考えている様子を表現

    if confidence_level >= 3:
        speech = f"プロジェクトの進捗報告書を読んだ。{player_name}、正直に言うと、君の判断は**大胆**すぎる。だが、その自信は評価する。次の一手は？"
        choices = [
            {"text": "このまま強気で押し通すと断言する (大胆/高リスク)", "consequence": "favor_up"},
            {"text": "彼の指摘を受け入れ、リスクヘッジ案を提示する", "consequence": "neutral"},
            {"text": "動揺を隠して、曖昧な返事をする", "consequence": "favor_down"}
        ]
    else:
        speech = f"進捗状況は？{player_name}はプレッシャーを感じているようだ。君のペースで構わないが、報告は正確に。"
        choices = [
            {"text": "今の不安な気持ちを正直に相談する", "consequence": "neutral"},
            {"text": "曖昧な返事で、とりあえずやり過ごす", "consequence": "favor_down"},
            {"text": "一歩踏み出し、具体的な解決策を提案する", "consequence": "favor_up"}
        ]

    return {
        "character_name": "氷室 涼",
        "character_speech": speech,
        "choices": choices,
        "current_status": {"confidence_level": confidence_level, "player_gender": player_gender}
    }

def handle_choice(choice_consequence):
    """選択肢が選ばれた時の好感度・自信ゲージの処理"""
    
    if choice_consequence == "favor_up":
        st.session_state['favor_ryo'] = min(100, st.session_state['favor_ryo'] + 10)
        st.toast("好感度が少し上がりました！", icon='❤️')
    elif choice_consequence == "favor_down":
        st.session_state['favor_ryo'] = max(0, st.session_state['favor_ryo'] - 5)
        st.toast("好感度が少し下がってしまいました...", icon='💔')
    elif choice_consequence == "confidence_up":
        # 好感度を上げる選択肢ではないが、自信が増すケース
        st.session_state['confidence_level'] = min(3, st.session_state['confidence_level'] + 1)
        st.toast("自信が湧いてきました！", icon='✨')
        
    # 次の会話を生成するため、一時的にロード状態に遷移し、リロード
    st.session_state['game_state'] = 'CONVERSATION_LOAD'
    st.rerun()

# ----------------------------------------------------
# 4. Streamlit UIとアクション
# ----------------------------------------------------

st.set_page_config(layout="centered", page_title=get_text("TITLE"))
st.title(get_text("TITLE"))

if st.session_state['game_state'] in ['START', 'DIARY_LOADED']:
    
    # --- 言語選択 ---
    LANGUAGES = {"JA": "日本語", "EN": "English"}
    st.session_state['game_language'] = st.selectbox(
        get_text("LANG_SELECT"), 
        options=list(LANGUAGES.keys()), 
        format_func=lambda x: LANGUAGES[x]
    )
    st.markdown("---")

    # --- 主人公情報入力 ---
    st.subheader("👤 Character Setup")
    col_g, col_n = st.columns([0.4, 0.6])

    with col_g:
        st.session_state['player_gender'] = st.selectbox(
            get_text("GENDER_SELECT"), 
            options=["Female", "Male"],
            format_func=lambda x: get_text("GENDER_FEMALE") if x == "Female" else get_text("GENDER_MALE")
        )

    with col_n:
        st.session_state['player_name'] = st.text_input(
            get_text("NAME_INPUT"), 
            value=st.session_state['player_name'],
            max_chars=10
        )

    st.markdown("---")

    # --- CSVアップロードとデータロード ---
    st.subheader(get_text("CSV_HEADER"))

    uploaded_file = st.file_uploader(
        get_text("CSV_UPLOAD"), 
        type="csv",
        help=get_text("CSV_HINT")
    )

    if uploaded_file is not None and st.session_state['game_state'] == 'START':
        try:
            df = pd.read_csv(uploaded_file)
            streak = calculate_streak_from_df(df)
            st.session_state['continuous_days'] = streak
            st.session_state['game_state'] = 'DIARY_LOADED'
            st.toast(get_text("DATA_SUCCESS"), icon='💾')
            st.rerun() 
            
        except Exception as e:
            st.error(get_text("DATA_ERROR") + f"\n{e}")
            st.session_state['continuous_days'] = 0
            st.session_state['game_state'] = 'START'

    # --- 読み込み結果の表示とゲーム開始ボタン ---
    if st.session_state['game_state'] == 'DIARY_LOADED':
        st.success(get_text("DATA_SUCCESS"))
        
        days = st.session_state['continuous_days']
        
        # 自信ゲージの計算と表示
        if days >= 7:
            confidence_level = 3
            confidence_text = "✨ HIGH (大胆な選択肢が出現！)" if st.session_state['game_language'] == 'JA' else "✨ HIGH (Bold choices available!)"
        elif days >= 3:
            confidence_level = 2
            confidence_text = "💪 MEDIUM (バランスの取れた選択肢)" if st.session_state['game_language'] == 'JA' else "💪 MEDIUM (Balanced choices)"
        else:
            confidence_level = 1
            confidence_text = "😥 LOW (消極的な選択肢が多い)" if st.session_state['game_language'] == 'JA' else "😥 LOW (Passive choices dominate)"
            
        st.session_state['confidence_level'] = confidence_level 
        
        st.markdown(f"**{get_text('CONTINUOUS_DAYS')}** **{days}** 日")
        st.markdown(f"**{get_text('CONFIDENCE_GAUGE')}**")
        st.progress(confidence_level / 3) 
        st.write(confidence_text)
        
        st.markdown("---")
        
        # ゲーム開始ボタン
        if st.button(get_text("START_GAME"), type="primary"):
            st.session_state['game_state'] = 'CONVERSATION_LOAD' # 最初の会話生成をトリガー
            st.rerun()


# --- 会話画面のレンダリング ---

def render_conversation_ui():
    """ゲームの会話画面をレンダリングする"""
    
    # --- UIヘッダー ---
    st.header("💬 Reframe Lovers")
    st.subheader(f"Day 1: 氷室 涼との会話")
    
    col_fav, col_conf = st.columns([0.5, 0.5])
    with col_fav:
        st.markdown(f"❤️ **好感度**: **{st.session_state['favor_ryo']}** / 100")
    with col_conf:
        st.markdown(f"✨ **自信レベル**: **{st.session_state.get('confidence_level', 1)}** / 3")
        
    st.markdown("---")

    # --- 会話履歴の表示エリア（チャットUI風） ---
    chat_container = st.container(height=350)

    # 履歴を逆順にして、新しいものが下に表示されるようにする
    with chat_container:
        for turn in st.session_state['conversation_history']:
            st.markdown(f"""
            <div style="background-color: #e6f7ff; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                👤 **{turn['character_name']}**: {turn['character_speech']}
            </div>
            """, unsafe_allow_html=True)
            
    # 現在の会話データを取得 (最新のターン)
    current_turn = st.session_state['conversation_history'][-1] if st.session_state['conversation_history'] else None

    if st.session_state['game_state'] == 'CONVERSATION' and current_turn:
        
        # --- 選択肢の表示 ---
        st.markdown("---")
        st.write("➡️ あなたの選択...")
        
        # 選択肢の数に応じてカラムを分割
        cols = st.columns(len(current_turn['choices']))
        for i, choice in enumerate(current_turn['choices']):
            with cols[i]:
                st.button(
                    choice['text'], 
                    key=f"choice_{len(st.session_state['conversation_history'])}_{i}", # キーに履歴の長さを加えて一意性を確保
                    on_click=handle_choice, 
                    args=(choice['consequence'],) # 好感度への影響を渡す
                )
                
    elif st.session_state['game_state'] == 'CONVERSATION_LOAD':
        # AIのターンを生成
        with st.spinner('氷室 涼が思考中... データ生成中...'):
            # generate_conversation_turn 関数を呼び出す
            new_turn = generate_conversation_turn(st.session_state['conversation_theme']) 
        
        if new_turn:
            st.session_state['conversation_history'].append(new_turn)
            st.session_state['game_state'] = 'CONVERSATION'
            st.rerun()
        else:
            st.error("会話の生成に失敗しました。AIの設定を確認してください。")

# --- メインロジックの末尾に会話レンダリングを追加 ---
if st.session_state['game_state'] in ['CONVERSATION', 'CONVERSATION_LOAD']:
    render_conversation_ui()
