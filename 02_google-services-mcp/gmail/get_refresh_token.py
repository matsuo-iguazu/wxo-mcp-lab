#!/usr/bin/env python3
"""Google OAuth2 refresh_token 取得スクリプト（Plan B 用）"""
import urllib.parse
import urllib.request
import json
import http.server
import threading
import webbrowser

CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send"

auth_code = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write("<h1>OK! Back to terminal.</h1>".encode())

    def log_message(self, format, *args):
        pass  # ログを抑制


# 認証 URL を生成してブラウザで開く
auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
})

print("以下の URL をブラウザで開いてください:\n")
print(auth_url)
print("\n認証後、ブラウザが localhost:8080 にリダイレクトされます...")
server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
t = threading.Thread(target=server.handle_request)
t.start()
t.join()

if not auth_code:
    print("認証コードが取得できませんでした")
    exit(1)

# auth_code を refresh_token に交換
data = urllib.parse.urlencode({
    "code": auth_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

with urllib.request.urlopen(req) as resp:
    tokens = json.loads(resp.read())

print("\n=== 取得成功 ===")
print(f"refresh_token: {tokens.get('refresh_token', 'なし（prompt=consent を確認）')}")
print("\n上記の refresh_token を set-credentials に使用してください。")
