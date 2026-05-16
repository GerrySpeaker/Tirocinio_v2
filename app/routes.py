from flask import Blueprint, request, jsonify, render_template, abort
from bson.objectid import ObjectId
import os
import cv2
import numpy as np

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

        # Campi obbligatori
        numero      = dati.get('numero_livello')
        titolo      = dati.get('titolo')
        tipologia_id = dati.get('tipologia_id')
        contenuto   = dati.get('contenuto')

        if not all([numero, titolo, tipologia_id, contenuto]):
            return jsonify({"error": "Campi obbligatori mancanti: numero_livello, titolo, tipologia_id, contenuto"}), 400

        livello_id = db.crea_livello(
            numero       = numero,
            titolo       = titolo,
            tipologia_id = tipologia_id,
            contenuto    = contenuto,
            difficolta   = dati.get('difficolta', 'medio')
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

@main.route('/livelli/<livello_id>/analisi-lipnet', methods=['POST'])
def analisi_lipnet(livello_id):
    try:
        video_file = request.files.get('video')
        frase_attesa = request.form.get('frase_attesa')

        if not video_file:
            return jsonify({"success": False, "error": "File video non ricevuto"}), 400

        if not frase_attesa:
            return jsonify({"success": False, "error": "Frase attesa non ricevuta"}), 400

        # Salva il video nella cartella uploads
        video_path = os.path.join("uploads", "temp_mimo.webm")
        video_file.save(video_path)

        # Invia il video al server LipNet e ottieni trascrizione + metriche
        risultato = db.trascrivi_video(video_path, frase_attesa)

        if not risultato.get("trascrizione"):
            return jsonify({"success": False, "error": risultato.get("error", "Errore sconosciuto")}), 500

        return jsonify({
            "success": risultato.get("livello_superato", False),
            "trascrizione": risultato.get("trascrizione"),
            "frase_attesa": frase_attesa,
            "message": "Analisi completata",
            "metriche": risultato.get("metriche", {}),
            "mock_attivo": risultato.get("mock_attivo", False),
        }), 200

    except Exception as e:
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


# ==================== ROUTE ADMIN ====================

@main.route('/admin')
def admin():
    """Pannello amministratore"""
    return render_template('admin.html')


@main.route('/admin/livelli/<livello_id>', methods=['PUT'])
def aggiorna_livello(livello_id):
    """Modifica un livello esistente (usato dal pannello admin)"""
    try:
        dati = request.get_json()

        update_fields = {}

        if 'numero_livello' in dati:
            update_fields['numero_livello'] = dati['numero_livello']
            update_fields['ordine'] = dati['numero_livello']
        if 'titolo' in dati:
            update_fields['titolo'] = dati['titolo']
        if 'difficolta' in dati:
            update_fields['difficolta'] = dati['difficolta']
        if 'sbloccato' in dati:
            update_fields['sbloccato'] = dati['sbloccato']
        if 'completato' in dati:
            update_fields['completato'] = dati['completato']
        if 'contenuto' in dati:
            update_fields['contenuto'] = dati['contenuto']

        if not update_fields:
            return jsonify({"error": "Nessun campo da aggiornare"}), 400

        risultato = db.livelli_collection.update_one(
            {"_id": ObjectId(livello_id)},
            {"$set": update_fields}
        )

        if risultato.matched_count == 0:
            return jsonify({"error": "Livello non trovato"}), 404

        rinumera_livelli()
        return jsonify({"success": True, "message": "Livello aggiornato"}), 200  

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route('/admin/livelli/<livello_id>', methods=['DELETE'])
def elimina_livello(livello_id):
    """Soft-delete di un livello"""
    try:
        # Imposta l'action del livello a False così da nasconderlo e non eliminarlo del tutto
        risultato = db.livelli_collection.update_one(
            {"_id": ObjectId(livello_id)},
            {"$set": {"attivo": False}}
        )

        if risultato.matched_count == 0:
            return jsonify({"error": "Livello non trovato"}), 404
        
        rinumera_livelli() # Riordina tutti i livelli dopo l'eliminazione
        return jsonify({"success": True, "message": "Livello eliminato"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

def rinumera_livelli():
    """
    Riordina tutti i livelli attivi in sequenza (1,2,3,...)
    Va chiamata dopo la creazione di ogni livello o eliminazione di un livello
    E i livelli vengono ordinati in base al campo 'ordine' corrente
    """
    livelli = list(
        db.livelli_collection.find({"attivo": True}).sort("ordine", 1)
    )
    for i,livello in enumerate(livelli, start=1):
        db.livelli_collection.update_one(
            {"_id": livello["_id"]},
            {"$set": {"ordine": i, "numero_livello": i}}
        )