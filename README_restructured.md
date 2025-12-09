# 🏥 Medical Audio Transcription & Reporting System

Sistem complet pentru transcrierea audio-ului medical și generarea automată de rapoarte structurate.

## 🗂️ Structura Proiectului

```
📦 projects-voice-to-text-15/
├── 📄 README.md                    # Documentația principală
├── 📄 .gitignore                   # Fișiere ignorate de Git  
├── 📄 main.ipynb                   # Notebook principal (demo complet)
│
├── 📁 core/                        # Module principale
│   ├── medical_entity_extractor.py # Extragere entități medicale
│   └── word_report_generator.py    # Generare rapoarte Word
│
├── 📁 scripts/                     # Script-uri utilitare
│   ├── extract_entities.py         # Script pentru extragere entități
│   └── pipeline_complete.py        # Pipeline complet CLI
│
├── 📁 data/                        # Date și rezultate
│   ├── fhir_observations.json      # Date în format FHIR
│   ├── fisa_pacient_medical_structured.json
│   ├── fisa_pacient_output_generalist.json
│   └── reports/                    # Rapoarte generate
│
├── 📁 config/                      # Configurații
│   └── venv_requirements.txt       # Dependențe Python
│
├── 📁 docs/                        # Documentație
│   ├── QUICK_START.md              # Ghid rapid
│   └── observatii_pipeline.md      # Observații pipeline
│
├── 📁 training/                    # Utilitare pentru antrenare modele
│   ├── model_1/                    # Primul model Whisper
│   └── model_2/                    # Al doilea model
│
├── 📁 templates/                   # Șabloane Word
│   └── template_fisa_pacient.docx  # Șablon raport medical
│
├── 📁 uploads/                     # Audio încărcat
├── 📁 outputs/                     # Output-uri diverse
├── 📁 dataset/                     # Date de antrenament
└── 📁 tests/                       # Teste (viitor)
```

## 🚀 Utilizare Rapidă

### 1. Instalare
```bash
pip install -r config/venv_requirements.txt
```

### 2. Rulare completă în Jupyter
```bash
jupyter notebook main.ipynb
```

### 3. Pipeline complet CLI
```bash
python scripts/pipeline_complete.py path/to/audio.wav
```

## 🔧 Componente Principale

### `core/medical_entity_extractor.py`
- Extragere entități medicale din transcripții
- Support pentru măsurători ecografice, medicamente, simptome
- Export în format JSON și FHIR

### `core/word_report_generator.py` 
- Generare rapoarte Word formatate
- Support pentru șabloane personalizate
- Output profesional pentru medici

### `main.ipynb`
- Demo complet interactiv
- Pipeline pas cu pas
- Vizualizare rezultate
- API FastAPI integrat

## 📊 Workflow

```
🎵 Audio Input → 📝 Whisper → 🔍 NER → 📋 JSON → 📄 Word Report
```

1. **Audio → Text**: Whisper fine-tuned pentru română medicală
2. **Text → Entități**: Pattern matching medical specializat  
3. **Entități → JSON**: Structurare date + format FHIR
4. **JSON → Word**: Raport formatat pentru medici

## 🛠️ Configurare

Editează `config/venv_requirements.txt` pentru dependențe sau folosește variabilele de mediu pentru configurări avansate.

## 📝 Note

- **Modele**: Whisper și BERT se descarcă automat
- **Performance**: Folosește GPU pentru viteză
- **Formate audio**: .wav, .mp3, .m4a, .mpeg, .flac
- **Limba**: Optimizat pentru română medicală

Pentru detalii complete, vezi `docs/QUICK_START.md`.

---

🏥 **Medical Audio Transcription System** - Sistem profesional pentru transcrierea și raportarea medicală automatizată.