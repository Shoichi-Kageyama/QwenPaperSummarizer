import streamlit as st
from vllm import LLM
import re
from pdfminer.high_level import extract_text
import time
import os

from QSP_webapp_module import run_qps

model_id = "Qwen/Qwen2-7B-Instruct"
CUSTOM_RETRY_LIMIT = 3
CUSTOM_TIME_N = 10

DEBUG = False


@st.cache_resource
def load_model(model_id):
    llm = LLM(model_id)
    return llm

def render():
    # title
    st.title("Qwen Paper Summarizer")

    global model_id, CUSTOM_RETRY_LIMIT, CUSTOM_TIME_N

    # セッションステート
    if "process_start" not in st.session_state:
        st.session_state.process_start = False
    if "uploaded_file"  not in st.session_state:
        st.session_state.uploaded_file = None
    if "text" not in st.session_state:
        st.session_state.text = None
    if "html" not in st.session_state:
        st.session_state.html = None
    if "final_output" not in st.session_state:
        st.session_state.final_output = None

    # セッションステートの確認(debug)
    if DEBUG:
        #st.write(st.session_state)
        pass

    try:
        if  st.session_state.uploaded_file is None or not st.session_state.process_start:
            st.session_state.uploaded_file = st.file_uploader("Choose a file", "pdf")
            startbutton = st.button("RUN")
            if startbutton:
                if st.session_state.uploaded_file is not None:
                    st.session_state.process_start = True
                else:
                    st.warning("Please upload a PDF file.")
        else:
            st.warning("Please reload the page and try again.")

        # スタート
        if st.session_state.uploaded_file is not None and st.session_state.process_start:
            
            # pdfファイルを一時保存⇒テキスト抽出⇒一時ファイル削除
            if st.session_state.text is None:
                file_unique = time.strftime('%Y%m%d%H%M%S')
                print("process start:", file_unique, st.session_state.uploaded_file.name)

                uploaded_file = st.session_state.uploaded_file
                pdf_path =  f"./datafolder_webapp/{file_unique}.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                text = extract_text(pdf_path)
                text = text.replace('-\n', '')
                st.session_state.text = re.sub(r'\s+', ' ', text)
                os.remove(pdf_path)
                # textが短すぎる場合、エラーを出力
                if len(text) < 100:
                    raise ValueError("The extracted text is too short. Please check the PDF file.")
            else:
                text = st.session_state.text            

            # モデルのロード(初回のみ)
            llm = load_model(model_id)

            if st.session_state.html is None and st.session_state.final_output is None:
                # 要約実行(別のpyファイルによりモジュール化)
                st.session_state.html, st.session_state.final_output = run_qps(llm, text, CUSTOM_RETRY_LIMIT, CUSTOM_TIME_N)
                
            # 表示と保存ボタンの表示
            st.markdown("---")
            # html保存ボタン
            st.download_button(
                label="Download HTML",
                data=st.session_state.html,
                file_name=f"qps_{st.session_state.uploaded_file.name[:-4]}.html",
                mime="text/html"
            )

            # md保存ボタン
            st.download_button(
                label="Download md File",
                data=st.session_state.final_output,
                file_name=f"qps_{st.session_state.uploaded_file.name[:-4]}.md",
                mime="text/plain"
            )
            st.markdown(st.session_state.final_output)



    except Exception as e:
        if DEBUG:
            print(type(e).__name__)
            print(e)
            st.error(e)
        else:
            st.error("An error occurred. Please reload the page and try again.")

if __name__ == '__main__':
    # 現在時刻 yyyy/mm/dd hh:mm:ss
    nowtime = time.strftime('%Y/%m/%d %H:%M:%S')
    print("\n\n"+"="*40+"\n"+"page reload:", nowtime, "\n"+"="*40+"\n\n")

    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    st.markdown("""
  <style>
     /* Streamlit class name of the div that holds the expander's title*/
    .css-16idsys p {
      font-size: 32px;
      color: black;
      }
    .css-6awftf {visibility: hidden;}
  </style>""", unsafe_allow_html=True)
    
    render()