// SYMBIOSE — WorldView.Capture.cs (sprint JARDIN VIVANT, T0 — banc de capture VM)
// Mode CAPTURE : lancé par `tools/capture_vm.sh` (Godot sous Xvfb + Movie Maker),
// il saute l'écran de sélection, monte directement un monde/banc et cadre la
// caméra à un palier de zoom donné. Les PNG eux-mêmes sont écrits par le Movie
// Maker de Godot (`--write-movie`), pas par ce code. Sert d'« yeux » à l'agent
// sur la VM sans écran — ce n'est PAS un livrable joueur.
//
// 📖 Pédagogie Godot/C# :
//  - OS.GetCmdlineUserArgs() rend les arguments placés APRÈS `--` sur la ligne
//    de commande Godot (ceux que le moteur ne consomme pas). Comme argv en C,
//    mais déjà filtré des options moteur.
//  - INACTIF PAR DÉFAUT : sans `--capture-banc=…`, `CaptureBanc` reste null et
//    rien ne change (le F5 de Nico, lancé sans argument, est intact).
//
// Arguments reconnus (après `--`) :
//   --capture-banc=<nom>     monde/banc à monter (full, smoke, propre, ou un banc
//                            du registre Python `BANCS`) — active le mode
//   --capture-zoom=<z>       palier de zoom (0.5 1 2 4 8 16 32) ; défaut = cadrage
//   --capture-centre=<x>,<y> point visé en cm monde (défaut = centre 1000,1000)
//   --capture-souris=<x>,<y> souris posée en px ÉCRAN (survol : losange, étiquette)
//   --capture-geste=<n>      slot de geste armé (0..9) — losange qui « respire »
//   --capture-vent=<f>[,<d>] force de vent imposée (0 = calme) et direction
//                            D'OÙ il vient en rad (défaut = celle du snapshot) — T3
//   --capture-meteo=<kind>[,<intensité>[,<durée_s>]]  météo imposée (ex. Canicule,
//                            « Pluie prolongée », Orage) ; après <durée_s> secondes de
//                            jeu, retour à celle du snapshot (observe l'« après ») — T4
//   --capture-semaines=<n>   semaines de warmup (défaut WarmupWeeks = 12) — T4
//   --capture-defile=1       lance le défilé « jardin vivant » (touche F12) — T5
//   --capture-seed=<n>       seed du monde (défaut Seed = 42 ; ex. 12345 pour le
//                            collapse du banc `effondrement`, cf. BANC_SEED) — T5
//   --capture-orient=<n>     orientation D35 imposée (0..3 quarts de tour) — D106 T2
//   --capture-cacher=<N1>,<N2>  couches masquées par NOM de nœud (Ground, Decor,
//                            Objects…) — banc temps réel tools/perf_vm.sh, même
//                            mécanique que Shift+F4 (WorldView.Couches.cs) — D106 T1
//   --capture-turbo=<n>      fait passer n semaines en TURBO après le montage (le
//                            temps court : semaine paresseuse hors marge, gel
//                            hebdomadaire mesurable) puis revient en planification — D106 T4
//   --capture-pan=<x>,<y>    à la fin des semaines turbo, la caméra saute au point
//                            visé (cm monde) : les plantes en attente y entrent dans
//                            la marge (vérif « rien de périmé ») — D106 T4
//   --capture-planche=<s>    planche des paliers ×0,5→×32 (touche L), s secondes de
//                            jeu par palier, plante la plus proche du centre — D106 T7
//   --capture-etalonnage=<s> banc d'étalonnage (touche E), mesure de s secondes ;
//                            rapport imprimé puis sortie — PERF VUE ①
//   --capture-banc-semaine=<n> semaine moteur du banc (défaut 45) — PERF VUE ①
//   --capture-banc-zoom=<z> / --capture-banc-centre=<x>,<y>  cadrage du banc E
//                            (défaut ×4 sur EtalonCentreCm) — PERF VUE ①
//   --capture-ombres=0       ombres coupées (comme la touche O) — PERF VUE ①
//   --capture-banc-cadence=<s> cadence PENDANT la mesure du banc E : 0 = turbo,
//                            s > 0 = s par semaine ; absent = 60 s (nominale) — PERF VUE ④
//   --capture-kit=1          planche du kit d'éléments (touffes, fleurons) par-dessus
//                            le monde — PLANTE ASSEMBLÉE ④ (WorldView.PlancheKit.cs)
//   --capture-gerbes=1       planche de l'atlas de gerbes, bois et feuilles — HOUPPIER ④
//   --capture-chargement=1   écran de chargement au montage, durées au journal — HOUPPIER ④
//   --capture-cle-stable=<espèce>  coupe une branche, compare le feuillage — HOUPPIER ④
//   --capture-faune=1        planche de la faune (icônes ×2→×16, fond uni) — CASSÉ À
//                            L'ÉCRAN ⑤ (visuals/PlancheFaune.cs)
//   --capture-icones=1       planche des icônes de gestes (×4, ×2, silhouettes) —
//                            ICÔNES & CURSEUR ① (visuals/PlancheIcones.cs)
//   --capture-icones=2       planche des animations du curseur-geste (mouvements,
//                            refus, tap) — ICÔNES & CURSEUR ④ (visuals/PlancheAnimations.cs)
//   --capture-palier3=1 / --capture-technique=1  info-bulle apprise / technique
//                            (debug palier3 au montage ; Maj+F3) — PLANTE ASSEMBLÉE ⑦
//   --capture-pleine-res=1   monde rendu en 1920×1080 ×1 au lieu de 960×540 ×2
//                            (MESURE seulement, PERF VUE ⑤ ; le défaut ne change pas)
//   --capture-seuil=… / --capture-seuil-pose=… / --capture-palette=1  banc du seuil
//                            de visibilité des signes (INFO-BULLE ②, WorldView.BancSeuil.cs)
//   --capture-zoom-balayage=<s>  balayage ×0,5 → ×32 → ×0,5, s s par palier, rapport
//                            des à-coups de zoom imprimé puis sortie (WorldView.ZoomJournal.cs)
//   --capture-maison=1 / --capture-f6=1  maison + lisière transparentes (touche H) /
//                            heatmap F6 ouverte (1er champ du cycle) — CASSÉ À L'ÉCRAN ②
//   --capture-lut=0          palette indexée coupée (comme F11) : capture « avant » ③
//   --capture-heure=<deg>    angle horaire du soleil imposé (−90 matin, 0 midi, +90 soir,
//                            borné au lever/coucher) — CASSÉ À L'ÉCRAN ③ (WorldView.Soleil.cs)
//   --capture-cueillette=1   clic « manger » sur chaque fruit du port visé, verdict au
//                            journal (FORMES DES PLANTES ④, WorldView.BancCueillette.cs)
//   --capture-acces=<o>[,<o>] achète ces outils à l'Atelier, palette relevée avant/après au
//                            journal `[AccesGestes]` — ACCÈS AUX GESTES ④
//   --capture-vivant=… / --capture-vivant-png=…  captures de l'info-bulle d'une bête
//                            ou d'un carpophore (INFO-BULLE ③, WorldView.BancVivant.cs)

