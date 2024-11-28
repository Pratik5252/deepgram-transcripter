import pyaudio
import wave
import asyncio
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from config import DEEPGRAM_API_KEY

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "recordedFile.wav"


# Async function to stream audio to Deepgram in real-time
async def transcribe_stream():
    # Open audio stream
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    print("Recording started... Speak into the microphone.")

    # Open the WAV file for writing
    wave_file = wave.open(WAVE_OUTPUT_FILENAME, "wb")
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(audio.get_sample_size(FORMAT))
    wave_file.setframerate(RATE)

    try:
        deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = deepgram.listen.websocket.v("1")

        # Process transcript in real-time
        def process_transcript(self, result, **kwargs):
            if result.channel:
                transcript = result.channel.alternatives[0].transcript
                words = transcript.split()
                for word in words:
                    print(word, end=" ", flush=True)
                # print(f"Transcript: {transcript}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, process_transcript)

        options = LiveOptions(
            model="nova-2",
            language="multi",
            encoding="linear16",
            sample_rate=RATE,
            interim_results=False,
        )

        if not dg_connection.start(options):
            print("Failed to start Deepgram connection")
            raise Exception("Deepgram connection failed")
        else:
            print("Deepgram Connection Successful")

        while True:
            # Read audio data from the microphone
            data = stream.read(CHUNK, exception_on_overflow=False)

            # Send the audio chunk to Deepgram
            dg_connection.send(data)

            # Write the audio chunk to the WAV file
            wave_file.writeframes(data)

    except KeyboardInterrupt:
        print("\nStopping transcription.")

    finally:
        # Stop audio stream and close connections
        dg_connection.finish()
        stream.stop_stream()
        stream.close()
        wave_file.close()
        audio.terminate()
        print("Audio saved to", WAVE_OUTPUT_FILENAME)


# Run the async function
asyncio.run(transcribe_stream())