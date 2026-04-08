#!/usr/bin/env python3
"""Gmail MCP Server — watsonx Orchestrate から Gmail を操作する (Plan B: key_value + refresh_token)"""
import os
import json
import base64
import urllib.request
import urllib.parse
from fastmcp import FastMCP

mcp = FastMCP("gmail-mcp")

# WxO key_value connection から注入される環境変数（キー名がそのまま env var 名になる）
REFRESH_TOKEN = os.environ.get("refresh_token", "")
CLIENT_ID = os.environ.get("client_id", "")
CLIENT_SECRET = os.environ.get("client_secret", "")

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _get_access_token() -> str:
    """refresh_token を使って access_token を取得する"""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())
    return tokens["access_token"]


def _gmail_get(path: str, params: dict = None) -> dict:
    """Gmail API への GET リクエスト"""
    access_token = _get_access_token()
    url = f"{GMAIL_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _gmail_post(path: str, body: dict) -> dict:
    """Gmail API への POST リクエスト"""
    access_token = _get_access_token()
    url = f"{GMAIL_API_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


@mcp.tool()
def list_messages(max_results: int = 10) -> str:
    """受信トレイの最新メール一覧を返す。件名・送信者・日付を含む。"""
    data = _gmail_get("/messages", {"labelIds": "INBOX", "maxResults": max_results})
    messages = data.get("messages", [])
    if not messages:
        return "メールが見つかりませんでした。"

    results = []
    for msg in messages:
        detail = _gmail_get(f"/messages/{msg['id']}", [("format", "metadata"), ("metadataHeaders", "Subject"), ("metadataHeaders", "From"), ("metadataHeaders", "Date")])
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        results.append(
            f"ID: {msg['id']}\n"
            f"  件名: {headers.get('Subject', '(件名なし)')}\n"
            f"  送信者: {headers.get('From', '(不明)')}\n"
            f"  日付: {headers.get('Date', '(不明)')}"
        )
    return "\n\n".join(results)


@mcp.tool()
def get_message(message_id: str) -> str:
    """指定した ID のメール本文を返す。message_id は list_messages で取得した ID を使う。"""
    detail = _gmail_get(f"/messages/{message_id}", {"format": "full"})
    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}

    payload = detail.get("payload", {})

    def extract_body(part):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        for p in part.get("parts", []):
            result = extract_body(p)
            if result:
                return result
        return ""

    body = extract_body(payload)
    if not body:
        body = "(本文を取得できませんでした)"

    return (
        f"件名: {headers.get('Subject', '(件名なし)')}\n"
        f"送信者: {headers.get('From', '(不明)')}\n"
        f"日付: {headers.get('Date', '(不明)')}\n"
        f"\n{body}"
    )


@mcp.tool()
def send_message(to: str, subject: str, body: str) -> str:
    """メールを送信する。to: 宛先アドレス、subject: 件名、body: 本文。"""
    raw_message = f"To: {to}\nSubject: {subject}\n\n{body}"
    encoded = base64.urlsafe_b64encode(raw_message.encode()).decode()
    result = _gmail_post("/messages/send", {"raw": encoded})
    return f"送信完了。メッセージ ID: {result.get('id', '不明')}"


if __name__ == "__main__":
    mcp.run()
