import streamlit as st
import requests
import base64
import json
from datetime import datetime
from streamlit_mic_recorder import mic_recorder

API_TRANSCRIBE = "https://xw92ygr212.execute-api.us-east-1.amazonaws.com/default/fxTranscribeAudio"
API_POLLY = "https://ohff8f7yfk.execute-api.us-east-1.amazonaws.com/default/fxPollyCrearAudio"

st.set_page_config(layout="wide")
st.title("🎧 Transcripción y Síntesis de Voz con AWS")

if "transcripcion" not in st.session_state:
    st.session_state.transcripcion = {"texto": "", "audio_url": ""}
if "texto_editable" not in st.session_state:
    st.session_state.texto_editable = "Escribe o graba un audio para transcribir..."
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "audio_ext" not in st.session_state:
    st.session_state.audio_ext = "mp3"  

col1, col2 = st.columns(2)

# ==================  Procesamiento de Audio ==================
with col1:
    st.header("🎙 Procesamiento de Audio")

    metodo = st.radio("Selecciona el método de entrada:", ["Subir archivo", "Grabar audio"])

    if metodo == "Subir archivo":
        uploaded_audio = st.file_uploader("Sube un archivo de audio (MP3)", type=["mp3"])
        if uploaded_audio:
            st.audio(uploaded_audio, format="audio/mp3")
            st.session_state.audio_bytes = uploaded_audio.read()
            st.session_state.audio_ext = "mp3"

    elif metodo == "Grabar audio":
        # mic_recorder devuelve WAV (PCM)
        audio_data = mic_recorder(start_prompt="🎤 Grabar", stop_prompt="⏹ Detener", key="recorder")
        if audio_data:
            st.audio(audio_data["bytes"], format="audio/wav")
            st.session_state.audio_bytes = audio_data["bytes"]
            st.session_state.audio_ext = "wav"  # <- importante

    if st.session_state.audio_bytes and st.button("Transcribir"):
        with st.spinner("Procesando (1-3 minutos)..."):
            try:
                audio_b64 = base64.b64encode(st.session_state.audio_bytes).decode("utf-8")
                payload = {"body": audio_b64}

                # Pasa el formato a Lambda vía querystring
                url = f"{API_TRANSCRIBE}?ext={st.session_state.audio_ext}"
                response = requests.post(url, json=payload, timeout=300)

                if response.status_code == 200:
                    api_resp = response.json()
                    body_dict = json.loads(api_resp["body"]) if "body" in api_resp else api_resp

                    st.session_state.transcripcion = {
                        "texto": body_dict["texto_transcrito"],
                        "audio_url": body_dict["audio_url"]
                    }
                    st.session_state.texto_editable = st.session_state.transcripcion["texto"]
                    st.success("✅ Transcripción completada")
                else:
                    error_data = json.loads(response.json().get("body", "{}"))
                    st.error(f"Error: {error_data.get('error', 'Desconocido')}")
            except Exception as e:
                st.error(f"Error crítico: {str(e)}")

# ================== Síntesis de voz con Polly ==================
with col2:
    st.header("🗣 Síntesis de voz con Polly")

    st.session_state.texto_editable = st.text_area(
        "Texto editable para Polly:",
        value=st.session_state.texto_editable,
        height=200
    )

    if st.session_state.transcripcion.get("audio_url"):
        st.markdown(f"""
        **Audio original:**  
        [Descargar]({st.session_state.transcripcion["audio_url"]})  
        `{st.session_state.transcripcion["audio_url"]}`
        """)

    if st.button("Generar audio con Polly"):
        with st.spinner("Generando audio..."):
            try:
                payload = {"texto": st.session_state.texto_editable}
                response = requests.post(API_POLLY, json=payload, timeout=300)

                if response.status_code == 200:
                    api_resp = response.json()
                    body_dict = json.loads(api_resp["body"]) if "body" in api_resp else api_resp
                    audio_polly_url = body_dict["audio_url"]

                    st.success("✅ Audio generado con Polly")
                    st.audio(audio_polly_url, format="audio/mp3")
                    st.markdown(f"[⬇️ Descargar audio generado]({audio_polly_url})")
                else:
                    error_data = json.loads(response.json().get("body", "{}"))
                    st.error(f"Error: {error_data.get('error', 'Desconocido')}")
            except Exception as e:
                st.error(f"Error crítico: {str(e)}")
