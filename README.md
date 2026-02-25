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

- **Source :** : Web scraping "automobile.tn"
- **Format :** CSV
- **Nombre d’observations** : 2141 lignes
- **Nombre de variables** : 24 colonnes

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

## Équipe

- **Nom de l’équipe :** Data Vision
- **Membres :**
  - Amira May
  - Yasmine ben attaia
  - Aziz oueslati

---

## Objectifs pédagogiques

- Comprendre la structure du jeu de données
- Réaliser une **Analyse Exploratoire des Données (EDA)**
- Nettoyer et préparer les données
- Construire et entraîner des modèles de régression
- Évaluer et comparer les performances des modèles
- Prédire les prix avec le meilleur modèle

---

## Exécution du projet

1. Cloner le dépôt

```bash
git clone https://github.com/Mayamira10/mon-projet-ml.git


Installer les dépendances
pip install -r requirements.txt

## Contact

Pour toute question ou remarque :
mayamiratir@gmail.com

---
```
