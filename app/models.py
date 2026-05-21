# database.py
import random

import cv2
import numpy as np
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Connessione al database
client = MongoClient("mongodb://localhost:27017/")
db = client.labiale_db

livelli_collection = db["livelli_collection"]


# ============ FUNZIONI PER TIPOLOGIE ============

def crea_tipologia(nome, titolo, descrizione, punti_base=10):
    """Crea una nuova tipologia di esercizio"""
    tipologia = {
        "nome": nome,
        "titolo_display": titolo,
        "descrizione": descrizione,
        "punti_base": punti_base,
        "attiva": True,
        "creata_il": datetime.now()
    }
    risultato = db.tipologie_collection.insert_one(tipologia)
    return str(risultato.inserted_id)


def ottieni_tipologie():
    """Ottiene tutte le tipologie attive"""
    tipologie = []
    for tip in db.tipologie_collection.find({"attiva": True}):
        tip['_id'] = str(tip['_id'])
        tipologie.append(tip)
    return tipologie


def trova_tipologia(tipologia_id):
    """Trova una tipologia per ID"""
    return db.tipologie_collection.find_one({"_id": ObjectId(tipologia_id)})


# ============ FUNZIONI PER LIVELLI ============

def crea_livello(numero, titolo, tipologia_id, contenuto, difficolta="medio", sbloccato= True, completato= False):
    """Crea un nuovo livello con un contenuto tipo esercizio mimo labiale"""
    # Trova la tipologia
    tipologia = trova_tipologia(tipologia_id)
    if not tipologia:
        return None
    
    livello = {
        "numero_livello": numero,
        "titolo": titolo,
        "tipologia_id": ObjectId(tipologia_id),
        "tipologia_nome": tipologia['nome'],
        "contenuto": contenuto, # Qui viene aggiunto il contenuto dell'esercizio, che si trova nell'app.py (/livelli)
        "difficolta": difficolta,
        "punti_ricompensa": tipologia.get('punti_base', 10),
        "ordine": numero,
        "attivo": True,
        "sbloccato": sbloccato,         # Questi due dati servono per una visualizzazione dinamica dei livelli
        "completato": completato,
        "creato_il": datetime.now()
    }

    risultato = db.livelli_collection.insert_one(livello)
    return str(risultato.inserted_id)


def ottieni_livelli():
    """Ottiene tutti i livelli ordinati"""
    livelli = []
    
    for liv in db.livelli_collection.find({"attivo": True}).sort("ordine", 1):
        liv['_id'] = str(liv['_id'])
        liv['tipologia_id'] = str(liv['tipologia_id'])
        livelli.append(liv)
    return livelli


def trova_livello(livello_id):
    """Trova un livello per ID"""
    
    return db.livelli_collection.find_one({"_id": ObjectId(livello_id)})

def trova_livello_per_numero(numero):
    """Trova livello per numero_livello"""
    return db.livelli_collection.find_one({"numero_livello": numero, "attivo": True})

# ============ FUNZIONI PER PROGRESSI ============

def calcola_stelle(accuratezza):
    """Calcola le stelle in base all'accuratezza"""
    if accuratezza >= 90:
        return 3  # Oro
    elif accuratezza >= 70:
        return 2  # Argento
    elif accuratezza >= 50:
        return 1  # Bronzo
    return 0


