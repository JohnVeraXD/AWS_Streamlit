import streamlit as st
import requests
import base64
import json
from datetime import datetime

# Configuración
API_TRANSCRIBE = "https://xw92ygr212.execute-api.us-east-1.amazonaws.com/default/fxTranscribeAudio"
API_POLLY = "https://ohff8f7yfk.execute-api.us-east-1.amazonaws.com/default/fxPollyCrearAudio"

# Interfaz
st.set_page_config(layout="centered")
st.title("🎧 Transcripción de Audio con AWS")

# Estados
if "transcripcion" not in st.session_state:
    st.session_state.transcripcion = {"texto": "", "audio_url": ""}
if "texto_editable" not in st.session_state:
    st.session_state.texto_editable = "Escribe o sube un audio para transcribir..."

# --- Procesamiento de Audio ---
uploaded_audio = st.file_uploader("Sube tu archivo de audio (MP3)", type=["mp3"])

# --- Conversión de audio a texto ---

if uploaded_audio:
    st.audio(uploaded_audio, format="audio/mp3")
    
    if st.button("Transcribir", type="primary"):
        with st.spinner("Procesando (esto puede tomar 1-3 minutos)..."):
            try:
                audio_bytes = uploaded_audio.read()
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8").replace("\n","")
                
                payload = {"body": audio_b64}
                response = requests.post(API_TRANSCRIBE, json=payload, timeout=300)
                
                if response.status_code == 200:
                    api_resp = response.json()
                    body_dict = json.loads(api_resp["body"]) if "body" in api_resp else api_resp
                    
                    st.session_state.transcripcion = {
                        "texto": body_dict["texto_transcrito"],
                        "audio_url": body_dict["audio_url"]
                    }

                    st.session_state.texto_editable = st.session_state.transcripcion["texto"]
                    
                    st.success("Transcripción completada")
                else:
                    api_resp = response.json()
                    error_data = json.loads(api_resp.get("body", "{}"))
                    st.error(f"Error: {error_data.get('error','Desconocido')}")
            except Exception as e:
                st.error(f"Error crítico: {str(e)}")


st.subheader("✏️ Texto para Polly")
st.session_state.texto_editable = st.text_area(
    "Texto editable (se actualizará con la transcripción si subes audio):",
    value=st.session_state.texto_editable,
    height=200
)


if st.session_state.transcripcion.get("audio_url"):
    st.markdown(f"""
    **Audio original:**  
    [Descargar]({st.session_state.transcripcion["audio_url"]})  
    `{st.session_state.transcripcion["audio_url"]}`
    """)

# --- Síntesis de voz con Polly ---
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
                api_resp = response.json()
                error_data = json.loads(api_resp.get("body", "{}"))
                st.error(f"Error al generar audio: {error_data.get('error','Desconocido')}")
        except Exception as e:
            st.error(f"Error crítico al generar audio: {str(e)}")