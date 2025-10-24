# Ghid de Fine-Tuning Model NER pentru Domeniul Medical Românesc

## 📚 Introducere

Acest ghid descrie pașii necesari pentru a crea un model NER custom, specializat pe domeniul medical românesc, care să identifice cu acuratețe maximă entități precum:
- **MASURARE_ECOGRAFICA** (ex: "Aorta la inel", "Valva aortică")
- **VALOARE_NUMERICA** (ex: "8mm", "opt milimetri")
- **MEDICAMENT** (ex: "Aspenter", "Algocalmin 500mg")
- **SIMPTOM** (ex: "dureri toracice", "dispnee")
- **DIAGNOSTIC** (ex: "hipertensiune arterială", "insuficiență cardiacă")
- **STRUCTURA_ANATOMICA** (ex: "ventricul stâng", "atriu drept")

## 🎯 Obiective

- ✅ Acuratețe >95% pentru entități medicale specifice
- ✅ Robustețe la variații lingvistice (sinonime, abrevieri)
- ✅ Performanță în timp real (<100ms pe transcripție medie)

## 📋 Prerequisite

### Hardware
- **Minim**: GPU cu 8GB VRAM (ex: RTX 3060)
- **Recomandat**: GPU cu 16-24GB VRAM (ex: RTX 4090, L40S)
- **Alternativă**: Google Colab (T4 GPU gratuit, 15GB VRAM)

### Software
```bash
pip install transformers datasets accelerate evaluate seqeval
pip install label-studio  # Pentru anotarea datelor
```

## 📊 Pas 1: Pregătirea Setului de Date

### 1.1. Colectare Date

**Obiectiv**: Minim 500-1000 transcripții medicale anotate

**Surse posibile**:
- Înregistrări audio din clinici (cu consimțământ GDPR)
- Rapoarte medicale sintetizate cu TTS
- Dataset-uri publice medicale traduse/adaptate

### 1.2. Instalare și Configurare Label Studio

```bash
# Instalare
pip install label-studio

# Pornire server
label-studio start
```

Accesează: http://localhost:8080

### 1.3. Configurare Proiect în Label Studio

**Template XML pentru NER Medical**:

```xml
<View>
  <Header value="Anotare Entități Medicale - Limba Română"/>
  
  <Text name="text" value="$text"/>
  
  <Labels name="label" toName="text">
    <!-- Măsurători -->
    <Label value="MASURARE_ECOGRAFICA" background="#FF6B6B"/>
    <Label value="VALOARE_NUMERICA" background="#4ECDC4"/>
    <Label value="UNITATE_MASURA" background="#45B7D1"/>
    
    <!-- Anatomie -->
    <Label value="STRUCTURA_ANATOMICA" background="#FFA07A"/>
    <Label value="ORGAN" background="#98D8C8"/>
    
    <!-- Clinice -->
    <Label value="SIMPTOM" background="#F7DC6F"/>
    <Label value="DIAGNOSTIC" background="#BB8FCE"/>
    
    <!-- Tratament -->
    <Label value="MEDICAMENT" background="#85C1E2"/>
    <Label value="DOZAJ" background="#52B788"/>
    <Label value="FRECVENTA" background="#74C69D"/>
    
    <!-- General -->
    <Label value="PROCEDURA_MEDICALA" background="#AED9E0"/>
    <Label value="DATA" background="#D4A5A5"/>
  </Labels>
</View>
```

### 1.4. Exemplu de Date Anotate (Format CoNLL)

Creează fișier `data/train.conll`:

```
Aorta	B-STRUCTURA_ANATOMICA
la	I-STRUCTURA_ANATOMICA
inel	I-STRUCTURA_ANATOMICA
,	O
opt	B-VALOARE_NUMERICA
milimetri	B-UNITATE_MASURA
.	O

Valva	B-STRUCTURA_ANATOMICA
aortică	I-STRUCTURA_ANATOMICA
,	O
treisprezece	B-VALOARE_NUMERICA
mm	B-UNITATE_MASURA
.	O

Pacientul	O
prezintă	O
dureri	B-SIMPTOM
toracice	I-SIMPTOM
.	O

Diagnostic	O
:	O
hipertensiune	B-DIAGNOSTIC
arterială	I-DIAGNOSTIC
.	O
```

