# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print(" SERVER AVVIATO (Struttura a Package) ")
    print("=" * 50)
    print(" Vai su: http://localhost:500")
    print("=" * 50)
    app.run(debug=True, port=500)