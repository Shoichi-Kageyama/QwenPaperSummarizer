import markdown
from vllm import SamplingParams
import string
import time

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
                           
## ABSTRACT
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

def run_qps(llm, text, CUSTOM_RETRY_LIMIT=3, CUSTOM_TIME_N=10):
    # タイトルとサマリーのプロンプトの準備
    title_prompts = prepare_prompts(title_template, text, 1000)
    summarize_prompts = prepare_prompts(summarize_template, text, 0)

    # タイトルの抽出
    title = llm.generate(
        title_prompts,
        sampling_params = SamplingParams(
            temperature=0.1,
            max_tokens=50,
        )
    )

    title_md = "# "+title[0].outputs[0].text.split("'")[0]+"\n\n"
    
    # サマリーの抽出
    summary = outputting_text(llm, summarize_prompts, 0.5, 999999, CUSTOM_RETRY_LIMIT, CUSTOM_TIME_N)
    output_text = "## ABSTRACT\n-"+summary

    # 最終的な出力を作成
    final_output = title_md + output_text

    # HTMLに変換
    html = mark_to_html(final_output)

    return html, final_output

