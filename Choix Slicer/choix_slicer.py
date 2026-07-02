import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk

# Fonction indispensable pour trouver les images intégrées dans le .exe par PyInstaller
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

if len(sys.argv) < 2:
    print("Aucun fichier à ouvrir. Glissez un fichier 3D sur ce script ou associez-le.")
    sys.exit()
    
fichier_3d = sys.argv[1]

# --- CONFIGURATION DES LOGICIELS ---
SLICERS_CONFIG = [
    {
        "nom": "AnycubicSlicer",
        "chemin": r"C:\Program Files\AnycubicSlicerNext\AnycubicSlicerNext.exe",
        "image_nom": "logo_anycubic.png",
        "type_taille": "anycubic",
        "hauteur_encart": 35
    },
    {
        "nom": "Creality Print",
        "chemin": r"C:\Program Files\Creality\Creality Print 7.0\CrealityPrint.exe",
        "image_nom": "logo_creality.png",
        "type_taille": "creality_xl",
        "hauteur_encart": 45
    }
]

def lancer_slicer(chemin_slicer):
    subprocess.Popen([chemin_slicer, fichier_3d])
    fenetre.destroy()

# Interface graphique
fenetre = tk.Tk()
fenetre.title("Trancheur Unique")

# 1. RETIRER LA BARRE DE TITRE NATIVE DE WINDOWS
fenetre.overrideredirect(True)

# Taille globale de la fenêtre
fenetre.geometry("450x640")
fenetre.resizable(False, False)

style = ttk.Style()
style.theme_use('vista')

# --- FONCTIONS POUR POUVOIR DÉPLACER LA FENÊTRE À LA SOURIS ---
def demarrer_deplacement(event):
    fenetre.x = event.x
    fenetre.y = event.y

def deplacer_fenetre(event):
    deltax = event.x - fenetre.x
    deltay = event.y - fenetre.y
    x = fenetre.winfo_x() + deltax
    y = fenetre.winfo_y() + deltay
    fenetre.geometry(f"+{x}+{y}")

# --- 2. CRÉATION DE LA BARRE DE TITRE BLEU FONCÉ ---
COULEUR_BARRE = "#0a2540"

barre_titre = tk.Frame(fenetre, bg=COULEUR_BARRE, height=90)
barre_titre.pack(fill="x", side="top")
barre_titre.pack_propagate(False)

# Rendre la barre cliquable pour déplacer la fenêtre
barre_titre.bind("<Button-1>", demarrer_deplacement)
barre_titre.bind("<B1-Motion>", deplacer_fenetre)

# --- 3. LOGO EN 20x20 mm (Trancheur Unique logo.png - 80x80 PX) ---
try:
    chemin_logo_unique = resource_path("Trancheur Unique logo.png")
    img_brute = tk.PhotoImage(file=chemin_logo_unique)
    
    facteur_x = max(1, img_brute.width() // 80)
    facteur_y = max(1, img_brute.height() // 80)
    img_ico_barre = img_brute.subsample(facteur_x, facteur_y)
    
    label_ico = tk.Label(barre_titre, image=img_ico_barre, bg=COULEUR_BARRE)
    label_ico.pack(side="left", padx=15)
except Exception as e:
    try:
        img_ico_barre = tk.PhotoImage(file=resource_path("logo_anycubic.png")).subsample(4, 4)
        label_ico = tk.Label(barre_titre, image=img_ico_barre, bg=COULEUR_BARRE)
        label_ico.pack(side="left", padx=15)
    except:
        pass

# Titre personnalisé du logiciel dans la barre ("Trancheur Unique")
titre_logiciel = tk.Label(barre_titre, text="Trancheur Unique", fg="white", bg=COULEUR_BARRE, font=("Helvetica", 11, "bold"))
titre_logiciel.pack(side="left", padx=5)
titre_logiciel.bind("<Button-1>", demarrer_deplacement)
titre_logiciel.bind("<B1-Motion>", deplacer_fenetre)

# --- 4. BOUTONS SYSTEME ---
btn_fermer = tk.Button(
    barre_titre, text="✕", fg="white", bg=COULEUR_BARRE, activebackground="#e81123", activeforeground="white",
    bd=0, font=("Helvetica", 14, "bold"), width=4, height=3, command=fenetre.destroy
)
btn_fermer.pack(side="right")

def reduire_fenetre():
    fenetre.update_idletasks()
    fenetre.overrideredirect(False)
    fenetre.state('iconic')

btn_reduire = tk.Button(
    barre_titre, text="—", fg="white", bg=COULEUR_BARRE, activebackground="#163e65", activeforeground="white",
    bd=0, font=("Helvetica", 12, "bold"), width=4, height=3, command=reduire_fenetre
)
btn_reduire.pack(side="right")

def sur_focus(event):
    fenetre.overrideredirect(True)
fenetre.bind("<FocusIn>", sur_focus)

# --- CONTENU DE LA FENÊTRE ---
label = ttk.Label(fenetre, text="Quel trancheur pour ce projet ?", font=("Helvetica", 12, "bold"))
label.pack(pady=20)

label_fichier = ttk.Label(fenetre, text=os.path.basename(fichier_3d), font=("Helvetica", 9, "italic"))
label_fichier.pack(pady=2)

frame_boutons = ttk.Frame(fenetre)
frame_boutons.pack(pady=10, fill="both", expand=True)

boutons_crees = 0
images_stockage = []

for config in SLICERS_CONFIG:
    chemin = config["chemin"]
    if os.path.exists(chemin):
        chemin_image_complete = resource_path(config["image_nom"])
        try:
            img = tk.PhotoImage(file=chemin_image_complete)
            
            if config["type_taille"] == "anycubic":
                img_intermediaire = img.zoom(3, 3)
                img_finale = img_intermediaire.subsample(10, 10)
            elif config["type_taille"] == "creality_xl":
                img_finale = img.subsample(2, 2)
            else:
                img_finale = img.subsample(4, 4)
                
            images_stockage.append(img_finale)
            
            btn = ttk.Button(
                frame_boutons, 
                image=img_finale, 
                command=lambda c=chemin: lancer_slicer(c)
            )
        except Exception as e:
            btn = ttk.Button(frame_boutons, text=config["nom"], command=lambda c=chemin: lancer_slicer(c))

        btn.pack(pady=15, padx=50, fill="x", ipady=config["hauteur_encart"])
        boutons_crees += 1

if boutons_crees == 0:
    label_erreur = ttk.Label(
        frame_boutons, 
        text="⚠️ Aucun trancheur trouvé.\nVérifiez les chemins d'installation.", 
        foreground="red", 
        justify="center"
    )
    label_erreur.pack(pady=20)

fenetre.mainloop()