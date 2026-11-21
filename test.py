
import streamlit as st
import yt_dlp
import tempfile
import shutil
import os
from pathlib import Path
from urllib.parse import urlparse

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="YouTube to MP3 Converter",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 YouTube to MP3 Converter")
st.write("Paste a YouTube video URL and convert its audio into MP3.")

# ---------------- FFMPEG CONFIG ----------------

FFMPEG_PATH = shutil.which("ffmpeg")

# Optional custom FFmpeg path
if not FFMPEG_PATH:
    custom_path = os.environ.get("FFMPEG_PATH")
    if custom_path and Path(custom_path).is_file():
        FFMPEG_PATH = custom_path

# ---------------- USER INPUT ----------------

youtube_url = st.text_input(
    "Enter YouTube URL",
    placeholder="https://www.youtube.com/watch?v=..."
)

quality = st.selectbox(
    "Select MP3 Bitrate",
    ["128", "192", "256", "320"],
    index=1
)

# ---------------- URL VALIDATION ----------------

def valid_youtube_url(url):
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc.lower().split(":")[0]

        return (
            parsed.scheme in ("http", "https")
            and domain in (
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
                "youtu.be",
                "www.youtu.be"
            )
        )
    except Exception:
        return False


# ---------------- CONVERSION ----------------

if st.button("Convert to MP3", type="primary"):

    if not youtube_url.strip():
        st.warning("Please enter a YouTube URL.")
        st.stop()

    if not valid_youtube_url(youtube_url):
        st.error("Please enter a valid YouTube URL.")
        st.stop()

    if not FFMPEG_PATH:
        st.error(
            "FFmpeg not found. Please install FFmpeg "
            "using packages.txt on Streamlit Cloud."
        )
        st.stop()

    try:
        with tempfile.TemporaryDirectory() as temp:

            temp_dir = Path(temp)

            options = {
                "format": "bestaudio/best",

                "outtmpl": str(
                    temp_dir / "audio.%(ext)s"
                ),

                "ffmpeg_location": FFMPEG_PATH,

                "noplaylist": True,

                "quiet": True,
                "no_warnings": True,

                # Prefer IPv4 if IPv6 routing is problematic
                "force_ipv4": True,

                # YouTube extraction configuration
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": quality
                    }
                ]
            }

            with st.spinner(
                "Downloading and converting audio... Please wait."
            ):

                with yt_dlp.YoutubeDL(options) as ydl:

                    info = ydl.extract_info(
                        youtube_url.strip(),
                        download=True
                    )

                # Locate generated MP3
                output_files = list(
                    temp_dir.glob("*.mp3")
                )

                if not output_files:
                    st.error("MP3 file was not generated.")
                    st.stop()

                output_file = output_files[0]

                audio_data = output_file.read_bytes()

                video_title = info.get(
                    "title",
                    "converted_audio"
                )

            # ---------------- SUCCESS ----------------

            st.success("Audio converted successfully!")

            st.subheader("Conversion Details")

            st.write(f"**Video:** {video_title}")
            st.write("**Format:** MP3")
            st.write(f"**Bitrate:** {quality} kbps")

            file_size = len(audio_data) / (1024 * 1024)

            st.write(
                f"**File size:** {file_size:.2f} MB"
            )

            st.download_button(
                label="⬇️ Download MP3",
                data=audio_data,
                file_name="converted_audio.mp3",
                mime="audio/mpeg",
                type="primary"
            )

    except yt_dlp.utils.DownloadError as error:

        st.error(
            "YouTube refused the download request (or "
            "the video is unavailable)."
        )

        st.info(
            "HTTP 403 can indicate a YouTube restriction "
            "on the hosting server. Updating yt-dlp may "
            "help, but cannot guarantee a fix."
        )

        with st.expander("Technical error details"):
            st.code(str(error))

    except Exception as error:

        st.error("Conversion failed!")

        with st.expander("Technical error details"):
            st.exception(error)