using Godot;
using System.Globalization;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView
	{
		// Parsés UNE fois au chargement de la classe (les arguments ne changent pas
		// pendant l'exécution). null / NaN = option absente.
		private static readonly string CaptureBanc = ArgCapture("banc");
		private static readonly float CaptureZoom = ParseFloat(ArgCapture("zoom"));
		private static readonly string CaptureCentre = ArgCapture("centre");
		private static readonly string CaptureSouris = ArgCapture("souris");
		private static readonly float CaptureGeste = ParseFloat(ArgCapture("geste"));
		private static readonly string CaptureVent = ArgCapture("vent");
		private static readonly string CaptureMeteo = ArgCapture("meteo");
		private static readonly float CaptureSemaines = ParseFloat(ArgCapture("semaines"));
		private static readonly bool CaptureDefile = ArgCapture("defile") != null;
		// Graine lue en ENTIER (fluidité an 2 ①) : un float n'a que 24 bits de mantisse,
		// 1521550718 y devenait 1521550720 (pas de 128 à cette échelle) → mauvais jardin.
		private static readonly int? CaptureSeed =
			int.TryParse(ArgCapture("seed"), NumberStyles.Integer, CultureInfo.InvariantCulture, out int g)
				? g : null;
		private static readonly string CaptureCacher = ArgCapture("cacher");
		// Orientation D35 imposée (0..3 quarts de tour, D106 T2 : vérifier le sol
		// en un lot sous les 4 orientations). Appliquée AVANT le centrage caméra.
		private static readonly float CaptureOrient = ParseFloat(ArgCapture("orient"));
		// Semaines turbo puis saut caméra (D106 T4, banc de la semaine paresseuse).
		private static readonly float CaptureTurbo = ParseFloat(ArgCapture("turbo"));
		private static readonly string CapturePan = ArgCapture("pan");
		// --capture-planche=<s> : planche des paliers (touche L), s secondes de jeu par
		// palier, sur la plante la plus proche du point visé — D106 T7.
		private static readonly float CapturePlanche = ParseFloat(ArgCapture("planche"));
		// --capture-decor-f10=<s> : s secondes de jeu après le montage, rejoue F10 ×2
		// (banc décor ON puis OFF = reconstruction forcée du décor) — FLUIDITÉ PC ②,
		// pour comparer l'image de démarrage à celle « réparée » par F10 (D112 c).
		private static readonly float CaptureDecorF10 = ParseFloat(ArgCapture("decor-f10"));
		// --capture-decor-banc=1 : banc décor F10 ON dès le montage (4 motifs côte à
		// côte) — FLUIDITÉ PC ③, contrôle visuel du kit sur la rivière et la falaise.
		private static readonly bool CaptureDecorBanc = ArgCapture("decor-banc") == "1";
		private int _captureTurboRestant;

		// --- Pleine résolution, MESURE seulement (PERF VUE ⑤) ----------------
		// 📖 Pédagogie — le monde est peint dans un SubViewport fenêtre/2 (960×540)
		// que le conteneur agrandit ×2 (stretch_shrink = 2, WorldView.tscn) : c'est le
		// pixel-art. Avec shrink = 1, le SubViewport fait 1920×1080 : 4× plus de pixels
		// à remplir. Pour garder la MÊME image (même cadrage, mêmes tailles à l'écran),
		// la caméra zoome 2× plus : palier ×4 → Zoom caméra 8. Toutes les constantes en
		// px internes (TileWPx, 1/CurrentZoom de la vie macro…) restent justes : le
		// palier logique (CurrentZoom, LOD) ne change pas, seul l'agrandissement passe
		// du conteneur à la caméra. Seule l'option mesure le surcoût de remplissage.
		private static readonly bool CapturePleineRes = ArgCapture("pleine-res") == "1";
		// Aide clavier F1 affichée (PLANTE ASSEMBLÉE ③ : vérifier qu'elle tient à l'écran).
		private static readonly bool CaptureAide = ArgCapture("aide") == "1";
		// Info-bulle (PLANTE ASSEMBLÉE ⑦) : debug palier3 au montage / mode technique.
		private static readonly bool CapturePalier3 = ArgCapture("palier3") == "1";
		private static readonly bool CaptureTechnique = ArgCapture("technique") == "1";
		// CASSÉ À L'ÉCRAN ② : touche H et heatmap F6 au montage (vérif (n) et (d)).
		private static readonly bool CaptureMaison = ArgCapture("maison") == "1";
		private static readonly bool CaptureF6 = ArgCapture("f6") == "1";
		// CASSÉ À L'ÉCRAN ⑤ : planche de la faune par-dessus le monde (fond uni).
		private static readonly bool CaptureFaune = ArgCapture("faune") == "1";
		// ICÔNES & CURSEUR ① : planche des icônes de gestes par-dessus le monde.
		private static readonly bool CaptureIcones = ArgCapture("icones") == "1";
		// ICÔNES & CURSEUR ④ : planche des animations du curseur (même option, valeur 2).
		private static readonly bool CaptureAnimations = ArgCapture("icones") == "2";
		private static float EchelleCamera => CapturePleineRes ? 2f : 1f;

		// Zoom de la Camera2D pour un palier logique (seul écrivain : les 4 poses).
		private static Vector2 ZoomCamera(float palier) => Vector2.One * palier * EchelleCamera;

		// Appelé dans _Ready, après la mise à taille du conteneur.
		private static void AppliquerPleineRes(SubViewportContainer container)
		{
			if (!CapturePleineRes) return;
			container.StretchShrink = 1;
			GD.Print("[Capture] pleine résolution : monde rendu en 1920×1080 ×1 (mesure).");
		}

		// Météo imposée par le banc (T4) : active jusqu'à l'échéance de sa durée.
		private bool _captureMeteoActive = CaptureMeteo != null;
		private GDict _lastWeather;

		// Vrai quand le jeu est lancé par le banc de capture (WorldView._Ready
		// saute alors le sélecteur de monde).
		internal static bool CaptureActive => CaptureBanc != null;

		private static string ArgCapture(string cle)
		{
			string prefixe = $"--capture-{cle}=";
			foreach (string a in OS.GetCmdlineUserArgs())
				if (a.StartsWith(prefixe)) return a.Substring(prefixe.Length);
			return null;
		}

		private static float ParseFloat(string s) =>
			s != null && float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v)
				? v : float.NaN;

		// Appelé AVANT StartSimulation : warmup imposé et fin programmée de la
		// météo imposée (minuterie de l'arbre = temps de jeu, fixe en Movie Maker).
		private void PreparerCapture()
		{
			if (!float.IsNaN(CaptureSemaines)) WarmupWeeks = Mathf.Max(0, (int)CaptureSemaines);
			if (CaptureSeed.HasValue) Seed = CaptureSeed.Value;
			string[] m = CaptureMeteo?.Split(',');
			if (m == null || m.Length < 3) return;
			GetTree().CreateTimer(ParseFloat(m[2])).Timeout += () =>
			{
				_captureMeteoActive = false;
				GD.Print("[Capture] fin de la météo imposée → météo du snapshot.");
				if (_lastWeather != null) ApplyWeather(_lastWeather);
			};
		}

		// Bloc `weather` éventuellement remplacé par la météo imposée du banc.
		private GDict CaptureMeteoOverride(GDict weather)
		{
			if (!_captureMeteoActive) return weather;
			string[] m = CaptureMeteo.Split(',');
			var w = weather.Duplicate();
			w["kind"] = m[0];
			if (m.Length > 1) w["intensity"] = ParseFloat(m[1]);
			return w;
		}

		// Appelé APRÈS FrameCamera (monde construit) : impose le palier de zoom et
		// le point visé. On n'utilise pas StepZoom (zoom centré SOURIS — sous Xvfb
		// la souris n'a pas de position utile) : on pose directement l'état caméra,
		// puis on refait ce que StepZoom fait après coup (redraw LOD + culling).
		private void AppliquerCapture()
		{
			if (!CaptureActive || _camera == null) return;
			GD.Print($"[Capture] banc « {CaptureBanc} », zoom {CaptureZoom}, centre {CaptureCentre ?? "monde"}.");
			if (!float.IsNaN(CaptureOrient) && (int)CaptureOrient % 4 != 0)
				RotateView((int)CaptureOrient % 4);
			if (ArgCapture("lut") == "0" && PaletteIndexee.Active) PaletteIndexee.Basculer();   // ③ : avant

			if (CaptureCentre != null)
			{
				string[] xy = CaptureCentre.Split(',');
				if (xy.Length == 2)
					_camera.Position = ClampToWorld(WorldToScreen(ParseFloat(xy[0]), ParseFloat(xy[1])));
			}
			if (!float.IsNaN(CaptureZoom))
			{
				int idx = System.Array.IndexOf(ZoomSteps, CaptureZoom);
				if (idx < 0)
					GD.PushWarning($"[Capture] zoom {CaptureZoom} hors paliers {string.Join(" ", ZoomSteps)} — ignoré.");
				else
				{
					_zoomIndex = idx;
					_camera.Zoom = ZoomCamera(CaptureZoom);
					CurrentZoom = CaptureZoom;
				}
			}
			// Xvfb a un vrai pointeur X : WarpMouse le déplace, GetMousePosition le relit.
			if (CaptureSouris != null)
			{
				string[] s = CaptureSouris.Split(',');
				if (s.Length == 2)
				{
					Input.WarpMouse(new Vector2(ParseFloat(s[0]), ParseFloat(s[1])));
					ResemerSouris();   // T3 : la frame suivante relit le pointeur
				}
			}
			if (!float.IsNaN(CaptureGeste)) SelectSlot((int)CaptureGeste);
			// Vent imposé (T3) : rend l'onde observable quelle que soit la semaine.
			if (CaptureVent != null)
			{
				string[] v = CaptureVent.Split(',');
				WindWave.SetCaptureOverride(ParseFloat(v[0]),
											v.Length > 1 ? ParseFloat(v[1]) : float.NaN);
			}
			if (CaptureDefile) ToggleDefile();   // défilé jardin vivant (T5)
			if (CaptureCacher != null) AppliquerMasqueCouches();   // D106 T1
			if (!float.IsNaN(CaptureTurbo) && CaptureTurbo >= 1f)
			{
				_captureTurboRestant = (int)CaptureTurbo;
				_simMode = SimMode.Turbo;
				SetPhase(Phase.Saison);
			}
			RedrawAllPlants();
			CullPlants();
			if (!float.IsNaN(CapturePlanche)) TogglePlanche(CapturePlanche, parSouris: false);   // D106 T7
			if (CaptureAide) { _hudTextMode = 2; ApplyHudTextMode(); }   // F1 mode Aide
			if (CaptureKit) AfficherPlancheKit();   // planche du kit (PLANTE ASSEMBLÉE ④)
			if (CaptureGerbes) AfficherPlancheGerbes();   // planche des gerbes (HOUPPIER ④)
			if (CaptureFaune)   // planche de la faune (D112 ⑤) : calque au-dessus du HUD
			{
				var calque = new CanvasLayer { Layer = 100 };
				AddChild(calque);
				calque.AddChild(new ColorRect { Color = Palette16.SolTerre, Size = new Vector2(1920f, 1080f) });
				calque.AddChild(new PlancheFaune());
			}
			if (CaptureIcones)   // planche des icônes de gestes : calque au-dessus du HUD
			{
				var calque = new CanvasLayer { Layer = 100 };
				AddChild(calque);
				calque.AddChild(new PlancheIcones());
			}
			if (CaptureAnimations)   // planche des animations du curseur (④), même calque
			{
				var calque = new CanvasLayer { Layer = 100 };
				AddChild(calque);
				calque.AddChild(new PlancheAnimations());
			}
			if (CaptureSouris != null) PoserTemoinCurseur();   // curseur visible au banc (ICÔNES & CURSEUR ③)
			if (CapturePalier3) DebugMaitrise("palier3");   // info-bulle apprise (⑦)
			if (CaptureTechnique) ToggleInfoTechnique();    // info-bulle technique (⑦)
			if (CaptureMaison) ToggleHouseGhost();          // maison + lisière (D112 ②)
			if (CaptureF6) ToggleFieldOverlay();            // heatmap, champ de tête (D112 ②)
			AppliquerCaptureBanc();   // ombres / banc d'étalonnage (WorldView.Etalonnage.cs)
			LancerBancSeuil();        // seuil de visibilité des signes (WorldView.BancSeuil.cs)
			LancerBancCueillette();   // manger au clic sur un fruit de port (WorldView.BancCueillette.cs)
			LancerBancVivant();       // captures info-bulle bête / carpophore (WorldView.BancVivant.cs)
			LancerBancCleStable();    // couper une branche ne déplace aucune feuille (WorldView.BancCleStable.cs)
			LancerBancAccesGestes();  // acheter un outil, relever la palette (WorldView.BancAccesGestes.cs)
			LancerBancObjetEnMain();  // objet en main, récolte au fruit (WorldView.BancObjetEnMain.cs)
			LancerTesteurCapture();   // mode testeur : plan de test du banc (WorldView.Testeur.cs, ⑤)
			LancerBancClicMur();      // D118 (c) : le bois devant la maison est-il vu par le clic ? (WorldView.BancClicMur.cs)
			if (!float.IsNaN(CaptureDecorF10))   // F10 ×2 programmé (FLUIDITÉ PC ②)
				GetTree().CreateTimer(CaptureDecorF10).Timeout += () =>
				{ _decorLayer?.ToggleBanc(); _decorLayer?.ToggleBanc(); };
			if (CaptureDecorBanc) _decorLayer?.ToggleBanc();   // banc décor ON (③)
			LancerBalayageZoom();   // --capture-zoom-balayage (ZoomJournal.cs, FLUIDITÉ PC LEVIERS ①)
		}

		// Appelé à chaque step consommé (_Process) : décompte des semaines turbo du
		// banc ; à la dernière, retour en planification + saut caméra éventuel, 3 s
		// de jeu plus tard (la dernière semaine est alors appliquée : les plantes
		// hors marge attendent → c'est la file d'entrée qui les rattrape).
		private void CaptureApresStep()
		{
			if (_captureTurboRestant <= 0 || --_captureTurboRestant > 0) return;
			SetPhase(Phase.Planification);
			string[] xy = CapturePan?.Split(',');
			if (xy == null || xy.Length != 2 || _camera == null) return;
			GetTree().CreateTimer(3.0).Timeout += () =>
			{
				_camera.Position = ClampToWorld(WorldToScreen(ParseFloat(xy[0]), ParseFloat(xy[1])));
				CullPlants();
				GD.Print($"[Capture] fin des semaines turbo → caméra sur {CapturePan} "
					+ $"({_fileEntree.Count} plantes en attente entrent dans la marge).");
			};
		}
	}
}