def salva_progresso(utente_id, livello_id, punteggio, accuratezza):
    """Salva o aggiorna il progresso di un utente"""
    livello = trova_livello(livello_id)
    if not livello:
        return None
    
    stelle = calcola_stelle(accuratezza)
    
    # Cerca se esiste già un progresso
    progresso_esistente = db.progressi_collection.find_one({
        "utente_id": utente_id,
        "livello_id": ObjectId(livello_id)
    })
    
    if progresso_esistente:
        # Aggiorna solo se il punteggio è migliore
        if punteggio > progresso_esistente.get('punteggio_migliore', 0):
            db.progressi_collection.update_one(
                {"_id": progresso_esistente['_id']},
                {
                    "$set": {
                        "punteggio_migliore": punteggio,
                        "accuratezza_migliore": accuratezza,
                        "stelle": stelle,
                        "ultimo_tentativo": datetime.now()
                    },
                    "$inc": {"tentativi": 1}
                }
            )
        else:
            db.progressi_collection.update_one(
                {"_id": progresso_esistente['_id']},
                {
                    "$set": {"ultimo_tentativo": datetime.now()},
                    "$inc": {"tentativi": 1}
                }
            )
    else:
        # Crea nuovo progresso
        nuovo_progresso = {
            "utente_id": utente_id,
            "livello_id": ObjectId(livello_id),
            "tipologia_nome": livello['tipologia_nome'],
            "punteggio_migliore": punteggio,
            "accuratezza_migliore": accuratezza,
            "stelle": stelle,
            "tentativi": 1,
            "completato_il": datetime.now(),
            "ultimo_tentativo": datetime.now()
        }
        db.progressi_collection.insert_one(nuovo_progresso)
    
    return stelle


def ottieni_progressi_utente(utente_id):
    """Ottiene tutti i progressi di un utente"""
    progressi = []
    for prog in db.progressi_collection.find({"utente_id": utente_id}):
        prog['_id'] = str(prog['_id'])
        prog['livello_id'] = str(prog['livello_id'])
        progressi.append(prog)
    return progressi


# ============ UTILITY ============

def verifica_connessione():
    """Verifica che MongoDB sia raggiungibile"""
    try:
        client.server_info()
        print("✅ Connessione a MongoDB riuscita!")
        return True
    except Exception as e:
        print(f"❌ Errore connessione MongoDB: {e}")
        return False

# ======= Cambio dei flag di completamento e sblocco ===========

def sblocca_e_completa_livello(livello_id_attuale, livello_id_successivo = None):
    """
    Imposta il livello attuale come completato e, se fornito,
    sblocca il livello successivo.
    """
    # 1) Imposta il livello attuale come completato
    db.livelli_collection.update_one(
        {"_id": ObjectId(livello_id_attuale)},
        {"$set": {"completato": True}}
    )
    
    #2) Se c'è un livello successivo, cambiamo il flag "sbloccato" a True
    if livello_id_successivo:
        db.livelli_collection.update_one(
            {"_id": ObjectId(livello_id_successivo)},
            {"$set": {"sbloccato": True}}
        )

    return True

def ottieni_livello_per_id(livello_id):
    try:
        # Cerca nel database i livello in base all'id
        return db.livelli_collection.find_one({"_id": ObjectId(livello_id)})
    except Exception as e:
        print("Errore nel trovare il livello: {e}")
        return None

# --- CER e WER ---

def _levenshtein(seq1, seq2):
    """Distanza di Levenshtein generica su sequenze (liste o stringhe)."""
    n, m = len(seq1), len(seq2)
    # matrice (n+1) x (m+1)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, m + 1):
            temp = dp[j]
            if seq1[i - 1] == seq2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[m]


