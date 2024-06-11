# QwenPaperSummarizer

## 機能

* Qwen2モデルを使用してpdf化された論文を要約します。
* webアプリとCUI上での２通りの使い方があります。

##### 注意：LLMの出力は不安定です。期待しない出力をする場合があります。


## セットアップと使い方

#### 1.Anaconda3を使用して環境を作成する

```bash
git clone https://github.com/Shoichi-Kageyama/QwenPaperSummarizer.git
cd QwenPaperSummarizer
conda create -n QwenPaperSummarizer python=3.10
conda activate QwenPaperSummarizer
pip install -r requirements.txt
```

## Webアプリ起動
#### streamlitで作成されたwebアプリを起動します
```bash
streamlit run QPS_webapp.py  
```

## CUIでアプリ起動

#### 1.datafolderに要約したい論文のPDFを入れる

#### 2.CUIでアプリを起動する
**datafolder** に **sample.pdf** を置いた場合


##### 簡単な例：

```bash
python QwenPaperSummarizer.py ./datafolder/sample.pdf  
```  
  
  
* **datafolder** に **sample.html** が作成されます。　　


##### 全ての引数を使用する例：  

```bash
python QwenPaperSummarizer.py ./datafolder/sample.pdf --html_path ./datafolder/summary.html --TIME_N 10 --RETRY_LIMIT 3 --output_textfile 1 
```

* **第１引数(必須)** : pdfのパス。
* **第２引数 --html_path (任意)** : 出力するhtmlのパス。  指定なしの場合はpdfのパスと同一フォルダにhtmlを作成します。
* **第３引数 --TIME_N (任意)** : LLMの最短生成時間の指定。指定時間より短い時間で出力した場合は **RETRY_LIMIT** の回数だけ生成をやり直します。 **0** を指定した場合無効となり、デフォルトでは **10** です。論文のような巨大なテキストの要約の場合、生成時間が短いとでたらめな出力をしている場合があるため設定しました。それぞれの環境で生成時間を調整してください。
* **第４引数 --RETRY_LIMIT (任意)** : 上記の再生成の上限回数。 デフォルトでは **3** です
* **第５引数 --output_textfile (任意)** : **1** を設定することでhtmlと同じ場所にテキストファイルを作成します。ファイル名はhtmlファイルと同一の.txtファイルです。デフォルトでは **0** です。(デフォルトでは作成されません)  
