from __future__ import annotations

import argparse
import getpass
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: "OAuthServer"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        self.server.authorization_code = query.get("code", [""])[0]
        self.server.authorization_error = query.get("error", [""])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>OAuth complete</h1><p>You can return to the terminal.</p></body></html>"
        )

    def log_message(self, format: str, *args) -> None:
        return


class OAuthServer(HTTPServer):
    authorization_code = ""
    authorization_error = ""


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Google Drive OAuth refresh token.")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", default="")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    client_secret = args.client_secret or getpass.getpass("Google OAuth client secret: ")
    redirect_uri = f"http://{args.host}:{args.port}/oauth2callback"
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": args.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": DRIVE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    authorization_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("Opening browser for Google OAuth consent.")
    print(f"Redirect URI must be allowed in the OAuth client: {redirect_uri}")
    print("If the browser does not open, paste this URL manually:")
    print(authorization_url)
    webbrowser.open(authorization_url)

    server = OAuthServer((args.host, args.port), OAuthCallbackHandler)
    server.handle_request()

    if server.authorization_error:
        raise SystemExit(f"OAuth error: {server.authorization_error}")
    if not server.authorization_code:
        raise SystemExit("No authorization code received.")

    tokens = exchange_code_for_tokens(
        args.client_id,
        client_secret,
        server.authorization_code,
        redirect_uri,
    )
    refresh_token = tokens.get("refresh_token", "")
    if not refresh_token:
        raise SystemExit(
            "No refresh_token returned. Revoke the app grant in Google Account permissions and retry with prompt=consent."
        )

    print("\nAdd this to Streamlit Secrets. Do not commit it:")
    print("[connections.gdrive.oauth]")
    print(f'client_id = "{args.client_id}"')
    print(f'client_secret = "{client_secret}"')
    print(f'refresh_token = "{refresh_token}"')
    print('token_uri = "https://oauth2.googleapis.com/token"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
