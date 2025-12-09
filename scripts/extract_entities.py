#!/usr/bin/env python3
"""
Script pentru extragerea entităților medicale din transcripții audio
"""

import sys
import os
import json

# Adaugă calea către directorul părinte pentru a accesa core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.medical_entity_extractor import MedicalEntityExtractor


def extract_entities_from_text(text):
    """Extrage entități din text folosind extractorul medical specializat"""
    extractor = MedicalEntityExtractor()
    fisa_pacient = extractor.extract_all_entities(text)
    return fisa_pacient


def process_audio_to_json(audio_path, output_json_path):
    """Procesează fișier audio și salvează entitățile în JSON"""
    print("Transcribing audio...")
    # Aici ar trebui să implementezi transcrierea audio
    # Pentru moment, folosim un placeholder
    transcription = "Exemplu transcripție audio medical"
    print(f"Transcription: {transcription}")

    print("Extracting entities...")
    fisa_pacient = extract_entities_from_text(transcription)
    
    print("Structured Data extracted successfully")

    # Salvare în JSON
    extractor = MedicalEntityExtractor()
    extractor.save_to_json(fisa_pacient, output_json_path)
    print(f"Data saved to {output_json_path}")


if __name__ == "__main__":
    audio_file_path = "uploads/exempleNoisy.mpeg"  
    output_json = "data/output_data.json"

    process_audio_to_json(audio_file_path, output_json)
