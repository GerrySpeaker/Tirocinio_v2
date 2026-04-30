from flask import Blueprint, request, jsonify, render_template, abort
from bson.objectid import ObjectId
import os
import cv2
import numpy as np
from Levenshtein import ratio
from jiwer import cer, wer


# Il mio nuovo file models.py è il mio vecchio database.py
# ora rimanendo della stessa idea continuerò ad usare db per evitare che si rompa il codice
from app import models as db

# Creiamo il Blueprint 
main = Blueprint('main', __name__)

# ===== ROUTE HOME =====


@main.route('/')
def home():
    # Recupera i livelli dal database
    livelli = db.ottieni_livelli()
    return render_template('index.html', livelli=livelli)


# ===== ROUTE TIPOLOGIE =====

@main.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@main.route('/about', methods=['GET'])
def about():
    return render_template('about.html')
    
@main.route('/tipologie', methods=['GET'])
def get_tipologie():
    """Mostra tutte le tipolige"""
    try:
        tipologie = db.ottieni_tipologie()
        return jsonify(tipologie), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@main.route('/tipologie', methods=['POST'])
def post_tipologia():
    """Crea una nuova tipologia"""
    try:
        dati = request.get_json()

        tipologia_id = db.crea_tipologia(
            nome = dati['nome'],
            titolo = dati['titolo_display'],
            descrizione = dati.get('descrizione', ''),
            punti_base = dati.get('punti_base', 10)
        )
    
        return jsonify({
            "message": "Tipologia creata",
            "id" : tipologia_id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

# ================ ROUTE LIVELLI ====================

@main.route('/livelli', methods = ['GET'])
def get_livelli():
    """Mostra tutti i livelli"""
    try: 
        livelli = db.ottieni_livelli()
        return jsonify(livelli), 200
    except Exception as e:
        return jsonify({"error" : str(e)}), 400
    

@main.route('/livelli', methods = ['POST'])
def post_livello():
    try:
        dati = request.get_json()

        contenuto = {
            "tipo": "mimo_labiale",
            "video": dati['video'],
            "testo": dati['testo'],
            "scelte": dati['scelte'],
            "risposta": dati['risposta']
        }

        livello_id = db.crea_livello(
            numero = dati['numero_livello'],
            titolo = dati['titolo'],
            tipologia_id = dati['tipologia_id'], # Poiché il livello appartiene alla tipologia
            contenuto = dati['contenuto'],
            difficolta = dati.get('difficolta', 'medio')
        )

        if livello_id:
            return jsonify({
                "message": "Livello creato",
                "id": livello_id
            }), 201
        else:
            return jsonify({"error": "Tipologia non trovata"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@main.route('/livelli/<livello_id>', methods = ['GET'])
def get_livello(livello_id):
    try:
        livello = db.trova_livello(livello_id)

        if livello:
            livello['_id'] = str(livello['_id'])
            livello['tipologia_id'] = str(livello['tipologia_id'])

            # Aggiunge anche i dettagli della tipologia
            tipologia = db.trova_tipologia(livello['tipologia_id'])

            if tipologia:
                tipologia['_id'] = str(tipologia['_id'])
                livello['tipologia_dettagli'] = tipologia
            
            return jsonify(livello), 200
        else:
            return jsonify({"error": str(e)}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
# ==================== ROUTE GIOCA ===========================

@main.route('/livelli/<livello_id>/gioca', methods=['GET'])
def gioca_livello(livello_id):
    try:
        livello = db.ottieni_livello_per_id(livello_id) 
        
        if not livello:
            return jsonify({"error": "Livello non trovato"}), 404

        contenuto = livello.get("contenuto", {})
        
        # Costruiamo un oggetto base con i dati comuni
        dati_esercizio = {
            "id": str(livello.get("_id")),
            "titolo": livello.get("titolo", f"Livello {livello.get('numero_livello')}"),
            "testo": livello.get("testo", ""),
            # Passiamo l'intero oggetto contenuto così il JS ha tutto (tipo, frase, video, scelte)
            "contenuto": contenuto 
        }
        
        # Opzionale: aggiungiamo scorciatoie per comodità nel JS
        dati_esercizio["tipo"] = contenuto.get("tipo")
        dati_esercizio["video"] = contenuto.get("video", "")
        dati_esercizio["scelte"] = contenuto.get("scelte", [])

        return jsonify(dati_esercizio), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ================ ROUTE RIPOSTA CORRETTA =====================

@main.route('/livelli/<livello_id>/verifica', methods=['POST'])
def verifica_risposta(livello_id):
    try: 
        livello = db.ottieni_livello_per_id(livello_id) # Usa la stessa funzione di ottieni_livello
        if not livello:
            return jsonify({"error": "Livello non trovato"}), 404
        
        contenuto = livello.get("contenuto", {})
        dati = request.get_json()
        scelta_utente = dati.get("scelta")

        # Recuperiamo la risposta corretta dal database
        # Assicurati che nel DB il campo si chiami "risposta_corretta" o "risposta"
        risposta_corretta = contenuto.get("risposta_corretta") or contenuto.get("risposta")

        # Debug per capire cosa stiamo confrontando
        print(f"Utente ha scelto: {scelta_utente}, La corretta è: {risposta_corretta}")

        corretta = (str(scelta_utente).strip().lower() == str(risposta_corretta).strip().lower())

        return jsonify({
            "corretta": corretta,
            "risposta_corretta": risposta_corretta
        }), 200

    except Exception as e:
        print(f"Errore verifica: {e}")
        return jsonify({"error": str(e)}), 400
    

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

@main.route('/livelli/<livello_id>/analisi-lipnet', methods=['POST'])
def analisi_lipnet(livello_id):
    try:
        video_file = request.files.get('video')
        frase_attesa = request.form.get('frase_attesa')

        if not video_file:
            return jsonify({"success": False, "error": "File video non ricevuto"}), 400

        # Salvataggio
        video_path = os.path.join("uploads", "temp_mimo.mp4")
        video_file.save(video_path)

        # Elaborazione
        dati_per_ia = elabora_video_per_lipnet(video_path)
        
        # Controllo se l'elaborazione ha prodotto dati
        if dati_per_ia is None or len(dati_per_ia) == 0:
            return jsonify({"success": False, "error": "Impossibile elaborare i frame del video"}), 400

        # Simulazione Trascrizione (Placeholder per il futuro modello)
        trascrizione = frase_attesa 

        successo = (trascrizione.lower().strip() == frase_attesa.lower().strip())

        # RITORNO VALIDO
        return jsonify({
            "success": successo, 
            "trascrizione": trascrizione,
            "message": "Analisi completata"
        })

    except Exception as e:
        # In caso di qualsiasi errore (DB spento, file mancante, ecc.)
        print(f"Errore durante l'analisi: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# =============== ROUTE STATO DI COMPLETAMENTO =========================

@main.route('/api/livelli', methods=['GET'])
def get_livelli_api():
    try:
        # Prendiamo i livelli dal database
        livelli = db.ottieni_livelli()
        
        # Converte l'ObjectId di MongoDB in stringa per poterlo inviare come JSON
        for liv in livelli:
            if '_id' in liv:
                liv['_id'] = str(liv['_id'])
                
        return jsonify(livelli), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============ ROUTE LIVELLO ====================

@main.route('/livello/<int:numero>', methods=['GET'])
def livello(numero):
    print("Route /livello chiamata con numero=", numero)
    livello = db.trova_livello_per_numero(numero)
    print("Livello trovato? ", bool(livello))
    if not livello:
        return render_template("404.html"), 404
    
    livello["_id"] = str(livello["_id"])
    livello["tipologia_id"] = str(livello["tipologia_id"])
    
    contenuto = livello.get("contenuto", {})
    if not isinstance(contenuto, dict):
        return render_template("error.html", error= "Contenuto non valido"), 500
    
    # Renderizza la pagina dell'esercizio con i dettagli del livello
    return render_template("esercizio_mimo.html", livello=livello, contenuto=contenuto, prossimo_numero = numero + 1)


# =========== ROUTE AVANTI PER ID======================

@main.route('/livello/<livello_id>/avanti', methods=['GET'])
def livello_successivo(livello_id):
    # Trova livello corrente
    livello_corrente = db.trova_livello(livello_id)
    if not livello_corrente:
        return render_template("404.html"), 404 # Se non esiste il livello allora non mostro la pagina
    
    # Trova il prossimo livello in base a quello selezionato
    prossimo_livello = db.livelli_collection.find_one({
        "numero_livello": livello_corrente["numero_livello"] + 1
    })

    if not prossimo_livello:
        return render_template("completato.html") # Se non ci sono livelli, mostra un messaggio di completato
    
    # Rendi il prossimo livello disponibile
    return render_template("esercizio_mimo.html", livello = prossimo_livello, contenuto = prossimo_livello.get("contenuto", {}))


# ============= ROUTE AGGIORNA STATO ===================

@main.route('/api/livello/aggiorna_stato', methods=['POST'])
def aggiorna_stato_livello():
    # Riceviamo i dati ricevuti da Javascript
    dati = request.get_json()

    livello_corrente = dati.get('livello_id')
    livello_prossimo = dati.get('prossimo_id')                      # Questo valore può essere null se non esiste un livello successivo

    try: 
        # Chiamiamo il nostro Model per fare la query al database!
        db.sblocca_e_completa_livello(livello_corrente, livello_prossimo)

        # Rispondiamo al frontend che è andato tutto bene
        return jsonify({"Success": True, "message": "Database aggiornato con successo."}), 200
    except Exception as e:
        return jsonify({"Success": False, "error": str(e)}), 500

# =================== ROUTE PROGRESSI ===================

@main.route('/progressi/completa', methods=['POST'])
def completa_livello():
    data = request.json
    # Usiamo .strip() per rimuovere eventuali spazi bianchi accidentali
    livello_id = data.get('livello_id').strip()
    
    try:
        # 1. Recupera il livello attuale con controllo di esistenza
        livello_attuale = db.livelli_collection.find_one({"_id": ObjectId(livello_id)})
        
        if livello_attuale is None:
            print(f"ERRORE: Nessun livello trovato con ID {livello_id}")
            return jsonify({"error": "Livello non trovato nel database"}), 404

        # 2. Segna il livello attuale come completato
        db.livelli_collection.update_one(
            {"_id": ObjectId(livello_id)},
            {"$set": {"completato": True}}
        )
        
        # 3. Sblocca il livello successivo (solo se esiste un numero_livello)
        if 'numero_livello' in livello_attuale:
            prossimo_numero = livello_attuale['numero_livello'] + 1
            db.livelli_collection.update_one(
                {"numero_livello": prossimo_numero},
                {"$set": {"sbloccato": True}}
            )
            print(f"Livello {livello_attuale['numero_livello']} completato. Sbloccato il {prossimo_numero}.")
        
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"ERRORE CRITICO in completa_livello: {str(e)}")
        return jsonify({"error": str(e)}), 500
            
            
# ====================== ROUTE UTENTE ========================

@main.route('/progressi/<utente_id>', methods = ['GET'])
def get_progressi(utente_id):
    try: 
        progressi = db.ottieni_progressi_utente(utente_id)
        return jsonify(progressi), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

# =============== ROUTE PROVA ================
@main.route('/test_prova')
def test_prova():
    return "La route funziona", 200

