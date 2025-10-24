"""
Generator de Rapoarte Word pentru Fișa Pacientului
Folosește python-docx-template (docxtpl) pentru a genera rapoarte formatate
din datele JSON structurate extrase din transcripții medicale.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


class MedicalReportGenerator:
    """Generator de rapoarte Word pentru fișa pacientului"""

    def __init__(self, template_path: str = None):
        """
        Inițializează generatorul de rapoarte

        Args:
            template_path: Calea către șablonul Word (opțional)
        """
        self.template_path = template_path

    def load_json_data(self, json_path: str) -> Dict[str, Any]:
        """Încarcă datele din fișierul JSON"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_simple_report_without_template(self, json_path: str, output_path: str):
        """
        Creează un raport Word simplu fără șablon (folosind python-docx)
        Util când nu ai un șablon predefinit
        """
        # Încarcă datele
        data = self.load_json_data(json_path)

        # Creează un document nou
        doc = Document()

        # Adaugă header
        header = doc.sections[0].header
        header_para = header.paragraphs[0]
        header_para.text = "RAPORT MEDICAL - ECOGRAFIE CARDIACĂ"
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Titlu
        title = doc.add_heading('FIȘA PACIENTULUI', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Informații generale
        doc.add_heading('Informații Generale', level=1)
        info_table = doc.add_table(rows=2, cols=2)
        info_table.style = 'Light Grid Accent 1'

        # Date raport
        info_table.rows[0].cells[0].text = 'Data raportului:'
        info_table.rows[0].cells[1].text = datetime.now().strftime("%d.%m.%Y %H:%M")
        info_table.rows[1].cells[0].text = 'Tip investigație:'
        info_table.rows[1].cells[1].text = 'Ecografie cardiacă'

        # Măsurători ecografice
        doc.add_heading('Măsurători Ecografice', level=1)

        if data.get('masuratori_ecografice'):
            # Creează tabel pentru măsurători
            masuratori_table = doc.add_table(rows=1, cols=3)
            masuratori_table.style = 'Light Grid Accent 1'

            # Header tabel
            hdr_cells = masuratori_table.rows[0].cells
            hdr_cells[0].text = 'Structură Anatomică'
            hdr_cells[1].text = 'Valoare'
            hdr_cells[2].text = 'Unitate'

            # Adaugă măsurătorile
            for masurare in data['masuratori_ecografice']:
                row_cells = masuratori_table.add_row().cells
                row_cells[0].text = masurare['structura_anatomica'].capitalize()
                row_cells[1].text = str(masurare['valoare_numerica'])
                row_cells[2].text = masurare['unitate_masura']
        else:
            doc.add_paragraph('Nu au fost identificate măsurători ecografice.')

        # Medicamente
        doc.add_heading('Medicație Prescrisă', level=1)

        if data.get('medicamente'):
            for med in data['medicamente']:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(f"{med['nume']}").bold = True
                p.add_run(f" - {med['dozaj']}, {med['frecventa']}")
        else:
            doc.add_paragraph('Nu au fost identificate medicamente.')

        # Simptome
        doc.add_heading('Simptome Raportate', level=1)

        if data.get('simptome'):
            for simptom in data['simptome']:
                doc.add_paragraph(simptom, style='List Bullet')
        else:
            doc.add_paragraph('Nu au fost identificate simptome.')

        # Diagnostice
        doc.add_heading('Diagnostic', level=1)

        if data.get('diagnostice'):
            for diagnostic in data['diagnostice']:
                doc.add_paragraph(diagnostic, style='List Bullet')
        else:
            doc.add_paragraph('Nu au fost identificate diagnostice.')

        # Observații
        if data.get('observatii'):
            doc.add_heading('Observații', level=1)
            for obs in data['observatii']:
                doc.add_paragraph(obs)

        # Footer
        doc.add_paragraph()
        footer_para = doc.add_paragraph()
        footer_para.add_run('___________________________').italic = True
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_para = doc.add_paragraph('Semnătura medicului')
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Salvează documentul
        doc.save(output_path)
        print(f"✅ Raport Word generat cu succes: {output_path}")

    def create_report_with_template(self, json_path: str, template_path: str, output_path: str):
        """
        Creează un raport Word folosind un șablon existent (cu docxtpl)
        Șablonul trebuie să conțină variabile Jinja2
        """
        # Încarcă datele
        data = self.load_json_data(json_path)

        # Încarcă șablonul
        doc = DocxTemplate(template_path)

        # Pregătește contextul pentru șablon
        context = {
            'data_raport': datetime.now().strftime("%d.%m.%Y"),
            'ora_raport': datetime.now().strftime("%H:%M"),
            'masuratori': data.get('masuratori_ecografice', []),
            'medicamente': data.get('medicamente', []),
            'simptome': data.get('simptome', []),
            'diagnostice': data.get('diagnostice', []),
            'observatii': data.get('observatii', []),
            'are_masuratori': len(data.get('masuratori_ecografice', [])) > 0,
            'are_medicamente': len(data.get('medicamente', [])) > 0,
            'are_simptome': len(data.get('simptome', [])) > 0,
            'are_diagnostice': len(data.get('diagnostice', [])) > 0
        }

        # Renderizează șablonul cu datele
        doc.render(context)

        # Salvează documentul
        doc.save(output_path)
        print(f"✅ Raport Word generat din șablon: {output_path}")

    def create_template(self, output_path: str = "template_fisa_pacient.docx"):
        """
        Creează un șablon Word de bază cu variabile Jinja2
        pentru a fi folosit cu docxtpl
        """
        doc = Document()

        # Titlu
        title = doc.add_heading('FIȘA PACIENTULUI', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Informații generale
        doc.add_heading('Informații Generale', level=1)
        doc.add_paragraph('Data raportului: {{ data_raport }} {{ ora_raport }}')
        doc.add_paragraph('Tip investigație: Ecografie cardiacă')

        # Măsurători
        doc.add_heading('Măsurători Ecografice', level=1)
        doc.add_paragraph('{% if are_masuratori %}')
        doc.add_paragraph('{% for masurare in masuratori %}')
        doc.add_paragraph('• {{ masurare.structura_anatomica }}: {{ masurare.valoare_numerica }} {{ masurare.unitate_masura }}')
        doc.add_paragraph('{% endfor %}')
        doc.add_paragraph('{% else %}')
        doc.add_paragraph('Nu au fost identificate măsurători.')
        doc.add_paragraph('{% endif %}')

        # Medicamente
        doc.add_heading('Medicație', level=1)
        doc.add_paragraph('{% if are_medicamente %}')
        doc.add_paragraph('{% for med in medicamente %}')
        doc.add_paragraph('• {{ med.nume }} - {{ med.dozaj }}, {{ med.frecventa }}')
        doc.add_paragraph('{% endfor %}')
        doc.add_paragraph('{% else %}')
        doc.add_paragraph('Nu au fost identificate medicamente.')
        doc.add_paragraph('{% endif %}')

        # Simptome
        doc.add_heading('Simptome', level=1)
        doc.add_paragraph('{% if are_simptome %}')
        doc.add_paragraph('{% for simptom in simptome %}')
        doc.add_paragraph('• {{ simptom }}')
        doc.add_paragraph('{% endfor %}')
        doc.add_paragraph('{% else %}')
        doc.add_paragraph('Nu au fost raportate simptome.')
        doc.add_paragraph('{% endif %}')

        # Diagnostic
        doc.add_heading('Diagnostic', level=1)
        doc.add_paragraph('{% if are_diagnostice %}')
        doc.add_paragraph('{% for diagnostic in diagnostice %}')
        doc.add_paragraph('• {{ diagnostic }}')
        doc.add_paragraph('{% endfor %}')
        doc.add_paragraph('{% else %}')
        doc.add_paragraph('Nu au fost identificate diagnostice.')
        doc.add_paragraph('{% endif %}')

        # Footer
        doc.add_paragraph()
        doc.add_paragraph('___________________________')
        doc.add_paragraph('Semnătura medicului')

        doc.save(output_path)
        print(f"✅ Șablon creat: {output_path}")
        print(f"💡 Poți edita acest șablon în Word și apoi îl poți folosi cu create_report_with_template()")


def generate_word_report(json_path: str, output_path: str = None, use_template: bool = False, template_path: str = None):
    """
    Funcție helper pentru generarea rapidă a raportului Word

    Args:
        json_path: Calea către fișierul JSON cu datele
        output_path: Calea unde să salveze raportul (opțional)
        use_template: Dacă True, folosește un șablon Word
        template_path: Calea către șablonul Word (necesar dacă use_template=True)
    """
    if output_path is None:
        output_path = f"raport_medical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

    generator = MedicalReportGenerator()

    if use_template:
        if template_path is None:
            print("❌ Trebuie să specifici template_path când use_template=True")
            return
        generator.create_report_with_template(json_path, template_path, output_path)
    else:
        generator.create_simple_report_without_template(json_path, output_path)

    return output_path


# Exemplu de utilizare
if __name__ == "__main__":
    print("=" * 80)
    print("GENERATOR RAPOARTE MEDICALE WORD")
    print("=" * 80)

    # Exemplu 1: Creează un raport simplu (fără șablon)
    print("\n1️⃣  Generare raport simplu (fără șablon)...")
    try:
        generate_word_report(
            json_path="fisa_pacient_medical_structured.json",
            output_path="raport_medical_simplu.docx",
            use_template=False
        )
    except FileNotFoundError:
        print("⚠️  Fișierul JSON nu a fost găsit. Rulează mai întâi medical_entity_extractor.py")

    # Exemplu 2: Creează un șablon Word
    print("\n2️⃣  Generare șablon Word...")
    generator = MedicalReportGenerator()
    generator.create_template("template_fisa_pacient.docx")

    # Exemplu 3: Folosește șablonul pentru generarea raportului
    print("\n3️⃣  Generare raport folosind șablonul...")
    try:
        generate_word_report(
            json_path="fisa_pacient_medical_structured.json",
            output_path="raport_medical_cu_template.docx",
            use_template=True,
            template_path="template_fisa_pacient.docx"
        )
    except FileNotFoundError:
        print("⚠️  Fișierul JSON sau șablonul nu au fost găsite.")

    print("\n" + "=" * 80)
    print("✅ PROCESARE COMPLETĂ!")
    print("=" * 80)

