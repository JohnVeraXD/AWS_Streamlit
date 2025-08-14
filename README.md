# Streamlit + Amazon Transcribe + Amazon Polly

https://johnveraxd-aws-streamlit-app-audio-zsbbrq.streamlit.app/

La aplicación en Streamlit permite grabar o subir un archivo de audio que se almacena en Amazon S3 y se envía a Amazon Transcribe, el cual analiza el contenido y lo convierte en texto de forma automática; este texto se muestra en pantalla y puede ser editado por el usuario. A continuación, el texto resultante (o cualquier texto ingresado manualmente) se envía a Amazon Polly, que lo procesa con su motor de síntesis de voz y genera un archivo de audio con voz natural, el cual puede reproducirse directamente en la aplicación o descargarse para su uso posterior.

# Codigo de la función Lambda para convertir el auido a texto con Amazon Transcribe y guardado en Amazon S3

    import boto3
    import base64
    from datetime import datetime
    import json
    import time
    import urllib.request
    
    s3 = boto3.client("s3")
    transcribe = boto3.client("transcribe")
    
    BUCKET_NAME = "guardaaudios"
    REGION = "us-east-1"
    
    def lambda_handler(event, context):
        try:
            # Decodificar audio
            body = base64.b64decode(event["body"])
            
            audio_id = f"audio-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.mp3"
            
            # Subir a S3
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=audio_id,
                Body=body,
                ContentType="audio/mpeg"
            )
            
            job_name = audio_id.replace(".", "-")
            
            # Iniciar transcripción
            transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f's3://{BUCKET_NAME}/{audio_id}'},
                MediaFormat='mp3',  
                LanguageCode='es-ES', 
                OutputBucketName=BUCKET_NAME,
                OutputKey=f"transcripciones/{job_name}.json"
            )
            
            while True:
                status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
                    break
                time.sleep(2)
            
            if status["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "Error en transcripción"})
                }
            
            transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            with urllib.request.urlopen(transcript_uri) as response:
                transcript_data = json.loads(response.read().decode('utf-8'))
            
            transcript_text = transcript_data["results"]["transcripts"][0]["transcript"]
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "texto_transcrito": transcript_text,
                    "audio_url": f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{audio_id}"
                })
            }
        
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }


# Codigo de la función Lambda para crear de texto a audio con Amazon Polly y guardando en Amazon S3

    import boto3
    import json
    from datetime import datetime
    
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

