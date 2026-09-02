from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.audit import log_action
from core.auto_maintenance import creer_maintenance_automatique
from core.security import get_current_user, require_admin_ou_technicien
from database import get_db
from models import Equipement, Incident, Utilisateur

router = APIRouter(prefix="/simulation", tags=["simulation"])

SCENARIOS = {
    "ber_eleve": {
        "nom": "ber_eleve",
        "description": "Taux d'erreur (BER) élevé sur le port PON",
        "type": "degradation",
        "priorite": "moyenne",
        "emoji": "📈",
        "actions": [
            "Vérifier le niveau de puissance optique reçue",
            "Contrôler la propreté des connecteurs",
            "Comparer le BER avec les seuils constructeur",
        ],
    },
    "perte_signal": {
        "nom": "perte_signal",
        "description": "Perte de signal optique (LOS) détectée",
        "type": "panne",
        "priorite": "critique",
        "emoji": "🔴",
        "actions": [
            "Vérifier la continuité de la fibre depuis l'OLT",
            "Contrôler l'alimentation de l'équipement",
            "Envoyer un technicien sur site si le signal ne revient pas",
        ],
    },
    "coupure_fibre": {
        "nom": "coupure_fibre",
        "description": "Coupure de fibre optique sur le tronçon principal",
        "type": "coupure",
        "priorite": "critique",
        "emoji": "✂️",
        "actions": [
            "Localiser la coupure avec un réflectomètre (OTDR)",
            "Dépêcher une équipe de réparation sur le tronçon concerné",
            "Basculer sur un chemin de secours si disponible",
        ],
    },
    "temperature_elevee": {
        "nom": "temperature_elevee",
        "description": "Température élevée sur l'équipement (78°C)",
        "type": "panne",
        "priorite": "haute",
        "emoji": "🔥",
        "actions": [
            "Vérifier la ventilation de l'armoire/local technique",
            "Contrôler la charge de l'équipement",
            "Planifier une maintenance préventive si récurrent",
        ],
    },
    "connecteur_oxyde": {
        "nom": "connecteur_oxyde",
        "description": "Connecteur oxydé - Perte de 3dB",
        "type": "degradation",
        "priorite": "moyenne",
        "emoji": "🔌",
        "actions": [
            "Nettoyer ou remplacer le connecteur optique",
            "Mesurer l'atténuation après intervention",
        ],
    },
    "surcharge_reseau": {
        "nom": "surcharge_reseau",
        "description": "Surcharge de trafic sur l'OLT",
        "type": "panne",
        "priorite": "haute",
        "emoji": "⚠️",
        "actions": [
            "Analyser la répartition de charge entre ports PON",
            "Envisager un équilibrage ou une extension de capacité",
        ],
    },
}


@router.get("/scenarios")
def scenarios(_=Depends(get_current_user)):
    return [
        {"nom": s["nom"], "description": s["description"], "actions": s["actions"]}
        for s in SCENARIOS.values()
    ]


@router.post("/panne-reelle")
def panne_reelle(
    scenario_nom: str,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    scenario = SCENARIOS.get(scenario_nom)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scénario inconnu")

    equipement = (
        db.query(Equipement)
        .filter(Equipement.supprime == False, Equipement.etat == "actif")  # noqa: E712
        .order_by(func.rand())
        .first()
    )
    if not equipement:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun équipement actif disponible pour la simulation")

    description = f"[SIMULATION] {scenario['emoji']} {scenario['description']} - Équipement: {equipement.libelle}"
    incident = Incident(
        type=scenario["type"],
        source="automatique",
        description=description,
        equipement_id=equipement.id_equipement,
        statut="ouvert",
        priorite=scenario["priorite"],
        date_ouverture=date.today(),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    log_action(db, "creation", "incident", incident.id_incident, f"Simulation panne: {scenario['nom']} sur {equipement.libelle}", utilisateur, request)
    creer_maintenance_automatique(db, incident, utilisateur, request)

    return {
        "scenario": scenario["nom"],
        "equipement_impacte": equipement.libelle,
        "description": description,
        "actions": scenario["actions"],
    }


@router.post("/reparer-tout")
def reparer_tout(
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin_ou_technicien),
):
    incidents = db.query(Incident).filter(
        Incident.supprime == False,  # noqa: E712
        Incident.statut.in_(["ouvert", "en_cours"]),
        Incident.description.like("[SIMULATION]%"),
    ).all()

    for incident in incidents:
        incident.statut = "resolu"
        incident.date_fermeture = date.today()
    db.commit()

    log_action(db, "modification", "incident", None, f"Réparation simulation: {len(incidents)} incident(s) résolu(s)", utilisateur, request)

    return {"message": f"{len(incidents)} incident(s) de simulation résolu(s)"}
