from flask import Flask, request, jsonify, render_template, abort
import database as db

#Sembrerebbe un inizio interessante
app = Flask(__name__)

# Configurazione
app.config['DEBUG'] = True


# ===== ROUTE HOME =====


@app.route('/')
def home():
    # Recupera i livelli dal database
    livelli = db.ottieni_livelli()
    return render_template('index.html', livelli=livelli)


# ===== ROUTE TIPOLOGIE =====

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


    
@app.route('/tipologie', methods=['GET'])
def get_tipologie():
    """Mostra tutte le tipolige"""
    try:
        tipologie = db.ottieni_tipologie()
        return jsonify(tipologie), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/tipologie', methods=['POST'])
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

@app.route('/livelli', methods = ['GET'])
def get_livelli():
    """Mostra tutti i livelli"""
    try: 
        livelli = db.ottieni_livelli()
        return jsonify(livelli), 200
    except Exception as e:
        return jsonify({"error" : str(e)}), 400
    

@app.route('/livelli', methods = ['POST'])
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
    

@app.route('/livelli/<livello_id>', methods = ['GET'])
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

@app.route('/livelli/<livello_id>/gioca', methods=['GET'])
def gioca_livello(livello_id):
    "Renderizza la pagina esercizio per il livello selezionato"
    try:
        livello = db.trova_livello(livello_id)
        if not livello:
            return render_template("404.html"), 404

        # Assumendo che livello['contenuto'] contenga i dati dell'esercizio
        # es: {"tipo":"mimo_labiale","video":"videos/ciao.mp4","choices":[...],"answer":"CIAO"}
        contenuto = livello.get("contenuto", {})

        if not isinstance(contenuto, dict):
            return render_template("error.html", error = "Contenuto livello non valido"), 500
        
        if contenuto.get("tipo") != "mimo labiale":
            return render_template("unsupported_exercise.html", livello=livello), 400
        
        return jsonify({
            "titolo": livello['titolo'],
            "testo": contenuto.get('testo', ''),
            "video": contenuto.get('video', ''),
            "scelte": contenuto.get('scelte', [])
        })

    except Exception as e:
        return render_template("error.html", error=str(e)), 500
    
# ================ ROUTE RIPOSTA CORRETTA =====================

@app.route('/livelli/<livello_id>/verifica', methods=['POST'])      # Il metodo POST mi serve per visualizzare la pagina con la corretta risposta
def verifica_risposta(livello_id):
    try: 
        livello = db.trova_livello(livello_id)
        if not livello:
            return jsonify({"error": "Livello non trovato"}), 404
        
        contenuto = livello.get("contenuto", {})
        if not isinstance(contenuto, dict) or contenuto.get("tipo") != "mimo_labiale":
            return jsonify({"error": "Contenuto livello non valido"}), 400

        dati = request.get_json()
        scelta = dati.get("scelta")

        corretta = (scelta == contenuto.get("risposta"))

        return jsonify({
            "corretta": corretta,
            "risposta_corretta": contenuto.get("risposta", "")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============== ROUTE STATO DI COMPLETAMENTO =========================

@app.route("/api/livelli", methods=["GET"])
def api_livelli():
    livelli = db.ottieni_livelli() # ritorna la lista con _id come stringa

    # Esempio: progressi utente 
    utente_id = "demo"
    progressi = db.ottieni_progressi_utente(utente_id)

    # Se esiste un progresso per quel livello allora è completato
    completati = set(p["livello_id"] for p in progressi)

    livelli.sort(key=lambda x: x.get("numero_livello", 0))

    prev_completato = True

    for liv in livelli:
        liv_id = liv["_id"]

        liv["completato"] = (liv_id in completati)

        # Sblocco progressivo
        liv["sbloccato"] = prev_completato

        prev_completato = liv["completato"]

    return jsonify(livelli), 200

# ============ ROUTE LIVELLO ====================

@app.route('/livello/<int:numero>', methods=['GET'])
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

@app.route('/livello/<livello_id>/avanti', methods=['GET'])
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


# ===== ROUTE PROGRESSI =====

@app.route('/progressi/completa', methods = ['POST'])
def completa_livello():
    """Salva il completamento di un livello"""
    try:
        dati = request.get_json()

        stelle = db.salva_progresso(
            utente_id = dati['utente_id'],
            livello_id = dati['livello_id'],
            punteggio = dati['punteggio'],
            accuratezza = dati['accuratezza']
        )

        if stelle is not None:
            return jsonify({
                "message": "Progresso salvato",
                "stelle": stelle
            }), 200
        else:
            return jsonify({"error": "Livello non trovato"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400    

@app.route('/progressi/<utente_id>', methods = ['GET'])
def get_progressi(utente_id):
    try: 
        progressi = db.ottieni_progressi_utente(utente_id)
        return jsonify(progressi), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

# ===== AVVIO SERVER =====

if __name__ == '__main__':
    print("=" * 50)
    print(" SERVER AVVIATO ")
    print("=" * 50)
    print(" URL: http//localhost:500")
    print("=" * 50)
    app.run(debug=True, port=500)