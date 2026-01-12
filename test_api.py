import requests
import json
import time

# Configurazione
BASE_URL = "http://localhost:500"

# Colori per output nel terminale
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def stampa_sezione(titolo):
    """Stampa un titolo di sezione formattato"""
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}{Colors.BLUE}{titolo}{Colors.END}")
    print("=" * 60)


def stampa_successo(messaggio):
    """Stampa un messaggio di successo"""
    print(f"{Colors.GREEN}✅ {messaggio}{Colors.END}")


def stampa_errore(messaggio):
    """Stampa un messaggio di errore"""
    print(f"{Colors.RED}❌ {messaggio}{Colors.END}")


def stampa_info(messaggio):
    """Stampa un messaggio informativo"""
    print(f"{Colors.YELLOW}ℹ️  {messaggio}{Colors.END}")


def verifica_server():
    """Verifica che il server Flask sia attivo"""
    try:
        response = requests.get(BASE_URL, timeout=2)
        if response.status_code == 200:
            stampa_successo("Server Flask attivo e raggiungibile")
            return True
        else:
            stampa_errore("Server risponde ma con errore")
            return False
    except requests.exceptions.ConnectionError:
        stampa_errore("Server non raggiungibile! Assicurati che Flask sia avviato.")
        stampa_info("Esegui prima: python app.py")
        return False


def test_crea_tipologie():
    """Test: Creazione di tipologie di esercizio"""
    stampa_sezione("TEST 1: Creazione Tipologie")
    
    tipologie_da_creare = [
        {
            "nome": "capire_labiale",
            "titolo_display": "Comprensione Labiale",
            "descrizione": "Guarda il video e comprendi cosa viene detto leggendo le labbra",
            "punti_base": 10
        },
        {
            "nome": "mimare_labiale",
            "titolo_display": "Riproduzione Labiale",
            "descrizione": "Ripeti la frase mimando il movimento labiale",
            "punti_base": 15
        },
        {
            "nome": "ascolto_parole",
            "titolo_display": "Ascolto e Comprensione",
            "descrizione": "Ascolta e seleziona la parola corretta",
            "punti_base": 8
        }
    ]
    
    tipologie_create = []
    
    for tipologia in tipologie_da_creare:
        try:
            response = requests.post(f"{BASE_URL}/tipologie", json=tipologia)
            
            if response.status_code == 201:
                dati = response.json()
                tipologie_create.append(dati['id'])
                stampa_successo(f"Tipologia '{tipologia['nome']}' creata - ID: {dati['id']}")
            else:
                stampa_errore(f"Errore nella creazione: {response.text}")
                
        except Exception as e:
            stampa_errore(f"Eccezione: {str(e)}")
    
    return tipologie_create


def test_visualizza_tipologie():
    """Test: Visualizzazione di tutte le tipologie"""
    stampa_sezione("TEST 2: Visualizzazione Tipologie")
    
    try:
        response = requests.get(f"{BASE_URL}/tipologie")
        
        if response.status_code == 200:
            tipologie = response.json()
            stampa_successo(f"Trovate {len(tipologie)} tipologie:")
            
            for tip in tipologie:
                print(f"  📋 {tip['titolo_display']} ({tip['nome']}) - {tip['punti_base']} punti")
            
            return tipologie
        else:
            stampa_errore(f"Errore: {response.text}")
            return []
            
    except Exception as e:
        stampa_errore(f"Eccezione: {str(e)}")
        return []


def test_crea_livelli(tipologie_ids):
    """Test: Creazione di livelli per ogni tipologia"""
    stampa_sezione("TEST 3: Creazione Livelli")
    
    if len(tipologie_ids) < 2:
        stampa_errore("Non ci sono abbastanza tipologie per creare i livelli")
        return []
    
    livelli_da_creare = [
        {
            "numero_livello": 1,
            "titolo": "Saluti Base",
            "tipologia_id": tipologie_ids[0],  # capire_labiale
            "contenuto": {
                "video_url": "videos/ciao.mp4",
                "opzioni": ["Ciao", "Buongiorno", "Casa", "Cane"],
                "risposta_corretta": "Ciao"
            },
            "difficolta": "facile"
        },
        {
            "numero_livello": 2,
            "titolo": "Parole Quotidiane",
            "tipologia_id": tipologie_ids[0],  # capire_labiale
            "contenuto": {
                "video_url": "videos/acqua.mp4",
                "opzioni": ["Acqua", "Aria", "Fuoco", "Terra"],
                "risposta_corretta": "Acqua"
            },
            "difficolta": "facile"
        },
        {
            "numero_livello": 3,
            "titolo": "Ripeti il Saluto",
            "tipologia_id": tipologie_ids[1],  # mimare_labiale
            "contenuto": {
                "frase_da_mimare": "Buongiorno, come stai?",
                "video_esempio": "videos/esempio_buongiorno.mp4"
            },
            "difficolta": "medio"
        }
    ]
    
    livelli_creati = []
    
    for livello in livelli_da_creare:
        try:
            response = requests.post(f"{BASE_URL}/livelli", json=livello)
            
            if response.status_code == 201:
                dati = response.json()
                livelli_creati.append(dati['id'])
                stampa_successo(f"Livello {livello['numero_livello']}: '{livello['titolo']}' creato - ID: {dati['id']}")
            else:
                stampa_errore(f"Errore nella creazione: {response.text}")
                
        except Exception as e:
            stampa_errore(f"Eccezione: {str(e)}")
    
    return livelli_creati


