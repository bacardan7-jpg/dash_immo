#!/usr/bin/env python
"""Entry point for running the application"""
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database.models import db   # ← À vérifier : module où tu initialises SQLAlchemy
from app.database import models          # ← Important pour que les modèles soient connus par SQLAlchemy


if __name__ == '__main__':

    # 🔥 Tout le code qui touche la base doit être dans ce bloc
    with app.app_context():

        # Exemple : si tu as des fonctions d'initialisation à exécuter
        try:
            # initialise les tables si besoin
            db.create_all()
        except Exception as e:
            print("Erreur lors de l'initialisation de la base :", e)

    # Mode développement
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
