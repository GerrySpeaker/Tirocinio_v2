# database.py
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



# Test connessione all'avvio
if __name__ == "__main__":
    verifica_connessione()
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")