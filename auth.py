from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import urllib.parse
import secrets
import base64
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = "http://127.0.0.1:8888/callback"
login_uri = "http://127.0.0.1:8888/login"

@app.get("/login")
def login():

    state = secrets.token_urlsafe(16)
    scope = 'user-library-read playlist-modify-public playlist-modify-private'

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    }

    auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(params)

    return RedirectResponse(auth_url)

@app.get('/callback')
async def callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if (state == None):
        return RedirectResponse('/#' + urllib.parse.urlencode({'error': 'state_mismatch'}))
    else:
        auth_str = f"{client_id}:{client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://accounts.spotify.com/api/token', 
                data=payload, 
                headers=headers
            )

            tokens = response.json()

            with open(".tokens.json", "w") as f:
                json.dump(tokens, f)
            
            return HTMLResponse(content="""
            <html>
                <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                    <h1 style="color: #1DB954;">Success! ✅</h1>
                    <p>Tokens saved successfully. You can close this window now.</p>
                    <script>
                        setTimeout(function() {
                            window.close();
                        }, 9000);
                    </script>
                </body>
            </html>
            """)