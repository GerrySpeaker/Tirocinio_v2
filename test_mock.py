# test_mock.py — eseguilo con: python test_mock.py
from app.models import mock_lipnet_trascrizione, calcola_wer, calcola_cer

casi = [
    ("perfetta",   "ciao come stai"),
    ("realistica", "buongiorno a tutti"),
    ("pessima",    "mi chiamo marco"),
    ("vuota",      "arrivederci"),
]

for modalita, frase in casi:
    trascrizione = mock_lipnet_trascrizione(frase, modalita=modalita)
    wer = calcola_wer(frase, trascrizione)
    cer = calcola_cer(frase, trascrizione)
    superato = wer <= 0.25

    print(f"\n[{modalita.upper()}]")
    print(f"  Attesa:      '{frase}'")
    print(f"  Trascritto:  '{trascrizione}'")
    print(f"  WER: {wer*100:.1f}%  CER: {cer*100:.1f}%")
    print(f"  Livello superato: {'✅' if superato else '❌'}")