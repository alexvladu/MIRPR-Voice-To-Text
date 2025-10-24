"""
Extractor de Entități Medicale pentru Transcripții în Limba Română
Folosește pattern matching și reguli pentru a extrage date structurate din transcripții medicale
până la implementarea unui model NER fine-tuned pe date medicale.
"""

import re
import json
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import inflect

@dataclass
class MasuratoareEcografica:
    """Structură pentru o măsurătoare ecografică"""
    structura_anatomica: str
    valoare_numerica: float
    unitate_masura: str = "mm"

@dataclass
class FisaPacient:
    """Structură pentru fișa pacientului - compatibil cu FHIR"""
    masuratori_ecografice: List[Dict[str, Any]]
    simptome: List[str]
    diagnostice: List[str]
    medicamente: List[Dict[str, str]]
    observatii: List[str]

class MedicalEntityExtractor:
    """Extractor de entități medicale din transcripții în limba română"""

    def __init__(self):
        # Dicționar pentru conversia numerelor în cifre
        self.numere_text_to_cifre = {
            'zero': 0, 'unu': 1, 'doi': 2, 'doua': 2, 'două': 2, 'trei': 3, 'patru': 4,
            'cinci': 5, 'șase': 6, 'sase': 6, 'șapte': 7, 'sapte': 7, 'opt': 8,
            'noua': 9, 'nouă': 9, 'zece': 10, 'unsprezece': 11, 'doisprezece': 12,
            'doisprezece': 12, 'treisprezece': 13, 'paisprezece': 14, 'paispe': 14,
            'cincisprezece': 15, 'șaisprezece': 16, 'saisprezece': 16, 'șaptesprezece': 17,
            'saptesprezece': 17, 'optsprezece': 18, 'nouăsprezece': 19, 'nouasprezece': 19,
            'douăzeci': 20, 'douazeci': 20, 'treizeci': 30, 'patruzeci': 40, 'cincizeci': 50
        }

        # Pattern-uri pentru structuri anatomice comune în ecografii
        self.structuri_anatomice_cardio = [
            r'aorta\s+la\s+inel',
            r'aorta\s+la\s+sinusuri',
            r'aort[ăa]\s+ascendent[ăa]',
            r'valva\s+aortic[ăa]',
            r'valva\s+mitral[ăa]',
            r'ventricul\s+stâng',
            r'ventricul\s+drept',
            r'atriu\s+stâng',
            r'atriu\s+drept',
            r'sept\s+interventricular',
            r'perete\s+posterior',
            r'fracție\s+de\s+ejecție',
            r'diametru\s+telediastolic',
            r'diametru\s+telesistolic'
        ]

        # Pattern-uri pentru medicamente comune
        self.medicamente_comune = [
            'aspenter', 'algocalmin', 'paracetamol', 'ibuprofen', 'nurofen',
            'concor', 'bisoprolol', 'enalapril', 'losartan', 'amlodipină',
            'atorvastatină', 'simvastatină', 'metformin', 'insulină'
        ]

        # Pattern-uri pentru simptome
        self.simptome_comune = [
            'dureri toracice', 'durere toracică', 'dispnee', 'dificultate în respirație',
            'palpitații', 'amețeli', 'oboseală', 'cefalee', 'tuse', 'febră'
        ]

    def text_to_number(self, text: str) -> float:
        """Convertește un număr scris în text în cifră"""
        text = text.lower().strip()

        # Verifică dacă este deja un număr
        try:
            return float(text)
        except ValueError:
            pass

        # Verifică dicționarul
        if text in self.numere_text_to_cifre:
            return float(self.numere_text_to_cifre[text])

        # Încearcă să proceseze numere compuse (ex: "douăzeci și trei")
        if 'și' in text or 'si' in text:
            parts = re.split(r'\s+și\s+|\s+si\s+', text)
            total = 0
            for part in parts:
                if part.strip() in self.numere_text_to_cifre:
                    total += self.numere_text_to_cifre[part.strip()]
            if total > 0:
                return float(total)

        return None

    def extract_masuratori_ecografice(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrage măsurătorile ecografice din text.
        Pattern: "structura anatomică, valoare numerică" sau "structura anatomică: valoare"
        """
        masuratori = []

        # Normalizare text
        text_norm = text.lower()

        # Pattern 1: "structura, număr" (ex: "aorta la inel, opt")
        for pattern in self.structuri_anatomice_cardio:
            # Caută pattern-ul urmat de virgulă și număr
            regex = rf'({pattern})[,:\s]+([a-zăâîșț]+|\d+(?:[.,]\d+)?)\s*(mm|cm|m)?'
            matches = re.finditer(regex, text_norm, re.IGNORECASE)

            for match in matches:
                structura = match.group(1).strip()
                valoare_text = match.group(2).strip()
                unitate = match.group(3) if match.group(3) else 'mm'

                # Convertește valoarea în număr
                valoare = self.text_to_number(valoare_text)

                if valoare is not None:
                    masuratori.append({
                        'structura_anatomica': structura,
                        'valoare_numerica': valoare,
                        'unitate_masura': unitate,
                        'tip_masurare': 'ecografie_cardiaca'
                    })

        return masuratori

    def extract_medicamente(self, text: str) -> List[Dict[str, str]]:
        """Extrage medicamentele și dozajele din text"""
        medicamente = []
        text_norm = text.lower()

        for medicament in self.medicamente_comune:
            if medicament in text_norm:
                # Caută dozaj în apropiere
                pattern = rf'{medicament}\s*(\d+\s*mg|\d+\s*g|o\s+tabletă|două\s+tablete)?'
                match = re.search(pattern, text_norm)

                if match:
                    dozaj = match.group(1) if match.group(1) else 'nedefinit'
                    medicamente.append({
                        'nume': medicament.capitalize(),
                        'dozaj': dozaj.strip(),
                        'frecventa': 'conform prescripție'
                    })

        return medicamente

    def extract_simptome(self, text: str) -> List[str]:
        """Extrage simptomele menționate în text"""
        simptome = []
        text_norm = text.lower()

        for simptom in self.simptome_comune:
            if simptom in text_norm:
                simptome.append(simptom.capitalize())

        return simptome

    def extract_diagnostice(self, text: str) -> List[str]:
        """Extrage diagnosticele din text"""
        diagnostice = []
        text_norm = text.lower()

        # Pattern-uri pentru diagnostice comune
        pattern_diagnostic = r'diagnostic[:\s]+([^.]+)'
        matches = re.finditer(pattern_diagnostic, text_norm)

        for match in matches:
            diagnostic = match.group(1).strip()
            diagnostice.append(diagnostic.capitalize())

        return diagnostice

    def extract_all_entities(self, text: str) -> FisaPacient:
        """Extrage toate entitățile medicale din text"""

        masuratori = self.extract_masuratori_ecografice(text)
        simptome = self.extract_simptome(text)
        diagnostice = self.extract_diagnostice(text)
        medicamente = self.extract_medicamente(text)

        # Observații generale (restul textului care nu s-a potrivit)
        observatii = []
        if not masuratori and not simptome and not diagnostice:
            observatii.append("Text neprocesabil - necesită revizuire manuală")

        return FisaPacient(
            masuratori_ecografice=masuratori,
            simptome=simptome,
            diagnostice=diagnostice,
            medicamente=medicamente,
            observatii=observatii
        )

    def to_fhir_observation(self, masuratori: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convertește măsurătorile în format FHIR Observation
        Conform standardului HL7 FHIR R4
        """
        fhir_observations = []

        for i, masurare in enumerate(masuratori):
            observation = {
                "resourceType": "Observation",
                "id": f"obs-{i+1}",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "imaging",
                        "display": "Imaging"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "79376-8",  # LOINC code pentru ecografie cardiacă
                        "display": masurare['structura_anatomica']
                    }],
                    "text": masurare['structura_anatomica']
                },
                "valueQuantity": {
                    "value": masurare['valoare_numerica'],
                    "unit": masurare['unitate_masura'],
                    "system": "http://unitsofmeasure.org",
                    "code": masurare['unitate_masura']
                },
                "interpretation": [{
                    "text": f"Măsurătoare ecografică: {masurare['structura_anatomica']}"
                }]
            }

            fhir_observations.append(observation)

        return fhir_observations

    def to_json(self, fisa_pacient: FisaPacient, pretty: bool = True) -> str:
        """Convertește fișa pacientului în JSON"""
        data = asdict(fisa_pacient)

        # Adaugă și format FHIR
        data['fhir_observations'] = self.to_fhir_observation(fisa_pacient.masuratori_ecografice)

        if pretty:
            return json.dumps(data, indent=4, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def save_to_json(self, fisa_pacient: FisaPacient, filepath: str):
        """Salvează fișa pacientului în fișier JSON"""
        json_data = self.to_json(fisa_pacient)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print(f"✅ Fișa pacientului salvată în: {filepath}")


# Funcție helper pentru testare rapidă
def process_medical_transcription(transcription: str, output_path: str = None) -> Dict:
    """
    Procesează o transcriere medicală și returnează datele structurate

    Args:
        transcription: Textul transcris
        output_path: Calea unde să salveze JSON-ul (opțional)

    Returns:
        Dict cu datele extrase
    """
    extractor = MedicalEntityExtractor()
    fisa_pacient = extractor.extract_all_entities(transcription)

    if output_path:
        extractor.save_to_json(fisa_pacient, output_path)

    # Returnează și ca dicționar pentru procesare ulterioară
    return json.loads(extractor.to_json(fisa_pacient))


# Exemplu de utilizare
if __name__ == "__main__":
    # Test cu transcrierea din problema ta
    transcription_test = """
    Aorta la inel, opt, aorta la sinusuri, doisprezece, aortă ascendentă, zece, 
    a se treisprezece, vede, șase, vede, șase, vede, șase, vede, șase, 
    vede, valva aortică, valva aortică, veice, treisprezece, bară șase, bară șase.
    """

    print("=" * 80)
    print("EXTRACȚIE ENTITĂȚI MEDICALE - TEST")
    print("=" * 80)

    result = process_medical_transcription(
        transcription_test,
        output_path="fisa_pacient_medical_structured.json"
    )

    print("\n📊 REZULTAT EXTRACȚIE:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("✅ Procesare completă!")
    print("=" * 80)

