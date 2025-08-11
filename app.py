import streamlit as st
from audio_recorder_streamlit import audio_recorder
from tempfile import NamedTemporaryFile
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Google Gemini APIキーを環境変数から取得
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("Please set the GEMINI_API_KEY in your environment variables.")
    st.stop()

# genaiクライアントを初期化
genai.configure(api_key=API_KEY)

# --- カスタムプロンプトをコード上で固定 ---
FIXED_SYSTEM_INSTRUCTION = "あなたは親切で丁寧なアシスタントです。ユーザーの質問には簡潔に答えてください。ユーザーは小学生なので、小学生にわかりやすい言葉遣いや仮名遣いで返答してください"

# 音声入力のテキスト変換 (Gemini APIを使用)
def transcribe_audio_to_text(audio_bytes):
    """
    音声をGemini APIでテキストに変換
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 音声データを一時ファイルとして保存
        with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(audio_bytes)
            temp_filename = temp_file.name

        # 一時ファイルへの参照を含むプロンプトを作成
        audio_file = genai.upload_file(path=temp_filename)
        
        response = model.generate_content([
            "以下の音声ファイルの内容を日本語で文字起こししてください。",
            audio_file
        ])

        # 一時ファイルを削除
        os.remove(temp_filename)
        
        return response.text
    
    except Exception as e:
        st.error(f"音声認識中にエラーが発生しました: {e}")
        return ""

# Gemini APIを使って、チャットの返答テキストを取得
def get_reply_from_gemini(all_messages: dict, system_instruction: str):
    """
    Gemini APIを使って、チャットの返答テキストを取得
    """
    try:
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_instruction
        )
        
        history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in all_messages
        ]
        
        chat = model.start_chat(history=history)
        response = chat.send_message(history[-1]['parts'][0])
        return response.text
    except Exception as e:
        st.error(f"テキスト生成中にエラーが発生しました: {e}")
        return "エラーが発生しました。"
    

def main():
    # サイドバーの表示
    sidebar()

    # タイトルの表示
    st.title('🎙️💬 Audio-Chat with Gemini')
    st.markdown("---")

    # セッションステートの初期化
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "何でも聞いてください。"}]
    if "chat_ended" not in st.session_state:
        st.session_state["chat_ended"] = False
    
    # 終了ボタンが押された後のメッセージを表示
    if st.session_state.chat_ended:
        st.info("お疲れさまでした！")
    
    # チャット履歴の表示
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # --- ボタンを固定するためのコンテナ ---
    with st.container():
        st.markdown(
            """
            <style>
                .fixed-bottom {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    background-color: white;
                    padding: 10px;
                    box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
                    display: flex;
                    justify-content: space-around;
                    align-items: center;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
        # 会話が終了していない場合のみ、ボタンを表示
        if not st.session_state.chat_ended:
            col1, col2 = st.columns(2)
            with col1:
                # 音声入力ボタン
                audio_bytes = audio_recorder(
                    text="音声で入力",
                    pause_threshold=3.0,
                    key="audio_recorder"
                )
            with col2:
                # 会話終了ボタン
                if st.button("会話を終了する", use_container_width=True, key="end_chat_button"):
                    st.session_state.chat_ended = True
                    st.session_state.messages.append({"role": "assistant", "content": "お疲れさまでした！"})
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    # --- 会話が終了していない場合のみ、入力フォームを表示 ---
    if not st.session_state.chat_ended:
        # チャットボックスの表示＆プロンプト入力時のユーザー・AIチャット表示追加
        if prompt := st.chat_input("何でも聞いてください...", disabled=st.session_state.chat_ended):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.chat_message("user", avatar=None).write(prompt)
            
            reply = get_reply_from_gemini(st.session_state.messages, FIXED_SYSTEM_INSTRUCTION)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.write(reply)
                
        # 音声入力時の処理
        # audio_recorderが値を返した場合のみ処理を実行
        if audio_bytes:
            # 音声入力のテキスト変換
            with st.spinner("音声を文字起こししています..."):
                transcript = transcribe_audio_to_text(audio_bytes)
            
            if transcript:
                st.session_state["messages"].append({"role": "user", "content": transcript})
                st.chat_message("user").write(transcript)

                with st.spinner("回答を生成しています..."):
                    reply = get_reply_from_gemini(st.session_state.messages, FIXED_SYSTEM_INSTRUCTION)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.write(reply)


def sidebar():
    """
    サイドバー
    """
    with st.sidebar:
        st.markdown("# 設定")
        st.markdown("---")

        st.markdown("#### システム設定")
        st.markdown(f"**役割:** {FIXED_SYSTEM_INSTRUCTION}")
        st.markdown("---")
        
        st.subheader("セッション")
        if st.button("チャット履歴をクリア"):
            st.session_state["messages"] = [{"role": "assistant", "content": "何でも聞いてください。"}]
            st.session_state["chat_ended"] = False
            st.rerun()
        st.markdown("---")


if __name__ == '__main__':
    main()