def test_visualizza_livelli():
    """Test: Visualizzazione di tutti i livelli"""
    stampa_sezione("TEST 4: Visualizzazione Livelli")
    
    try:
        response = requests.get(f"{BASE_URL}/livelli")
        
        if response.status_code == 200:
            livelli = response.json()
            stampa_successo(f"Trovati {len(livelli)} livelli:")
            
            for liv in livelli:
                print(f"  🎯 Livello {liv['numero_livello']}: {liv['titolo']}")
                print(f"     Tipologia: {liv['tipologia_nome']}, Difficoltà: {liv['difficolta']}")
            
            return livelli
        else:
            stampa_errore(f"Errore: {response.text}")
            return []
            
    except Exception as e:
        stampa_errore(f"Eccezione: {str(e)}")
        return []


def test_dettaglio_livello(livello_id):
    """Test: Visualizzazione dettagli di un livello specifico"""
    stampa_sezione(f"TEST 5: Dettagli Livello {livello_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/livelli/{livello_id}")
        
        if response.status_code == 200:
            livello = response.json()
            stampa_successo("Dettagli livello recuperati:")
            print(f"  📌 Titolo: {livello['titolo']}")
            print(f"  📌 Tipologia: {livello['tipologia_nome']}")
            print(f"  📌 Difficoltà: {livello['difficolta']}")
            print(f"  📌 Punti: {livello['punti_ricompensa']}")
            print(f"  📌 Contenuto: {json.dumps(livello['contenuto'], indent=6)}")
            
            return livello
        else:
            stampa_errore(f"Errore: {response.text}")
            return None
            
    except Exception as e:
        stampa_errore(f"Eccezione: {str(e)}")
        return None


def test_completa_livelli(livelli_ids, utente_id="user_test_123"):
    """Test: Simulazione completamento livelli da parte di un utente"""
    stampa_sezione("TEST 6: Completamento Livelli")
    
    simulazioni = [
        {"livello_idx": 0, "punteggio": 100, "accuratezza": 95},  # Oro
        {"livello_idx": 1, "punteggio": 80, "accuratezza": 75},   # Argento
        {"livello_idx": 2, "punteggio": 60, "accuratezza": 55},   # Bronzo
    ]
    
    for sim in simulazioni:
        if sim["livello_idx"] >= len(livelli_ids):
            continue
            
        livello_id = livelli_ids[sim["livello_idx"]]
        
        try:
            response = requests.post(f"{BASE_URL}/progressi/completa", json={
                "utente_id": utente_id,
                "livello_id": livello_id,
                "punteggio": sim["punteggio"],
                "accuratezza": sim["accuratezza"]
            })
            
            if response.status_code == 200:
                dati = response.json()
                stelle = "⭐" * dati['stelle']
                stampa_successo(f"Livello completato - Punteggio: {sim['punteggio']}, Stelle: {stelle}")
            else:
                stampa_errore(f"Errore: {response.text}")
                
        except Exception as e:
            stampa_errore(f"Eccezione: {str(e)}")
        
        time.sleep(0.5)  # Pausa per rendere più leggibile


def test_visualizza_progressi(utente_id="user_test_123"):
    """Test: Visualizzazione progressi utente"""
    stampa_sezione("TEST 7: Visualizzazione Progressi Utente")
    
    try:
        response = requests.get(f"{BASE_URL}/progressi/{utente_id}")
        
        if response.status_code == 200:
            progressi = response.json()
            stampa_successo(f"Trovati {len(progressi)} progressi per l'utente {utente_id}:")
            
            for prog in progressi:
                stelle = "⭐" * prog['stelle']
                print(f"  🏆 Livello: {prog['livello_id']}")
                print(f"     Tipologia: {prog['tipologia_nome']}")
                print(f"     Punteggio: {prog['punteggio_migliore']}")
                print(f"     Accuratezza: {prog['accuratezza_migliore']}%")
                print(f"     Stelle: {stelle}")
                print(f"     Tentativi: {prog['tentativi']}")
                print()
            
            return progressi
        else:
            stampa_errore(f"Errore: {response.text}")
            return []
            
    except Exception as e:
        stampa_errore(f"Eccezione: {str(e)}")
        return []


def esegui_tutti_i_test():
    """Esegue tutti i test in sequenza"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "TEST API - SISTEMA A LIVELLI" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Verifica che il server sia attivo
    if not verifica_server():
        return
    
    time.sleep(1)
    
    # Test 1: Crea tipologie
    tipologie_ids = test_crea_tipologie()
    time.sleep(1)
    
    # Test 2: Visualizza tipologie
    tipologie = test_visualizza_tipologie()
    time.sleep(1)
    
    # Test 3: Crea livelli
    livelli_ids = test_crea_livelli(tipologie_ids)
    time.sleep(1)
    
    # Test 4: Visualizza livelli
    livelli = test_visualizza_livelli()
    time.sleep(1)
    
    # Test 5: Dettagli di un livello
    if livelli_ids:
        test_dettaglio_livello(livelli_ids[0])
        time.sleep(1)
    
    # Test 6: Completa livelli
    test_completa_livelli(livelli_ids)
    time.sleep(1)
    
    # Test 7: Visualizza progressi
    test_visualizza_progressi()
    
    # Riepilogo finale
    stampa_sezione("RIEPILOGO TEST")
    stampa_successo(f"Tipologie create: {len(tipologie_ids)}")
    stampa_successo(f"Livelli creati: {len(livelli_ids)}")
    stampa_successo("Tutti i test completati!")
    
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}📊 Il sistema è pronto all'uso!{Colors.END}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        esegui_tutti_i_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrotti dall'utente")
    except Exception as e:
        stampa_errore(f"Errore imprevisto: {str(e)}")