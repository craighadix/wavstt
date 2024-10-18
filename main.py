import os
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage

# Configure environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/service_account.json"
BUCKET_NAME = "wav_input"
OUTPUT_BUCKET_NAME = "wav_transcribe_out"  # Bucket to store transcriptions

def transcribe_gcs(gcs_uri):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""

    client = speech.SpeechClient()

    audio   = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",   
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)   

    # Extract the transcript
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    # Save the transcript to a text file in GCS
    output_filename = os.path.splitext(os.path.basename(gcs_uri))[0] + ".txt"
    output_uri = f"gs://{OUTPUT_BUCKET_NAME}/{output_filename}"
    storage_client = storage.Client()
    bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
    blob = bucket.blob(output_filename)
    blob.upload_from_string(transcript)

    print(f"Transcription saved to: {output_uri}")


def process_new_file(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    print(f"Processing   file: {file['name']}.")   

    # Check if the file is a WAV file
    if not file['name'].lower().endswith('.wav'):
        print(f"Skipping non-WAV file: {file['name']}")
        return

    gcs_uri = f"gs://{BUCKET_NAME}/{file['name']}"
    transcribe_gcs(gcs_uri)


# For local testing
if __name__ == "__main__":
    # Replace with a real GCS URI of your WAV file
    test_gcs_uri = "gs://your-gcs-bucket-name/your-audio-file.wav"
    transcribe_gcs(test_gcs_uri)