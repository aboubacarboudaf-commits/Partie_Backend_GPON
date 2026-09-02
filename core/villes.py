import math

# Miroir du dictionnaire VILLES_GPS de frontend/src/pages/CarteReseau.js.
# Sert à valider côté serveur que les coordonnées saisies correspondent à la ville choisie.
VILLES_GPS = {
    "Niamey": {"lat": 13.5127, "lng": 2.1126},
    "Zinder": {"lat": 13.8072, "lng": 8.9881},
    "Maradi": {"lat": 13.5000, "lng": 7.1021},
    "Agadez": {"lat": 16.9733, "lng": 7.9911},
    "Tahoua": {"lat": 14.8888, "lng": 5.2692},
    "Dosso": {"lat": 13.0490, "lng": 3.1937},
    "Diffa": {"lat": 13.3154, "lng": 12.6113},
    "Tillabéri": {"lat": 14.2117, "lng": 1.4531},
}

DISTANCE_MAX_KM = 150


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rayon_terre_km = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * rayon_terre_km * math.asin(math.sqrt(a))


def valider_coordonnees_ville(ville: str, latitude, longitude) -> None:
    """Lève ValueError si les coordonnées sont trop éloignées de la ville connue."""
    if not ville or latitude is None or longitude is None:
        return
    ref = VILLES_GPS.get(ville.strip())
    if not ref:
        return
    ecart = distance_km(latitude, longitude, ref["lat"], ref["lng"])
    if ecart > DISTANCE_MAX_KM:
        raise ValueError(
            f"Les coordonnées ({latitude}, {longitude}) sont à {ecart:.0f} km de {ville} "
            f"— elles ne semblent pas correspondre à cette ville."
        )
