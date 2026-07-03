import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<Motion>", self.move_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Helvetica", 9, "normal"))
        label.pack(ipadx=4, ipady=1)
        
        self.move_tip(event)

    def move_tip(self, event):
        if self.tip_window and event:
            x = event.x_root + 15
            y = event.y_root + 15
            self.tip_window.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# --- CONFIGURATION DU CHEMIN DU FICHIER CONFIG ---
if getattr(sys, 'frozen', False):
    DOSSIER_APP = os.path.dirname(sys.executable)
else:
    DOSSIER_APP = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(DOSSIER_APP, "config_slicers.txt")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = DOSSIER_APP
    chemin_complet = os.path.join(base_path, relative_path)
    if os.path.exists(chemin_complet):
        return chemin_complet
    chemin_local = os.path.join(DOSSIER_APP, relative_path)
    if os.path.exists(chemin_local):
        return chemin_local
    return None

# --- FORCE L'ICÔNE SUR L'EXTENSION .3MF DANS WINDOWS ---
def associer_icone_extension_3mf(chemin_ico):
    if not chemin_ico or not os.path.exists(chemin_ico):
        return
    try:
        import winreg
        # Crée/Modifie l'association dans le registre utilisateur actuel (Pas besoin d'être Admin !)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.3mf") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "TrancheurUnique.3mf")
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\TrancheurUnique.3mf\DefaultIcon") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{os.path.abspath(chemin_ico)}",0')
            
        # Force la mise à jour immédiate de l'affichage Windows
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception as e:
        print("Erreur registre :", e)

# --- GESTION DU FICHIER EN ENTRÉE ---
fichier_3d = sys.argv[1] if len(sys.argv) > 1 else None
demander_confirmation = True

# --- CHARGEMENT ET SAUVEGARDE DES SLICERS ---
def charger_slicers_personnalises():
    slicers = []
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for ligne in f:
                    ligne = ligne.strip()
                    if ligne and "||" in ligne:
                        elements = ligne.split("||")
                        nom = elements[0]
                        chemin = elements[1]
                        icone = elements[2] if len(elements) > 2 else None
                        
                        slicers.append({
                            "nom": nom,
                            "chemin": chemin,
                            "image_nom": icone, 
                            "type_taille": "custom_user"
                        })
        except Exception as e:
            print("Erreur de lecture de la config:", e)
            
    slicers.sort(key=lambda x: x["nom"].lower())
    return slicers

def réécrire_tous_slicers(liste_slicers):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            for s in liste_slicers:
                valeur_icone = s["image_nom"] if s["image_nom"] else "None"
                f.write(f"{s['nom']}||{s['chemin']}||{valeur_icone}\n")
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de mettre à jour le fichier de configuration :\n{e}")
        return False

def sauvegarder_slicer_personnalise(nom, chemin, icone_chemin):
    try:
        with open(CONFIG_FILE, "a", encoding="utf-8") as f:
            valeur_icone = icone_chemin if icone_chemin else "None"
            f.write(f"{nom}||{chemin}||{valeur_icone}\n")
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de sauvegarder le trancheur :\n{e}")
        return False

def supprimer_slicer_personnalise(nom_a_supprimer):
    if not os.path.exists(CONFIG_FILE):
        return
        
    reponse = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment retirer '{nom_a_supprimer}' de la liste ?")
    if not reponse:
        return

    lignes_a_garder = []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for ligne in f:
                if ligne.strip() and "||" in ligne:
                    nom = ligne.split("||")[0]
                    if nom != nom_a_supprimer:
                        lignes_a_garder.append(ligne)
                        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lignes_a_garder)
            
        rafraichir_boutons()
        redimensionner_et_centrer()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de modifier le fichier de configuration :\n{e}")