### 1.5. Script pentru Export din Label Studio

```python
import json
from label_studio_sdk import Client

# Conectează la Label Studio
ls = Client(url='http://localhost:8080', api_key='YOUR_API_KEY')

# ID-ul proiectului
project = ls.get_project(id=1)

# Exportă anotările
annotations = project.export_tasks()

# Convertește în format CoNLL
def convert_to_conll(annotations):
    with open('data/medical_ner_train.conll', 'w', encoding='utf-8') as f:
        for task in annotations:
            text = task['data']['text']
            labels = task['annotations'][0]['result']
            
            # Procesare token-uri și etichete
            # ... (implementare detaliată)
            
convert_to_conll(annotations)
```

## 🏗️ Pas 2: Fine-Tuning Modelul

### 2.1. Script Complet de Fine-Tuning

```python
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorForTokenClassification
)
from evaluate import load as load_metric
import numpy as np

# ========== CONFIGURARE ==========
MODEL_NAME = "dumitrescustefan/bert-base-romanian-cased-v1"
OUTPUT_DIR = "./model_ner_medical_ro"

# Definire etichete
label_list = [
    "O",  # Outside
    "B-MASURARE_ECOGRAFICA", "I-MASURARE_ECOGRAFICA",
    "B-VALOARE_NUMERICA", "I-VALOARE_NUMERICA",
    "B-UNITATE_MASURA", "I-UNITATE_MASURA",
    "B-STRUCTURA_ANATOMICA", "I-STRUCTURA_ANATOMICA",
    "B-SIMPTOM", "I-SIMPTOM",
    "B-DIAGNOSTIC", "I-DIAGNOSTIC",
    "B-MEDICAMENT", "I-MEDICAMENT",
    "B-DOZAJ", "I-DOZAJ",
]

label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for i, label in enumerate(label_list)}

# ========== ÎNCĂRCARE DATE ==========
dataset = load_dataset("conll2003")  # Înlocuiește cu calea la datele tale

# ========== TOKENIZARE ȘI ALINIERE ETICHETE ==========
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_and_align_labels(examples):
    """
    Funcție critică: aliniază etichetele cu token-urile de subcuvinte
    Conform Secțiunii 2.3 din ghid
    """
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
        max_length=512
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        
        for word_idx in word_ids:
            if word_idx is None:
                # Token special ([CLS], [SEP], [PAD])
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # Primul subcuvânt al unui token → eticheta reală
                label_ids.append(label[word_idx])
            else:
                # Subcuvintele ulterioare → -100 (ignorate în loss)
                label_ids.append(-100)
            
            previous_word_idx = word_idx
        
        labels.append(label_ids)
    
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# Aplică tokenizarea
tokenized_datasets = dataset.map(
    tokenize_and_align_labels,
    batched=True,
    remove_columns=dataset["train"].column_names
)

# ========== MODEL ȘI METRICI ==========
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label_list),
    id2label=id2label,
    label2id=label2id
)

# Colector de date
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# Metrica seqeval (nivel entitate, nu token)
metric = load_metric("seqeval")

def compute_metrics(p):
    """
    Calculează Precision, Recall, F1 la nivel de entitate
    Conform Secțiunii 4.1 din ghid
    """
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Elimină etichetele ignorate (-100)
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# ========== ANTRENAMENT ==========
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    warmup_steps=500,
    logging_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    fp16=True,  # Precizie mixtă pentru viteză
    push_to_hub=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# Pornește antrenamentul
trainer.train()

# Salvează modelul final
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"✅ Model salvat în: {OUTPUT_DIR}")
```

## 📈 Pas 3: Evaluare și Validare

### 3.1. Script de Testare

```python
from transformers import pipeline

# Încarcă modelul antrenat
ner_pipeline = pipeline(
    "ner",
    model=OUTPUT_DIR,
    tokenizer=OUTPUT_DIR,
    aggregation_strategy="simple"
)

# Test
text = """
Aorta la inel, opt milimetri. Valva aortică, treisprezece milimetri.
Pacientul prezintă dureri toracice. Diagnostic: hipertensiune arterială.
Tratament: Aspenter 500mg, două ori pe zi.
"""

entities = ner_pipeline(text)

for entity in entities:
    print(f"{entity['entity_group']:25} → {entity['word']:30} (score: {entity['score']:.2f})")
```

