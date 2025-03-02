import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, colorchooser
import json
import random
import re
import os
import importlib.util
import sys

class ExerciceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exercices Interactifs")
        
        # Système d'extensions
        self.extensions = {}
        self.extensions_actives = {}
        self.extensions_python = {}
        self.hooks = {
            'apres_creation_interface': [],
            'avant_verification': [],
            'apres_verification': [],
            'avant_nouveau_terme': [],
            'apres_nouveau_terme': [],
            'avant_correction': [],
            'apres_correction': []
        }
        self.charger_extensions()
        
        # Variables pour les préférences
        self.afficher_score_var = tk.BooleanVar(value=True)
        self.afficher_corrections_var = tk.BooleanVar(value=True)
        self.animations_var = tk.BooleanVar(value=True)
        self.mode_sombre_var = tk.BooleanVar(value=False)
        self.afficher_temps_var = tk.BooleanVar(value=True)
        self.mode_plein_ecran_var = tk.BooleanVar(value=False)
        
        # Nouvelles variables de personnalisation
        self.bordures_arrondies_var = tk.BooleanVar(value=True)
        self.ombres_var = tk.BooleanVar(value=True)
        self.mode_compact_var = tk.BooleanVar(value=False)
        self.mode_focus_var = tk.BooleanVar(value=False)
        self.mode_dyslexie_var = tk.BooleanVar(value=False)
        self.contraste_eleve_var = tk.BooleanVar(value=False)
        self.mode_daltonien_var = tk.StringVar(value="normal")
        self.position_boutons_var = tk.StringVar(value="bas")
        self.style_boutons_var = tk.StringVar(value="moderne")
        self.espacement_lignes = tk.IntVar(value=1)
        self.marge_laterale = tk.IntVar(value=10)
        self.marge_verticale = tk.IntVar(value=10)
        
        self.taille_texte = 12
        self.police = "Arial"
        self.opacite = 1.0
        
        # Bouton quitter plein écran
        self.bouton_quitter_plein_ecran = None
        
        # Obtenir la taille de l'écran
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")
        
        # Charger les préférences
        self.preferences = self.charger_preferences()
        
        # Variables pour le style
        self.style = ttk.Style()
        self.background_image = None
        self.background_label = None
        
        self.definitions = {}
        
        # Créer tous les widgets
        self.creer_interface()
        
        # Appliquer le thème après la création des widgets
        self.appliquer_theme()
        
        # Lier la touche Échap
        self.root.bind('<Escape>', lambda e: self.quitter_plein_ecran())
        
    def creer_interface(self):
        # Menu principal
        self.creer_menu()
        
        # Frame principal avec scrollbar
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal
        self.main_frame = ttk.Frame(self.main_container, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Zone de texte pour coller la liste
        ttk.Label(self.main_frame, text="Collez votre liste de définitions ici (format: terme : définition)", 
                 style="Custom.TLabel").grid(row=0, column=0, columnspan=2, pady=5)
        self.text_zone = scrolledtext.ScrolledText(self.main_frame, width=70, height=10)
        self.text_zone.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Sélection du mode d'exercice
        ttk.Label(self.main_frame, text="Type d'exercice:", style="Custom.TLabel").grid(row=2, column=0, pady=5)
        self.mode_var = tk.StringVar(value="aleatoire")
        modes = [
            ("Aléatoire", "aleatoire"),
            ("Questions/Réponses", "qr"),
            ("Vrai/Faux", "vf"),
            ("QCM", "qcm"),
            ("Association", "association")
        ]
        
        # Frame pour les boutons radio
        radio_frame = ttk.Frame(self.main_frame)
        radio_frame.grid(row=2, column=1, pady=5)
        for i, (text, value) in enumerate(modes):
            ttk.Radiobutton(radio_frame, text=text, value=value, variable=self.mode_var).grid(row=0, column=i, padx=5)
        
        # Bouton pour analyser le texte
        ttk.Button(self.main_frame, text="Analyser et créer les exercices", 
                  command=self.analyser_texte, style="Custom.TButton").grid(row=3, column=0, columnspan=2, pady=10)
        
        # Frame pour l'exercice
        self.frame_exercice = ttk.Frame(self.main_container, padding="10")
        self.frame_exercice.grid(row=1, column=0, sticky="nsew")
        
        self.score_label = ttk.Label(self.frame_exercice, text="Score: 0/0", style="Custom.TLabel")
        self.score_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.label_question = ttk.Label(self.frame_exercice, text="", wraplength=800, style="Custom.TLabel")
        self.label_question.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Frame pour les réponses
        self.frame_reponses = ttk.Frame(self.frame_exercice)
        self.frame_reponses.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Entry pour les questions/réponses simples
        self.reponse_entry = ttk.Entry(self.frame_exercice, width=60)
        self.reponse_entry.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Boutons Vrai/Faux
        self.frame_vf = ttk.Frame(self.frame_exercice)
        self.frame_vf.grid(row=4, column=0, columnspan=2, pady=5)
        self.btn_vrai = ttk.Button(self.frame_vf, text="Vrai", command=lambda: self.verifier_vf(True), style="Custom.TButton")
        self.btn_faux = ttk.Button(self.frame_vf, text="Faux", command=lambda: self.verifier_vf(False), style="Custom.TButton")
        self.btn_vrai.grid(row=0, column=0, padx=5)
        self.btn_faux.grid(row=0, column=1, padx=5)
        
        # Frame pour les boutons de contrôle
        self.frame_controle = ttk.Frame(self.frame_exercice)
        self.frame_controle.grid(row=5, column=0, columnspan=2, pady=5)
        
        self.bouton_verifier = ttk.Button(self.frame_controle, text="Vérifier", 
                                        command=self.verifier_reponse, style="Custom.TButton")
        self.bouton_verifier.grid(row=0, column=0, padx=5)
        
        self.bouton_reessayer = ttk.Button(self.frame_controle, text="Réessayer", 
                                         command=self.reessayer, style="Custom.TButton")
        
        self.bouton_correction = ttk.Button(self.frame_controle, text="Voir la correction", 
                                          command=self.montrer_correction, style="Custom.TButton")
        
        self.frame_exercice.grid_remove()
        self.frame_vf.grid_remove()
        self.bouton_reessayer.grid_remove()
        self.bouton_correction.grid_remove()
        
        # Variables pour le score et l'exercice en cours
        self.score = 0
        self.total_questions = 0
        self.type_exercice_actuel = None
        self.reponse_correcte = None
        self.choix_qcm = []
        self.peut_reessayer = True
        
    def creer_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Extensions
        extensions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extensions", menu=extensions_menu)
        
        # Sous-menu Gérer les extensions
        extensions_menu.add_command(label="Gérer les extensions", command=self.afficher_gestionnaire_extensions)
        extensions_menu.add_separator()
        
        # Menu Personnalisation
        perso_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Personnalisation", menu=perso_menu)
        
        # Sous-menu Thèmes
        theme_menu = tk.Menu(perso_menu, tearoff=0)
        perso_menu.add_cascade(label="Thèmes", menu=theme_menu)
        
        # Thèmes clairs
        theme_clair_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Thèmes clairs", menu=theme_clair_menu)
        theme_clair_menu.add_command(label="Clair", command=lambda: self.changer_theme("clair"))
        theme_clair_menu.add_command(label="Bleu clair", command=lambda: self.changer_theme("bleu"))
        theme_clair_menu.add_command(label="Vert clair", command=lambda: self.changer_theme("vert"))
        theme_clair_menu.add_command(label="Orange clair", command=lambda: self.changer_theme("orange"))
        theme_clair_menu.add_command(label="Rose clair", command=lambda: self.changer_theme("rose"))
        theme_clair_menu.add_command(label="Violet clair", command=lambda: self.changer_theme("violet"))
        
        # Thèmes sombres
        theme_sombre_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Thèmes sombres", menu=theme_sombre_menu)
        theme_sombre_menu.add_command(label="Sombre", command=lambda: self.changer_theme("sombre"))
        theme_sombre_menu.add_command(label="Bleu sombre", command=lambda: self.changer_theme("bleu_sombre"))
        theme_sombre_menu.add_command(label="Vert sombre", command=lambda: self.changer_theme("vert_sombre"))
        theme_sombre_menu.add_command(label="Rouge sombre", command=lambda: self.changer_theme("rouge_sombre"))
        theme_sombre_menu.add_command(label="Violet sombre", command=lambda: self.changer_theme("violet_sombre"))
        
        # Sous-menu Interface
        interface_menu = tk.Menu(perso_menu, tearoff=0)
        perso_menu.add_cascade(label="Interface", menu=interface_menu)
        interface_menu.add_command(label="Taille du texte", command=self.changer_taille_texte)
        interface_menu.add_command(label="Police", command=self.changer_police)
        interface_menu.add_command(label="Opacité", command=self.changer_opacite)
        interface_menu.add_separator()
        interface_menu.add_checkbutton(label="Mode plein écran", variable=self.mode_plein_ecran_var, command=self.toggle_plein_ecran)
        interface_menu.add_checkbutton(label="Mode sombre", variable=self.mode_sombre_var, command=self.toggle_mode_sombre)
        
        # Sous-menu Affichage
        affichage_menu = tk.Menu(perso_menu, tearoff=0)
        perso_menu.add_cascade(label="Affichage", menu=affichage_menu)
        affichage_menu.add_checkbutton(label="Afficher le score", variable=self.afficher_score_var, command=self.toggle_score)
        affichage_menu.add_checkbutton(label="Afficher les corrections", variable=self.afficher_corrections_var, command=self.toggle_corrections)
        affichage_menu.add_checkbutton(label="Afficher le temps", variable=self.afficher_temps_var, command=self.toggle_temps)
        affichage_menu.add_checkbutton(label="Animations", variable=self.animations_var, command=self.toggle_animations)
        
        # Nouveau sous-menu Avancé
        avance_menu = tk.Menu(perso_menu, tearoff=0)
        perso_menu.add_cascade(label="Avancé", menu=avance_menu)
        
        # Options d'apparence
        apparence_menu = tk.Menu(avance_menu, tearoff=0)
        avance_menu.add_cascade(label="Apparence", menu=apparence_menu)
        apparence_menu.add_checkbutton(label="Bordures arrondies", variable=self.bordures_arrondies_var, command=self.appliquer_style)
        apparence_menu.add_checkbutton(label="Ombres", variable=self.ombres_var, command=self.appliquer_style)
        apparence_menu.add_checkbutton(label="Mode compact", variable=self.mode_compact_var, command=self.appliquer_style)
        
        # Options d'accessibilité
        accessibilite_menu = tk.Menu(avance_menu, tearoff=0)
        avance_menu.add_cascade(label="Accessibilité", menu=accessibilite_menu)
        accessibilite_menu.add_checkbutton(label="Mode focus", variable=self.mode_focus_var, command=self.appliquer_style)
        accessibilite_menu.add_checkbutton(label="Police dyslexie", variable=self.mode_dyslexie_var, command=self.appliquer_style)
        accessibilite_menu.add_checkbutton(label="Contraste élevé", variable=self.contraste_eleve_var, command=self.appliquer_style)
        
        # Sous-menu Mode daltonien
        daltonien_menu = tk.Menu(accessibilite_menu, tearoff=0)
        accessibilite_menu.add_cascade(label="Mode daltonien", menu=daltonien_menu)
        for mode in ["Normal", "Protanopie", "Deutéranopie", "Tritanopie"]:
            daltonien_menu.add_radiobutton(label=mode, value=mode.lower(), 
                                         variable=self.mode_daltonien_var, command=self.appliquer_style)
        
        # Options de mise en page
        layout_menu = tk.Menu(avance_menu, tearoff=0)
        avance_menu.add_cascade(label="Mise en page", menu=layout_menu)
        
        # Position des boutons
        positions_menu = tk.Menu(layout_menu, tearoff=0)
        layout_menu.add_cascade(label="Position des boutons", menu=positions_menu)
        for pos in ["Haut", "Bas", "Gauche", "Droite"]:
            positions_menu.add_radiobutton(label=pos, value=pos.lower(), 
                                        variable=self.position_boutons_var, command=self.appliquer_style)
        
        # Style des boutons
        style_boutons_menu = tk.Menu(layout_menu, tearoff=0)
        layout_menu.add_cascade(label="Style des boutons", menu=style_boutons_menu)
        for style in ["Moderne", "Classique", "Minimaliste", "Arrondi"]:
            style_boutons_menu.add_radiobutton(label=style, value=style.lower(), 
                                             variable=self.style_boutons_var, command=self.appliquer_style)
        
        # Espacement
        espacement_menu = tk.Menu(layout_menu, tearoff=0)
        layout_menu.add_cascade(label="Espacement des lignes", menu=espacement_menu)
        for esp in [1, 1.15, 1.5, 2]:
            espacement_menu.add_radiobutton(label=f"{esp}x", value=esp, 
                                          variable=self.espacement_lignes, command=self.appliquer_style)
        
        # Marges
        layout_menu.add_command(label="Marges...", command=self.configurer_marges)
        
        # Sous-menu Raccourcis
        raccourcis_menu = tk.Menu(perso_menu, tearoff=0)
        perso_menu.add_cascade(label="Raccourcis clavier", menu=raccourcis_menu)
        raccourcis_menu.add_command(label="Ctrl+Z : Annuler")
        raccourcis_menu.add_command(label="Ctrl+Y : Refaire")
        raccourcis_menu.add_command(label="Ctrl+S : Sauvegarder")
        raccourcis_menu.add_command(label="F11 : Plein écran")
        
        # Option de réinitialisation
        perso_menu.add_separator()
        perso_menu.add_command(label="Réinitialiser les préférences", command=self.reinitialiser_preferences)

    def charger_extensions(self):
        """Charge les extensions depuis les dossiers 'extensions' et 'extensions_python'"""
        try:
            # Créer les dossiers s'ils n'existent pas
            for dossier in ['extensions', 'extensions_python']:
                if not os.path.exists(dossier):
                    os.makedirs(dossier)
                    if dossier == 'extensions_python':
                        # Créer un fichier __init__.py vide
                        with open(os.path.join(dossier, '__init__.py'), 'w') as f:
                            pass
            
            # Charger les extensions activées depuis les préférences
            self.extensions_actives = self.preferences.get('extensions_actives', {})
            
            # Scanner le dossier des extensions JSON
            for fichier in os.listdir('extensions'):
                if fichier.endswith('.json'):
                    chemin = os.path.join('extensions', fichier)
                    try:
                        with open(chemin, 'r', encoding='utf-8') as f:
                            extension = json.load(f)
                            self.extensions[extension['id']] = extension
                    except:
                        print(f"Erreur lors du chargement de l'extension : {fichier}")
            
            # Scanner le dossier des extensions Python
            sys.path.append('extensions_python')
            for fichier in os.listdir('extensions_python'):
                if fichier.endswith('.py') and fichier != '__init__.py':
                    nom_module = fichier[:-3]
                    try:
                        spec = importlib.util.spec_from_file_location(
                            nom_module, 
                            os.path.join('extensions_python', fichier)
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, 'EXTENSION_INFO'):
                            ext_info = module.EXTENSION_INFO
                            ext_id = ext_info['id']
                            self.extensions[ext_id] = ext_info
                            self.extensions_python[ext_id] = module
                            
                            # Enregistrer les hooks si l'extension est active
                            if ext_id in self.extensions_actives:
                                self.enregistrer_hooks_extension(ext_id, module)
                                
                    except Exception as e:
                        print(f"Erreur lors du chargement de l'extension Python {fichier}: {e}")
                    
        except Exception as e:
            print(f"Erreur lors du chargement des extensions : {e}")

    def enregistrer_hooks_extension(self, ext_id, module):
        """Enregistre les hooks d'une extension Python"""
        for nom_hook in self.hooks.keys():
            nom_fonction = f"hook_{nom_hook}"
            if hasattr(module, nom_fonction):
                self.hooks[nom_hook].append(getattr(module, nom_fonction))

    def executer_hooks(self, nom_hook, *args, **kwargs):
        """Exécute tous les hooks enregistrés pour un événement donné"""
        resultats = []
        for hook in self.hooks[nom_hook]:
            try:
                resultat = hook(self, *args, **kwargs)
                if resultat is not None:
                    resultats.append(resultat)
            except Exception as e:
                print(f"Erreur lors de l'exécution du hook {nom_hook}: {e}")
        return resultats

    def toggle_extension(self, extension_id):
        """Active ou désactive une extension"""
        if extension_id in self.extensions_actives:
            del self.extensions_actives[extension_id]
            # Supprimer les hooks si c'est une extension Python
            if extension_id in self.extensions_python:
                for hook_list in self.hooks.values():
                    hook_list[:] = [h for h in hook_list 
                                  if not h.__module__ == self.extensions_python[extension_id].__name__]
        else:
            self.extensions_actives[extension_id] = True
            # Ajouter les hooks si c'est une extension Python
            if extension_id in self.extensions_python:
                self.enregistrer_hooks_extension(
                    extension_id, 
                    self.extensions_python[extension_id]
                )
        self.sauvegarder_extensions()

    def sauvegarder_extensions(self):
        """Sauvegarde l'état des extensions dans les préférences"""
        self.preferences['extensions_actives'] = self.extensions_actives
        self.sauvegarder_preferences()

    def afficher_gestionnaire_extensions(self):
        """Affiche la fenêtre de gestion des extensions"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Gestionnaire d'extensions")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label d'information
        ttk.Label(main_frame, 
                 text="Gérez vos extensions installées",
                 font=(self.police, 12, 'bold')).pack(pady=(0,10))
        
        # Frame pour la liste des extensions
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas pour le défilement
        canvas = tk.Canvas(list_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame pour le contenu
        content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Variables pour les checkboxes
        checkboxes = {}
        
        # Ajouter les extensions à la liste
        for ext_id, ext in self.extensions.items():
            frame_ext = ttk.Frame(content_frame)
            frame_ext.pack(fill=tk.X, pady=5)
            
            # Checkbox pour activer/désactiver
            var = tk.BooleanVar(value=ext_id in self.extensions_actives)
            checkboxes[ext_id] = var
            cb = ttk.Checkbutton(frame_ext, 
                               variable=var,
                               command=lambda id=ext_id: self.toggle_extension(id))
            cb.pack(side=tk.LEFT)
            
            # Informations sur l'extension
            info_frame = ttk.Frame(frame_ext)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            ttk.Label(info_frame, 
                     text=ext.get('nom', 'Sans nom'),
                     font=(self.police, 10, 'bold')).pack(anchor="w")
            
            ttk.Label(info_frame, 
                     text=ext.get('description', ''),
                     wraplength=400).pack(anchor="w")
            
            ttk.Label(info_frame, 
                     text=f"Version: {ext.get('version', '1.0')} | Auteur: {ext.get('auteur', 'Inconnu')}",
                     font=(self.police, 8)).pack(anchor="w")
        
        # Configurer le scrolling
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content_frame.bind('<Configure>', on_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)
        
        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10,0))
        
        # Bouton Installer une nouvelle extension
        ttk.Button(button_frame, 
                  text="Installer une extension",
                  command=self.installer_extension).pack(side=tk.LEFT, padx=5)
        
        # Bouton Fermer
        ttk.Button(button_frame, 
                  text="Fermer",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def installer_extension(self):
        """Ouvre une boîte de dialogue pour installer une nouvelle extension"""
        fichier = filedialog.askopenfilename(
            title="Sélectionner une extension",
            filetypes=[("Fichiers JSON", "*.json")],
            initialdir="."
        )
        
        if fichier:
            try:
                # Copier le fichier dans le dossier extensions
                nom_fichier = os.path.basename(fichier)
                destination = os.path.join('extensions', nom_fichier)
                
                # Vérifier si c'est une extension valide
                with open(fichier, 'r', encoding='utf-8') as f:
                    extension = json.load(f)
                    if 'id' not in extension or 'nom' not in extension:
                        raise ValueError("Format d'extension invalide")
                
                # Copier le fichier
                import shutil
                shutil.copy2(fichier, destination)
                
                # Recharger les extensions
                self.charger_extensions()
                
                # Rafraîchir la fenêtre de gestion
                self.afficher_gestionnaire_extensions()
                
                messagebox.showinfo("Succès", 
                                  f"L'extension '{extension.get('nom')}' a été installée avec succès!")
                
            except Exception as e:
                messagebox.showerror("Erreur", 
                                   f"Impossible d'installer l'extension : {str(e)}")

    def charger_preferences(self):
        try:
            with open('preferences.json', 'r') as f:
                prefs = json.load(f)
                # Charger les préférences de base
                self.afficher_score_var.set(prefs.get('afficher_score', True))
                self.afficher_corrections_var.set(prefs.get('afficher_corrections', True))
                self.animations_var.set(prefs.get('animations', True))
                self.mode_sombre_var.set(prefs.get('mode_sombre', False))
                self.afficher_temps_var.set(prefs.get('afficher_temps', True))
                self.mode_plein_ecran_var.set(prefs.get('mode_plein_ecran', False))
                self.taille_texte = prefs.get('taille_texte', 12)
                self.police = prefs.get('police', 'Arial')
                self.opacite = prefs.get('opacite', 1.0)
                
                # Charger les préférences avancées
                self.bordures_arrondies_var.set(prefs.get('bordures_arrondies', True))
                self.ombres_var.set(prefs.get('ombres', True))
                self.mode_compact_var.set(prefs.get('mode_compact', False))
                self.mode_focus_var.set(prefs.get('mode_focus', False))
                self.mode_dyslexie_var.set(prefs.get('mode_dyslexie', False))
                self.contraste_eleve_var.set(prefs.get('contraste_eleve', False))
                self.mode_daltonien_var.set(prefs.get('mode_daltonien', 'normal'))
                self.position_boutons_var.set(prefs.get('position_boutons', 'bas'))
                self.style_boutons_var.set(prefs.get('style_boutons', 'moderne'))
                self.espacement_lignes.set(prefs.get('espacement_lignes', 1))
                self.marge_laterale.set(prefs.get('marge_laterale', 10))
                self.marge_verticale.set(prefs.get('marge_verticale', 10))
                
                return prefs
        except:
            return {
                'theme': 'clair',
                'afficher_score': True,
                'afficher_corrections': True,
                'animations': True,
                'mode_sombre': False,
                'afficher_temps': True,
                'mode_plein_ecran': False,
                'taille_texte': 12,
                'police': 'Arial',
                'opacite': 1.0,
                'bordures_arrondies': True,
                'ombres': True,
                'mode_compact': False,
                'mode_focus': False,
                'mode_dyslexie': False,
                'contraste_eleve': False,
                'mode_daltonien': 'normal',
                'position_boutons': 'bas',
                'style_boutons': 'moderne',
                'espacement_lignes': 1,
                'marge_laterale': 10,
                'marge_verticale': 10
            }
            
    def sauvegarder_preferences(self):
        self.preferences.update({
            'afficher_score': self.afficher_score_var.get(),
            'afficher_corrections': self.afficher_corrections_var.get(),
            'animations': self.animations_var.get(),
            'mode_sombre': self.mode_sombre_var.get(),
            'afficher_temps': self.afficher_temps_var.get(),
            'mode_plein_ecran': self.mode_plein_ecran_var.get(),
            'taille_texte': self.taille_texte,
            'police': self.police,
            'opacite': self.opacite,
            'bordures_arrondies': self.bordures_arrondies_var.get(),
            'ombres': self.ombres_var.get(),
            'mode_compact': self.mode_compact_var.get(),
            'mode_focus': self.mode_focus_var.get(),
            'mode_dyslexie': self.mode_dyslexie_var.get(),
            'contraste_eleve': self.contraste_eleve_var.get(),
            'mode_daltonien': self.mode_daltonien_var.get(),
            'position_boutons': self.position_boutons_var.get(),
            'style_boutons': self.style_boutons_var.get(),
            'espacement_lignes': self.espacement_lignes.get(),
            'marge_laterale': self.marge_laterale.get(),
            'marge_verticale': self.marge_verticale.get()
        })
        with open('preferences.json', 'w') as f:
            json.dump(self.preferences, f)
            
    def appliquer_theme(self):
        theme = self.preferences.get('theme', 'clair')
        
        themes = {
            'clair': {'bg': '#ffffff', 'fg': '#000000', 'button': '#e0e0e0'},
            'sombre': {'bg': '#2d2d2d', 'fg': '#ffffff', 'button': '#404040'},
            'bleu': {'bg': '#e3f2fd', 'fg': '#1976d2', 'button': '#bbdefb'},
            'bleu_sombre': {'bg': '#1a237e', 'fg': '#ffffff', 'button': '#3949ab'},
            'vert': {'bg': '#e8f5e9', 'fg': '#2e7d32', 'button': '#c8e6c9'},
            'vert_sombre': {'bg': '#1b5e20', 'fg': '#ffffff', 'button': '#388e3c'},
            'orange': {'bg': '#fff3e0', 'fg': '#e65100', 'button': '#ffe0b2'},
            'rouge_sombre': {'bg': '#b71c1c', 'fg': '#ffffff', 'button': '#e53935'},
            'rose': {'bg': '#fce4ec', 'fg': '#c2185b', 'button': '#f8bbd0'},
            'violet': {'bg': '#f3e5f5', 'fg': '#7b1fa2', 'button': '#e1bee7'},
            'violet_sombre': {'bg': '#4a148c', 'fg': '#ffffff', 'button': '#7c4dff'}
        }
        
        theme_actuel = themes.get(theme, themes['clair'])
        
        if self.mode_sombre_var.get():
            theme_actuel = themes['sombre']
        
        # Configurer les styles avec la police et la taille
        style_config = {
            'background': theme_actuel['bg'],
            'foreground': theme_actuel['fg'],
            'font': (self.police, self.taille_texte)
        }
        
        self.style.configure(".", **style_config)
        self.style.configure("Custom.TLabel", **style_config)
        self.style.configure("Custom.TButton",
                            background=theme_actuel['button'],
                            foreground=theme_actuel['fg'],
                            font=(self.police, self.taille_texte))
        self.style.configure("TFrame", background=theme_actuel['bg'])
        
        # Configurer les widgets de texte
        self.text_zone.configure(
            background=theme_actuel['bg'],
            foreground=theme_actuel['fg'],
            insertbackground=theme_actuel['fg'],
            font=(self.police, self.taille_texte)
        )
        
        # Configurer la fenêtre principale
        self.root.configure(bg=theme_actuel['bg'])
        self.root.attributes('-alpha', self.opacite)
        
        # Mettre à jour le style du bouton plein écran si présent
        if self.bouton_quitter_plein_ecran is not None:
            self.bouton_quitter_plein_ecran.configure(
                bg=theme_actuel['bg'],
                fg=theme_actuel['fg'],
                activebackground=theme_actuel['button'],
                activeforeground=theme_actuel['fg']
            )
                
    def changer_theme(self, theme):
        self.preferences['theme'] = theme
        self.appliquer_theme()
        self.sauvegarder_preferences()
        
    def changer_taille_texte(self):
        tailles = [8, 10, 12, 14, 16, 18, 20, 24]
        dialog = tk.Toplevel(self.root)
        dialog.title("Taille du texte")
        dialog.geometry("300x200")
        
        for taille in tailles:
            ttk.Radiobutton(dialog, 
                           text=f"{taille} points",
                           value=taille,
                           command=lambda t=taille: self.appliquer_taille_texte(t)).pack(pady=2)

    def appliquer_taille_texte(self, taille):
        self.taille_texte = taille
        self.appliquer_theme()
        self.sauvegarder_preferences()

    def changer_police(self):
        polices = [
            # Polices sans serif
            'Arial', 'Helvetica', 'Verdana', 'Tahoma', 'Trebuchet MS',
            # Polices avec serif
            'Times New Roman', 'Georgia', 'Garamond', 'Palatino', 'Book Antiqua',
            # Polices monospace
            'Courier New', 'Consolas', 'Lucida Console', 'Monaco',
            # Polices stylisées
            'Comic Sans MS', 'Impact', 'Arial Black', 'Century Gothic'
        ]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Police de caractères")
        dialog.geometry("400x500")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label d'instruction
        ttk.Label(main_frame, text="Choisissez une police :", 
                 font=(self.police, 12, 'bold')).pack(pady=(0,10))
        
        # Frame pour les catégories
        categories = {
            'Sans Serif': ['Arial', 'Helvetica', 'Verdana', 'Tahoma', 'Trebuchet MS'],
            'Serif': ['Times New Roman', 'Georgia', 'Garamond', 'Palatino', 'Book Antiqua'],
            'Monospace': ['Courier New', 'Consolas', 'Lucida Console', 'Monaco'],
            'Stylisée': ['Comic Sans MS', 'Impact', 'Arial Black', 'Century Gothic']
        }
        
        # Créer un Notebook pour les onglets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Variable pour le bouton radio
        police_var = tk.StringVar(value=self.police)
        
        # Créer un onglet pour chaque catégorie
        for categorie, polices_cat in categories.items():
            # Frame pour la catégorie
            frame_cat = ttk.Frame(notebook, padding="5")
            notebook.add(frame_cat, text=categorie)
            
            # Canvas et scrollbar pour le défilement
            canvas = tk.Canvas(frame_cat)
            scrollbar = ttk.Scrollbar(frame_cat, orient="vertical", command=canvas.yview)
            frame_scroll = ttk.Frame(canvas)
            
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Ajouter les polices de la catégorie
            for police in polices_cat:
                frame_police = ttk.Frame(frame_scroll)
                frame_police.pack(fill=tk.X, pady=2)
                
                rb = ttk.Radiobutton(frame_police, text=police, value=police, 
                                   variable=police_var)
                rb.pack(side=tk.LEFT)
                
                # Exemple de texte avec la police
                exemple = tk.Label(frame_police, text="Exemple de texte", 
                                 font=(police, 10))
                exemple.pack(side=tk.RIGHT)
        
            # Configurer le canvas
            canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
            frame_scroll.bind("<Configure>", lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame pour les boutons
        frame_boutons = ttk.Frame(main_frame)
        frame_boutons.pack(fill=tk.X, pady=(10,0))
        
        # Bouton Appliquer
        ttk.Button(frame_boutons, text="Appliquer", 
                   command=lambda: self.appliquer_police(police_var.get())).pack(side=tk.LEFT, padx=5)
        
        # Bouton Annuler
        ttk.Button(frame_boutons, text="Annuler", 
                   command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Aperçu en direct
        frame_apercu = ttk.LabelFrame(main_frame, text="Aperçu", padding="10")
        frame_apercu.pack(fill=tk.X, pady=(10,0))
        
        texte_apercu = tk.Label(frame_apercu, 
                               text="Le rapide renard brun saute par-dessus le chien paresseux",
                               wraplength=350)
        texte_apercu.pack(pady=5)
        
        # Mettre à jour l'aperçu quand on change de police
        def update_apercu(*args):
            police = police_var.get()
            texte_apercu.configure(font=(police, 10))
        
        police_var.trace('w', update_apercu)

    def appliquer_police(self, police):
        self.police = police
        self.appliquer_theme()
        self.sauvegarder_preferences()

    def changer_opacite(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Opacité de la fenêtre")
        dialog.geometry("300x100")
        
        scale = ttk.Scale(dialog, from_=0.3, to=1.0, orient=tk.HORIZONTAL, 
                         value=self.opacite, command=self.appliquer_opacite)
        scale.pack(pady=20, padx=10, fill=tk.X)
        
        ttk.Label(dialog, text="Déplacez le curseur pour ajuster l'opacité").pack()

    def appliquer_opacite(self, valeur):
        self.opacite = float(valeur)
        self.root.attributes('-alpha', self.opacite)
        self.sauvegarder_preferences()

    def toggle_score(self):
        if self.afficher_score_var.get():
            self.score_label.grid()
        else:
            self.score_label.grid_remove()
        self.sauvegarder_preferences()

    def toggle_corrections(self):
        self.sauvegarder_preferences()

    def toggle_animations(self):
        self.sauvegarder_preferences()

    def toggle_plein_ecran(self):
        if self.mode_plein_ecran_var.get():
            self.root.attributes('-fullscreen', True)
            self.creer_bouton_quitter_plein_ecran()
            messagebox.showinfo("Mode plein écran", 
                              "Pour quitter le mode plein écran :\n" +
                              "- Cliquez sur le bouton ❌ en haut à droite\n" +
                              "- Ou appuyez sur la touche Échap\n" +
                              "- Ou décochez l'option dans le menu Personnalisation > Interface")
        else:
            self.quitter_plein_ecran()
        self.sauvegarder_preferences()

    def toggle_mode_sombre(self):
        self.appliquer_theme()
        self.sauvegarder_preferences()

    def toggle_temps(self):
        self.sauvegarder_preferences()

    def reinitialiser_preferences(self):
        if messagebox.askyesno("Réinitialiser", "Voulez-vous vraiment réinitialiser toutes les préférences ?"):
            self.preferences = {
                'theme': 'clair',
                'afficher_score': True,
                'afficher_corrections': True,
                'animations': True,
                'mode_sombre': False,
                'afficher_temps': True,
                'mode_plein_ecran': False,
                'taille_texte': 12,
                'police': 'Arial',
                'opacite': 1.0,
                'bordures_arrondies': True,
                'ombres': True,
                'mode_compact': False,
                'mode_focus': False,
                'mode_dyslexie': False,
                'contraste_eleve': False,
                'mode_daltonien': 'normal',
                'position_boutons': 'bas',
                'style_boutons': 'moderne',
                'espacement_lignes': 1,
                'marge_laterale': 10,
                'marge_verticale': 10
            }
            self.afficher_score_var.set(True)
            self.afficher_corrections_var.set(True)
            self.animations_var.set(True)
            self.mode_sombre_var.set(False)
            self.afficher_temps_var.set(True)
            self.mode_plein_ecran_var.set(False)
            self.taille_texte = 12
            self.police = 'Arial'
            self.opacite = 1.0
            self.root.attributes('-fullscreen', False)
            self.root.attributes('-alpha', 1.0)
            self.appliquer_theme()
            self.sauvegarder_preferences()
            messagebox.showinfo("Réinitialisation", "Les préférences ont été réinitialisées avec succès.")
        
    def analyser_texte(self):
        texte = self.text_zone.get("1.0", tk.END).strip()
        lignes = texte.split('\n')
        self.definitions = {}
        
        for ligne in lignes:
            match = re.split(r'\s*[:|-]\s*', ligne.strip(), maxsplit=1)
            if len(match) == 2:
                terme, definition = match
                terme = terme.strip()
                definition = definition.strip()
                if terme and definition:
                    self.definitions[terme] = definition
        
        if self.definitions:
            messagebox.showinfo("Succès", f"{len(self.definitions)} définitions ont été trouvées!")
            self.demarrer_exercice()
        else:
            messagebox.showerror("Erreur", "Aucune définition n'a été trouvée. Utilisez le format 'terme : définition' ou 'terme - définition'")
    
    def creer_exercice_vf(self):
        self.type_exercice_actuel = "vf"
        terme = random.choice(list(self.definitions.keys()))
        est_vrai = random.choice([True, False])
        
        if est_vrai:
            question = f"Vrai ou Faux : '{terme}' signifie '{self.definitions[terme]}'"
            self.reponse_correcte = True
        else:
            autre_definition = random.choice([d for k, d in self.definitions.items() if k != terme])
            question = f"Vrai ou Faux : '{terme}' signifie '{autre_definition}'"
            self.reponse_correcte = False
            
        return question
    
    def creer_exercice_qcm(self):
        self.type_exercice_actuel = "qcm"
        terme = random.choice(list(self.definitions.keys()))
        bonne_reponse = self.definitions[terme]
        
        # Sélectionner 3 mauvaises réponses
        autres_definitions = [d for k, d in self.definitions.items() if k != terme]
        if len(autres_definitions) >= 3:
            mauvaises_reponses = random.sample(autres_definitions, 3)
        else:
            mauvaises_reponses = autres_definitions
            
        self.choix_qcm = [bonne_reponse] + mauvaises_reponses
        random.shuffle(self.choix_qcm)
        self.reponse_correcte = bonne_reponse
        
        # Créer les boutons radio
        for widget in self.frame_reponses.winfo_children():
            widget.destroy()
            
        self.qcm_var = tk.StringVar()
        for i, choix in enumerate(self.choix_qcm):
            ttk.Radiobutton(self.frame_reponses, text=choix, value=choix, variable=self.qcm_var).grid(row=i, column=0, sticky=tk.W)
            
        return f"Quelle est la définition de '{terme}' ?"
    
    def creer_exercice_association(self):
        self.type_exercice_actuel = "association"
        # Sélectionner 4 paires terme-définition
        paires = random.sample(list(self.definitions.items()), min(4, len(self.definitions)))
        termes, definitions = zip(*paires)
        definitions_melangees = list(definitions)
        random.shuffle(definitions_melangees)
        
        # Créer les menus déroulants pour chaque terme
        for widget in self.frame_reponses.winfo_children():
            widget.destroy()
            
        self.associations = {}
        for i, terme in enumerate(termes):
            ttk.Label(self.frame_reponses, text=terme).grid(row=i, column=0, padx=5, pady=2)
            var = tk.StringVar()
            menu = ttk.Combobox(self.frame_reponses, textvariable=var, values=definitions_melangees, state="readonly")
            menu.grid(row=i, column=1, padx=5, pady=2)
            self.associations[terme] = (var, self.definitions[terme])
            
        return "Associez chaque terme à sa définition correcte :"
    
    def reessayer(self):
        """Permet de réessayer la question actuelle"""
        self.peut_reessayer = False
        self.bouton_reessayer.grid_remove()
        self.bouton_correction.grid_remove()
        
        if self.type_exercice_actuel == "qr":
            self.reponse_entry.delete(0, tk.END)
            self.reponse_entry.focus()
        elif self.type_exercice_actuel == "qcm":
            self.qcm_var.set("")
        elif self.type_exercice_actuel == "association":
            for terme, (var, _) in self.associations.items():
                var.set("")
                
    def montrer_correction(self):
        """Montre la correction pour la question actuelle"""
        self.executer_hooks('avant_correction')
        
        if self.type_exercice_actuel == "qr":
            messagebox.showinfo("Correction", f"La bonne réponse est : {self.reponse_correcte}")
        elif self.type_exercice_actuel == "qcm":
            messagebox.showinfo("Correction", f"La bonne réponse est : {self.reponse_correcte}")
        elif self.type_exercice_actuel == "association":
            correction = "Les associations correctes sont :\n\n"
            for terme, (_, bonne_reponse) in self.associations.items():
                correction += f"{terme} ➔ {bonne_reponse}\n"
            messagebox.showinfo("Correction", correction)
        elif self.type_exercice_actuel == "vf":
            if self.reponse_correcte:
                messagebox.showinfo("Correction", "La bonne réponse est : Vrai")
            else:
                messagebox.showinfo("Correction", "La bonne réponse est : Faux")
                
        self.executer_hooks('apres_correction')
        self.nouveau_terme()
            
    def verifier_vf(self, reponse):
        self.total_questions += 1
        if reponse == self.reponse_correcte:
            self.score += 1
            messagebox.showinfo("Correct!", "Bonne réponse!")
            self.nouveau_terme()
        else:
            messagebox.showerror("Incorrect", "Mauvaise réponse!")
            if self.peut_reessayer:
                self.bouton_reessayer.grid(row=0, column=1, padx=5)
                self.bouton_correction.grid(row=0, column=2, padx=5)
            else:
                self.nouveau_terme()
        self.score_label.config(text=f"Score: {self.score}/{self.total_questions}")
        
    def verifier_reponse(self):
        self.executer_hooks('avant_verification')
        
        if not self.peut_reessayer:
            self.total_questions += 1
            
        correct = False
        
        if self.type_exercice_actuel == "qr":
            reponse = self.reponse_entry.get().strip().lower()
            correct = reponse == self.reponse_correcte.lower()
        elif self.type_exercice_actuel == "qcm":
            reponse = self.qcm_var.get()
            correct = reponse == self.reponse_correcte
        elif self.type_exercice_actuel == "association":
            correct = True
            for terme, (var, bonne_reponse) in self.associations.items():
                if var.get() != bonne_reponse:
                    correct = False
                    break
                    
        self.executer_hooks('apres_verification', correct=correct)
        
        if correct:
            self.score += 1
            messagebox.showinfo("Correct!", "Bonne réponse!")
            self.nouveau_terme()
        else:
            if self.peut_reessayer:
                messagebox.showerror("Incorrect", "Mauvaise réponse! Vous pouvez réessayer.")
                self.bouton_reessayer.grid(row=0, column=1, padx=5)
                self.bouton_correction.grid(row=0, column=2, padx=5)
            else:
                if self.type_exercice_actuel == "qr":
                    messagebox.showerror("Incorrect", f"La bonne réponse était : {self.reponse_correcte}")
                else:
                    messagebox.showerror("Incorrect", "Mauvaise réponse!")
                self.nouveau_terme()
                
        self.score_label.config(text=f"Score: {self.score}/{self.total_questions}")
        
    def nouveau_terme(self):
        self.executer_hooks('avant_nouveau_terme')
        
        self.peut_reessayer = True
        self.bouton_reessayer.grid_remove()
        self.bouton_correction.grid_remove()
        self.frame_reponses.grid_remove()
        self.reponse_entry.grid_remove()
        self.frame_vf.grid_remove()
        self.bouton_verifier.grid_remove()
        
        mode = self.mode_var.get()
        if mode == "aleatoire":
            mode = random.choice(["qr", "vf", "qcm", "association"])
            
        if mode == "vf":
            question = self.creer_exercice_vf()
            self.frame_vf.grid()
        elif mode == "qcm":
            question = self.creer_exercice_qcm()
            self.frame_reponses.grid()
            self.bouton_verifier.grid(row=0, column=0, padx=5)
        elif mode == "association":
            question = self.creer_exercice_association()
            self.frame_reponses.grid()
            self.bouton_verifier.grid(row=0, column=0, padx=5)
        else:  # questions/réponses
            self.type_exercice_actuel = "qr"
            terme = random.choice(list(self.definitions.keys()))
            question = f"Quelle est la définition de : {terme}"
            self.reponse_correcte = self.definitions[terme]
            self.reponse_entry.grid()
            self.bouton_verifier.grid(row=0, column=0, padx=5)
            
        self.label_question.config(text=question)
        if hasattr(self, 'reponse_entry'):
            self.reponse_entry.delete(0, tk.END)
            self.reponse_entry.focus()
            
        self.executer_hooks('apres_nouveau_terme')

    def demarrer_exercice(self):
        if not self.definitions:
            messagebox.showerror("Erreur", "Ajoutez d'abord quelques définitions!")
            return
            
        self.score = 0
        self.total_questions = 0
        self.frame_exercice.grid()
        self.nouveau_terme()

    def creer_bouton_quitter_plein_ecran(self):
        if self.bouton_quitter_plein_ecran is None:
            self.bouton_quitter_plein_ecran = tk.Button(
                self.root,
                text="❌",
                font=("Arial", 16),
                command=self.quitter_plein_ecran,
                relief="flat",
                cursor="hand2"
            )
            
            # Style du bouton
            self.bouton_quitter_plein_ecran.configure(
                bg=self.style.lookup("TFrame", "background"),
                fg=self.style.lookup("TFrame", "foreground"),
                activebackground=self.style.lookup("TButton", "background"),
                activeforeground=self.style.lookup("TButton", "foreground"),
                width=2,
                height=1
            )
            
            # Positionner le bouton en haut à droite
            self.bouton_quitter_plein_ecran.place(x=self.root.winfo_screenwidth()-50, y=10)
            
            # Effet de survol
            def on_enter(e):
                self.bouton_quitter_plein_ecran.configure(bg=self.style.lookup("TButton", "background"))
            def on_leave(e):
                self.bouton_quitter_plein_ecran.configure(bg=self.style.lookup("TFrame", "background"))
            
            self.bouton_quitter_plein_ecran.bind('<Enter>', on_enter)
            self.bouton_quitter_plein_ecran.bind('<Leave>', on_leave)

    def supprimer_bouton_quitter_plein_ecran(self):
        if self.bouton_quitter_plein_ecran is not None:
            self.bouton_quitter_plein_ecran.destroy()
            self.bouton_quitter_plein_ecran = None

    def quitter_plein_ecran(self):
        self.mode_plein_ecran_var.set(False)
        self.root.attributes('-fullscreen', False)
        self.supprimer_bouton_quitter_plein_ecran()
        self.sauvegarder_preferences()

    def configurer_marges(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuration des marges")
        dialog.geometry("300x200")
        
        # Marge latérale
        ttk.Label(dialog, text="Marge latérale (px):").pack(pady=5)
        scale_lat = ttk.Scale(dialog, from_=0, to=50, orient=tk.HORIZONTAL,
                             variable=self.marge_laterale)
        scale_lat.pack(fill=tk.X, padx=10)
        
        # Marge verticale
        ttk.Label(dialog, text="Marge verticale (px):").pack(pady=5)
        scale_vert = ttk.Scale(dialog, from_=0, to=50, orient=tk.HORIZONTAL,
                              variable=self.marge_verticale)
        scale_vert.pack(fill=tk.X, padx=10)
        
        # Boutons
        frame_boutons = ttk.Frame(dialog)
        frame_boutons.pack(pady=20)
        ttk.Button(frame_boutons, text="Appliquer", 
                   command=lambda: [self.appliquer_style(), dialog.destroy()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_boutons, text="Annuler", 
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def appliquer_style(self):
        # Appliquer les styles de base
        self.appliquer_theme()
        
        # Appliquer les styles avancés
        style = self.style
        
        # Configuration des bordures arrondies
        radius = "10" if self.bordures_arrondies_var.get() else "0"
        
        # Configuration des ombres
        shadow = "2 2 4 #00000040" if self.ombres_var.get() else "0 0 0 #00000000"
        
        # Mode compact
        padding = "2" if self.mode_compact_var.get() else "5"
        
        # Style des boutons selon la sélection
        button_styles = {
            'moderne': {'padding': '8', 'relief': 'flat'},
            'classique': {'padding': '5', 'relief': 'raised'},
            'minimaliste': {'padding': '4', 'relief': 'flat'},
            'arrondi': {'padding': '8', 'relief': 'flat', 'borderradius': '20'}
        }
        button_style = button_styles.get(self.style_boutons_var.get(), button_styles['moderne'])
        
        # Appliquer les styles aux widgets
        style.configure("Custom.TButton", **button_style)
        
        # Appliquer l'espacement des lignes
        line_spacing = self.espacement_lignes.get()
        self.text_zone.configure(spacing1=line_spacing, spacing2=line_spacing, spacing3=line_spacing)
        
        # Appliquer les marges
        self.main_frame.configure(padding=(self.marge_laterale.get(), self.marge_verticale.get()))
        
        # Mode focus
        if self.mode_focus_var.get():
            self.text_zone.configure(insertwidth=3, insertbackground='red')
        
        # Police dyslexie
        if self.mode_dyslexie_var.get():
            self.police = "OpenDyslexic"  # Nécessite d'avoir la police installée
        
        # Contraste élevé
        if self.contraste_eleve_var.get():
            style.configure(".", foreground='white', background='black')
            style.configure("Custom.TButton", foreground='black', background='white')
        
        # Mode daltonien
        daltonien_colors = {
            'protanopie': {'rouge': '#FFB7B7', 'vert': '#B7FFB7'},
            'deuteranopie': {'rouge': '#FFD7B7', 'vert': '#B7FFD7'},
            'tritanopie': {'bleu': '#B7B7FF', 'jaune': '#FFFFB7'}
        }
        if self.mode_daltonien_var.get() != 'normal':
            colors = daltonien_colors[self.mode_daltonien_var.get()]
            # Appliquer les couleurs adaptées
        
        # Position des boutons
        self.repositionner_boutons()

    def repositionner_boutons(self):
        position = self.position_boutons_var.get()
        if position == "haut":
            self.frame_controle.grid(row=0, column=0, columnspan=2, pady=5)
        elif position == "bas":
            self.frame_controle.grid(row=5, column=0, columnspan=2, pady=5)
        elif position == "gauche":
            self.frame_controle.grid(row=2, column=0, pady=5, sticky="ns")
        elif position == "droite":
            self.frame_controle.grid(row=2, column=1, pady=5, sticky="ns")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExerciceApp(root)
    root.mainloop() 