def lancer_slicer(chemin_slicer, nom_slicer):
    global demander_confirmation
    
    if not os.path.exists(chemin_slicer):
        messagebox.showerror("Erreur", f"Le trancheur est introuvable à l'adresse :\n{chemin_slicer}")
        return

    if not fichier_3d:
        messagebox.showwarning("Aucun fichier", "Veuillez d'abord sélectionner un fichier 3D avec le bouton dossier jaune avant de lancer un trancheur.")
        return

    if demander_confirmation:
        fenetre_conf = tk.Toplevel(fenetre)
        fenetre_conf.title("Confirmation")
        fenetre_conf.geometry("270x100")
        fenetre_conf.resizable(False, False)
        fenetre_conf.transient(fenetre)
        fenetre_conf.grab_set()
        
        couleur_fond = fenetre_conf.cget("bg")
        
        text_widget = tk.Text(
            fenetre_conf, 
            font=("Helvetica", 10), 
            bg=couleur_fond, 
            bd=0, 
            highlightthickness=0,
            width=35, 
            height=2,
            wrap="word"
        )
        
        text_widget.tag_configure("centre", justify="center")
        text_widget.tag_configure("gras", font=("Helvetica", 10, "bold"))
        
        text_widget.insert("1.0", "Ouvrir le fichier avec ", "centre")
        text_widget.insert("end", nom_slicer, ("centre", "gras"))
        text_widget.insert("end", " ?", "centre")
        
        text_widget.config(state="disabled")
        text_widget.pack(pady=(15, 6), padx=15, fill="x")
        
        var_ne_plus_afficher = tk.BooleanVar(value=False)
        chk_ne_plus = ttk.Checkbutton(
            fenetre_conf, 
            text="Ne plus afficher ce message", 
            variable=var_ne_plus_afficher
        )
        chk_ne_plus.pack(pady=(0, 8))
        
        frame_boutons = ttk.Frame(fenetre_conf)
        frame_boutons.pack(side="bottom", pady=(0, 12))
        
        action_validee = [False]
        
        def oui_clic():
            global demander_confirmation
            if var_ne_plus_afficher.get():
                demander_confirmation = False
            action_validee[0] = True
            fenetre_conf.destroy()
            
        def non_clic():
            fenetre_conf.destroy()
            
        ttk.Button(frame_boutons, text="Oui", command=oui_clic, width=8).pack(side="left", padx=8)
        ttk.Button(frame_boutons, text="Non", command=non_clic, width=8).pack(side="right", padx=8)
        
        fenetre_conf.update_idletasks()
        largeur_boite = fenetre_conf.winfo_width()
        hauteur_boite = fenetre_conf.winfo_height()
        
        pos_x = fenetre.winfo_x() + (fenetre.winfo_width() // 2) - (largeur_boite // 2)
        pos_y = fenetre.winfo_y() + (fenetre.winfo_height() // 2) - (hauteur_boite // 2)
        
        fenetre_conf.geometry(f"{largeur_boite}x{hauteur_boite}+{pos_x}+{pos_y}")
        
        fenetre.wait_window(fenetre_conf)
        
        if not action_validee[0]:
            return
            
    subprocess.Popen([chemin_slicer, fichier_3d])
    fenetre.destroy()

# --- INITIALISATION DE L'INTERFACE PRINCIPALE ---

try:
    # Force Windows à grouper l'icône correctement sur la barre des tâches
    mon_app_id = 'monentreprise.trancheurunique.version.1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(mon_app_id)
except:
    pass

# La racine DEVIENT la fenêtre visible directement (Adieu la plume)
fenetre = tk.Tk()
fenetre.title("Trancheur Unique")
fenetre.overrideredirect(True)

h_maximisee = False
w_maximisee = False

def reduire_fenetre():
    fenetre.overrideredirect(False)
    fenetre.iconify()

def restaurer_fenetre(event):
    if fenetre.state() == "normal" and not fenetre.overrideredirect():
        fenetre.overrideredirect(True)

fenetre.bind("<Map>", restaurer_fenetre)

style = ttk.Style()
style.theme_use('vista')

taille_origine = {"w": 480, "h": 500, "x": 0, "y": 0}

# --- MOUVEMENTS ET REDIMENSIONNEMENTS ---
def demarrer_deplacement(event):
    global w_maximisee, h_maximisee
    if w_maximisee or h_maximisee:
        w_maximisee, h_maximisee = False, False
        btn_agrandir.config(text="⬜")
        fenetre.geometry(f"{taille_origine['w']}x{taille_origine['h']}")
    fenetre.x = event.x
    fenetre.y = event.y

def deplacer_fenetre(event):
    deltax = event.x - fenetre.x
    deltay = event.y - fenetre.y
    x = fenetre.winfo_x() + deltax
    y = fenetre.winfo_y() + deltay
    fenetre.geometry(f"+{x}+{y}")

BORDURE_SENSIVITE = 8  

def evaluer_bord(event):
    x, y = event.x, event.y
    w = fenetre.winfo_width()
    h = fenetre.winfo_height()
    gauche = x < BORDURE_SENSIVITE
    droite = x > w - BORDURE_SENSIVITE
    haut = y < BORDURE_SENSIVITE
    bas = y > h - BORDURE_SENSIVITE
    if gauche and haut: return "top_left"
    elif droite and haut: return "top_right"
    elif gauche and bas: return "bottom_left"
    elif droite and bas: return "bottom_right"
    elif gauche: return "left"
    elif droite: return "right"
    elif haut: return "top"
    elif bas: return "bottom"
    else: return "none"

def changer_curseur(event):
    if hasattr(fenetre, '_bord_actif') and fenetre._bord_actif != "none":
        return
    bord = evaluer_bord(event)
    if bord in ("top_left", "bottom_right"): fenetre.config(cursor="size_nw_se")
    elif bord in ("top_right", "bottom_left"): fenetre.config(cursor="size_ne_sw")
    elif bord in ("left", "right"): fenetre.config(cursor="size_we")
    elif bord in ("top", "bottom"): fenetre.config(cursor="size_ns")
    else: fenetre.config(cursor="")

def demarrer_redimensionnement_bord(event):
    global w_maximisee, h_maximisee
    bord_detecte = evaluer_bord(event)
    if bord_detecte == "none": return
    
    if w_maximisee or h_maximisee:
        w_maximisee, h_maximisee = False, False
        btn_agrandir.config(text="⬜")
        fenetre.geometry(f"{taille_origine['w']}x{taille_origine['h']}+{taille_origine['x']}+{taille_origine['y']}")
        fenetre.update_idletasks()

    fenetre._bord_actif = bord_detecte
    fenetre._w_init = fenetre.winfo_width()
    fenetre._h_init = fenetre.winfo_height()
    fenetre._x_init = fenetre.winfo_x()
    fenetre._y_init = fenetre.winfo_y()
    fenetre._x_racine_init = event.x_root
    fenetre._y_racine_init = event.y_root

def executer_redimensionnement_bord(event):
    if hasattr(fenetre, '_bord_actif') and fenetre._bord_actif != "none":
        dx = event.x_root - fenetre._x_racine_init
        dy = event.y_root - fenetre._y_racine_init
        w_min, h_min = 420, 360
        nw, nh = fenetre._w_init, fenetre._h_init
        nx, ny = fenetre._x_init, fenetre._y_init
        
        utile_h = fenetre.winfo_screenheight() - 60
        
        if "right" in fenetre._bord_actif: nw = max(w_min, fenetre._w_init + dx)
        if "left" in fenetre._bord_actif:
            nw = max(w_min, fenetre._w_init - dx)
            if nw > w_min: nx = fenetre._x_init + dx
        if "bottom" in fenetre._bord_actif: 
            nh = max(h_min, fenetre._h_init + dy)
            if ny + nh > utile_h: nh = utile_h - ny  
        if "top" in fenetre._bord_actif:
            nh = max(h_min, fenetre._h_init - dy)
            if nh > h_min: ny = fenetre._y_init + dy
        fenetre.geometry(f"{nw}x{nh}+{nx}+{ny}")

def finir_redimensionnement_bord(event):
    fenetre._bord_actif = "none"
    fenetre.config(cursor="")

def verif_double_clic_bord(event):
    global h_maximisee, w_maximisee, taille_origine
    bord = evaluer_bord(event)
    if bord == "none": return
    
    utile_w = fenetre.winfo_screenwidth()
    utile_h = fenetre.winfo_screenheight() - 60

    if not h_maximisee and not w_maximisee:
        taille_origine["w"] = fenetre.winfo_width()
        taille_origine["h"] = fenetre.winfo_height()
        taille_origine["x"] = fenetre.winfo_x()
        taille_origine["y"] = fenetre.winfo_y()

    x_actuel = fenetre.winfo_x()
    y_actuel = fenetre.winfo_y()
    w_actuel = fenetre.winfo_width()
    h_actuel = fenetre.winfo_height()

    if bord in ["left", "right"]:
        if w_maximisee:
            fenetre.geometry(f"{taille_origine['w']}x{h_actuel}+{taille_origine['x']}+{y_actuel}")
            w_maximisee = False
        else:
            fenetre.geometry(f"{utile_w}x{h_actuel}+0+{y_actuel}")
            w_maximisee = True
    elif bord in ["top", "bottom"]:
        if h_maximisee:
            fenetre.geometry(f"{w_actuel}x{taille_origine['h']}+{x_actuel}+{taille_origine['y']}")
            h_maximisee = False
        else:
            fenetre.geometry(f"{w_actuel}x{utile_h}+{x_actuel}+0")
            h_maximisee = True
    else:
        if w_maximisee and h_maximisee:
            fenetre.geometry(f"{taille_origine['w']}x{taille_origine['h']}+{taille_origine['x']}+{taille_origine['y']}")
            w_maximisee, h_maximisee = False, False
        else:
            fenetre.geometry(f"{utile_w}x{utile_h}+0+0")
            w_maximisee, h_maximisee = True, True

    btn_agrandir.config(text="🗗" if (w_maximisee and h_maximisee) else "⬜")

fenetre.bind("<Motion>", changer_curseur)
fenetre.bind("<Button-1>", demarrer_redimensionnement_bord)
fenetre.bind("<B1-Motion>", executer_redimensionnement_bord)
fenetre.bind("<ButtonRelease-1>", finir_redimensionnement_bord)
fenetre.bind("<Double-Button-1>", verif_double_clic_bord)

# --- BARRE DE TITRE ---
COULEUR_BARRE = "#0a2540"
barre_titre = tk.Frame(fenetre, bg=COULEUR_BARRE, height=90)
barre_titre.pack(fill="x", side="top")
barre_titre.pack_propagate(False)

def verif_deplacement(event):
    if evaluer_bord(event) == "none": demarrer_deplacement(event)
def verif_action_deplacement(event):
    if hasattr(fenetre, '_bord_actif') and fenetre._bord_actif == "none": deplacer_fenetre(event)

barre_titre.bind("<Button-1>", verif_deplacement)
barre_titre.bind("<B1-Motion>", verif_action_deplacement)

# --- CHARGEMENT DES ICÔNES ---
chemin_ico = resource_path("Trancheur Unique logo.ico")
chemin_png = resource_path("Trancheur Unique logo.png")

if chemin_ico and os.path.exists(chemin_ico):
    try:
        fenetre.iconbitmap(chemin_ico)
        # Écrit l'icône dans la zone utilisateur du registre pour les .3mf
        associer_icone_extension_3mf(chemin_ico)
    except Exception as e:
        print("Erreur iconbitmap :", e)

logo_affiche = False
if chemin_png and os.path.exists(chemin_png):
    try:
        img_icone_app = tk.PhotoImage(file=chemin_png)
        facteur_x = max(1, img_icone_app.width() // 70)
        facteur_y = max(1, img_icone_app.height() // 60)
        img_ico_barre = img_icone_app.subsample(facteur_x, facteur_y)
        
        label_ico = tk.Label(barre_titre, image=img_ico_barre, bg=COULEUR_BARRE)
        label_ico.image = img_ico_barre  
        label_ico.pack(side="left", padx=10)
        label_ico.bind("<Button-1>", verif_deplacement)
        label_ico.bind("<B1-Motion>", verif_action_deplacement)
        logo_affiche = True
    except Exception as e:
        print("Erreur d'affichage du logo PNG :", e)

if not logo_affiche:
    lbl_alt_logo = tk.Label(barre_titre, text="", font=("Helvetica", 12), bg=COULEUR_BARRE, fg="#00a2ed")
    lbl_alt_logo.pack(side="left", padx=10)

titre_logiciel = tk.Label(barre_titre, text="Trancheur Unique", fg="white", bg=COULEUR_BARRE, font=("Helvetica", 10, "bold"))
titre_logiciel.pack(side="left", padx=2)
titre_logiciel.bind("<Button-1>", verif_deplacement)
titre_logiciel.bind("<B1-Motion>", verif_action_deplacement)

btn_fermer = tk.Button(barre_titre, text="✕", fg="white", bg=COULEUR_BARRE, activebackground="#e81123", activeforeground="white", bd=0, font=("Helvetica", 11, "bold"), width=4, height=2, command=fenetre.destroy)
btn_fermer.pack(side="right")

def basculer_agrandissement(event=None):
    global h_maximisee, w_maximisee, taille_origine
    utile_w = fenetre.winfo_screenwidth()
    utile_h = fenetre.winfo_screenheight() - 60
    if not (h_maximisee and w_maximisee):
        if not h_maximisee and not w_maximisee:
            taille_origine = {"w": fenetre.winfo_width(), "h": fenetre.winfo_height(), "x": fenetre.winfo_x(), "y": fenetre.winfo_y()}
        fenetre.geometry(f"{utile_w}x{utile_h}+0+0")
        btn_agrandir.config(text="🗗")  
        h_maximisee, w_maximisee = True, True
    else:
        fenetre.geometry(f"{taille_origine['w']}x{taille_origine['h']}+{taille_origine['x']}+{taille_origine['y']}")
        btn_agrandir.config(text="⬜")  
        h_maximisee, w_maximisee = False, False

barre_titre.bind("<Double-Button-1>", basculer_agrandissement)
titre_logiciel.bind("<Double-Button-1>", basculer_agrandissement)

btn_agrandir = tk.Button(barre_titre, text="⬜", fg="white", bg=COULEUR_BARRE, activebackground="#163e65", activeforeground="white", bd=0, font=("Helvetica", 9), width=4, height=2, command=basculer_agrandissement)
btn_agrandir.pack(side="right")

btn_reduire = tk.Button(barre_titre, text="—", fg="white", bg=COULEUR_BARRE, activebackground="#163e65", activeforeground="white", bd=0, font=("Helvetica", 10, "bold"), width=4, height=2, command=reduire_fenetre)
btn_reduire.pack(side="right")

# --- CONTENU PRINCIPAL ---
label = ttk.Label(fenetre, text="Quel Slicer pour ce projet ?", font=("Helvetica", 12, "bold"))
label.pack(pady=(4, 0))

frame_selection = tk.Frame(fenetre, bg=fenetre.cget("bg"))
frame_selection.pack(pady=0)

def action_parcourir_3d():
    global fichier_3d
    fichier = filedialog.askopenfilename(
        title="Sélectionner un fichier 3D", 
        filetypes=[("Fichiers 3D", "*.stl *.3mf *.obj *.step *.stp"), ("Tous les fichiers", "*.*")]
    )
    if fichier:
        fichier_3d = os.path.normpath(fichier)
        mettre_a_jour_affichage_fichier()

btn_parcourir_3d = tk.Button(
    frame_selection, 
    text="📁",  # Remplacé ici par le dossier rempli
    font=("Segoe UI Symbol", 22), 
    fg="#ffcc00",       
    bg=fenetre.cget("bg"), 
    bd=0, 
    relief="flat",
    activebackground=fenetre.cget("bg"),
    command=action_parcourir_3d,
    cursor="hand2"
)
btn_parcourir_3d.grid(row=0, column=0, padx=(10, 5), pady=0)
Tooltip(btn_parcourir_3d, "Parcourir un fichier 3D...")

label_fichier = ttk.Label(frame_selection, font=("Helvetica", 9, "italic"))
label_fichier.grid(row=0, column=1, sticky="w", pady=0) 

def mettre_a_jour_affichage_fichier():
    global fichier_3d
    if fichier_3d:
        label_fichier.config(text=os.path.basename(fichier_3d), font=("Helvetica", 9, "bold"), foreground="black")
    else:
        label_fichier.config(text="Parcourir un fichier 3D", font=("Helvetica", 10, "italic"), foreground="gray")

mettre_a_jour_affichage_fichier()

frame_contenu_boutons = tk.Frame(fenetre, bg="white")
frame_contenu_boutons.pack(pady=4, fill="both", expand=True)

images_stockage = []

def rafraichir_boutons():
    global images_stockage
    for widget in frame_contenu_boutons.winfo_children(): 
        widget.destroy()
    images_stockage.clear()
    
    liste_complete = charger_slicers_personnalises()
    liste_valide = [cfg for cfg in liste_complete if os.path.exists(cfg["chemin"])]
    
    if not liste_valide:
        lbl = ttk.Label(frame_contenu_boutons, text="⚠️ Aucun Slicer enregistré...", foreground="orange", background="white")
        lbl.pack(pady=20)
        return

    lignes_par_colonne = 4
    nb_colonnes = ((len(liste_valide) - 1) // lignes_par_colonne) + 1

    for index, config in enumerate(liste_valide):
        chemin = config["chemin"]
        nom_logiciel = config["nom"]
        
        col = index // lignes_par_colonne
        lig = index % lignes_par_colonne
        
        row_frame = tk.Frame(frame_contenu_boutons, bg="white")
        
        if nb_colonnes == 1:
            row_frame.pack(pady=8, padx=40)
        else:
            row_frame.grid(row=lig, column=col, padx=20, pady=8, sticky="nsew")
        
        container_bouton = tk.Frame(row_frame, bg="white")
        container_bouton.pack(side="left", padx=10)
        container_bouton.grid_rowconfigure(0, weight=1)
        container_bouton.grid_columnconfigure(0, weight=1)

        btn = tk.Button(container_bouton, command=lambda c=chemin, n=nom_logiciel: lancer_slicer(c, n), bg="white", bd=0, relief="flat")
        Tooltip(btn, nom_logiciel)
        if config["image_nom"] and config["image_nom"] != "None" and os.path.exists(config["image_nom"]):
            try:
                img = tk.PhotoImage(file=config["image_nom"])
                images_stockage.append(img)
                btn.config(image=img)
            except: pass
        btn.grid(row=0, column=0, sticky="nsew")
        
        btn_modif = tk.Button(container_bouton, text="⚙️", fg="gray", bg="white", bd=0, font=("Helvetica", 10), command=lambda c=config: ouvrir_fenetre_ajout(slicer_a_modifier=c))
        btn_modif.grid(row=0, column=0, sticky="nw", padx=3, pady=3)
        btn_suppr = tk.Button(container_bouton, text="✕", fg="red", bg="white", bd=0, font=("Helvetica", 12, "bold"), command=lambda n=nom_logiciel: supprimer_slicer_personnalise(n))
        btn_suppr.grid(row=0, column=0, sticky="ne", padx=3, pady=3)

# --- DIALOGUE D'AJOUT ET DE MODIFICATION ---
def ouvrir_fenetre_ajout(slicer_a_modifier=None):
    fenetre_ajout = tk.Toplevel(fenetre)
    fenetre_ajout.resizable(False, False)
    fenetre_ajout.transient(fenetre) 
    fenetre_ajout.grab_set()         
    
    mode_edition = slicer_a_modifier is not None
    if mode_edition:
        fenetre_ajout.title("Modifier le Slicer")
    else:
        fenetre_ajout.title("Ajouter un Trancheur")
        
    fenetre_ajout.geometry("420x260")
    fenetre_ajout.geometry(f"+{fenetre.winfo_x() + (fenetre.winfo_width() // 2) - 210}+{fenetre.winfo_y() + (fenetre.winfo_height() // 2) - 130}")
    
    ttk.Label(fenetre_ajout, text="Nom du trancheur :", font=("Helvetica", 10, "bold")).pack(pady=(12, 2), padx=20, anchor="w")
    entry_nom = ttk.Entry(fenetre_ajout, width=34)
    entry_nom.pack(padx=20, pady=2, anchor="w")
    if mode_edition:
        entry_nom.insert(0, slicer_a_modifier["nom"])
    
    ttk.Label(fenetre_ajout, text="Chemin de l'exécutable (.exe) :", font=("Helvetica", 10, "bold")).pack(pady=(10, 2), padx=20, anchor="w")
    frame_parcourir = ttk.Frame(fenetre_ajout)
    frame_parcourir.pack(padx=20, pady=2, fill="x")
    entry_chemin = ttk.Entry(frame_parcourir, width=34)
    entry_chemin.pack(side="left", fill="x", expand=True, padx=(0, 5))
    if mode_edition:
        entry_chemin.insert(0, slicer_a_modifier["chemin"])
    
    def action_parcourir():
        fichier = filedialog.askopenfilename(title="Sélectionner l'exécutable", filetypes=[("Applications", "*.exe")])
        if fichier:
            entry_chemin.delete(0, tk.END)
            entry_chemin.insert(0, os.path.normpath(fichier))
    ttk.Button(frame_parcourir, text="Parcourir...", command=action_parcourir).pack(side="right")
    
    ttk.Label(fenetre_ajout, text="Icône du Slicer (.png optionnel) :", font=("Helvetica", 10, "bold")).pack(pady=(10, 2), padx=20, anchor="w")
    frame_icone = ttk.Frame(fenetre_ajout)
    frame_icone.pack(padx=20, pady=2, fill="x")
    entry_icone = ttk.Entry(frame_icone, width=34)
    entry_icone.pack(side="left", fill="x", expand=True, padx=(0, 5))
    if mode_edition and slicer_a_modifier["image_nom"] and slicer_a_modifier["image_nom"] != "None":
        entry_icone.insert(0, slicer_a_modifier["image_nom"])
    
    def action_parcourir_icone():
        fichier = filedialog.askopenfilename(title="Sélectionner l'icône PNG", filetypes=[("Images PNG", "*.png")])
        if fichier:
            entry_icone.delete(0, tk.END)
            entry_icone.insert(0, os.path.normpath(fichier))
    ttk.Button(frame_icone, text="Parcourir...", command=action_parcourir_icone).pack(side="right")
    
    def valider_action():
        nom, chemin, icone = entry_nom.get().strip(), entry_chemin.get().strip(), entry_icone.get().strip()
        if not nom or not chemin:
            messagebox.showwarning("Champs vides", "Veuillez remplir le nom et spécifier un chemin d'accès.", parent=fenetre_ajout)
            return
        if not os.path.exists(chemin):
            messagebox.showerror("Fichier introuvable", "L'exécutable spécifié n'existe pas.", parent=fenetre_ajout)
            return
        if icone and not os.path.exists(icone):
            messagebox.showerror("Fichier introuvable", "L'icône spécifiée n'existe pas.", parent=fenetre_ajout)
            return
            
        chemin_normalise = os.path.normpath(chemin).lower()
        liste_existante = charger_slicers_personnalises()
        
        for s in liste_existante:
            if mode_edition and s["nom"] == slicer_a_modifier["nom"]:
                continue
            if os.path.normpath(s["chemin"]).lower() == chemin_normalise:
                messagebox.showwarning(
                    "Doublon détecté", 
                    f"Cet exécutable est déjà associé au trancheur '{s['nom']}'.\nIl ne peut pas être ajouté une seconde fois.", 
                    parent=fenetre_ajout
                )
                return

        valeur_icone = icone if icone else None

        if mode_edition:
            for s in liste_existante:
                if s["nom"] == slicer_a_modifier["nom"]:
                    s["nom"] = nom
                    s["chemin"] = chemin
                    s["image_nom"] = valeur_icone
                    break
            if réécrire_tous_slicers(liste_existante):
                rafraichir_boutons()
                redimensionner_et_centrer()
                fenetre_ajout.destroy()
        else:
            if sauvegarder_slicer_personnalise(nom, chemin, valeur_icone):
                rafraichir_boutons()
                redimensionner_et_centrer()
                fenetre_ajout.destroy()
            
    texte_bouton = "Appliquer les modifications" if mode_edition else "Ajouter le logiciel"
    ttk.Button(fenetre_ajout, text=texte_bouton, command=valider_action).pack(pady=22)

frame_actions_basse = ttk.Frame(fenetre)
frame_actions_basse.pack(side="bottom", fill="x", pady=10, padx=15)
ttk.Button(frame_actions_basse, text="➕ Ajouter un Slicer", command=ouvrir_fenetre_ajout).pack(side="left", padx=5)


# --- FONCTION DE CALCUL ET DE CENTRAGE GARANTI ---
def redimensionner_et_centrer():
    global taille_origine
    fenetre.update_idletasks()
    
    largeur_cible = max(480, fenetre.winfo_reqwidth() + 40)
    hauteur_cible = max(460, fenetre.winfo_reqheight())
    
    utile_w = fenetre.winfo_screenwidth()
    utile_h = fenetre.winfo_screenheight() - 60
    
    pos_x = (utile_w // 2) - (largeur_cible // 2)
    pos_y = (utile_h // 2) - (hauteur_cible // 2)
    
    taille_origine = {"w": largeur_cible, "h": hauteur_cible, "x": pos_x, "y": pos_y}
    
    if not h_maximisee and not w_maximisee:
        fenetre.geometry(f"{largeur_cible}x{hauteur_cible}+{pos_x}+{pos_y}")


# --- LANCEMENT DE L'APPLICATION ---
rafraichir_boutons()
redimensionner_et_centrer()

fenetre.mainloop()