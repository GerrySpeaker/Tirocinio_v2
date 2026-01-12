from flask import Flask, request, jsonify, render_template
import database as db

#Sembrerebbe un inizio interessante
app = Flask(__name__)

# Configurazione
app.config['DEBUG'] = True


# ===== ROUTE HOME =====


@app.route('/')
def home():
    return render_template('index.html')


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
    

# ===== ROUTE LIVELLI =====


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