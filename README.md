# AWS_Streamlit
Streamlit + Amazon Transcribe + Amazon Polly

La aplicación en Streamlit permite grabar o subir un archivo de audio que se almacena en Amazon S3 y se envía a Amazon Transcribe, el cual analiza el contenido y lo convierte en texto de forma automática; este texto se muestra en pantalla y puede ser editado por el usuario. A continuación, el texto resultante (o cualquier texto ingresado manualmente) se envía a Amazon Polly, que lo procesa con su motor de síntesis de voz y genera un archivo de audio con voz natural, el cual puede reproducirse directamente en la aplicación o descargarse para su uso posterior.

# Codigo de la función Lambda para crear de texto a audio con Amazon Polly

import boto3
import json
from datetime import datetime

# Configuración AWS
s3 = boto3.client("s3")
polly = boto3.client("polly")

BUCKET_NAME = "guardaaudios"
REGION = "us-east-1"

def lambda_handler(event, context):
    try:
        # Obtener el texto enviado desde Streamlit
        body_json = json.loads(event["body"])
        texto = body_json.get("texto", "").strip()
        
        if not texto:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No se recibió texto para sintetizar"})
            }

        audio_id = f"polly-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.mp3"

        # Amazon Polly
        response = polly.synthesize_speech(
            Text=texto,
            OutputFormat="mp3",
            VoiceId="Lucia"  # Puedes usar otra voz compatible con español
        )

        # Guardar el audio en S3
        audio_stream = response.get("AudioStream")
        if audio_stream:
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_id,
                Body=audio_stream.read(),
                ContentType="audio/mpeg"
            )
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "No se generó el audio en Polly"})
            }

        # Devolver URL accesible del audio
        audio_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{audio_id}"

        return {
            "statusCode": 200,
            "body": json.dumps({"audio_url": audio_url})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

