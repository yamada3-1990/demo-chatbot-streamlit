# demo-chatbot-streamlit

## 手順
### 1. ```.env.dev``` -> ```.env``` に変更してAPIキーをセットする
```
GEMINI_API_KEY = "" 
```

### 2. 仮想環境のセットアップを行う
```
$ python -m venv env <-初回のみ
$ .\env\Scripts\activate
```

### 3. 必要なパッケージをインストールする
```
$ pip install -r requirements.txt
```

### 4. 実行
```
$ streamlit run app.py
```

## 参考
[Streamlitで音声入力もできるチャットアプリを作ってみた（〜ChatGPT下位互換編〜）](https://qiita.com/harutine/items/db04dd05c09e3e25a0a8)