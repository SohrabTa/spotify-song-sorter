from flask import Flask, redirect, request
import requests
import urllib.parse
import secrets
import string

app = Flask(__name__)

CLIENT_ID = "fc905c176efe4246968394312ee2c4e4"
CLIENT_SECRET = "59f2d7e5bb7e4a0bb240112a329484ce"
REDIRECT_URI = "http://localhost:8888/callback"


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login")
def login():
    state = generate_random_string(16)
    scope = "user-read-private user-read-email playlist-read-private playlist-modify-private"
    query_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
        query_params
    )
    return redirect(url)


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for i in range(length))
    return random_string


@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        return f"Error: {error}"
    if code:
        access_token = fetch_spotify_token(code)
        auth_header = {"Authorization": f"Bearer {access_token}"}
        user_playlists = get_current_user_playlists(auth_header)
        user_tracks = get_current_user_tracks(auth_header)
        return format_playlists_info(user_playlists)
    return "No code provided"


def fetch_spotify_token(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error fetching token: {response.status_code}")


def get_current_user_playlists(auth_header):
    url = "https://api.spotify.com/v1/me/playlists"
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching playlists: {response.status_code}")


def get_current_user_tracks(auth_header):
    url = "https://api.spotify.com/v1/me/tracks"
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching tracks: {response.status_code}")


def format_playlists_info(response):
    formatted_info = ""
    if "items" in response:
        for i, playlist in enumerate(response["items"], start=1):
            formatted_info += f"Playlist {i}:\n"
            formatted_info += f"  Name: {playlist.get('name', 'N/A')}\n"
            formatted_info += (
                f"  Description: {playlist.get('description', 'No description')}\n"
            )
            formatted_info += (
                f"  Playlist URL: {playlist['external_urls']['spotify']}\n"
            )
            formatted_info += f"  Total Tracks: {playlist['tracks']['total']}\n"
            formatted_info += f"  Public: {'Yes' if playlist['public'] else 'No'}\n\n"
    else:
        formatted_info = "No playlists found.\n"
    return formatted_info


if __name__ == "__main__":
    app.run(port=8888, debug=True)
