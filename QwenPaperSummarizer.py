import markdown
from vllm import LLM, SamplingParams
import string
import re
from pdfminer.high_level import extract_text
import time

# argv #第一引数：pdfファイルのパス, 第二引数：出力先のhtmlファイルのパス, 第三引数：TIME_N, 第四引数：RETRY_LIMIT 第五引数：output_textfile
import argparse

model_id = "Qwen/Qwen2-7B-Instruct"

# パラメータの取得
parser = argparse.ArgumentParser()
parser.add_argument("pdf_path", help="pdf file path")
parser.add_argument("--html_path", help="html file path",type=str, default="empty")
parser.add_argument("--TIME_N", type=int, default=10, help="TIME_N")
parser.add_argument("--RETRY_LIMIT", type=int, default=3, help="RETRY_LIMIT")
parser.add_argument("--output_textfile", type=int, default=0, help="output_textfile")

args = parser.parse_args()

pdf_path = args.pdf_path

if args.html_path == "empty":
    output_html_path = pdf_path.replace(".pdf", ".html")
else:
    output_html_path = args.html_path

CUSTOM_TIME_N = int(args.TIME_N)
CUSTOM_RETRY_LIMIT = int(args.RETRY_LIMIT)

if args.output_textfile == 1:
    output_textfile = True
else:
    output_textfile = False





# プロンプトテンプレートの準備
summarize_template = string.Template("""<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Please summarize the paper below in Markdown format.
Summarize the content in great detail. In particular, the proposed methods and new algorithms in this paper should be extracted and summarized in detail.

                                                  
Preferred format:                 
## Table of contents (ABSTRACT, INTRODUCTION, etc.)
- Summary of the contents of the table of contents in bullet points (If your summary is long, split it into multiple bullet points.)

                                               
Note: The provided text contains noise, so please summarize using only the parts you think are important for understanding the content of the pape
                                             
${instruct}<|im_end|>
<|im_start|>assistant                      
## Table of contents (ABSTRACT, INTRODUCTION, etc.)
- Summary of the contents of the table of contents in bullet points (If your summary is long, split it into multiple bullet points.)
                           
##ABSTRACT
-""")

title_template = string.Template("""<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
This is the beginning of the text of the paper. The title of this paper is included in this text.
Please extract the title and answer the question. Please do not answer anything else.
                                             
${instruct}<|im_end|>
<|im_start|>assistant
Title: '""")



# FUNCTIONS
def mark_to_html(md_txt):
    
    text = md_txt
    md = markdown.Markdown()
    body = md.convert(text)
    # HTML書式に合わせる
    html = '<html lang="ja"><meta charset="utf-8"><body>'
    html += body + '</body></html>' 
    return html

def save_html(html, save_path):
    with open(save_path, mode="w", encoding='utf-8') as f:
        f.write(html)

def extract_text_from_pdf(file_path):
    text = extract_text(file_path)
    return text

def clean_extracted_text(text):
    text = text.replace('-\n', '')
    text = re.sub(r'\s+', ' ', text)
    return text

def prepare_prompts(template: string.Template, cleaned_text: str, head_num=0):

    if head_num > 0:
        cleaned_text = cleaned_text[:head_num]

    # プロンプトの準備
    prompts = [
        cleaned_text,
    ]

    for i in range(len(prompts)):
        prompts[i] =  template.safe_substitute({"instruct": prompts[i]})
    
    return prompts

def outputting_text(llm, prompts, temperature, maxtoken, RETRY_LIMIT, TIME_N):
    # 実行時間がN秒以下の場合、出力を再度やり直す
    # 再出力の回数はRETRY_LIMIT回まで

    #　出力完了フラグ
    output_flag = False
    retry_num = 0

    while not output_flag:
        
        #実行時間計測開始
        start = time.time() 

        # 推論の実行
        outputs = llm.generate(
            prompts,
            sampling_params = SamplingParams(
                temperature=temperature,
                max_tokens=maxtoken,
            )
        )
        # 実行時間計測終了
        elapsed_time = time.time() - start

        if retry_num >= RETRY_LIMIT:
            print("The maximum number of reprints has been reached.")
            break

        # 実行時間がN秒以下の場合
        if elapsed_time < TIME_N:
            output_flag = False
            retry_num += 1
            print(f"Retry output: {retry_num} times")
        else:
            print("Done Output. elapsed time:", elapsed_time)
            output_flag = True

        return outputs[0].outputs[0].text

# MAIN
if __name__ == "__main__":
    print("\n\ntarget pdf file path:", pdf_path)
    # PDFからテキストを抽出
    extracted_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_extracted_text(extracted_text)

    # cleaned_textが短すぎる場合、エラーを出力
    if len(cleaned_text) < 100:
        raise ValueError("The extracted text is too short. Please check the PDF file.")

    # タイトルとサマリーのプロンプトの準備
    title_prompts = prepare_prompts(title_template, cleaned_text, 1000)
    summarize_prompts = prepare_prompts(summarize_template, cleaned_text, 0)

    # モデルの読み込み
    llm = LLM(model=model_id)

    # タイトルの抽出
    title = llm.generate(
        title_prompts,
        sampling_params = SamplingParams(
            temperature=0.1,
            max_tokens=50,
        )
    )

    title_md = "#"+title[0].outputs[0].text.split("'")[0]+"\n\n"
    
    # サマリーの抽出
    summary = outputting_text(llm, summarize_prompts, 0.5, 999999, CUSTOM_RETRY_LIMIT, CUSTOM_TIME_N)
    output_text = "##ABSTRACT\n-"+summary

    # 最終的な出力を作成
    final_output = title_md + output_text

    # HTMLに変換
    html = mark_to_html(final_output)
    save_html(html, output_html_path)
    print("saved html file :", output_html_path)
    

    if output_textfile:
        output_textfile_path = output_html_path.replace(".html",".txt")
        print("saved text file :", output_textfile_path)
        # テキストファイルで保存(実験)
        with open(output_textfile_path, "w") as f:
            f.write(final_output)

    print("Done")

    