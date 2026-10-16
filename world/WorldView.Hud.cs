// SYMBIOSE — WorldView.Hud.cs (partial de WorldView, SS⑥ refactor global)
// Le HUD PROVISOIRE — instrument de validation des tranches (horloge, Vigueur,
// perfs F4, légende heatmap F6). Le HUD définitif (philo #5 : pas de chiffres
// en HUD primaire) viendra au sprint UI ; celui-ci sautera. Inclut aussi la
// machine de l'overlay heatmap côté joueur (toggle F6, cycle de champ Maj+F6)
// — la MACHINE de requêtes `fields` elle-même vit dans _Process (pipe 1↔1).

using Godot;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// --- Overlay debug champs écologiques (t6·C, touche F6) -------------
		// ZIndex 3 : par-dessus le sol et l'ombre maison, sous la vie macro et
		// les objets. La MACHINE de requêtes vit ici (maître/esclave : la même
		// file qu'un step/action — UNE requête en vol, leçon t4·B) ; le nœud
		// FieldOverlay ne fait que dessiner la dernière grille reçue.
		private FieldOverlay _fieldOverlay;
		private bool _overlayOn;
		private string[] _fieldNames;          // registre du serveur (1 requête)
		private int _fieldIndex;
		private bool _fieldsStale;             // snapshot reçu depuis la grille
		private Task<GDict> _pendingFields;    // requête fields en vol (ou null)
		// Légende de la heatmap (correctif C2) : RichTextLabel — le BBCode
		// [color] permet les PAVÉS colorés du dégradé, un Label ne sait pas.
		private RichTextLabel _fieldLabel;

		// Labels du HUD provisoire.
		private Label _actionLabel;                // 2e ligne HUD (Vigueur+geste)
		private Label _clockLabel;
		private Label _versionLabel;               // version du pont (haut-droit) — masquable en vue nue (T4)
		private Label _legendLabel;                // aide-mémoire clavier (bas, T2)

		// Cycle du texte HUD (T4, item 6). F1 fait tourner 3 états :
		//  0 Jeu  → texte du haut (horloge/Vigueur/version) VISIBLE · aide bas masquée (défaut)
		//  1 Nu   → tout le texte HUD MASQUÉ (screenshot / observation nue ; palette + overlays intacts)
		//  2 Aide → texte du haut VISIBLE · aide clavier du bas VISIBLE
		// Chaque bloc garde son défaut naturel (le haut est montré, l'aide est cachée) ;
		// le cycle réconcilie leurs polarités opposées sans réassigner de touche.
		private int _hudTextMode;                  // 0 Jeu (défaut) · 1 Nu · 2 Aide

		// --- Overlay de perfs (F4, volet C2 — demande Nico) -----------------
		// Mesuré dans la vue, sans instrumenter le moteur : durée du dernier
		// tick COMPLET (pipe + sim + parse, côté joueur c'est ça la vérité),
		// cadence réelle entre deux semaines, et volumes du dernier snapshot.
		private Label _perfLabel;
		private bool _perfVisible;
		private ulong _stepStartMs;            // départ du step en vol
		private ulong _lastStepEndMs;          // fin du step précédent
		private double _lastTickMs = -1;       // durée du dernier tick (ms)
		private double _lastWeekGapSec = -1;   // s réelles entre 2 semaines
		private int _nSegments;                // segments dessinés (snapshot)
		private int _nPousses;                 // plantes sans segments

		// --- Banc d'observation perf (sprint « run éternel » ④) --------------
		// Mesures CÔTÉ SERVEUR lues dans le bloc `perf` du snapshot (serialize.py) :
		// `ms/tick` chronométré AUTOUR de tick_semaine() (≠ tick CLIENT ci-dessus,
		// qui inclut pipe+parse — les deux se comparent), N plantes VIVANTES et RSS
		// du process moteur. Le VRAI banc de la stabilisation : en turbo longue durée
		// sur le monde complet, `N plantes` doit PLAFONNER (③) et `tick moteur` cesser
		// de doubler d'année en année. -1 = pas encore reçu (tolérance pré-perf).
		private double _srvMsTick = -1;        // ms du dernier tick_semaine() (serveur)
		private int _srvNPlants = -1;          // plantes vivantes (snapshot serveur)
		private double _srvRssMo = -1;         // RSS process serveur (Mo)

		// -------------------------------------------------------------------
		// HUD PROVISOIRE — horloge + état, instrument de validation de la
		// tranche 3. Le HUD définitif (philo #5 : pas de chiffres en HUD
		// primaire) viendra au sprint UI ; celui-ci sautera.
		// -------------------------------------------------------------------

		private void BuildHud()
		{
			// CanvasLayer : se dessine en coordonnées ÉCRAN, ignore la Camera2D
			// (sinon le label serait projeté/zoomé avec le monde).
			var hud = new CanvasLayer { Name = "Hud" };
			_clockLabel = new Label { Position = new Vector2(16f, 10f) };
			// Gros + contour noir : lisible sur le fond gris pierre clair (le
			// label t3 v1 était blanc/petit → invisible). Overrides de thème =
			// le mécanisme Godot pour styler UN Control sans thème global.
			_clockLabel.AddThemeFontSizeOverride("font_size", 28);
			_clockLabel.AddThemeColorOverride("font_color", Colors.White);
			_clockLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_clockLabel.AddThemeConstantOverride("outline_size", 8);
			// Témoin de build : visible dès _Ready, AVANT le premier snapshot.
			// Si ce texte n'apparaît pas, c'est que ce code ne tourne pas
			// (sync Nextcloud ou build) — pas un bug d'horloge.
			_clockLabel.Text = "t4 — chargement du monde…";
			hud.AddChild(_clockLabel);

			// 2e ligne (volet B) : Vigueur + geste sélectionné + dernier ACK/NAK
			// du serveur. Chiffres au HUD = assumé PROVISOIRE (philo #5 : le HUD
			// final passera par des indices visuels, ceci est l'instrument de
			// validation de la tranche).
			_actionLabel = new Label { Position = new Vector2(16f, 52f) };
			_actionLabel.AddThemeFontSizeOverride("font_size", 20);
			_actionLabel.AddThemeColorOverride("font_color", Colors.White);
			_actionLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_actionLabel.AddThemeConstantOverride("outline_size", 6);
			hud.AddChild(_actionLabel);

			// Légende heatmap (t6·C2, demande Nico) : SOUS la ligne Vigueur,
			// AU-DESSUS du FPS. RichTextLabel pour les pavés colorés du
			// dégradé ; visible seulement quand le champ est affiché.
			_fieldLabel = new RichTextLabel
			{
				Position = new Vector2(16f, 80f),
				CustomMinimumSize = new Vector2(1300f, 30f),
				BbcodeEnabled = true, FitContent = true,
				ScrollActive = false, Visible = false,
				AutowrapMode = TextServer.AutowrapMode.Off,
			};
			_fieldLabel.AddThemeFontSizeOverride("normal_font_size", 16);
			_fieldLabel.AddThemeColorOverride("default_color", new Color(0.85f, 0.92f, 1f));
			_fieldLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_fieldLabel.AddThemeConstantOverride("outline_size", 5);
			hud.AddChild(_fieldLabel);

			// Overlay de perfs (F4, volet C2) : sous la légende heatmap, caché
			// par défaut. Instrument debug (philo #5 : autorisé, hors HUD final).
			_perfLabel = new Label { Position = new Vector2(16f, 112f), Visible = false };
			_perfLabel.AddThemeFontSizeOverride("font_size", 16);
			_perfLabel.AddThemeColorOverride("font_color", new Color(1f, 1f, 0.8f));
			_perfLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_perfLabel.AddThemeConstantOverride("outline_size", 5);
			hud.AddChild(_perfLabel);

			// Survol gènes (DIVERSITÉ FONDATRICE ③) : sous l'overlay de perfs, caché
			// par défaut, toggle F7. Instrument d'observation (philo #5 : chiffres
			// tolérés en HUD debug, hors HUD final). Cf. WorldView.Genes.cs.
			_genesLabel = new Label { Position = new Vector2(16f, 300f), Visible = false };
			_genesLabel.AddThemeFontSizeOverride("font_size", 16);
			_genesLabel.AddThemeColorOverride("font_color", new Color(0.8f, 1f, 0.85f));
			_genesLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_genesLabel.AddThemeConstantOverride("outline_size", 5);
			hud.AddChild(_genesLabel);

			// Témoin de build (coin haut-droit) : LA réponse à « est-ce que je
			// fais tourner la bonne version ? ». Discret mais toujours visible.
			var build = new Label
			{
				Text = Build,
				Position = new Vector2(1920f - 16f, 10f),
				// Ancré à droite : on aligne la FIN du texte sur x=1904 en
				// décalant de sa largeur estimée — un Label n'a pas d'ancrage
				// droit sans Container ; à 14 px, ~7 px/caractère suffit.
			};
			build.Position -= new Vector2(Build.Length * 7f, 0f);
			build.AddThemeFontSizeOverride("font_size", 14);
			build.AddThemeColorOverride("font_color", new Color(1f, 1f, 1f, 0.65f));
			build.AddThemeColorOverride("font_outline_color", Colors.Black);
			build.AddThemeConstantOverride("outline_size", 4);
			hud.AddChild(build);
			_versionLabel = build;   // mémorisé pour la vue nue (T4) — masquable comme le reste du texte du haut

			// Légende des commandes (décision Nico 2026-06-10) : ce que le
			// joueur PEUT faire, coin bas-gauche, petite police. PROVISOIRE
			// (philo #5/#6 : pas de tutoriel imposé — la v1 aura la page
			// d'accueil pictogrammes ; ici c'est l'instrument de validation).
			// Position fixe : la résolution projet est 1920×1080. AutowrapMode +
			// largeur bornée (retour F5 Nico : le texte des gestes débordait) :
			// la ligne se replie au lieu de sortir de l'écran, quoi qu'on écrive.
			// ESCAMOTABLE (T2, item 3 : le texte recouvrait le bas du champ de jeu) :
			// masqué par défaut, révélé/caché par F1 (voir ToggleLegend). Le champ
			// de jeu reste dégagé tant qu'on ne demande pas l'aide.
			var legend = new Label
			{
				Position = new Vector2(16f, 1080f - 96f),
				CustomMinimumSize = new Vector2(1888f, 0f),
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
				Visible = false,
			};
			legend.AddThemeFontSizeOverride("font_size", 18);
			legend.AddThemeColorOverride("font_color", Colors.White);
			legend.AddThemeColorOverride("font_outline_color", Colors.Black);
			legend.AddThemeConstantOverride("outline_size", 6);
			// Ligne toggles triée par POSITION des touches sur AZERTY, de gauche à
			// droite (retour F5 Nico) : F3 F4 (rangée Fn) · H (rangée du milieu) ·
			// F6 · I O (rangée du haut) · M (rangée du milieu, à droite).
			// La liste des gestes n'est plus énumérée (elle débordait) : Tab cycle,
			// le HUD en haut à gauche montre toujours le geste courant et sa cible.
			legend.Text = "Espace lancer/pause · flèches déplacer"
				+ " · molette zoom · PageUp/PageDown pivoter\n"
				+ "F3 étiquettes · F4 perfs (Maj+F4 couches) · C copier perfs · H maison transparente · F6 heatmap debug (Maj+F6 champ)"
				+ " · F7 carte T sol · G survol gènes · L planche des paliers · I vie macro · O ombres · M mode simu · A jardinier automate (Maj+A objectif démo)\n"
				+ "palette de gestes = colonne d'icônes à GAUCHE (clic) · Tab/1..9 accélérateurs · S graine (planter) · B substrat (poser pot/bac) · N nature (pailler) · clic gauche = agir"
				+ " — geste courant affiché en haut à gauche";
			hud.AddChild(legend);
			_legendLabel = legend;
			AddChild(hud);
			UpdateActionHud();
		}

		// Touche F1 (T4, item 6) : fait tourner le mode d'affichage du texte HUD
		// (Jeu → Nu → Aide → Jeu). Le mode « Nu » dégage le champ de tout MOT pour
		// l'observation nue / les screenshots — la palette de gestes et les overlays
		// debug (F4/F6/G, allumés délibérément) restent, eux, intouchés.
		private void CycleHudText()
		{
			_hudTextMode = (_hudTextMode + 1) % 3;
			ApplyHudTextMode();
			string nom = _hudTextMode switch
			{
				1 => "Nu (texte masqué)",
				2 => "Aide (état + aide clavier)",
				_ => "Jeu (état seul)",
			};
			GD.Print($"[WorldView] F1 → texte HUD : {nom}.");
		}

		// Applique la visibilité des labels selon _hudTextMode. Le texte du HAUT
		// (horloge, Vigueur/geste, version du pont) est visible sauf en mode Nu ;
		// l'aide clavier du BAS n'est visible qu'en mode Aide.
		private void ApplyHudTextMode()
		{
			bool hautVisible = _hudTextMode != 1;   // masqué uniquement en Nu
			bool aideVisible = _hudTextMode == 2;   // révélée seulement en Aide
			if (_clockLabel != null)   _clockLabel.Visible = hautVisible;
			if (_actionLabel != null)  _actionLabel.Visible = hautVisible;
			if (_versionLabel != null) _versionLabel.Visible = hautVisible;
			if (_legendLabel != null)  _legendLabel.Visible = aideVisible;
		}

		private void UpdateClock()
		{
			if (_clockLabel == null) return;
			string etat = _phase switch
			{
				Phase.Saison => "saison en cours",
				Phase.Pause  => "pause (Espace pour reprendre)",
				_            => "planification — Espace pour lancer la saison",
			};
			// Jauge intra-semaine : se remplit en SecondsPerWeek s, retombe au
			// départ du step, FIGE en pause — le « temps qui coule » est visible
			// même quand rien ne change à l'écran. ASCII pur (pas de glyphe
			// exotique : la police par défaut les remplacerait par des carrés).
			if (_simMode != SimMode.Saison)
				etat += _simMode == SimMode.Turbo ? " · TURBO" : " · continu";
			string jauge = "";
			if (_phase != Phase.Planification)
			{
				if (_simMode == SimMode.Turbo)
					jauge = "  [>>>>>>>>>>]";   // pas de cadence : plein régime
				else
				{
					float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;
					int n = Mathf.Clamp((int)(_timeAccum / spw * 10f), 0, 10);
					jauge = "  [" + new string('=', n) + new string('-', 10 - n) + "]";
				}
			}
			_clockLabel.Text =
				$"{_season} · an {_year} — semaine {_weekInSeason}/13{jauge}   {etat}";
		}

		private void UpdateActionHud()
		{
			if (_actionLabel == null) return;
			string vig = _vigueur < 0 ? "Vigueur —"
				: $"Vigueur {_vigueur:F0}/{_vigueurMax:F0}";
			string geste;
			if (_gesteIndex < 0)
				geste = "aucun (Tab ou 1..9)";
			else
			{
				var g = Gestes[_gesteIndex];
				geste = $"{g.Nom} [{_gesteIndex + 1}]";
				// `planter` affiche l'espèce courante (S cycle) — la cible attendue.
				if (g.Verb == "planter")
					geste += _seeds.Count == 0 ? " : aucune graine (S)"
						   : $" : {_seeds[_seedIndex].Key} (×{_seeds[_seedIndex].Count}, S)";
				// `ameublir` rappelle la variante Maj (grelinette, global).
				else if (g.Verb == "becher")
					geste += " (Maj : grelinette)";
				// `écraser` rappelle l'auto plante/nuisible.
				else if (g.Verb == "ecraser")
					geste += " (plante ou nuisible)";
				// poser pot/bac : substrat courant (cycle B) joint à la pose.
				else if (g.Verb == "poser_pot" || g.Verb == "poser_bac_culture")
					geste += $" : {Substrats[_substratIndex]} (B)";
				// pailler : nature de mulch courante (cycle N) déposée au plot.
				else if (g.Verb == "pailler")
					geste += $" : {Natures[_natureIndex]} (N)";
				// planter dans un pot : même espèce que le cycle S.
				else if (g.Verb == "planter_conteneur")
					geste += _seeds.Count == 0 ? " : aucune graine (S)"
						   : $" : {_seeds[_seedIndex].Key} (S)";
				// déplacer : rappelle le geste à 2 temps + l'état de saisie.
				else if (g.Verb == "deplacer_pot")
					geste += _grabbedContainer >= 0
						? $" : pot #{_grabbedContainer} saisi → cliquez la destination"
						: " (cliquez un pot, puis sa destination)";
				// bouturer / greffer : gestes à 2 temps (palette ④), rappel de l'état
				// de saisie (mère/greffon saisi → cliquez la cible).
				else if (g.Verb == "bouturer")
					geste += _grabbedMother != null
						? " : mère saisie → cliquez le plot cible"
						: " (cliquez la mère, puis le plot cible)";
				else if (g.Verb == "greffer")
					geste += _grabbedScion != null
						? " : greffon saisi → cliquez le porte-greffe"
						: " (cliquez le greffon, puis le porte-greffe)";
			}
			// État macro (⑤) : préfixe discret quand on enregistre ou qu'une
			// macro est armée pour le prochain clic (K enregistre, J arme).
			if (_recording)
				geste = $"● REC macro ({_macroRec.Count}) — {geste}";
			else if (_macroArmed)
				geste = $"▶ macro armée — {geste}";
			string msg = string.IsNullOrEmpty(_lastActionMsg) ? ""
				: $"   ·   {_lastActionMsg}";
			_actionLabel.Text = $"{vig} — geste : {geste}{msg}";
		}

		// Overlay de perfs (F4) — mesures côté VUE, le moteur n'est pas
		// instrumenté : tick complet (pipe+sim+parse — la vérité du joueur),
		// cadence réelle entre 2 semaines (→ jours simulés/seconde), volumes.
		private void UpdatePerf()
		{
			if (_perfLabel == null) return;
			string tick = _lastTickMs < 0 ? "—" : $"{_lastTickMs:F0} ms";
			string cad = _lastWeekGapSec <= 0 ? "—"
				: $"{_lastWeekGapSec:F1} s/sem ({7.0 / _lastWeekGapSec:F1} j/s)";
			// Banc d'observation perf (④) — ligne SERVEUR : les 3 observables du
			// snapshot `perf` (mesurés côté moteur, cf. serialize.py). C'est CETTE
			// ligne qu'on lit en turbo longue durée : `N` doit plafonner, `moteur`
			// cesser de dériver. Le `tick` client au-dessus inclut pipe+parse ; ici
			// c'est le tick_semaine() PUR — les comparer isole le coût du pont.
			string srvTick = _srvMsTick < 0 ? "—" : $"{_srvMsTick:F1} ms";
			string srvRss = _srvRssMo < 0 ? "—" : $"{_srvRssMo:F0} Mo";
			string srvN = _srvNPlants < 0 ? "—" : _srvNPlants.ToString();
			_perfLabel.Text =
				$"[debug] FPS {Engine.GetFramesPerSecond():F0} · tick {tick} · cadence {cad}\n"
				+ $"plantes {_plantNodes.Count} (+{_nPousses} pousses) · "
				+ $"segments {_nSegments} · vie macro "
				+ (_macroLife == null ? "—"
					: !_macroLife.Visible ? "OFF"
					: CurrentZoom < 4f ? $"{_macroLife.Count} (LOD : zoomez ×4)"
					: _macroLife.Count.ToString()) + " · "
				+ $"butineurs {(_foragerLayer == null ? "—" : _foragerLayer.Count.ToString())} · "
				+ $"ombres {(ShadowsOn ? "ON" : "OFF")} · "
				+ $"zoom ×{ZoomSteps[_zoomIndex]}\n"
				+ $"serveur (banc perf) — tick moteur {srvTick} · "
				+ $"N plantes {srvN} · RSS {srvRss}\n"
				+ LignePerfRendu();   // draw calls + temps de frame (WorldView.PerfMesure.cs)
		}

		// Refus métier → flash rouge de la 2e ligne (kickoff B·12 : pas de
		// popup ; le détail est en console).
		private void FlashActionLabel()
		{
			if (_actionLabel == null) return;
			_actionLabel.Modulate = new Color(1f, 0.35f, 0.35f);
			_actionLabel.CreateTween()
				.TweenProperty(_actionLabel, "modulate", Colors.White, 0.6f);
		}

		private void TogglePerf()
		{
			_perfVisible = !_perfVisible;
			if (_perfLabel != null) _perfLabel.Visible = _perfVisible;
			GD.Print($"[WorldView] F4 → perfs {(_perfVisible ? "ON" : "OFF")}.");
		}

		// Touche F6 (t6·C) : heatmap ON/OFF. OFF = coût STRICTEMENT nul
		// (critère kickoff) : nœud caché, _fieldsStale ignoré, plus AUCUNE
		// requête `fields` ne part — le serveur n'est même pas au courant.
		private void ToggleFieldOverlay()
		{
			_overlayOn = !_overlayOn;
			if (_fieldOverlay != null) _fieldOverlay.Visible = _overlayOn;
			if (_overlayOn) _fieldsStale = true;   // (re)fetch au prochain tour
			else if (_macroLife != null)
				_macroLife.FocusGuild = null;      // errance libre dès OFF
			UpdateFieldHud();
			GD.Print($"[WorldView] F6 → heatmap {(_overlayOn ? "ON" : "OFF")}.");
		}

		// Maj+F6 : champ suivant (cycle sur le registre du serveur).
		private void CycleField()
		{
			if (!_overlayOn || _fieldNames == null || _fieldNames.Length == 0)
			{
				GD.Print("[WorldView] Maj+F6 : ouvrir d'abord l'overlay (F6).");
				return;
			}
			_fieldIndex = (_fieldIndex + 1) % _fieldNames.Length;
			_fieldsStale = true;   // la grille du nouveau champ part au prochain tour
			UpdateFieldHud();
			GD.Print($"[WorldView] Maj+F6 → champ : {_fieldNames[_fieldIndex]}.");
		}

		// Légende de la heatmap (t6·C3, retour 1 du F5) : une RAMPE CONTINUE
		// de pavés interpolés entre les deux pôles — exactement le Lerp que
		// FieldOverlay applique aux losanges, en BBCode (zéro nouveau nœud).
		// Bornes affichées = celles de l'ÉCHELLE (fixes si le champ en a) ;
		// sur échelle fixe on ajoute « grille a..b » : où la grille VIT
		// réellement (« grille 14.1..14.1 » = uniforme, c'est la vérité du
		// modèle, pas un bug d'affichage). Affichée UNIQUEMENT à l'écran.
		private const int LegendSteps = 14;

		private void UpdateFieldHud()
		{
			if (_fieldLabel == null) return;
			if (!_overlayOn)
			{
				_fieldLabel.Visible = false;
				return;
			}
			_fieldLabel.Visible = true;
			string nom = _fieldNames != null && _fieldNames.Length > 0
				? _fieldNames[_fieldIndex] : "…";
			var (lo, hi, labLo, labHi, _, _) = FieldOverlay.PaletteOf(nom);
			string bornes;
			if (_fieldOverlay?.FieldName == nom)
			{
				var ramp = new System.Text.StringBuilder();
				for (int i = 0; i < LegendSteps; i++)
				{
					Color c = lo.Lerp(hi, i / (float)(LegendSteps - 1));
					ramp.Append($"[color=#{c.ToHtml(false)}]█[/color]");
				}
				bornes = $"{labLo} ({_fieldOverlay.Min:F2}) {ramp} "
					   + $"{labHi} ({_fieldOverlay.Max:F2})";
				if (_fieldOverlay.FixedScale)
					bornes += $"   ·   grille {_fieldOverlay.GridMin:F2}"
							+ $"..{_fieldOverlay.GridMax:F2}";
				// Pédagogie (t6·C3, retour 2) : ce champ EST l'air hebdo,
				// uniforme par construction (engine fill) — la température
				// du sol spatialisée a sa propre carte depuis le tronçon ⑩ : touche F7.
				if (nom == "temperature")
					bornes += "   ·   air hebdo (uniforme — temp. du sol spatialisée : F7)";
			}
			else
				bornes = "chargement…";
			_fieldLabel.Text =
				$"heatmap (debug) — {nom} : {bornes}   ·   Maj+F6 champ suivant";
		}
	}
}
