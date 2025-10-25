
def process_audio_to_json(audio_path, output_json_path):
    print("Transcribing audio...")
    transcription = transcribe_audio(audio_path)
    print("Transcription:", transcription)

    print("Extracting entities...")
    structured_data = extract_entities(transcription)
    print("Structured Data:", structured_data)

    with open(output_json_path, "w") as json_file:
        json.dump(structured_data, json_file, indent=4, ensure_ascii=False)
    print(f"Data saved to {output_json_path}")

if __name__ == "__main__":
    audio_file_path = "uploads/exempleNoisy.mpeg"  
    output_json = "output_data.json"

    process_audio_to_json(audio_file_path, output_json)
