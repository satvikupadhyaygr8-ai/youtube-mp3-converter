
import streamlit as st
import yt_dlp
import tempfile
import shutil
from pathlib import Path

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

# Fallback to your known installation path
if not FFMPEG_PATH:
    fallback = Path(r"C:\ffmpeg\bin\ffmpeg.exe")
    if fallback.is_file():
        FFMPEG_PATH = str(fallback)

if FFMPEG_PATH:
    FFMPEG_DIR = str(Path(FFMPEG_PATH).parent)
else:
    FFMPEG_DIR = None

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

# ---------------- CONVERSION ----------------

if st.button("Convert to MP3", type="primary"):

    if not youtube_url.strip():
        st.warning("Please enter a YouTube URL.")
        st.stop()

    if not FFMPEG_DIR:
        st.error("FFmpeg not found. Please check installation.")
        st.stop()

    try:
        with tempfile.TemporaryDirectory() as temp:

            temp_dir = Path(temp)

            options = {
                "format": "bestaudio/best",
                "outtmpl": str(temp_dir / "audio.%(ext)s"),
                "ffmpeg_location": FFMPEG_DIR,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,

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

                output_file = temp_dir / "audio.mp3"

                if not output_file.exists():
                    st.error("MP3 file was not generated.")
                    st.stop()

                audio_data = output_file.read_bytes()

                video_title = info.get(
                    "title",
                    "converted_audio"
                )

            # ---------------- SUCCESS ----------------

            st.success("Audio converted successfully!")

            st.subheader("Conversion Details")

            st.write(f"**Video:** {video_title}")
            st.write(f"**Format:** MP3")
            st.write(f"**Bitrate:** {quality} kbps")
            st.write(
                f"**File size:** {len(audio_data) / (1024 * 1024):.2f} MB"
            )

            st.download_button(
                label="⬇️ Download MP3",
                data=audio_data,
                file_name="converted_audio.mp3",
                mime="audio/mpeg",
                type="primary"
            )

    except Exception as error:

        st.error("Conversion failed!")
        st.exception(error)