def calcola_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate — distanza a livello di caratteri."""
    if len(reference) == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0
    return _levenshtein(reference, hypothesis) / len(reference)


def calcola_wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate — distanza a livello di parole."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0
    return _levenshtein(ref_words, hyp_words) / len(ref_words)

def mock_lipnet_trascrizione(frase_attesa: str, modalita: str = "realistica") -> str: 
    """
    Simula l'output di LipNet con errori controllati.

    modalita: 
      - "perfetta"   -> nessun errore (WER = 0, CER = 0)
      - "realistica" -> errori tipici del lip reading (circa 20-40% WER)
      - "pessima"    -> molti errori (stress test)
      - "vuota"      -> stringa vuota (caso estremo)
    """

    if modalita == "perfetta":
        return frase_attesa
    
    if modalita == "vuota":
        return ""
    
    parole = frase_attesa.lower().strip().split()

    if modalita == "pessima":
        # Sostituisce tutte le parole con il placeholder
        return " ".join(["***"] * len(parole))
    
    # modalita REALISTICA --------------------
    # Errori tipici del lipreading reale:
    # Confusione tra i fonemi visivamente simili (p/b, m/n, f/v)
    # Parole brevi spesso saltate
    # Inversione di parole vicine

    SOSTITUZIONI_FONETICHE = {
        "b": "p", "p": "b",
        "m": "n", "n": "m",
        "f": "v", "v": "f",
        "d": "t", "t": "d",
    }

    risultato = []
    for parola in parole:
        r = random.random()

        if r < 0.10 and len(parola) <= 3:
            # Parole corte -> spesso eliminate (10%)
            continue
        elif r < 0.20:
            # Sostituzione fonetica sul primo carattere (10%)
            primo = parola[0]
            nuovo = SOSTITUZIONI_FONETICHE.get(primo, primo)
            risultato.append(nuovo + parola[1:])
        elif r < 0.25:
            # Troncamneto (5%) - es. "ciao" -> "cia"
            risultato.append(parola[:-1] if len(parola) > 2 else parola)
        else:
            # Parola corretta
            risultato.append(parola)

    return " ".join(risultato)

# =============== ROUTE ANALISI LIPNET ================================

def elabora_video_per_lipnet(video_path):
    # Apriamo il video salvato nella cartella uploads
    cap = cv2.VideoCapture(video_path)
    frames = []

    # Lipnet spesso si aspetta un numero fisso di frame (esempio 75)
    while len(frames) < 75:
        ret, frame = cap.read()
        if not ret:
            break

        # 1 Conversione in scala di grigi (molti modelli usano solo il bianco e nero)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2 Ritaglio della zona centrale
        bocca = gray[240:400, 220:420]

        # 3 Ridimensionamento alle dimensioni del modello (100x50)
        bocca_res = cv2.resize(bocca, (100, 50))

        # 4 Normalizzazione (porta i valori dei pixel da 0-255 a 0-1)
        bocca_norm = bocca_res / 255.0

        frames.append(bocca_norm) 
    cap.release()

    # Trasformiamo la lista in un array NumPy pronto per l'IA
    return np.array(frames)

def trascrivi_video(video_path: str, frase_attesa: str) -> dict:
    """
    Funzione principale - black box completa.
    Invia il video al server LipNet su localhost:5001 e riceve la trascrizione.
    Il calcolo di WER e CER avviene qui, come prima.
    """
    import requests

    LIPNET_SERVER = "http://localhost:5001"

    try:
        # Apriamo il video e lo inviamo al server LipNet
        with open(video_path, "rb") as f:
            risposta = requests.post(
                f"{LIPNET_SERVER}/upload",
                files={"file": ("temp_mimo.webm", f, "video/webm")},
                data={"saliency_map": "false"},
                timeout=120  # LipNet può richiedere tempo per elaborare
            )

        if risposta.status_code != 200:
            return {"success": False, "error": f"Errore server LipNet: {risposta.status_code}"}

        # Il server restituisce {"message": "parola trascritta"}
        trascrizione = risposta.json().get("message", "").strip()

        if not trascrizione:
            return {"success": False, "error": "Trascrizione vuota dal server LipNet"}

    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Server LipNet non raggiungibile — assicurati che sia avviato su localhost:5001"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout — il server LipNet ha impiegato troppo tempo"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Calcolo WER e CER — invariato rispetto a prima
    ref = frase_attesa.lower().strip()
    hyp = trascrizione.lower().strip()
    cer = calcola_cer(ref, hyp)
    wer = calcola_wer(ref, hyp)

    print(f"REF: {ref}")
    print(f"HYP: {hyp}")
    print(f"WER: {wer}")
    print(f"CER: {cer}")

    # Soglia configurabile per considerare il livello superato
    livello_superato = wer <= 1.0

    return {
        "trascrizione": trascrizione,
        "livello_superato": livello_superato,
        "metriche": {
            "wer_percent": round(wer * 100, 2),
            "cer_percent": round(cer * 100, 2),
        },
        "mock_attivo": False  # LipNet reale attivo
    }


# Test connessione all'avvio
if __name__ == "__main__":
    verifica_connessione()
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")