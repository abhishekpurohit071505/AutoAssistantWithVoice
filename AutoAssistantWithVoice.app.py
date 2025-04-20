import streamlit as st
import openai
import requests
import os
from io import BytesIO

openai.api_key = st.secrets["OPENAI_API_KEY"]
LAMBDA_API_URL = "https://q3pk9j6x76.execute-api.us-east-1.amazonaws.com/staging/diagnose"

st.set_page_config(page_title="AutoFix Assistant", layout="centered")
st.title("🔧 AutoFix Assistant")
st.subheader("Diagnose and Fix Your Vehicle Problems")

# Initialize session state for audio input
if "audio_input" not in st.session_state:
    st.session_state.audio_input = None

# ---- 🎙️ AUDIO INPUT CONTROLS ----
st.markdown("### 🎤 Speak your issue (optional):")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🎙️ Record"):
        st.info("Recording... speak now.")
        audio_bytes = st.audio_recorder("Recording...", pause_threshold=3)
        if audio_bytes:
            st.session_state.audio_input = audio_bytes
            st.audio(audio_bytes, format="audio/wav")

with col2:
    if st.button("❌ Cancel"):
        st.session_state.audio_input = None
        st.success("Audio input cancelled.")

# ---- TEXT INPUT ----
user_input = st.text_area("Or type your issue below:", placeholder="e.g., My car is making noise while driving")

# ---- SUBMIT (Unified for Text/Audio) ----
if st.button("🚀 Diagnose"):
    final_input = user_input.strip()

    # Fallback to audio transcription if text input is empty
    if not final_input and st.session_state.audio_input:
        st.info("No text entered — transcribing your audio with Whisper...")
        try:
            audio_file = BytesIO(st.session_state.audio_input)
            audio_file.name = "audio.wav"
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            final_input = transcript["text"]
            st.success(f"Transcribed: {final_input}")
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            final_input = ""

    if not final_input:
        st.warning("Please type or record a description of your issue.")
    else:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(LAMBDA_API_URL, json={"query": final_input})
                if response.status_code == 200:
                    report = response.json()
                    st.success("Diagnosis Complete!")
                    st.markdown(f"**🔍 Problem:** {report.get('input', 'N/A')}")

                    diagnosis = report.get("diagnosis", "")
                    if "Reason:" in diagnosis:
                        cause = diagnosis.split("Cause:", 1)[1].split("Reason:")[0].strip()
                        reason = diagnosis.split("Reason:", 1)[1].strip()
                    else:
                        cause, reason = diagnosis, ""

                    st.markdown(f"**💥 Cause:** {cause}")
                    st.markdown(f"**🧠 Reason:** {reason}")
                    st.markdown("---")
                    st.markdown(f"**🛠 Fix Guide:**\n\n{report.get('fix_guide', '')}", unsafe_allow_html=True)
                else:
                    st.error(f"Lambda error: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"Error during processing: {e}")
