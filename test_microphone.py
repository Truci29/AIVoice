import pyttsx3

# Initialize text-to-speech engine
engine = pyttsx3.init()

# List available voices
voices = engine.getProperty("voices")
for i, voice in enumerate(voices):
    print(f"Voice {i}:")
    print(f" - ID: {voice.id}")
    print(f" - Name: {voice.name}")
    print(f" - Language: {voice.languages}")
    print(f" - Gender: {voice.gender}")
    print(f" - Age: {voice.age}")