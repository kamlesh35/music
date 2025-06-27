import streamlit as st
import requests
import base64

# --- Spotify Credentials ---
CLIENT_ID = '1edc6e0d85734aa48b49dc4d31919d8d'
CLIENT_SECRET = 'a862b0b0d41b4d469ffe61a537b3a243'

# --- Get Access Token ---
def get_spotify_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    return response.json().get("access_token", None)

# --- Search Songs by Title / Artist ---
def search_tracks(query, limit=10):
    token = get_spotify_token()
    if not token:
        return None, "❌ Could not fetch token."

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "track", "limit": limit, "market": "IN"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None, "❌ Failed to search tracks."

    items = response.json().get("tracks", {}).get("items", [])
    results = []
    for track in items:
        results.append({
            "name": track['name'],
            "artists": ", ".join(a['name'] for a in track['artists']),
            "image": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "spotify_url": track['external_urls']['spotify'],
            "preview_url": track.get("preview_url")
        })
    return results, None

# --- Get New Releases ---
def fetch_new_releases(limit=10, country="IN"):
    token = get_spotify_token()
    if not token:
        return None, "❌ Could not fetch Spotify token."

    url = "https://api.spotify.com/v1/browse/new-releases"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"country": country, "limit": limit}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None, "❌ Failed to fetch new releases."

    albums = response.json().get("albums", {}).get("items", [])
    songs = []
    for album in albums:
        songs.append({
            "name": album['name'],
            "artists": ", ".join(a['name'] for a in album['artists']),
            "image": album['images'][0]['url'] if album['images'] else None,
            "spotify_url": album['external_urls']['spotify'],
            "preview_url": None
        })

    return songs, None

# --- Streamlit UI ---
st.set_page_config(page_title="🎧 Spotify Search & Trending", layout="wide")
st.title("🎧Music Explorer")

# --- Search Form ---
with st.form("search_form"):
    search_query = st.text_input("Search by song title or artist name:", "Search here")
    search_button = st.form_submit_button("🔍 Search")

# --- Logic ---
if search_button and search_query.strip():
    songs, error = search_tracks(search_query)
    st.subheader(f"🔍 Results for: '{search_query}'")
else:
    songs, error = fetch_new_releases()
    st.subheader("🆕 Latest New Releases")

# --- Display Results ---
if error:
    st.error(error)
elif songs:
    cols = st.columns(5)
    for i, song in enumerate(songs):
        with cols[i % 5]:
            st.image(song['image'], use_column_width=True)
            st.markdown(f"**{song['name']}**")
            st.caption(f"🎤 {song['artists']}")
            if song.get("preview_url"):
                st.audio(song['preview_url'])
            st.markdown(
                f"[▶️ Listen on Spotify]({song['spotify_url']})",
                unsafe_allow_html=True
            )
