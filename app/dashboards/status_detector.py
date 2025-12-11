"""
🔍 UTILITAIRE DE DÉTECTION DU STATUT (VENTE/LOCATION)
Module partagé pour tous les dashboards
Auteur: Cos - ENSAE Dakar
"""

import re
import logging

logger = logging.getLogger(__name__)


class StatusDetector:
    """Détecteur ultra-robuste du statut Vente/Location"""
    
    # Patterns ultra-complets pour LOCATION
    LOCATION_PATTERNS = {
        # Mots-clés directs - très fort
        'explicit': [
            r'\blouer\b', r'\bloue\b', r'\blocation\b', r'\bà louer\b', r'\ba louer\b',
            r'\brent\b', r'\brental\b', r'\bfor rent\b', r'\bto rent\b', r'\bto let\b',
            r'\bletting\b', r'\blet\b'
        ],
        # Indicateurs temporels - très fort
        'temporal': [
            r'/mois\b', r'\bpar mois\b', r'\bmensuel\b', r'\bmensuelle\b', r'\bmensualité\b',
            r'/month\b', r'\bper month\b', r'\bmonthly\b',
            r'/jour\b', r'\bpar jour\b', r'\bjournalier\b',
            r'/semaine\b', r'\bpar semaine\b'
        ],
        # Contexte location - moyen
        'context': [
            r'\bbail\b', r'\blocataire\b', r'\bloyer\b', r'\bgarantie locative\b',
            r'\btenancy\b', r'\btenant\b', r'\blease\b',
            r'\bdisponible immédiatement\b', r'\bdispo\b', r'\blibre\b',
            r'\bavailable now\b'
        ],
        # Types spécifiques location - faible
        'property_types': [
            r'\bchambre\b', r'\broom\b', r'\bmeublé\b', r'\bmeuble\b',
            r'\bfurnished\b', r'\bstudio meublé\b'
        ]
    }
    
    # Patterns ultra-complets pour VENTE
    VENTE_PATTERNS = {
        # Mots-clés directs - très fort
        'explicit': [
            r'\bvendre\b', r'\bvend\b', r'\bvente\b', r'\bà vendre\b', r'\ba vendre\b',
            r'\bsell\b', r'\bsale\b', r'\bfor sale\b', r'\bto sell\b',
            r'\bselling\b'
        ],
        # Processus achat - fort
        'transaction': [
            r'\bacquisition\b', r'\bachat\b', r'\bacheter\b', r'\bacquérir\b',
            r'\bpurchase\b', r'\bbuy\b', r'\bbuying\b',
            r'\bcesssion\b', r'\bcéder\b'
        ],
        # Documents/légal - fort
        'legal': [
            r'\btitre foncier\b', r'\btf\b', r'\btitre de propriété\b',
            r'\bnotaire\b', r'\bacte de vente\b', r'\bimmatriculation\b',
            r'\bdeed\b', r'\btitle\b', r'\bproperty title\b'
        ],
        # Types spécifiques vente - moyen
        'property_types': [
            r'\bterrain\b', r'\bparcelle\b', r'\blot\b', r'\blotissement\b',
            r'\bplot\b', r'\bland\b',
            r'\bvilla à vendre\b', r'\bimmeuble\b', r'\bbuilding\b',
            r'\bduplex\b', r'\btriplex\b'
        ],
        # Contexte investissement - faible
        'investment': [
            r'\binvestissement\b', r'\binvestir\b', r'\binvestment\b',
            r'\brentabilité\b', r'\bplus-value\b', r'\bvalue appreciation\b'
        ]
    }
    
    @staticmethod
    def clean_text(text):
        """Nettoyer et normaliser le texte"""
        if not text or not isinstance(text, str):
            return ""
        
        # Lowercase et normalisation
        text = text.lower()
        
        # Remplacer les caractères accentués courants
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ô': 'o', 'ö': 'o',
            'î': 'i', 'ï': 'i',
            'ç': 'c'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Nettoyer les caractères spéciaux mais garder les espaces et slashes
        text = re.sub(r'[^\w\s/\-]', ' ', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @classmethod
    def search_patterns(cls, text, patterns_dict):
        """
        Cherche des patterns dans le texte et retourne un score pondéré
        
        Args:
            text: Texte à analyser
            patterns_dict: Dict avec catégories et leurs patterns
        
        Returns:
            int: Score total
        """
        if not text:
            return 0
        
        text_clean = cls.clean_text(text)
        total_score = 0
        
        # Poids par catégorie
        weights = {
            'explicit': 10,      # Mots-clés directs
            'temporal': 8,       # Indicateurs temporels
            'transaction': 7,    # Processus transaction
            'legal': 7,          # Documents légaux
            'context': 5,        # Contexte
            'property_types': 3, # Types de biens
            'investment': 2      # Investissement
        }
        
        for category, patterns in patterns_dict.items():
            weight = weights.get(category, 1)
            
            for pattern in patterns:
                if re.search(pattern, text_clean, re.IGNORECASE):
                    total_score += weight
                    logger.debug(f"Match trouvé: '{pattern}' (catégorie: {category}, poids: {weight})")
                    break  # Un match par catégorie suffit
        
        return total_score
    
    @classmethod
    def detect_from_price(cls, price, property_type=None):
        """
        Détection basée sur le prix (méthode conservatrice)
        
        Args:
            price: Prix en FCFA
            property_type: Type de bien (optionnel)
        
        Returns:
            tuple: (score_location, score_vente)
        """
        score_location = 0
        score_vente = 0
        
        if not price or price <= 0:
            return 0, 0
        
        # Analyse du prix (seuil: 1.5M FCFA)
        if price < 500_000:
            # < 500K : Presque certainement location (chambre)
            score_location = 8
        
        elif price < 1_500_000:
            # 500K - 1.5M : Très probablement location
            score_location = 6
        
        elif price < 5_000_000:
            # 1.5M - 5M : Zone ambiguë
            # Légèrement en faveur de la vente car > 1.5M
            score_vente = 2
            score_location = 1
        
        elif price < 20_000_000:
            # 5M - 20M : Probablement vente (petite propriété)
            score_vente = 4
        
        elif price < 50_000_000:
            # 20M - 50M : Vente (propriété moyenne)
            score_vente = 6
        
        else:
            # > 50M : Certainement vente (grande propriété)
            score_vente = 8
        
        # Ajustement selon le type de bien
        if property_type:
            prop_lower = cls.clean_text(property_type)
            
            # Terrain = toujours vente (poids très fort)
            if any(word in prop_lower for word in ['terrain', 'parcelle', 'lot', 'plot', 'land']):
                score_vente += 10
                score_location = 0
            
            # Chambre = souvent location
            elif 'chambre' in prop_lower or 'room' in prop_lower:
                score_location += 3
        
        return score_location, score_vente
    
    @classmethod
    def detect_status(cls, title=None, price=None, property_type=None, source=None, native_status=None):
        """
        Détection ultra-robuste du statut
        
        ORDRE DE PRIORITÉ:
        1. Statut natif (si disponible et fiable)
        2. Analyse du TITRE (patterns ultra-complets)
        3. Type de bien (terrains, etc.)
        4. Prix (seuil 1.5M FCFA)
        5. Source
        
        Args:
            title: Titre de l'annonce
            price: Prix en FCFA
            property_type: Type de bien
            source: Source de données
            native_status: Statut natif si disponible
        
        Returns:
            str: 'Vente' ou 'Location'
        """
        
        # 1. Statut natif (si disponible et valide)
        if native_status and isinstance(native_status, str):
            native_clean = native_status.lower().strip()
            if native_clean in ['vente', 'sale', 'sell', 'à vendre', 'a vendre']:
                return 'Vente'
            elif native_clean in ['location', 'rent', 'rental', 'à louer', 'a louer']:
                return 'Location'
        
        # Scores cumulatifs
        score_location = 0
        score_vente = 0
        
        # 2. ANALYSE DU TITRE (PRIORITÉ MAXIMALE)
        if title:
            title_score_location = cls.search_patterns(title, cls.LOCATION_PATTERNS)
            title_score_vente = cls.search_patterns(title, cls.VENTE_PATTERNS)
            
            score_location += title_score_location
            score_vente += title_score_vente
            
            logger.debug(f"Scores titre: Location={title_score_location}, Vente={title_score_vente}")
        
        # 3. ANALYSE DU TYPE DE BIEN
        if property_type:
            prop_clean = cls.clean_text(property_type)
            
            # Terrain = TOUJOURS vente (override tout)
            if any(word in prop_clean for word in ['terrain', 'parcelle', 'lot', 'plot', 'land']):
                logger.debug("Type 'terrain' détecté -> Force Vente")
                return 'Vente'
            
            # Chambre = souvent location
            if 'chambre' in prop_clean or 'room' in prop_clean:
                score_location += 3
        
        # 4. ANALYSE DU PRIX
        price_score_location, price_score_vente = cls.detect_from_price(price, property_type)
        score_location += price_score_location
        score_vente += price_score_vente
        
        logger.debug(f"Scores prix: Location={price_score_location}, Vente={price_score_vente}")
        
        # 5. FACTEUR SOURCE
        if source:
            if source == 'LogerDakar':
                score_location += 1
            elif source in ['CoinAfrique', 'ExpatDakar']:
                score_vente += 0.5
        
        # DÉCISION FINALE
        logger.debug(f"SCORES FINAUX: Location={score_location}, Vente={score_vente}")
        
        if score_location > score_vente:
            return 'Location'
        elif score_vente > score_location:
            return 'Vente'
        else:
            # Égalité: utiliser le prix comme arbitre (seuil 1.5M)
            if price and price >= 1_500_000:
                return 'Vente'
            else:
                return 'Location'


# Fonction helper pour utilisation rapide
def detect_listing_status(title=None, price=None, property_type=None, source=None, native_status=None):
    """
    Fonction helper pour détecter le statut
    
    Usage:
        status = detect_listing_status(
            title="Appartement à louer Plateau",
            price=350000,
            property_type="Appartement",
            source="CoinAfrique"
        )
    """
    return StatusDetector.detect_status(
        title=title,
        price=price,
        property_type=property_type,
        source=source,
        native_status=native_status
    )


# Tests unitaires
if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("TESTS DE DÉTECTION DU STATUT")
    print("=" * 60)
    
    test_cases = [
        # Format: (title, price, property_type, expected)
        ("Appartement à louer Plateau", 350_000, "Appartement", "Location"),
        ("Studio meublé disponible", 200_000, "Studio", "Location"),
        ("Villa à vendre Almadies", 150_000_000, "Villa", "Vente"),
        ("Terrain 500m² à vendre", 25_000_000, "Terrain", "Vente"),
        ("Belle chambre meublée", 80_000, "Chambre", "Location"),
        ("Duplex moderne", 2_500_000, "Duplex", "Vente"),
        ("Appartement 350K/mois", 350_000, "Appartement", "Location"),
        ("Parcelle lotie", 15_000_000, "Terrain", "Vente"),
        ("Studio", 1_200_000, "Studio", "Location"),
        ("Studio", 2_000_000, "Studio", "Vente"),
        ("Immeuble R+2", 80_000_000, "Immeuble", "Vente"),
        ("Location mensuelle", 450_000, "Appartement", "Location"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for i, (title, price, prop_type, expected) in enumerate(test_cases, 1):
        result = detect_listing_status(title=title, price=price, property_type=prop_type)
        is_correct = result == expected
        correct += is_correct
        
        status_icon = "✅" if is_correct else "❌"
        print(f"\n{status_icon} Test {i}:")
        print(f"  Titre: {title}")
        print(f"  Prix: {price:,} FCFA")
        print(f"  Type: {prop_type}")
        print(f"  Attendu: {expected} | Obtenu: {result}")
    
    print("\n" + "=" * 60)
    print(f"RÉSULTATS: {correct}/{total} ({correct/total*100:.1f}% de réussite)")
    print("=" * 60)