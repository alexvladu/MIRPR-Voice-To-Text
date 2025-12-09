Observații privind pipeline-ul:

- Pipeline-ul inițial a dus la o performanță foarte scăzută.
- S-a încercat segmentarea textului audio inițial în mai multe părți și deși performanța crește, există riscul de a se tăia video-ul în mijlocul unui cuvânt și atunci se pierde informație posibil prețioasă.
- In cazul in care segmentarea nu este una fixa, ci una bazata pe media frecventei dupa o anumita perioada de timp atunci performanta ramane una crescuta si informatia nu se pierde
- Dupa o prima etapa de fine-tuning, modelul bert, prezinta o performanta mai ridicata si un grad de clasificare mai ridicat
- Performanta medie pentru wer este: 1.0, iar pentru cer: 0.996996996996997
- Dupa un fine-tuning pentru modelul Whisper cu un set redus de date creat de la 0 performanta a crescut considerabil
- Performanta medie pentru wer este: 22.47, iar pentru cer: 4.55
