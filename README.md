# Prédiction du Prix des Voitures en Tunisie

### Mini-projet Machine Learning guidé

**Module :** Python for Data Science 2  
**Encadrant :** [Haythem Ghazouani](https://github.com/haythemghz)

---

## Présentation du projet

Ce projet consiste à développer un modèle de **Machine Learning** permettant de **prédire le prix des voitures d’occasion en Tunisie**, à partir de données réelles collectées depuis le site _automobile.tn_.

Le projet suit les étapes essentielles d’un **pipeline Data Science complet**, depuis la compréhension des données jusqu’à l’évaluation des modèles.

---

## Problématique

> Comment prédire le prix d’une voiture d’occasion en Tunisie à partir de ses caractéristiques techniques et générales ?

- **Type de problème :** Apprentissage supervisé
- **Tâche :** Régression
- **Variable cible :** Prix de la voiture

---

## Description du dataset

- **Source :** automobile.tn
- **Format :** CSV
- **Nombre d’observations :** 108 voitures
- **Nombre de variables :** 24 colonnes

### Principales variables :

- Marque
- Modèle
- Kilométrage
- Année de mise en circulation
- Énergie
- Boîte de vitesse
- Puissance
- Carrosserie
- État général

---

## Prétraitement des données

Les étapes de prétraitement incluent :

- Traitement des valeurs manquantes
- Nettoyage des variables textuelles numériques (prix, kilométrage)
- Encodage des variables catégorielles
- Normalisation des variables numériques
- Séparation des données (train / test)

---

## Modèles de Machine Learning utilisés

- Régression linéaire
- Random Forest Regressor
- Gradient Boosting

---

## Métriques d’évaluation

Les performances des modèles sont évaluées à l’aide des métriques suivantes :

- **MAE (Mean Absolute Error)**
- **RMSE (Root Mean Squared Error)**
- **R² Score**

---

## Outils et technologies

- Python 3
- Pandas
- NumPy
- Scikit-learn
- Matplotlib / Seaborn
- Jupyter Notebook
- visual studio code

---

## Structure du projet

prediction-prix-voitures-tn/
├── data/ # Données brutes et traitées
├── notebooks/ # Notebooks Jupyter
│ ├── 01_eda.ipynb # Analyse exploratoire
│ ├── 02_preprocessing.ipynb # Prétraitement
│ └── 03_modelisation.ipynb # Modélisation
├── src/ # Code source Python
│ ├── preprocessing.py # Script de prétraitement
│ └── entrainement_modele.py # Script d'entraînement
├── README.md # Documentation
└── requirements.txt # Dépendances Python

---

## Équipe

- **Nom de l’équipe :** Data Vision
- **Membres :**
  - Amira May
  - Yassemine ben attaia
  - Aziz oueslati

---

## Objectifs pédagogiques

- Appliquer les étapes d’un projet Machine Learning réel
- Manipuler un dataset issu du monde réel
- Comparer plusieurs modèles de régression
- Interpréter les résultats obtenus

---

## Contact

Pour toute question ou remarque :
mayamiratir@gmail.com

---
