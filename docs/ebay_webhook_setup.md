# eBay Webhook設定ガイド

eBay APIのProduction Keysetを有効化するためには、ユーザーデータ削除通知（Marketplace deletion/account closure notification）を受け取るためのWebhookを設定する必要があります。このガイドでは、必要なHTTPSエンドポイントURLと検証トークンの設定方法を説明します。

## 1. HTTPS形式の通知エンドポイントURL

### オプション1: 本番環境での設定

実際の本番環境では、以下の方法でHTTPSエンドポイントを設定できます：

1. **独自ドメインとサーバーを使用**
   - 自社サーバーまたはクラウドサービス（AWS、GCP、Azureなど）にWebhookエンドポイントを設定
   - Let's Encryptなどの無料SSL証明書を使用してHTTPSを有効化
   - 例: `https://api.yourcompany.com/ebay/webhook`

2. **クラウドサービスの活用**
   - AWS Lambda + API Gateway
   - Google Cloud Functions
   - Azure Functions
   - Vercel Serverless Functions
   - Netlify Functions

### オプション2: 開発・テスト用の一時的な設定

開発・テスト段階では、以下のサービスを使用して一時的なHTTPSエンドポイントを設定できます：

1. **ngrok**
   ```bash
   # インストール
   npm install -g ngrok
   
   # ローカルサーバーを起動（例: ポート3000）
   node webhook_server.js
   
   # ngrokでトンネルを作成
   ngrok http 3000
   ```
   
   これにより、`https://xxxx-xxxx-xxxx.ngrok.io` のような一時的なHTTPSエンドポイントが生成されます。

2. **Cloudflare Tunnel**
   ```bash
   # インストール
   npm install -g cloudflared
   
   # トンネルを作成
   cloudflared tunnel --url http://localhost:3000
   ```

3. **localtunnel**
   ```bash
   # インストール
   npm install -g localtunnel
   
   # トンネルを作成
   lt --port 3000
   ```

## 2. 検証トークン

検証トークンは、32～80文字の英数字で構成される文字列です。以下の方法で生成できます：

### 方法1: ランダム文字列の生成

```bash
# Linuxの場合
openssl rand -hex 32

# Node.jsの場合
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Pythonの場合
python -c "import secrets; print(secrets.token_hex(32))"
```

### 方法2: UUIDの使用

```bash
# Linuxの場合
uuidgen

# Node.jsの場合
node -e "console.log(require('crypto').randomUUID())"

# Pythonの場合
python -c "import uuid; print(uuid.uuid4().hex)"
```

生成した検証トークンは、安全な場所（環境変数や設定ファイルなど）に保存してください。

## 3. Webhook実装例

### Node.js実装例

```javascript
// webhook_server.js
const express = require('express');
const crypto = require('crypto');
const bodyParser = require('body-parser');
const app = express();
const port = process.env.PORT || 3000;

// 環境変数から検証トークンを取得
const VERIFICATION_TOKEN = process.env.EBAY_VERIFICATION_TOKEN;

// JSONリクエストのパース
app.use(bodyParser.json());

// GETリクエスト - チャレンジコード処理
app.get('/ebay/webhook', (req, res) => {
  const challengeCode = req.query.challenge_code;
  
  if (!challengeCode) {
    return res.status(400).json({ error: 'Challenge code is required' });
  }
  
  // チャレンジレスポンスの計算
  const endpointUrl = `${req.protocol}://${req.get('host')}${req.originalUrl.split('?')[0]}`;
  const dataToHash = challengeCode + VERIFICATION_TOKEN + endpointUrl;
  const challengeResponse = crypto.createHash('sha256').update(dataToHash).digest('hex');
  
  // レスポンスを返す
  res.json({ challengeResponse });
});

// POSTリクエスト - 削除通知処理
app.post('/ebay/webhook', (req, res) => {
  console.log('Received notification:', req.body);
  
  // 通知を処理
  // ユーザーデータの削除処理などを実装
  
  // 成功レスポンスを返す
  res.status(200).json({ status: 'success' });
});

// サーバー起動
app.listen(port, () => {
  console.log(`Webhook server listening at http://localhost:${port}`);
});
```

### Python実装例

```python
# webhook_server.py
import os
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 環境変数から検証トークンを取得
VERIFICATION_TOKEN = os.environ.get('EBAY_VERIFICATION_TOKEN')

@app.route('/ebay/webhook', methods=['GET'])
def handle_challenge():
    challenge_code = request.args.get('challenge_code')
    
    if not challenge_code:
        return jsonify({'error': 'Challenge code is required'}), 400
    
    # チャレンジレスポンスの計算
    endpoint_url = request.url_root + request.path.lstrip('/')
    data_to_hash = challenge_code + VERIFICATION_TOKEN + endpoint_url
    challenge_response = hashlib.sha256(data_to_hash.encode()).hexdigest()
    
    # レスポンスを返す
    return jsonify({'challengeResponse': challenge_response})

