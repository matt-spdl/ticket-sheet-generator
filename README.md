# Générateur de planche de billets

Ce projet génère un PDF de planches de billets à partir d'un modèle image, d'une configuration JSON et d'un fichier CSV.

## Contenu

- [generator.py](generator.py) : script principal.
- [src/config.json](src/config.json) : configuration active utilisée par défaut.
- [src/config.example.json](src/config.example.json) : modèle de configuration à copier pour démarrer.
- [src/data.csv](src/data.csv) : données réelles utilisées par défaut.
- [src/data.example.csv](src/data.example.csv) : exemple de structure CSV à copier ou adapter.
- [src/modele.example.png](src/modele.example.png) : image du ticket à personnaliser.
- [fonts/](fonts/) : polices utilisées pour le rendu.

## Installation

Le projet nécessite Python 3.10+ avec ces dépendances :

- Pillow
- reportlab

Installation rapide :

```bash
pip install -r requirements.txt
```

## Utilisation

1. Vérifier que le fichier CSV contient bien les colonnes attendues par la configuration.
2. Utiliser [src/config.json](src/config.json) directement, ou copier [src/config.example.json](src/config.example.json) si tu veux repartir d'un modèle propre.
3. Vérifier que le CSV et le modèle image pointés par la config existent bien dans `src/`.
4. Lancer le script :

```bash
python generator.py
```

Le PDF est généré dans `output.pdf` par défaut.

## Structure de la configuration

Le fichier de configuration est un JSON avec les clés suivantes :

- `template_path` : chemin vers l'image du ticket, résolu depuis `src/`.
- `csv_path` : chemin vers le fichier de données CSV, résolu depuis `src/`.
- `csv_delimiter` : séparateur utilisé dans le CSV.
- `debug` : active ou non les sorties de débogage.
- `output_path` : chemin du PDF généré, résolu depuis `src/`.
- `page` : dimensions de la page en millimètres.
- `ticket` : dimensions d'un ticket en millimètres.
- `spacing` : espacement horizontal et vertical entre tickets.
- `layout` : nombre de colonnes et de lignes sur une page.
- `crop_marks` : paramètres des repères de coupe.
- `fields` : liste des champs à écrire sur chaque billet.

Les sous-objets `page`, `ticket`, `spacing` et `layout` contiennent chacun des valeurs numériques en millimètres ou des compteurs.

Chaque élément de `fields` contient :

- `csv_field` : nom exact de la colonne CSV à afficher.
- `position` : coordonnées `[x, y]` du point d'ancrage.
- `font_path` : chemin vers la police, résolu depuis `src/`.
- `font_size` : taille de la police.
- `align` : alignement horizontal (`left`, `center`, `right`).
- `anchor` : ancrage vertical du texte.
- `color` : couleur du texte.

## Format CSV attendu

La configuration actuelle utilise les colonnes suivantes :

- `Prénom-Nom`
- `Poste`
- `Structure`

Le fichier [src/data.example.csv](src/data.example.csv) montre un exemple minimal compatible avec le script, et [src/config.example.json](src/config.example.json) pointe vers cet exemple.

## Notes

- Les chemins dans la config sont relatifs au dossier `src/`, ce qui permet de cloner et exécuter le dépôt ailleurs sans modification.
- Le script ignore les champs vides dans le CSV.