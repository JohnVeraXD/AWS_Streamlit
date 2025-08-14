# AWS_Streamlit
Streamlit + Amazon Transcribe + Amazon Polly

La aplicación en Streamlit permite grabar o subir un archivo de audio que se almacena en Amazon S3 y se envía a Amazon Transcribe, el cual analiza el contenido y lo convierte en texto de forma automática; este texto se muestra en pantalla y puede ser editado por el usuario. A continuación, el texto resultante (o cualquier texto ingresado manualmente) se envía a Amazon Polly, que lo procesa con su motor de síntesis de voz y genera un archivo de audio con voz natural, el cual puede reproducirse directamente en la aplicación o descargarse para su uso posterior.