@app.route('/ebay/webhook', methods=['POST'])
def handle_notification():
    notification = request.json
    print(f"Received notification: {notification}")
    
    # 通知を処理
    # ユーザーデータの削除処理などを実装
    
    # 成功レスポンスを返す
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
```

## 4. デプロイ方法

### Herokuへのデプロイ例（Python）

1. **Herokuアカウントを作成**
   - [Heroku](https://www.heroku.com/)にアクセスしてアカウントを作成

2. **Heroku CLIをインストール**
   ```bash
   npm install -g heroku
   ```

3. **必要なファイルを作成**
   - `requirements.txt`
     ```
     flask==2.0.1
     gunicorn==20.1.0
     ```
   
   - `Procfile`
     ```
     web: gunicorn webhook_server:app
     ```

4. **Gitリポジトリを初期化**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

5. **Herokuアプリを作成**
   ```bash
   heroku login
   heroku create ebay-webhook-app
   ```

6. **環境変数を設定**
   ```bash
   heroku config:set EBAY_VERIFICATION_TOKEN=your_verification_token
   ```

7. **デプロイ**
   ```bash
   git push heroku master
   ```

8. **URLを確認**
   ```bash
   heroku open
   ```
   
   生成されたURL（例: `https://ebay-webhook-app.herokuapp.com/ebay/webhook`）をeBayの通知設定で使用します。

### Vercelへのデプロイ例（Node.js）

1. **Vercelアカウントを作成**
   - [Vercel](https://vercel.com/)にアクセスしてアカウントを作成

2. **Vercel CLIをインストール**
   ```bash
   npm install -g vercel
   ```

3. **必要なファイルを作成**
   - `package.json`
     ```json
     {
       "name": "ebay-webhook",
       "version": "1.0.0",
       "main": "webhook_server.js",
       "dependencies": {
         "express": "^4.17.1",
         "body-parser": "^1.19.0"
       },
       "scripts": {
         "start": "node webhook_server.js"
       }
     }
     ```
   
   - `vercel.json`
     ```json
     {
       "version": 2,
       "builds": [
         { "src": "webhook_server.js", "use": "@vercel/node" }
       ],
       "routes": [
         { "src": "/ebay/webhook", "dest": "webhook_server.js" }
       ]
     }
     ```

4. **デプロイ**
   ```bash
   vercel
   ```

5. **環境変数を設定**
   ```bash
   vercel env add EBAY_VERIFICATION_TOKEN
   ```

6. **再デプロイ**
   ```bash
   vercel --prod
   ```

   生成されたURL（例: `https://ebay-webhook.vercel.app/ebay/webhook`）をeBayの通知設定で使用します。

## 5. eBay開発者ポータルでの設定

1. [eBay開発者ポータル](https://developer.ebay.com/)にログイン
2. Application Keysページで該当App IDの「Notifications」リンクをクリック
3. 以下の情報を入力：
   - メールアドレス
   - エンドポイントURL（上記で設定したHTTPSエンドポイント）
   - 検証トークン（上記で生成した32～80文字の文字列）
4. 「Save」をクリック
5. テスト通知を送信して動作確認

## 6. トラブルシューティング

### チャレンジコードの検証に失敗する場合

1. **検証トークンの確認**
   - 検証トークンが正しく設定されているか確認
   - 余分な空白や改行がないか確認

2. **エンドポイントURLの確認**
   - エンドポイントURLが正確に一致しているか確認
   - クエリパラメータを除いたベースURLを使用しているか確認

3. **ハッシュ計算の確認**
   - チャレンジコード + 検証トークン + エンドポイントURLの順序で連結しているか確認
   - SHA-256ハッシュを使用しているか確認

### 通知が届かない場合

1. **エンドポイントの可用性確認**
   - エンドポイントが公開されており、インターネットからアクセス可能か確認
   - ファイアウォールやセキュリティ設定を確認

2. **HTTPSの確認**
   - 有効なSSL証明書を使用しているか確認
   - 自己署名証明書ではなく、信頼された証明書を使用しているか確認

3. **レスポンスコードの確認**
   - 通知に対して200 OKレスポンスを返しているか確認
   - タイムアウトが発生していないか確認

## まとめ

1. **HTTPS形式の通知エンドポイントURL**
   - 本番環境: 独自ドメイン + サーバー、またはクラウドサービス
   - 開発環境: ngrok、Cloudflare Tunnel、localtunnelなど

2. **検証トークン**
   - 32～80文字の英数字
   - ランダム生成またはUUID

3. **実装とデプロイ**
   - Node.jsまたはPythonでWebhookサーバーを実装
   - Heroku、Vercel、AWS、GCPなどにデプロイ

これらの手順に従って設定することで、eBay APIのProduction Keysetを有効化し、Marketplace Insights APIを利用できるようになります。