### 3.2. Interpretare Rezultate

| Metrică | Obiectiv | Interpretare |
|---------|----------|--------------|
| F1 Score | >0.90 | Echilibru între precizie și recall |
| Precision | >0.92 | Cât de multe predicții sunt corecte |
| Recall | >0.88 | Câte entități reale sunt detectate |

**Acțiuni dacă F1 < 0.90**:
- ✅ Adaugă mai multe date de antrenament (500+ exemple)
- ✅ Verifică calitatea anotărilor (inter-annotator agreement)
- ✅ Ajustează hiperparametrii (learning rate, batch size)
- ✅ Folosește augmentare de date (sinonime, parafrazare)

## 🚀 Pas 4: Integrare în Pipeline

### 4.1. Înlocuire Pattern Matching cu Model Fine-Tuned

Modifică `medical_entity_extractor.py`:

```python
from transformers import pipeline

class MedicalEntityExtractor:
    def __init__(self, model_path="./model_ner_medical_ro"):
        # Încarcă modelul fine-tuned
        self.ner_pipeline = pipeline(
            "ner",
            model=model_path,
            tokenizer=model_path,
            aggregation_strategy="simple"
        )
    
    def extract_all_entities(self, text: str) -> FisaPacient:
        """Extrage entități folosind modelul fine-tuned"""
        entities = self.ner_pipeline(text)
        
        # Grupare pe tipuri
        masuratori = []
        medicamente = []
        simptome = []
        diagnostice = []
        
        for entity in entities:
            if entity['entity_group'] == 'MASURARE_ECOGRAFICA':
                # Extrage și valoarea numerică asociată
                # ...
                masuratori.append({...})
            elif entity['entity_group'] == 'MEDICAMENT':
                medicamente.append({...})
            # ...
        
        return FisaPacient(
            masuratori_ecografice=masuratori,
            medicamente=medicamente,
            simptome=simptome,
            diagnostice=diagnostice,
            observatii=[]
        )
```

## 📊 Pas 5: Monitorizare și Îmbunătățire Continuă

### 5.1. Logging Predicții

```python
import logging
from datetime import datetime

# Configurare logging
logging.basicConfig(
    filename=f'predictions_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO
)

# La fiecare predicție
logging.info({
    'timestamp': datetime.now().isoformat(),
    'text': text,
    'entities': entities,
    'confidence_avg': np.mean([e['score'] for e in entities])
})
```

### 5.2. Feedback Loop

1. **Colectare**: Salvează predicții cu scor scăzut (<0.80)
2. **Revizie**: Verifică manual și corectează
3. **Re-antrenare**: Adaugă exemplele corecte în setul de date
4. **Validare**: Testează modelul actualizat

## 🎓 Resurse Suplimentare

### Dataset-uri Medicale (Posibil Adaptabile)
- **i2b2/n2c2**: https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/
- **MIMIC-III**: https://mimic.mit.edu/ (engleză, tradus cu mT5)

### Modele de Bază Recomandate
- `dumitrescustefan/bert-base-romanian-cased-v1`
- `readerbench/RoBERT-base`
- `dumitrescustefan/bert-base-romanian-uncased-v1`

### Referințe Academice
- Devlin et al. (2019): "BERT: Pre-training of Deep Bidirectional Transformers"
- Vaswani et al. (2017): "Attention Is All You Need"
- Ma & Hovy (2016): "End-to-end Sequence Labeling via Bi-directional LSTM-CNNs-CRF"

## ✅ Checklist Final

- [ ] Colectate >500 transcripții medicale
- [ ] Anotate cu Label Studio (inter-annotator agreement >0.85)
- [ ] Convertite în format CoNLL
- [ ] Split train/val/test (70%/15%/15%)
- [ ] Fine-tuning complet cu logging
- [ ] Evaluare: F1 >0.90
- [ ] Integrare în pipeline
- [ ] Testare end-to-end
- [ ] Monitorizare predicții
- [ ] Plan de re-antrenare trimestrială

---

**💡 TIP**: Începe cu un subset mic (50 exemple) pentru a valida pipeline-ul înainte de a anota 500+ exemple!

