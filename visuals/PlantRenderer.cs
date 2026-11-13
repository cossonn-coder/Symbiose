// SYMBIOSE — PlantRenderer.cs
// Premier RENDU VISIBLE des branches (tronçon 4 du sprint Croissance).
// Un Node2D qui projette en isométrie la structure de segments (exportée par
// Python, source de vérité) et la rastérise en pixels. Consommateur passif :
// aucune logique écologique, aucun RNG — juste géométrie → pixels.
//
// Idiomes Godot expliqués (Nico débute le frontend) :
//  · Node2D = nœud d'arbre de scène avec une transform 2D (position/rotation/
//    échelle). Son `Position` place son ORIGINE locale à l'écran. Ici on pose
//    l'origine sur le COLLET de la plante (sa position au sol dans la grille).
//  · _Draw() = rappel de DESSIN IMMÉDIAT. Godot l'appelle quand le nœud doit se
//    redessiner ; on y émet des primitives (DrawLine, DrawColoredPolygon) en
//    coordonnées LOCALES (relatives à Position). Pour forcer un redraw après un
//    changement de données, on appelle QueueRedraw().
//  · antialiased:false sur DrawLine = pas de lissage → cohérent avec le pixel art
//    (filtre Nearest partout, cf. CLAUDE.md). Sans ça, les branches « bavent ».

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// --- Projection iso : DÉLÉGUÉE à WorldView.WorldToScreen (tranche 2) ---
		// UNE seule projection pour tout le monde (tuiles, maison, plantes),
		// calibrée sur le losange réel du sprite tuile (78×39 px pour 50 cm →
		// 0.78 px/cm) — c'est la levée de D2 : l'ancien couple cos30/sin30 ×
		// PxPerCm=0.42 (maquette SVG, allure « panneau ») dupliquait un 2ᵉ modèle
		// iso qui ne coïncidait pas avec la grille. dz (hauteur) tire vers le
		// HAUT : en 2D Godot +Y est vers le BAS, donc on SOUSTRAIT dz·PxPerCmZ.
		// NB : l'échelle est désormais celle du MONDE — un pommier de 350 cm fait
		// ~273 px de haut (~7 plots), c'est voulu (cohérence spatiale empreintes ↔
		// couronnes). L'ancienne démo TileGrid affichera donc ses spécimens plus
		// grands qu'avant — elle n'est plus la scène principale, assumé.

		// Seuil du LOD silhouette (sprint PERF rendu plantes, tronçon ①) : sous ×4
		// on est en VUE D'ENSEMBLE — la vie macro y est elle aussi éteinte
		// (MacroLife.MinZoom = 4). On ne rastérise alors pas chaque brindille +
		// organe (le gros du décompte de primitives rejouées/frame = le 5 FPS),
		// chaque plante se résume à sa silhouette de couronne (2 polygones). Le
		// zoom réel vit dans WorldView.CurrentZoom (static) ; la pompe de redraw
		// au franchissement de palier est dans WorldView.Camera.StepZoom.
		// DÉSYNC ③ (doc §3, Q3) : abaissé 4→1 — segments rastérisés dès ×1.
		// D106 T5 : sous ×4 le dessin passe aux PALIERS BAS (PlantRenderer.Paliers.cs,
		// PaliersHautsMinZoom) ; ce seuil ne pilote plus que la surbrillance de taille.
		private const float SegmentDetailMinZoom = 1f;

		// (L'ancien seuil OrganDetailMinZoom a disparu au D106 T6 : sous ×4 on
		// dessine les paliers bas, et dès ×4 les organes suivent l'échelle des
		// paliers hauts — masses ×4, organes ×8, symptômes ×16, intime ×32 —
		// cf. PlantRenderer.PaliersHauts.cs.)

		// Couleurs (palette centrale Palette16, T1) : apex vert vif, bois brun.
		private static readonly Color ApexColor = Palette16.BoisApex;
		private static readonly Color WoodColor = Palette16.BoisMur;
		// Bois MORT (squelette post-mortem, vue·rattrapage 02) : gris-brun éteint,
		// aucune teinte d'apex — la mort se lit à la couleur dès le premier regard.
		private static readonly Color DeadWoodColor = Palette16.BoisMort;
		// Surbrillance du segment sous la souris en mode tailler (tranche 5) :
		// même jaune clair que le flash de geste réussi — un seul langage visuel.
		private static readonly Color HighlightColor = Palette16.Surbrillance;
		// Sémiologie foliaire (sprint D33, tronçon ③) : la vue LIT le champ snapshot
		// `leaf_symptoms` (liste de {cause, intensité} déjà triée par le moteur) et le
		// rend. Elle ne recalcule RIEN (ni pH, ni pression ravageur) — elle ne fait que
		// teinter/texturer. DEUX canaux séparés pour que le cumul reste lisible sans
		// teintes boueuses (conception §3) :
		//  · COULEUR — le symptôme COLORANT dominant (plus forte intensité) pose la
		//    teinte du tissu vert (feuilles/apex/silhouette) ∝ son intensité. Le bois
		//    brun n'est jamais teinté (il ne se décolore pas). Indice diégétique,
		//    pas un chiffre (philo #5).
		//  · TEXTURE/FORME — ravageurs/grêle (limbe criblé), gel (bords noircis),
		//    sécheresse (feuilles tombantes), ADDITIFS et indépendants de la couleur,
		//    appliqués sur les feuilles (cf. PlantRenderer.Organs.cs).
		// Teintes des symptômes COLORANTS (= canal couleur). Une plante saine n'a
		// aucune entrée → identité. Causes inconnues ignorées (forward-compatible §7).
		private static readonly Dictionary<string, Color> ColorantTints = new()
		{
			["chlorose"]   = Palette16.SymChlorose,   // jaune inter-nervaire (carence ferrique)
			["asphyxie"]   = Palette16.SymAsphyxie,   // brun-vert terne (anoxie racinaire)
			["secheresse"] = Palette16.SymSecheresse, // beige désaturé, flétri
			["senescence"] = Palette16.SymSenescence, // jaune-rouge de fin de vie
			["maladie"]    = Palette16.SymMaladie,    // brun tacheté (cryptogamique)
			// ombre / étiolement (D33 chronique, lève dette 0.5.2) : à l'ombre la
			// plante s'étiole — feuilles PÂLES et anémiées (moins de chlorophylle).
			// Vert pâle délavé désaturé. Partage le canal COULEUR (1 dominant) : une
			// chlorose plus intense le masque, mais une plante seulement ombragée
			// révèle l'étiolement (apprenable, philo #5).
			// T3 (§5) : chaleur relevée b8c8a0 → c2c8a0 (un poil plus de rouge, moins
			// de bleu). Le délavé d'étiolement frôlait le froid du hue-shift côté nord
			// (risque de le confondre avec une simple ombre de volume) ; ce léger
			// réchauffement le re-décale vers le vert-jaune anémié, distinct du bleu.
			["ombre"]      = Palette16.SymOmbre, // vert pâle délavé désaturé (étiolement)
			// rongeur_racinaire (sommet trophique ①, campagnol) : herbivorie SOUTERRAINE
			// — collet rongé/écorcé, racine coupée → la sève ne monte plus, la plante se
			// fane par la BASE en jaune-brun sale. Canal COULEUR (comme les autres
			// carences chroniques) : un dégât plus aigu (asphyxie/sécheresse) le masque,
			// mais une plante seulement rongée au collet RÉVÈLE le flétrissement basal.
			// Distinct du criblage foliaire du ravageur (canal TEXTURE, trous dans le
			// limbe) : ici la cause est cachée sous terre — on l'INFÈRE (indices #5/#6).
			["rongeur_racinaire"] = Palette16.SymRongeurRacinaire, // jaune-brun sale (flétri par le collet)
			// acclimatation (plasticité ⑤) : pas un dégât mais un DURCISSEMENT —
			// feuillage coriace/glauque, voile de cire bleu-gris (synthèse bio §4).
			// Partage le canal COULEUR : un vrai signe de souffrance (intensité plus
			// forte) le masque, mais sur une plante sans pathologie le glauque RÉVÈLE
			// qu'elle s'est endurcie (apprenable, philo #5).
			["acclimatation"] = Palette16.SymAcclimatation, // glauque (cire) bleu-gris
		};
		// Teinte appliquée à intensité 1 (≤1 pour garder un fond vert lisible même au
		// pic). Ex-ChloroseAmount=0.6 ; un poil relevé : l'intensité module désormais.
		private const float SymptomTintMax = 0.7f;

		// Causes à MARQUE FOLIAIRE fine sans teinte propre (criblage, bord noirci) :
		// dessinées par DrawLeafDamage, donc visibles seulement dès ×16.
		private static readonly HashSet<string> MarquesFines = new() { "ravageurs", "gel", "grele" };

		// SEUILS DE VISIBILITÉ MESURÉS (INFO-BULLE DU VIVANT ②) — plus petite intensité
		// dont la teinte change AU MOINS UN PIXEL de la plante témoin à l'écran, prise
		// au MAX (le plus prudent) sur les paliers ×2/×4/×8 ET sur les deux rendus
		// (palette SNES F11 OFF = défaut, et ON = 34 couleurs + Bayer). Banc :
		// world/WorldView.BancSeuil.cs via sprints/narration/semiologie/
		// sprint_infobulle_vivant/mesures/mesure_seuil.sh. Palette OFF : tout change
		// dès 0,005 ; c'est la quantification SNES qui fixe ces valeurs. Grille
		// 0,005·0,01·0,02·0,03·0,05·0,075·0,1·0,15·0,2·0,3·0,5 → seuil réel dans
		// ]pas précédent, valeur]. [VM llvmpipe, n=1 témoin Clover banc smoke s12]
		private static readonly Dictionary<string, float> SeuilTeinte = new()
		{
			["chlorose"] = 0.03f,           // max ×4 palette ON
			["asphyxie"] = 0.075f,          // ×2 et ×4 palette ON
			["secheresse"] = 0.01f,         // ×2 palette ON
			["senescence"] = 0.1f,          // ×4 palette ON
			["maladie"] = 0.075f,           // ×2 et ×4 palette ON
			["ombre"] = 0.02f,              // ×4 palette ON
			["rongeur_racinaire"] = 0.2f,   // ×4 palette ON
			["acclimatation"] = 0.05f,      // ×4 palette ON
		};
		// Vitalité : ApplyVitality ternit un pixel dès un manque de 0,075 (×4 palette
		// ON ; OFF dès 0,01) → au-dessus de 0,925 le feuillage reste « vert franc ».
		// [VM llvmpipe, n=1 témoin, même banc]
		public const float VitaliteFranche = 0.925f;
		// Automne : la teinte de saison change un pixel dès 0,03 (×4 palette ON).
		// [VM llvmpipe, n=1 témoin, même banc]
		public const float SeuilAutomne = 0.03f;
		// Marques fines (DrawLeafDamage) : un CALCUL, pas une mesure — criblage =
		// ceil(i × 4) trous (≥ 1 dès i > 0), bord de gel en trait ≥ 1 px dès i > 0 →
		// toute intensité strictement positive dessine au moins une marque à ×16.

		/// <summary>Le signe `cause` d'intensité `intensite` se VOIT-il au palier
		/// `zoom` (info-bulle) ? Teinte de santé dès ×2 (`PalierSanteZoom`) ET au-dessus
		/// de son seuil mesuré ; marques foliaires fines dès ×16, dès i > 0. Miroir de
		/// ce que le dessin montre — pas une règle de jeu.</summary>
		public static bool SigneVisible(string cause, float intensite, float zoom)
			=> SeuilTeinte.TryGetValue(cause, out float seuil)
				? zoom >= PalierSanteZoom && intensite >= seuil
				: MarquesFines.Contains(cause) && zoom >= PalierSymptomesZoom && intensite > 0f;

		/// <summary>Seuil de visibilité (intensité) du signe `cause` — repère des
		/// jauges Maj+F3 (D112 ②). Marques fines : visibles dès i > 0 → 0.</summary>
		public static float SeuilSigne(string cause)
			=> SeuilTeinte.TryGetValue(cause, out float seuil) ? seuil : 0f;

		/// <summary>La santé (vitalité + teinte de symptôme) est-elle dessinée à ce
		/// palier ? Sous ×2 non : la voix saine ne parle alors que de l'automne.</summary>
		public static bool SanteVisible(float zoom) => zoom >= PalierSanteZoom;

		// Lus par la voix saine de l'info-bulle (lecture seule).
		public float Vitalite => _vitalite;
		public float Automne => _structure?.Automne ?? 0f;

		// Liste brute du snapshot, dans l'ordre du moteur (intensité décroissante) :
		// lue par l'info-bulle (WorldView.InfoBulle.cs), jamais par le dessin.
		private readonly List<(string Cause, float Intensite)> _symptomes = new();
		public IReadOnlyList<(string Cause, float Intensite)> Symptomes => _symptomes;

		// --- Largeur de trait du bois (lisibilité ligneuse D90, tronçon ②) ---------
		// Largeur (px LOGIQUES) d'un segment = round(thickness_cm · PxPerCmX · facteur),
		// bornée à 1 (une brindille ne disparaît jamais). RECALIBRÉ contre la NOUVELLE
		// échelle d'épaisseur du moteur (tronçon ①, pipe model + croissance secondaire
		// saturante) : `thickness_cm` porte désormais des cm de bois RÉELS — le collet
		// d'un vieux pommier est BORNÉ par `girth_max_cm` (~18 cm), les brindilles
		// restent fines (~THICKNESS_INIT). L'ancien facteur 2.2 était calé sur
		// l'accumulation uniforme non bornée (le tronc pouvait filer vers ~120 cm) : sous
		// la nouvelle échelle il rendrait le tronc excessivement épais. À 1.5, avec
		// PxPerCmX = 0.39 : collet ~17 cm → ~10 px, charpentière ~6 cm → ~4 px,
		// brindille ~1 cm → 1 px (plancher) — le contraste tronc↔brindille se LIT, sans
		// « baobab ». Centralisé (3 sites : DrawSegments, DrawSkeleton, DrawHighlight)
		// pour que la surbrillance suive exactement la largeur du bois qu'elle recouvre.
		// Valeur à confirmer au F5 (banc « vieux_pommier »).
		private const float WoodWidthFactor = 1.5f;

		// Organes procéduraux (feuilles/fleurs/fruits) : constantes, palettes et
		// méthodes de dessin → PlantRenderer.Organs.cs (partial, SS⑦).

		// La structure à dessiner (assignée par le spawner, cf. TileGrid). Null tant
		// que rien n'est chargé → _Draw ne fait rien.
		private PlantStructure _structure;
		// Étendue horizontale max des segments autour du collet (cm) — rayon de
		// l'ombre au sol, recalculé à chaque SetStructure (t4 A2).
		private float _spreadCm;
		// Hauteur de cime (cm) — porte la LONGUEUR de l'ombre-capsule (t4 volet
		// C) : longueur = hauteur × 1/tan(élévation), exactement le modèle
		// ombres-capsules du moteur (fields/light.py §3).
		private float _heightCm;
		// L'ombre n'est plus un nœud enfant (PERF VUE ③) : toutes les capsules
		// partent en UN lot (visuals/PlantShadow.cs), qui lit ces deux mesures.
		internal float OmbreSpreadCm => _spreadCm;
		internal float OmbreHeightCm => _gisant ? _heightCm * GisantRelief : _heightCm;   // un gisant n'ombre plus (③)

		// Segment à surligner (index dans Segments = l'ordre du SNAPSHOT, le
		// même que structure_to_dict() Python — c'est CET index qui part dans
		// target.segment). −1 = aucun. 📖 Propriété avec setter early-out : on
		// peut l'écrire chaque frame depuis WorldView, le QueueRedraw (coûteux
		// sur un vieil arbre) ne part qu'au CHANGEMENT de segment survolé.
		private int _highlightSegment = -1;
		public int HighlightSegment
		{
			get => _highlightSegment;
			set
			{
				if (value == _highlightSegment) return;
				_highlightSegment = value;
				QueueRedraw();
			}
		}

		public override void _Ready()
		{
			if (IsBrush) return;   // pinceau de cuisson (T2) : ni ombre ni registre
			PlantShadow.MarquerSale();   // nouvelle plante → nouvelle ombre dans le lot
		}

		// État post-mortem (vue·rattrapage 02) : null/"" = plante vivante ;
		// "seche" = squelette debout ; "couchee" = squelette au sol (silhouette
		// aplatie). Posé par WorldView.ApplySnapshot d'après le `dead`/`stade_mort`
		// du snapshot (0.3.6). Une fois mort, un nœud ne « ressuscite » jamais.
		private string _deadStade;
		// GESTES LISIBLES ③ : un mort « couché » GÎT — son axe vertical bascule au sol
		// (Iso), dans une direction propre à l'individu (hash, jamais Random).
		private bool _gisant;
		private Vector2 _axeGisant;
		public void SetSkeleton(string stadeMort)
		{
			if (_deadStade == stadeMort) return;   // early-out : pas de redraw inutile
			_deadStade = stadeMort;
			_gisant = stadeMort == "couchee";
			float a = Mathf.Tau * Hash01(213, GraineIndividu, 0);
			_axeGisant = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
			Invalidate();
		}

		// Canal COULEUR résolu : teinte du symptôme colorant dominant + force (=
		// intensité × SymptomTintMax). Canaux TEXTURE/FORME : intensité par cause
		// (0 = absent), lus par les feuilles (Organs). Poussés par SetSymptoms.
		private Color _colorTint;
		private float _colorAmount;       // 0 = aucun colorant → tissu vert intact
		private float _ravageurs, _gel, _grele, _drought, _ombre, _maladie;

		// Reçoit le `leaf_symptoms` du snapshot (liste de dicts {cause, intensity}),
		// null/absent → plante saine. Sépare le canal couleur (colorant dominant) des
		// canaux texture. La vue ne recalcule rien : elle traduit la liste en pixels.
		public void SetSymptoms(Godot.Collections.Array symptoms)
		{
			_lusTmp.Clear();
			if (symptoms != null) PlanteLue.LireSymptomes(symptoms, _lusTmp);
			SetSymptoms(_lusTmp);
		}
		private static readonly List<(string, float)> _lusTmp = new();

		// FLUIDITÉ AN 2 ④ : symptômes déjà LUS hors fil principal (core/PlanteLue.cs).
		public void SetSymptoms(IReadOnlyList<(string Cause, float Intensite)> symptoms)
		{
			if (MemesSymptomes(symptoms)) return;   // rien de neuf : pas de cuisson (Ports.cs)
			_colorTint = default;
			_colorAmount = 0f;
			_ravageurs = _gel = _grele = _drought = _ombre = _maladie = 0f;
			_symptomes.Clear();
			if (symptoms != null)
				for (int i = 0; i < symptoms.Count; i++)
				{
					var (cause, it) = symptoms[i];
					_symptomes.Add((cause, it));
					// COULEUR : on garde le colorant de plus forte intensité (pas de
					// mélange). On compare l'intensité brute (SymptomTintMax constant).
					if (ColorantTints.TryGetValue(cause, out var tint)
						&& it * SymptomTintMax > _colorAmount)
					{
						_colorTint = tint;
						_colorAmount = it * SymptomTintMax;
					}
					// TEXTURE/FORME : additifs, lus par cause. Cause inconnue → ignorée.
					switch (cause)
					{
						case "ravageurs": _ravageurs = it; break;
						case "gel":       _gel = it; break;
						case "grele":     _grele = it; break;
						case "secheresse": _drought = it; break;
						// ombre (étiolement) : limbe chétif → calotte éclairée réduite,
						// lu côté chemin feuille seulement (cf. PlantRenderer.Organs.cs).
						case "ombre":     _ombre = it; break;
						// maladie (cryptogames) : EN PLUS de la teinte brune (canal
						// COULEUR, ColorantTints), un semis de petites taches ponctuées
						// sur le limbe → distingue le ponctué de l'asphyxie uniforme
						// (cf. DrawLeafDamage, PlantRenderer.PaliersHauts.cs).
						case "maladie":   _maladie = it; break;
					}
				}
			RefreshMeteo();   // la variante canicule suit `secheresse` (T4)
			Invalidate();
		}

		// Vitalité continue (santé & résilience ④, snapshot 0.5.28) : `vitalite` ∈
		// [0,1] du snapshot, 1.0 = plante saine neuve. C'est un DESCRIPTEUR GLOBAL de
		// l'usure (érosion des stresseurs / convalescence côté moteur), distinct des
		// `leaf_symptoms` LOCALISÉS : la vitalité ternit/désature le FOND vert de tout
		// le feuillage (chlorophylle qui s'épuise, port qui se fane), les symptômes
		// posent leurs MARQUES par-dessus. La vue LIT — elle ne recalcule aucune
		// santé (moteur = source de vérité). Défaut 1.0 → snapshot pré-0.5.28 rend
		// la plante pleine (tolérance, aucune régression). Cf. ApplyVitality (Palette).
		private float _vitalite = 1f;
		public void SetVitality(float v)
		{
			v = Mathf.Clamp(v, 0f, 1f);
			if (Mathf.IsEqualApprox(v, _vitalite)) return;   // early-out : pas de redraw
			if (RecetteDeLaPlante(out _) && Echelon(v) == Echelon(_vitalite)) return;   // arbre : HOUPPIER ④
			_vitalite = v;
			Invalidate();
		}

		// Tire un tissu vert (feuilles/apex/silhouette) vers la teinte du symptôme
		// colorant dominant, ∝ son intensité ; identité si aucun colorant. Jamais
		// appliqué au bois (il ne se décolore pas). Généralise l'ex-Chlorotic().
		// COMPOSITION vitalité (④) : on applique d'abord le FOND global de vitalité
		// (ApplyVitality — ternissure/désaturation continue), PUIS la marque du
		// symptôme dominant par-dessus. Ordre volontaire : la vitalité ne doit pas
		// écraser un symptôme franc (chlorose/maladie garde sa teinte vive), elle
		// habille le tissu en amont. Plante saine (vitalité 1, aucun colorant) =
		// identité stricte → zéro régression.
		private Color SymptomTint(Color tissue)
		{
			Color bg = ApplyVitality(tissue);
			return _colorAmount > 0f ? bg.Lerp(_colorTint, _colorAmount) : bg;
		}

		// Silhouette d'espèce (luxuriance ⑥, descripteur data du moteur ③ : tapis/
		// rosette/touffe/étalée/dressée/buisson). Lue au snapshot (0.5.19), pilote la
		// FORME de la silhouette de couronne au LOD faible (§B). null/absent → défaut
		// « touffe » (comportement d'avant). Pur RENDU : aucun état moteur, aucune
		// géométrie de segment touchée (le détail segment reste inchangé au zoom fort).
		private string _silhouette;
		public void SetSilhouette(string silhouette)
		{
			if (_silhouette == silhouette) return;   // early-out : pas de redraw inutile
			_silhouette = silhouette;
			Invalidate();
		}

		// LOD des émetteurs d'ombre (D67, snapshot 0.5.21) : `emitteur` dérivé du
		// pouvoir ombrageant côté MOTEUR (hauteur × rayon × densité ≥ seuil). false =
		// semis sous-seuil que le LOD écarte des boucles d'ombre — reçoit toujours la
		// lumière, n'ombre plus. Pur INDICE technique : on ne change rien au rendu du
		// bois, on POSE seulement une teinte (SelfModulate) quand l'overlay debug est
		// actif, pour VOIR qui le LOD retire (posture « affichage technique »). Défaut
		// true (émetteur) → un snapshot pré-0.5.21 ne teinte jamais rien.
		private bool _isEmitter = true;
		// Teinte de repérage des NON-émetteurs sous l'overlay : bleu-gris translucide
		// (distinct des teintes de symptômes, canal SelfModulate ≠ Modulate des fondus).
		private static readonly Color LodDimTint = new(0.45f, 0.6f, 0.95f, 0.6f);

		public void SetEmitter(bool emitteur)
		{
			if (_isEmitter == emitteur) return;   // early-out
			_isEmitter = emitteur;
			ApplyLodTint();
		}

		// (Ré)applique la teinte de l'overlay LOD selon l'état global + le drapeau
		// émetteur de CETTE plante. SelfModulate ne touche QUE le dessin propre du nœud
		// (branches + organes), pas les fondus d'apparition/mort (Modulate:a) ni l'ombre
		// (nœud enfant). Overlay OFF ou plante émettrice → identité (blanc opaque).
		public void ApplyLodTint() =>
			SelfModulate = (WorldView.LodDebugOn && !_isEmitter)
				? LodDimTint : Colors.White;

		public void SetStructure(PlantStructure s)
		{
			_structure = s;
			NoterFloraison();   // pic de la floraison en cours : montée ou descente (FleursArbre.cs)
			// Les index de segments changent à chaque snapshot (une coupe
			// réindexe la structure côté moteur) : une surbrillance gardée
			// pointerait la mauvaise branche — le survol la re-résout au
			// prochain frame, on repart de « rien ».
			_highlightSegment = -1;
			_spreadCm = 8f;   // minimum visible, même pour une pousse droite
			_heightCm = 10f;  // plancher : même une pousse projette un soupçon
			if (s != null)
			{
				Vector3 collet = s.ColletCm;
				foreach (var seg in s.Segments)
				{
					Vector3 tip = seg.Base + seg.Dir * seg.LengthCm;
					float d = new Vector2(tip.X - collet.X, tip.Y - collet.Y).Length();
					if (d > _spreadCm) _spreadCm = d;
					float z = tip.Z - collet.Z;
					if (z > _heightCm) _heightCm = z;
				}
			}
			MesurerPort();        // taille réelle → port et tapis (Paliers.cs, T5)
			ComputeStiffness();   // raideur au vent suit la croissance (T3)
			if (DessinInchange()) return;   // port dessiné identique : pas de cuisson (Ports.cs)
			Invalidate(); // re-cuisson à venir (T2) — l'ancienne image reste d'ici là
		}

		// ---------------------------------------------------------------------------
		// PROJECTION
		// ---------------------------------------------------------------------------

		// dx/dy sont des OFFSETS au collet (vecteurs) → variante Offset de la
		// projection : seule la partie linéaire de l'orientation de vue (D35,
		// tranche 4) s'applique. WorldToScreen (points absolus) ajouterait la
		// translation du quart de tour et téléporterait chaque branche. Effet
		// gagné : la plante « tourne » avec le monde — son phototropisme penche
		// vers le même point monde (la maison) quelle que soit la vue.
		// T3 (jardin vivant) : la projection passe d'abord par la FLEXION au vent
		// (PlantRenderer.Wind.cs) — no-op à flexion nulle, donc dessin inchangé.
		private Vector2 Iso(float dx, float dy, float dz)
		{
			if (_bendFlex > 0f && dz > 0f) Bend(ref dx, ref dy, ref dz);
			// Couché (③) : la hauteur devient une longueur au sol ; il reste un relief
			// d'épaisseur (GisantRelief) pour que la tige ne se fonde pas dans la terre.
			if (_gisant) (dx, dy, dz) = (dx + dz * _axeGisant.X, dy + dz * _axeGisant.Y, dz * GisantRelief);
			return WorldView.WorldToScreenOffset(dx, dy) - new Vector2(0f, dz * WorldView.PxPerCmZ);
		}

		// ---------------------------------------------------------------------------
		// HIT-TEST DE SEGMENT (tranche 5 — taille au clic)
		// ---------------------------------------------------------------------------

		/// <summary>
		/// Portée du picking de segment autour du COLLET, en cm MONDE (correctif
		/// t5·B, retour F5 Nico : « les segments qui dépassent le carré de départ
		/// ne peuvent pas être taillés » — le filtre par collet à 30 cm excluait
		/// toute la couronne d'un arbre). 📖 Pourquoi spread + height : la souris
		/// est re-projetée au SOL (z=0) par ScreenToWorld ; un point de branche à
		/// hauteur dz recule son point-sol apparent de dz sur x ET y (l'inverse du
		/// tirage iso vertical) — l'écart max au collet est donc borné par
		/// l'étalement horizontal PLUS la hauteur, marge ×1,5 + tolérance fixe.
		/// </summary>
		public float PickExtentCm => 1.5f * (_spreadCm + _heightCm) + 40f;

		/// <summary>
		/// Le segment le plus proche de `canvasPos` (souris en coordonnées
		/// canvas, cf. GetGlobalMousePosition) à moins de `maxDistPx` px CANVAS,
		/// ou −1 ; `distPx` = la distance trouvée (pour comparer ENTRE plantes,
		/// correctif t5·B). L'index renvoyé est celui du SNAPSHOT (ordre préservé
		/// par StructureLoader.FromSnapshot) : il part tel quel dans target.segment.
		/// 📖 La géométrie est EXACTEMENT celle de DrawSegments (même Iso, mêmes
		/// extrémités — leçon D2 : pas de 2ᵉ projection « presque pareille ») :
		/// on surligne précisément ce qu'on dessine. Distance point-segment via
		/// Geometry2D.GetClosestPointToSegment (clamp aux extrémités compris).
		/// ~50 segments max par plante (MAX_SEGMENTS) : linéaire, trivial.
		/// Le segment 0 (collet, protégé moteur) est EXCLU : un clic au pied ne
		/// doit pas désigner l'incoupable — il retombe sur le repli t4
		/// (params.cible), comportement inchangé, critère 2 du kickoff.
		/// </summary>
		public int FindSegmentNear(Vector2 canvasPos, float maxDistPx, out float distPx)
		{
			distPx = float.MaxValue;
			if (_structure == null || _structure.Segments.Count < 2)
				return -1;
			// ToLocal : canvas → repère local du nœud (sa Position est le
			// collet à l'écran) — le même espace que les primitives de _Draw.
			Vector2 local = ToLocal(canvasPos);
			Vector3 collet = _structure.ColletCm;
			int best = -1;
			float bestD = maxDistPx;
			for (int i = 1; i < _structure.Segments.Count; i++)   // 0 = collet, exclu
			{
				var s = _structure.Segments[i];
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);
				float d = local.DistanceTo(
					Geometry2D.GetClosestPointToSegment(local, p1, p2));
				if (d < bestD) { bestD = d; best = i; }
			}
			if (best >= 0) distPx = bestD;
			return best;
		}

		// ---------------------------------------------------------------------------
		// DESSIN
		// ---------------------------------------------------------------------------

		// Dessin VECTORIEL d'origine = le PINCEAU de la pré-cuisson (jardin vivant
		// T2) : rejoué tel quel vers une image par PlantRenderer.Bake.cs, ou en
		// direct tant que la plante n'a pas d'image cuite. Le _Draw est dans Bake.
		private void DrawVector()
		{
			if (_structure == null || _structure.Segments.Count == 0)
				return;

			// L'ombre au sol n'est PLUS dessinée ici (volet C2) : elle part dans
			// le lot d'ombres (PlantShadow, PERF VUE ③) — le balayage du soleil
			// ne redessine qu'elle, jamais ces segments-ci.

			// Prairie (TRÈFLE DOMINANT ④) : port dessiné, à tous les paliers.
			if (DessinerPrairie()) return;
			// Ports des herbacées (FORMES DES PLANTES ②) : même chemin, depuis une fiche.
			if (DessinerPort()) return;
			// Tomate, lierre, jasmin vivants : leurs segments, leurs feuilles (FORMES ⑥).
			if (DessinerLiane()) return;

			// Paliers BAS ×0,5-×2 (D106 T5, PlantRenderer.Paliers.cs) : chaque palier
			// porte SON information (présence+saison / port / santé), squelette et
			// caduc d'hiver compris. Le détail (segments + organes) commence à ×4.
			if (WorldView.CurrentZoom < PaliersHautsMinZoom)
			{
				DrawPalierBas();
				return;
			}

			// Squelette post-mortem (vue·rattrapage 02) : bois nu, ni feuilles ni
			// organes — la mort se lit à la couleur et (couchée) à l'aplatissement.
			if (!string.IsNullOrEmpty(_deadStade))
			{
				DrawSkeleton();
				return;
			}

			DrawSegments();
		}

		private void DrawSegments()
		{
			Vector3 collet = _structure.ColletCm;
			// CASSÉ À L'ÉCRAN ④ : racines en éventail + halo dithéré sous un arbre.
			DrawAncrage();

			// Tri par épaisseur DÉCROISSANTE : le bois épais (tronc) se dessine
			// d'abord (dessous), les fines brindilles par-dessus — comme _panel.
			var segs = new List<Segment>(_structure.Segments);
			segs.Sort((a, b) => b.ThicknessCm.CompareTo(a.ThicknessCm));
			bool houppier = Houppier;   // HOUPPIER ⑤ : bois à sa vraie épaisseur, bout seul tendre

			for (int k = 0; k < segs.Count; k++)
			{
				var s = segs[k];
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				// On soustrait x,y du collet (recadrage horizontal) et on garde z
				// absolu (le collet est au sol, z=0) — exactement comme _iso(bx-cx,…).
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);

				// Largeur ∝ épaisseur, ARRONDIE au pixel (pixel art). NB : à un vrai
				// zoom ×N, 1 px logique = N px écran ; l'arrondi entier ici donne un
				// trait net au palier. min 1 px pour rester visible.
				float z = WorldView.CurrentZoom;
				float w = houppier
					? Mathf.Max(BoisArbreMinPx / z, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor * z) / z)
					: Mathf.Max(1f, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor));
				// SS② : rampe de lignification vert-tendre → brun (∝ épaisseur), au
				// lieu du binaire apex/bois. Les symptômes colorants ne teintent que
				// la part VIVANTE (verte) : le bois mûr (lig→1) ne se décolore pas.
				float lig = LigVue(s, houppier);
				Color baseCol = AvecEcorce(WoodRamp(lig), s);   // écorce de la fiche (AUTOMNE VISIBLE ④)
				Color col = baseCol.Lerp(SymptomTint(baseCol), 1f - lig);

				DrawBranch(p1, p2, col, w);
				if (houppier) DrawBoutTendre(s, collet);
				DrawSnowOnBranch(p1, p2, w, s, k);   // neige posée sur le bois (T5)
			}

			// Organes (tranche 6·A) : feuilles puis fleurs/fruits, PAR-DESSUS le
			// bois (ordre du prototype). Redessinés UNIQUEMENT avec la plante
			// (SetStructure à chaque snapshot) — jamais par frame ni au balayage
			// du soleil (leçon perf C2 : l'ombre seule vit dans un nœud séparé).
			// Paliers hauts (D106 T6) : masses ×4, organes ×8, symptômes ×16, intime ×32.
			DrawOrgans(collet);

			// Surbrillance (tranche 5) : le segment sous la souris en mode
			// tailler se redessine PAR-DESSUS, après tout le bois.
			DrawHighlight(collet);

		}

		// Aplatissement de la silhouette « couchée » : le moteur ne ré-oriente PAS
		// les segments d'un squelette (stade_mort est un simple flag), on écrase
		// donc la composante verticale à l'AFFICHAGE pour la lecture « à terre ».
		// "sèche" garde sa hauteur (facteur 1).
		// GESTES LISIBLES ③ : l'écrasement (0,18) faisait d'une tige de 2,5 m un moignon
		// DEBOUT ; le mort couché est désormais COUCHÉ par Iso (axe basculé au sol) →
		// pleine longueur, facteur neutre. Gardé pour ses lecteurs (Prairie, Graminées).
		private const float CoucheeFlatten = 1f;
		private const float GisantRelief = 0.06f;

		// Squelette = mêmes segments que DrawSegments (même tri tronc-dessous, même
		// projection Iso) mais en bois MORT uniforme, sans organes ni surbrillance,
		// et aplati au sol si "couchée". La disparition (bois épuisé) est gérée en
		// amont : le moteur retire la plante, le snapshot ne la liste plus, le nœud
		// fond et QueueFree (WorldView.ApplySnapshot).
		private void DrawSkeleton()
		{
			Vector3 collet = _structure.ColletCm;
			float zf = _deadStade == "couchee" ? CoucheeFlatten : 1f;
			var segs = new List<Segment>(_structure.Segments);
			segs.Sort((a, b) => b.ThicknessCm.CompareTo(a.ThicknessCm));
			for (int k = 0; k < segs.Count; k++)
			{
				var s = segs[k];
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z * zf);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z * zf);
				float w = Mathf.Max(1f, Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor));
				DrawLine(p1, p2, Lit(DeadWoodColor), w, antialiased: false);
			}
		}

		// Le segment surligné, en clair et un peu plus large — « c'est CETTE
		// branche que le sécateur va prendre ». Index lu dans la liste
		// ORIGINALE du snapshot (le tri par épaisseur de DrawSegments est une
		// copie locale) : ce qu'on surligne = ce qu'on enverra en target.segment.
		private void DrawHighlight(Vector3 collet)
		{
			int hi = HighlightSegment;
			if (hi < 0 || hi >= _structure.Segments.Count)
				return;
			var s = _structure.Segments[hi];
			Vector3 tip = s.Base + s.Dir * s.LengthCm;
			Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
			Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);
			float w = Mathf.Max(2f,
				Mathf.Round(s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor) + 2f);
			DrawLine(p1, p2, HighlightColor, w, antialiased: false);
		}
	}
}
