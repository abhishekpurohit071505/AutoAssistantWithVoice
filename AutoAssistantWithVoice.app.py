import streamlit as st
import openai
import requests
import os
from io import BytesIO
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set your OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Lambda endpoint
LAMBDA_API_URL = "https://q3pk9j6x76.execute-api.us-east-1.amazonaws.com/staging/diagnose"

# Streamlit page config
st.set_page_config(page_title="AutoFix Assistant", layout="centered")
st.title("🔧 AutoFix Assistant")
st.subheader("Diagnose and Fix Your Vehicle Problems")

# ---- AUDIO INPUT VIA FILE UPLOAD ----
st.markdown("### 🎤 Speak your issue (optional)")
audio_file = st.file_uploader("Upload your voice (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

# ---- TEXT INPUT ----
user_input = st.text_area("Or type your issue below:", placeholder="e.g., My car is making noise while driving")

# ---- SUBMIT (Unified for Text/Audio) ----
if st.button("🚀 Diagnose"):
    final_input = user_input.strip()

    # Use audio if text input is empty
    if not final_input and audio_file:
        st.info("Transcribing your audio with Whisper...")
        try:
            audio_file.name = "audio.wav"  # Required by Whisper
            transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
            )
            final_input = transcript.text
            st.success(f"Transcribed: {final_input}")
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            final_input = ""

    # If still no input
    if not final_input:
        st.warning("Please type or upload a description of your issue.")
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
