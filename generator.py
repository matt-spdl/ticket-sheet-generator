import json
import csv
import os
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, HexColor, black
from typing import Dict, List, Any, Tuple

# Types pour améliorer la lisibilité du code
ConfigType = Dict[str, Any]
TicketDataType = Dict[str, str]

# Cache global pour les polices
FONT_CACHE = {}


def load_config(config_path: str) -> ConfigType:
    """Charge la configuration depuis un fichier JSON."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def load_csv_data(csv_path: str, delimiter: str = ',') -> List[Dict[str, str]]:
    """Charge les données depuis un fichier CSV."""
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            data.append(row)
    return data


def get_font(font_path: str, font_size: int):
    """Récupère une police depuis le cache ou la charge si nécessaire."""
    key = (font_path, font_size)
    if key not in FONT_CACHE:
        try:
            if font_path and os.path.exists(font_path):
                FONT_CACHE[key] = ImageFont.truetype(font_path, font_size)
            else:
                print(f"Attention: Police '{font_path}' non trouvée. Utilisation de la police par défaut.")
                FONT_CACHE[key] = ImageFont.load_default()
        except Exception as e:
            print(f"Erreur lors du chargement de la police: {str(e)}")
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def create_ticket(
        template: Image.Image,
        ticket_data: TicketDataType,
        fields_config: List[Dict[str, Any]],
        debug: bool = False
) -> Image.Image:
    """
    Crée un billet avec les données spécifiées et un positionnement précis du texte.

    Args:
        template: Image du modèle de billet (déjà chargée)
        ticket_data: Données pour ce billet spécifique
        fields_config: Configuration des champs texte
        debug: Si True, active le mode débogage

    Returns:
        Image du billet avec les données insérées
    """
    # Créer une copie de l'image template pour ne pas modifier l'original
    ticket = template.copy()

    # Créer une couche transparente pour le texte
    text_layer = Image.new('RGBA', ticket.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Couche de debug si nécessaire
    debug_layer = None
    if debug:
        debug_layer = Image.new('RGBA', ticket.size, (0, 0, 0, 0))
        debug_draw = ImageDraw.Draw(debug_layer)

    # Ajouter chaque champ texte
    for field in fields_config:
        if field['csv_field'] not in ticket_data:
            continue

        text = str(ticket_data[field['csv_field']])
        if not text.strip():
            continue

        # Obtenir la police
        font = get_font(field.get('font_path'), field.get('font_size', 12))

        # Position spécifiée dans la configuration (la valeur verticale correspond à la ligne de base désirée)
        anchor_x, anchor_y = field['position']

        # Couleur du texte
        color = field.get('color', 'black')

        # Obtenir l'alignement horizontal et le type d'ancrage vertical
        align = field.get('align', 'left').lower()
        # Pour l'ancrage vertical, on accepte "top" (haut), "center" (centre), ou "bottom" (bas)
        vertical_anchor = field.get('anchor', 'top').lower()

        # Calcul des dimensions horizontales du texte
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Obtenir les métriques de la police
        ascent, descent = font.getmetrics()
        total_height = ascent + descent

        # Calcul horizontal
        final_x = anchor_x
        if align == 'center':
            final_x -= text_width // 2
        elif align == 'right':
            final_x -= text_width

        # Calcul vertical basé sur la ligne de base
        # On considère que anchor_y correspond à la ligne de base du texte
        if 'center' in vertical_anchor or 'milieu' in vertical_anchor or 'centre' in vertical_anchor:
            # Aligne le centre visuel du texte avec anchor_y
            final_y = anchor_y - total_height / 2
        elif 'bottom' in vertical_anchor or 'bas' in vertical_anchor:
            # Aligne le bas du texte avec anchor_y, donc la ligne de base est au-dessus de la descente
            final_y = anchor_y - descent
        else:  # Par défaut, alignement "top" (haut)
            # Aligne le haut du texte avec anchor_y, donc la ligne de base est décalée vers le bas de l'ascent
            final_y = anchor_y - ascent

        if debug:
            print(f"Champ: {field['csv_field']}, Texte: '{text}'")
            print(f"  Dimensions horizontales: {text_width}px")
            print(f"  Métriques: ascent={ascent}, descent={descent}, total_height={total_height}")
            print(f"  Position d'ancrage: ({anchor_x}, {anchor_y})")
            print(f"  Position finale: ({final_x}, {final_y})")

            # Rectangle pour visualiser la zone de texte
            debug_draw.rectangle(
                (final_x, final_y, final_x + text_width, final_y + total_height),
                outline=(255, 0, 0, 255),
                width=1
            )

            # Point marquant la position d'ancrage (ligne de base)
            debug_draw.ellipse(
                (anchor_x - 2, anchor_y - 2, anchor_x + 2, anchor_y + 2),
                fill=(0, 0, 255, 255)
            )
            # Lignes de guidage
            debug_draw.line(
                (anchor_x - 10, anchor_y, anchor_x + 10, anchor_y),
                fill=(0, 255, 0, 255),
                width=1
            )

        # Dessiner le texte à la position finale
        draw.text((final_x, final_y), text, fill=color, font=font)

    # Combiner les couches
    result = Image.alpha_composite(ticket, text_layer)

    # Ajouter la couche de debug si nécessaire
    if debug and debug_layer:
        result = Image.alpha_composite(result, debug_layer)
        ticket.save('debug_template.png')
        text_layer.save('debug_text.png')
        debug_layer.save('debug_boxes.png')
        result.save('debug_result.png')

    return result


def draw_crop_marks(c, ticket_positions, ticket_width, ticket_height, layout, crop_marks_config):
    """
    Ajoute des repères de coupe autour des billets.

    Args:
        c: Objet canvas ReportLab
        ticket_positions: Liste des positions (x, y) de chaque billet
        ticket_width: Largeur d'un billet
        ticket_height: Hauteur d'un billet
        layout: Configuration de mise en page (colonnes, lignes)
        crop_marks_config: Configuration des repères de coupe
    """
    # Vérifier si les repères de coupe sont activés
    if not crop_marks_config.get('enabled', True):
        return

    # Paramètres des repères de coupe
    mark_length = crop_marks_config.get('length_mm', 10) * mm
    line_width = crop_marks_config.get('line_width', 0.5)
    exterior_only = crop_marks_config.get('exterior_only', False)

    # Obtenir la couleur des repères
    color_value = crop_marks_config.get('color', 'black')
    try:
        if color_value.startswith('#'):
            color = HexColor(color_value)
        else:
            color = getattr(Color, color_value.lower(), black)
    except:
        color = black

    # Si nous n'avons pas de positions, nous ne pouvons pas dessiner les repères
    if not ticket_positions:
        return

    # Extraire les coordonnées de tous les tickets
    all_x = sorted(set(x for x, _ in ticket_positions))
    all_y = sorted(set(y for _, y in ticket_positions), reverse=True)  # Descendant car y commence en haut

    # Pour chaque ticket, ajouter également les coordonnées du bord inférieur
    all_y_bottom = sorted(set(y - ticket_height for _, y in ticket_positions), reverse=True)
    all_y = sorted(all_y + all_y_bottom, reverse=True)

    # Pour chaque ticket, ajouter également les coordonnées du bord droit
    all_x_right = sorted(set(x + ticket_width for x, _ in ticket_positions))
    all_x = sorted(all_x + all_x_right)

    # Définir le style des repères de coupe
    c.setStrokeColor(color)
    c.setLineWidth(line_width)

    # Si exterior_only est activé, dessiner uniquement les repères extérieurs
    if exterior_only:
        # Trouver les bords extérieurs
        left_edge = min(all_x)
        right_edge = max(all_x)
        top_edge = max(all_y)
        bottom_edge = min(all_y)

        # Dessiner les repères horizontaux uniquement pour les bords supérieur et inférieur
        for x in all_x:
            # Repère supérieur
            c.line(x, top_edge + mark_length, x, top_edge)
            # Repère inférieur
            c.line(x, bottom_edge - mark_length, x, bottom_edge)

        # Dessiner les repères verticaux uniquement pour les bords gauche et droit
        for y in all_y:
            # Repère gauche
            c.line(left_edge - mark_length, y, left_edge, y)
            # Repère droit
            c.line(right_edge + mark_length, y, right_edge, y)

    # Sinon, dessiner tous les repères comme avant
    else:
        # Collecter toutes les coordonnées uniques pour les lignes horizontales et verticales
        horizontal_lines = set()  # Ensembles pour éviter les duplications
        vertical_lines = set()

        for x, y in ticket_positions:
            # Pour chaque billet, on ajoute les coordonnées des 4 côtés
            horizontal_lines.add((x, y))  # Haut gauche
            horizontal_lines.add((x, y - ticket_height))  # Bas gauche
            vertical_lines.add((x, y))  # Haut gauche
            vertical_lines.add((x + ticket_width, y))  # Haut droite

        # Dessiner les repères horizontaux pour chaque ligne
        for x, y in horizontal_lines:
            # Repère à gauche
            c.line(x - mark_length, y, x, y)
            # Repère à droite
            c.line(x + ticket_width, y, x + ticket_width + mark_length, y)

        # Dessiner les repères verticaux pour chaque colonne
        for x, y in vertical_lines:
            # Repère en haut
            c.line(x, y + mark_length, x, y)
            # Repère en bas
            c.line(x, y - ticket_height, x, y - ticket_height - mark_length)


def generate_ticket_sheet(
        config: ConfigType,
        ticket_data_list: List[TicketDataType],
        output_path: str
) -> None:
    """
    Génère une ou plusieurs planches de billets en PDF.

    Args:
        config: Configuration globale
        ticket_data_list: Liste des données pour chaque billet
        output_path: Chemin pour sauvegarder le PDF
    """
    start_time = time.time()
    debug = config.get('debug', False)
    print(f"Démarrage de la génération avec {len(ticket_data_list)} billets...")

    # Extraire les paramètres de la configuration
    page_width = config['page']['width_mm'] * mm
    page_height = config['page']['height_mm'] * mm
    ticket_width = config['ticket']['width_mm'] * mm
    ticket_height = config['ticket']['height_mm'] * mm
    h_spacing = config.get('spacing', {}).get('horizontal_mm', 0) * mm
    v_spacing = config.get('spacing', {}).get('vertical_mm', 0) * mm
    cols = config['layout']['columns']
    rows = config['layout']['rows']

    # Configuration des repères de coupe
    crop_marks_config = config.get('crop_marks', {})

    # Calcul des marges pour centrer les billets sur la page
    content_width = (cols * ticket_width) + ((cols - 1) * h_spacing)
    content_height = (rows * ticket_height) + ((rows - 1) * v_spacing)
    margin_left = (page_width - content_width) / 2
    margin_top = (page_height - content_height) / 2

    if debug:
        print(f"Dimensions de la page: {page_width / mm}mm x {page_height / mm}mm")
        print(f"Dimensions d'un billet: {ticket_width / mm}mm x {ticket_height / mm}mm")
        print(f"Disposition: {cols} colonnes x {rows} lignes")
        print(f"Espacement: horizontal={h_spacing / mm}mm, vertical={v_spacing / mm}mm")
        print(f"Marges: gauche={margin_left / mm}mm, haut={margin_top / mm}mm")

    # Pré-charger le modèle de billet
    template = Image.open(config['template_path']).convert('RGBA')

    # Création du PDF
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    # Nombre de billets par page
    tickets_per_page = cols * rows
    total_pages = (len(ticket_data_list) + tickets_per_page - 1) // tickets_per_page

    # Pré-calculer les positions
    positions = []
    for row in range(rows):
        for col in range(cols):
            x = margin_left + (col * (ticket_width + h_spacing))
            y = page_height - margin_top - ticket_height - (row * (ticket_height + v_spacing))
            positions.append((x, y + ticket_height))  # Ajuster pour que y pointe vers le coin supérieur gauche

    # Générer les billets et les ajouter au PDF
    current_ticket = 0
    for page_num in range(total_pages):
        if page_num % 5 == 0 or page_num == 0:
            print(f"Page {page_num + 1}/{total_pages}...")

        # Liste pour stocker les positions des tickets sur la page actuelle
        page_positions = []

        # Pour chaque position sur la page
        for pos_index, (x, y) in enumerate(positions):
            if current_ticket >= len(ticket_data_list):
                break

            # Créer le billet
            ticket_img = create_ticket(
                template,
                ticket_data_list[current_ticket],
                config['fields'],
                debug=(debug and current_ticket < 3)  # Limiter le debug aux 3 premiers
            )

            # Conversion pour le PDF
            img_buffer = io.BytesIO()
            ticket_img_rgb = ticket_img.convert('RGB')
            ticket_img_rgb.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)

            # Ajouter l'image au PDF (y est ajusté pour pointer vers le coin supérieur gauche)
            c.drawImage(img_reader := ImageReader(img_buffer), x, y - ticket_height, width=ticket_width,
                        height=ticket_height)
            img_buffer.close()

            # Stocker la position pour les repères de coupe
            page_positions.append((x, y))

            current_ticket += 1

        # Ajouter les repères de coupe pour tous les tickets de la page
        draw_crop_marks(c, page_positions, ticket_width, ticket_height, config['layout'], crop_marks_config)

        # Ajouter une nouvelle page si nécessaire
        if page_num < total_pages - 1:
            c.showPage()

    # Finaliser le PDF
    c.save()

    elapsed = time.time() - start_time
    print(f"PDF généré avec succès: {output_path}")
    print(f"Total: {current_ticket} billets sur {total_pages} pages")
    print(f"Temps d'exécution: {elapsed:.2f} secondes")


def main():
    base_dir = Path(__file__).resolve().parent

    # Chemins résolus depuis la racine du projet pour rendre le projet portable
    config_path = base_dir / 'config.json'

    # Charger la configuration
    config = load_config(str(config_path))

    def resolve_path(path_value: str) -> str:
        path = Path(path_value)
        if path.is_absolute():
            return str(path)
        return str((base_dir / path).resolve())

    config['template_path'] = resolve_path(config['template_path'])
    config['csv_path'] = resolve_path(config['csv_path'])
    config['output_path'] = resolve_path(config['output_path'])

    for field in config.get('fields', []):
        if field.get('font_path'):
            field['font_path'] = resolve_path(field['font_path'])

    # Charger les données CSV
    data = load_csv_data(config['csv_path'], delimiter=config.get('csv_delimiter', ','))

    # Générer les planches de billets
    generate_ticket_sheet(config, data, config['output_path'])


if __name__ == "__main__":
    main()