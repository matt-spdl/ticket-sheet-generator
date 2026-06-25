# Générateur de planche de billets

Ce projet génère un PDF de planches de billets à partir d'un modèle image, d'une configuration JSON et d'un fichier CSV.

## Contenu

- [generator.py](generator.py) : script principal.
- [config.json](config.json) : modèle de configuration à copier pour démarrer.
- [data.csv](data.csv) : exemple de structure CSV à copier ou adapter.
- [modele.png](modele.png) : image du ticket à personnaliser.
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
2. Modifier [config.json](config.json).
3. Vérifier que le CSV et le modèle image pointés par la config existent bien.
4. Lancer le script :

```bash
python generator.py
```

Le PDF est généré dans `output.pdf` par défaut.

## Structure de la configuration

Le fichier de configuration est un JSON avec les clés suivantes :

- `template_path` : chemin vers l'image du ticket.
- `csv_path` : chemin vers le fichier de données CSV.
- `csv_delimiter` : séparateur utilisé dans le CSV.
- `debug` : active ou non les sorties de débogage.
- `output_path` : chemin du PDF généré.
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
- `font_path` : chemin vers la police
- `font_size` : taille de la police.
- `align` : alignement horizontal (`left`, `center`, `right`).
- `anchor` : ancrage vertical du texte.
- `color` : couleur du texte.

## Format CSV attendu

La configuration actuelle utilise les colonnes suivantes :

- `Prénom-Nom`
- `Poste`
- `Structure`

Le fichier [data.csv](data.csv) montre un exemple minimal compatible avec le script, et [config.json](config.json) pointe vers cet exemple.

## Notes

- Le script ignore les champs vides dans le CSV.