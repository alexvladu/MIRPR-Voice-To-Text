#!/usr/bin/env python3
"""
Pipeline Complet: Audio → Fisa Pacient (Format Word)
Demonstreaza intreaga arhitectura: ASR → NER → JSON → FHIR → DOCX
"""

import sys
import os
from datetime import datetime
from pathlib import Path


def check_dependencies():
    """Verifica dacă toate dependentele sunt instalate"""
    required = {
        'torch': 'PyTorch',
        'transformers': 'Hugging Face Transformers',
        'soundfile': 'SoundFile',
        'torchaudio': 'TorchAudio',
        'docx': 'python-docx',
        'docxtpl': 'docxtpl'
    }

    missing = []
    for module, name in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(name)

    if missing:
        print(f"Dependențe lipsă: {', '.join(missing)}")
        print("\n Instalează cu: pip install -r venv_requirements.txt")
        return False

    return True


def main(audio_path: str = None):
    """
    Pipeline complet de procesare

    Args:
        audio_path: Calea catre fisierul audio (optional)
    """
    print("=" * 100)
    print(" " * 20 + "SISTEM INTELIGENT DE AUTOMATIZARE A FISEI PACIENTULUI")
    print("=" * 100)

    # Verifică dependențele
    if not check_dependencies():
        return

    # Importuri (după verificarea dependențelor)
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    import soundfile as sf
    import torchaudio
    import torch
    from medical_entity_extractor import MedicalEntityExtractor
    from word_report_generator import generate_word_report

    # Determină fișierul audio
    if audio_path is None:
        # Caută primul fișier in uploads/
        upload_dir = Path("uploads")
        audio_files = list(upload_dir.glob("*.wav")) + list(upload_dir.glob("*.ogg")) + list(upload_dir.glob("*.mp3"))

        if not audio_files:
            print("Niciun fișier audio găsit in directorul 'uploads/'")
            print("Plasează un fisier .wav, .ogg sau .mp3 in 'uploads/' și reincearca")
            return

        audio_path = str(audio_files[0])

    print(f"\n📁 Fișier audio: {audio_path}")

    # ========== PASUL 1: ASR (Audio → Text) ==========
    print("\n" + "=" * 100)
    print("PASUL 1: RECUNOASTERE VOCALA (ASR)")
    print("=" * 100)

    model_name = "TransferRapid/whisper-large-v3-turbo_ro"

    try:
        processor = WhisperProcessor.from_pretrained(model_name)
        model = WhisperForConditionalGeneration.from_pretrained(model_name)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        print(f"Model incărcat cu succes (dispozitiv: {device})")

    except Exception as e:
        print(f"Eroare la incarcarea modelului: {e}")
        return

    print("\nSe transcrie audio...")

    try:
        waveform_np, sample_rate = sf.read(audio_path, dtype='float32')
        waveform = torch.from_numpy(waveform_np)

        #Convert stereo -> mono if needed
        if len(waveform.shape) > 1:
            waveform = waveform.mean(dim=1)

        # Resample la 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)

        waveform_np = waveform.numpy() if isinstance(waveform, torch.Tensor) else waveform
        inputs = processor(waveform_np, sampling_rate=16000, return_tensors="pt")
        inputs = {key: val.to(device) for key, val in inputs.items()}

        forced_decoder_ids = processor.tokenizer.get_decoder_prompt_ids(language="romanian", task="transcribe")

        with torch.no_grad():
            generated_ids = model.generate(inputs["input_features"], forced_decoder_ids=forced_decoder_ids)

        transcript = processor.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        print(f"Transcriere completă ({len(transcript)} caractere)")
        print(f"\nTRANSCRIPȚIE:\n{'-' * 100}")
        print(transcript)
        print("-" * 100)

    except Exception as e:
        print(f"Eroare la transcriere: {e}")
        return

    # ========== PASUL 2: NER (Text → Entități) ==========
    print("\n" + "=" * 100)
    print("PASUL 2: EXTRACȚIE ENTITATI MEDICALE (NER)")
    print("=" * 100)

    print("\n🔍 Se extrag entitatile medicale folosind pattern matching...")

    try:
        extractor = MedicalEntityExtractor()
        fisa_pacient = extractor.extract_all_entities(transcript)

        print("Extractie completa\n")

        print("📋MASURĂTORI ECOGRAFICE:")
        print("-" * 100)
        if fisa_pacient.masuratori_ecografice:
            for i, masurare in enumerate(fisa_pacient.masuratori_ecografice, 1):
                print(f"   {i}. {masurare['structura_anatomica'].upper()}: {masurare['valoare_numerica']} {masurare['unitate_masura']}")
        else:
            print("   Nicio măsurătoare detectată")

        print("\nMEDICAMENTE:")
        print("-" * 100)
        if fisa_pacient.medicamente:
            for med in fisa_pacient.medicamente:
                print(f"   • {med['nume']} - {med['dozaj']} ({med['frecventa']})")
        else:
            print("   ⚠️  Niciun medicament detectat")

        print("\nSIMPTOME:")
        print("-" * 100)
        if fisa_pacient.simptome:
            for simptom in fisa_pacient.simptome:
                print(f"   • {simptom}")
        else:
            print("     Niciun simptom detectat")

        print("\nDIAGNOSTICE:")
        print("-" * 100)
        if fisa_pacient.diagnostice:
            for diagnostic in fisa_pacient.diagnostice:
                print(f"   • {diagnostic}")
        else:
            print("   ⚠️  Niciun diagnostic detectat")

    except Exception as e:
        print(f"Eroare la extractia entitatilor: {e}")
        return

    # ========== PASUL 3: Salvare JSON + FHIR ==========
    print("\n" + "=" * 100)
    print("PASUL 3: STRUCTURARE DATE (JSON + FHIR R4)")
    print("=" * 100)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = f"fisa_pacient_{timestamp}.json"

    try:
        extractor.save_to_json(fisa_pacient, json_path)
        print(f"✅ Date salvate in: {json_path}")

    except Exception as e:
        print(f"❌ Eroare la salvarea JSON: {e}")
        return

    # ========== PASUL 4: Generare Raport Word ==========
    print("\n" + "=" * 100)
    print("PASUL 4: GENERARE RAPORT WORD")
    print("=" * 100)

    raport_path = f"raport_medical_{timestamp}.docx"

    try:
        print("\n📄 Se generează raportul Word...")
        generate_word_report(
            json_path=json_path,
            output_path=raport_path,
            use_template=False
        )

        print(f"\n✅ Raport Word generat: {raport_path}")

    except Exception as e:
        print(f"❌ Eroare la generarea raportului: {e}")
        return

    # ========== FINALIZARE ==========
    print("\n" + "=" * 100)
    print("🎉 PIPELINE COMPLET FINALIZAT CU SUCCES!")
    print("=" * 100)

    print("\n📊 FIȘIERE GENERATE:")
    print(f"   ✅ JSON structurat: {json_path}")
    print(f"   ✅ Raport Word:     {raport_path}")

    print("\n💡 URMATORII PAȘI:")
    print("   1. Deschide raportul Word pentru a verifica rezultatele")
    print("   2. Personalizează template-ul pentru branding-ul tău medical")
    print("   3. Consideră fine-tuning model NER pentru acuratețe >95%")
    print("   4. Integrează cu sistemul medical existent (FHIR, HL7)")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if not os.path.exists(audio_file):
            print(f"❌ Fisierul nu exista: {audio_file}")
            sys.exit(1)
        main(audio_file)
    else:
        main()

