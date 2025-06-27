import streamlit as st
import requests
import base64

# Spotify Credentials
CLIENT_ID = '1edc6e0d85734aa48b49dc4d31919d8d'
CLIENT_SECRET = 'a862b0b0d41b4d469ffe61a537b3a243'

def get_spotify_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}"
    }
    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    return response.json().get("access_token", None)

def get_artist_id(name, token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": name, "type": "artist", "limit": 1}
    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    items = response.json().get("artists", {}).get("items", [])
    return (items[0]['id'], items[0]) if items else (None, None)

def get_artist_albums(artist_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {"include_groups": "album,single", "market": "IN", "limit": 50}
    albums, next_url = [], url

    while next_url:
        resp = requests.get(next_url, headers=headers, params=params)
        data = resp.json()
        albums.extend(data.get("items", []))
        next_url = data.get("next")
        params = None
    return albums

def get_album_tracks(album_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    params = {"limit": 50}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("items", [])

def fetch_50_tracks(artist_name):
    token = get_spotify_token()
    if not token:
        return None, "Could not fetch Spotify token."

    artist_id, artist_info = get_artist_id(artist_name, token)
    if not artist_id:
        return None, f"No artist found for '{artist_name}'"

    albums = get_artist_albums(artist_id, token)
    track_list, seen = [], set()

    for album in albums:
        tracks = get_album_tracks(album['id'], token)
        for track in tracks:
            if track['name'] not in seen:
                seen.add(track['name'])
                track['album_image'] = album['images'][0]['url'] if album['images'] else None
                track_list.append(track)
            if len(track_list) >= 50:
                break
        if len(track_list) >= 50:
            break

    return {"artist": artist_info, "tracks": track_list}, None

# --- Streamlit UI ---
st.set_page_config(page_title="Spotify Songs Viewer", layout="wide")

st.title("🎵 Spotify Artist Songs Viewer")
artist_input = st.text_input("Enter artist name:", "Arijit Singh")

if st.button("Fetch Songs"):
    with st.spinner("Fetching songs..."):
        data, error = fetch_50_tracks(artist_input)

    if error:
        st.error(error)
    elif data:
        artist = data['artist']
        tracks = data['tracks']

        st.subheader(f"🎤 {artist['name']}")
        if artist['images']:
            st.image(artist['images'][0]['url'], width=200)
        st.write(f"Followers: {artist['followers']['total']:,}")

        st.markdown("### 🎶 Top 50 Tracks")

        cols = st.columns(5)
        for i, track in enumerate(tracks):
            with cols[i % 5]:
                st.markdown(f"**{track['name']}**")
                if track['preview_url']:
                    st.audio(track['preview_url'])
                else:
                    st.write("No preview available.")
                if track['album_image']:
                    st.image(track['album_image'], use_column_width=True)
                st.markdown(
                    f"[▶️ Play on Spotify](https://open.spotify.com/track/{track['id']})",
                    unsafe_allow_html=True
                )
