from pydantic import BaseModel
from typing import Optional

class CarData(BaseModel):
    Marque: str
    Kilometrage: float
    Energie: str
    Boite_vitesse: str
    Puissance_fiscale: int
    Puissance_ch: Optional[int] = None
    Transmission: str
    Carrosserie: str
    Proprietaires: Optional[int] = None
    Gouvernorat: str
    Couleur_exterieure: Optional[str] = None
    Couleur_interieure: Optional[str] = None
    Sellerie: Optional[str] = None
    Nombre_places: Optional[int] = None
    Nombre_portes: Optional[int] = None
    Cylindree: Optional[float] = None
    age_voiture: Optional[int] = None

class CarAnnonce(BaseModel):
    marque: str
    modele: Optional[str] = None
    kilometrage: float
    energie: str
    boite_vitesse: str
    puissance_fiscale: int
    puissance_ch: Optional[int] = None
    carrosserie: str
    gouvernorat: str
    couleur_exterieure: Optional[str] = None
    couleur_interieure: Optional[str] = None
    sellerie: Optional[str] = None
    nombre_places: Optional[int] = None
    nombre_portes: Optional[int] = None
    cylindree: Optional[float] = None
    age_voiture: Optional[int] = None
    prix: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    vendeur_nom: Optional[str] = None
    vendeur_telephone: Optional[str] = None
    images: Optional[list] = None

class CarStatut(BaseModel):
    statut: str 

class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str
    telephone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    gouvernorat: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class MessageCreate(BaseModel):
    receiver_id: int
    car_id: int
    content: str

class AutofillRequest(BaseModel):
    query: str
    history: list = []

class UserPreferences(BaseModel):
    marques: Optional[list] = []
    carrosseries: Optional[list] = []
    energies: Optional[list] = []
    gouvernorats: Optional[list] = []
    budget_min: Optional[float] = 0
    budget_max: Optional[float] = 999999
    km_max: Optional[float] = 999999
    age_max: Optional[int] = 20
    notify_enabled: Optional[bool] = True

class NotifPreferences(BaseModel):
    budget_min: Optional[float] = 0
    budget_max: Optional[float] = 9999999
    marques: Optional[list] = []
    energies: Optional[list] = []
    carrosseries: Optional[list] = []
    gouvernorats: Optional[list] = []
    kilometrage_max: Optional[float] = 999999
    annee_min: Optional[int] = 0
    notifications_actives: Optional[bool] = True

class ChatRequest(BaseModel):
    question: str
    history: Optional[list] = []
