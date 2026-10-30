// SYMBIOSE — DecorLayer.cs (T4 RENDU AMBIANCE — décor d'ambiance : OSSATURE)
// Le BACKDROP cosmétique AUTOUR du jardin (docs/rendu/ambiance/conception_rendu_ambiance.md
// §5.1). Une bande de terrain hors-jardin, dessinée DERRIÈRE le sol (ZIndex
// négatif, hors picking), qui pose l'ASSISE : quel motif occupe chaque bord du
// jardin (forêt / rivière / falaise / prairie fleurie par défaut) et la frontière
// SINUEUSE (jamais droite) qui l'ourle. Les MOTIFS détaillés (arbres, reflets
// d'eau, redans de roche) sont le tronçon T5 ; ici, des aplats teintés VOLUMÉS
// (≥ 2 valeurs) suffisent à valider placement et tracés au F5.
//
// 📖 Pédagogie — POURQUOI un Node2D à _Draw et pas des sprites :
// même patron que CouvertureLayer/LitterLayer. UN seul CanvasItem redessine tout
// dans son _Draw ; la rotation D35 est GRATUITE (re-projection par WorldToScreen à
// chaque dessin — les positions vivent en cm MONDE, jamais figées en px écran) ;
// zéro Random (philo #3) : tout le tracé sinueux + le grain viennent d'un hash
// stable dérivé du SEED du terrain (philo #7 : deux terrains n'ont pas le même
// entourage). Le décor est INERTE entre snapshots → on ne QueueRedraw qu'au build.
//
// 📖 Pédagogie — la COUTURE d'extensibilité, DÉSORMAIS BRANCHÉE (D73 ⑦) :
// le profil vient maintenant du PONT (bloc `ceinture` du snapshot, protocole
// 0.5.41 — cf. DecorLayer.Pont.cs, qui alimente la MÊME struct sans toucher aux
// tracés). `BuildProfile(seed)` reste, mais comme REPLI : binaire antérieur à
// 0.5.41, monde sans périphérie (smoke, bancs), banc F10. Le point d'entrée
// unique reste Build(seed), qui choisit la source.
//
// ⚠️ D92 est refermée PAR LE HAUT, pas corrigée sur place : le hash
// `decor|{seed}|{cote}` de BuildProfile ne brasse que ses bits bas (mesuré :
// 96 % de terrains aux 4 côtés identiques, 0 falaise sur 300 000 seeds). La
// distribution vient désormais de Python (`fields/peripherie.generer_ceinture`,
// tronçon ①, mesuré 2,7 % / 52 %). On ne touche pas au repli : le corriger ici
// dédoublerait un tirage dont Python est la source de vérité.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Les motifs possibles d'un secteur autour du jardin. Prairie = défaut.
		// `Friche` (D73 ⑦) double la table des types du moteur : une friche a des
		// ligneux ÉPARS et pas de canopée — assise + ourlet fleuri de la prairie,
		// plus un semis de ronciers rabougris (cf. DecorLayer.Pont.cs).
		public enum Motif { Prairie, Foret, Riviere, Falaise, Friche }
		// Pente de falaise (couplée à la rivière voisine) — donnée figée ici,
		// consommée au rendu fin en T5.
		public enum PenteFalaise { Douce, Verticale, Deversante }

		// Un secteur = un bord cardinal du jardin. `Motif` + tracé sinueux (la
		// frontière ondulée est recalculée au dessin depuis `SeedSecteur`).
		// `Pente` n'a de sens que pour Falaise (dérivée d'une rivière voisine).
		public struct Secteur
		{
			public int Cote;            // 0=nord, 1=est, 2=sud, 3=ouest (cm monde)
			public Motif Motif;
			public PenteFalaise Pente;
			public uint SeedSecteur;    // graine du tracé sinueux (stable)
			// --- État MOTEUR du secteur (pont 0.5.41, D73 ⑦) ------------------
			// `DuPont = false` ⇒ profil LOCAL de repli : tous les champs ci-dessous
			// sont ignorés et le rendu garde ses valeurs nominales (le décor d'avant,
			// au pixel près). Sinon ils pilotent la MASSE dessinée — une clairière se
			// voit, une trogne se voit, une falaise entaillée se voit (philo #5,
			// aucune jauge). Cf. DecorLayer.Pont.cs pour la traduction en facteurs.
			public bool DuPont;
			public float DensiteLigneuse;      // [0,1] couvert ligneux debout
			public float HauteurCanopeeCm;     // hauteur du peuplement
			public float LigneEauCm;           // ligne d'eau relative au bord (± cm)
			public float AltitudeRelativeCm;   // roche au-dessus du jardin (falaise)
			public float EntailleCm;           // roche RETIRÉE cumulée (irréversible)
			public string Essence;             // essence dominante, ou null
		}

		// La COUTURE d'extensibilité : le placement complet des zones. Calculée
		// depuis le seed aujourd'hui ; structurée pour un remplissage futur par le
		// pont (friche / extensions par maîtrise) sans réécriture du rendu.
		public struct SurroundingsProfile
		{
			public Secteur[] Secteurs;   // toujours 4 (un par bord cardinal)
		}

		// -----------------------------------------------------------------------
		// GÉOMÉTRIE de la bande de décor (cm MONDE). Le jardin occupe
		// [0, WorldCm]² ; le décor est une bande extérieure de DepthCm, ourlée par
		// une frontière sinueuse qui mord de ±AmplitudeCm dans/hors le jardin.
		// -----------------------------------------------------------------------
		private const float DepthCm     = 900f;   // profondeur de la bande hors-jardin
		private const float AmplitudeCm = 140f;   // amplitude de l'ondulation de frontière
		private const float StepCm      = 40f;    // pas d'échantillonnage du tracé sinueux
		// LOD : le décor cadre la vue d'ensemble → visible dès le dézoom (contraire
		// de la litière). On l'éteint au gros plan (on est « dans » le jardin).
		private const float MaxZoom = 4f;
		// LOD DÉTAIL à 2 niveaux (T4) : la MASSE (assises, houppiers, surface d'eau,
		// face de falaise) se dessine sur toute la plage visible ; les DÉTAILS FINS
		// (reflets de courant, fleurs de prairie, chevrons du bouleau, éboulis) — 1-2
		// px, invisibles au dézoom et calibrés vue proche — ne se peignent qu'à partir
		// de ce seuil. Recale l'échelle détail/distance ET allège le dessin au dézoom.
		private const float DetailZoom = 2f;
		private static bool DetailsVisibles => ZoomConstr >= DetailZoom;

		private SurroundingsProfile _profile;
		private bool _built;
		private int _seed;   // mémorisé pour reconstruire (rotation D35, bascule banc)

		// Hash djb2-xor (même choix que CouvertureLayer/LitterLayer : jamais
		// GetHashCode pour du visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		// Bruit déterministe 1D ∈ [-1, 1] : somme de 3 sinus déphasés par le hash.
		// Sert le tracé sinueux (jamais une droite) — pur, reproductible.
		private static float Ondulation(uint seed, float t)
		{
			float p0 = (seed & 0xff) / 255f * Mathf.Tau;
			float p1 = (seed >> 8 & 0xff) / 255f * Mathf.Tau;
			float p2 = (seed >> 16 & 0xff) / 255f * Mathf.Tau;
			return (Mathf.Sin(t * 1.7f + p0)
					+ 0.5f * Mathf.Sin(t * 3.9f + p1)
					+ 0.3f * Mathf.Sin(t * 7.3f + p2)) / 1.8f;
		}

		/// <summary>
		/// Point d'entrée UNIQUE (couture d'extensibilité) : construit le profil
		/// des alentours à partir du SEED du terrain. Le pont pourra plus tard
		/// alimenter la même struct sans toucher au rendu (dette D73).
		/// </summary>
		public static SurroundingsProfile BuildProfile(int seed)
		{
			var secteurs = new Secteur[4];
			// 1er passage : motif de chaque bord tiré du seed (prairie par défaut,
			// forêt/rivière fréquentes). La falaise n'est PAS tirée ici — elle
			// DÉRIVE d'une rivière voisine (couplage §5.1).
			for (int cote = 0; cote < 4; cote++)
			{
				uint h = HashKey($"decor|{seed}|{cote}");
				// Distribution : ~40 % prairie (défaut), ~35 % forêt, ~25 % rivière.
				int roll = (int)(h % 100u);
				Motif m = roll < 35 ? Motif.Foret
						: roll < 60 ? Motif.Riviere
						: Motif.Prairie;
				secteurs[cote] = new Secteur
				{
					Cote = cote,
					Motif = m,
					Pente = PenteFalaise.Douce,
					SeedSecteur = h,
				};
			}
			// 2e passage : couplage rivière ↔ falaise. Un bord voisin d'une rivière
			// (et resté prairie) devient falaise ; sa pente est tirée du seed
			// (l'érosion fluviale a creusé la roche — donnée figée, rendu fin en T5).
			for (int cote = 0; cote < 4; cote++)
			{
				if (secteurs[cote].Motif != Motif.Riviere) continue;
				int voisin = (cote + 1) % 4;   // bord adjacent (dans le sens horaire)
				if (secteurs[voisin].Motif != Motif.Prairie) continue;
				uint hp = HashKey($"pente|{seed}|{cote}");
				secteurs[voisin].Motif = Motif.Falaise;
				secteurs[voisin].Pente = (PenteFalaise)(hp % 3u);
			}
			return new SurroundingsProfile { Secteurs = secteurs };
		}

		/// <summary>
		/// Construit (ou reconstruit) le décor pour un seed de terrain. Appelé au
		/// build du monde ET à chaque rotation D35 (comme le sol). Le rendu se fait
		/// au _Draw suivant (positions en cm monde → suit le monde).
		/// </summary>
		public void Build(int seed)
		{
			_seed = seed;
			// Trois sources, dans cet ordre de priorité :
			//  1. le banc F10 (force les 4 motifs côte à côte pour valider la
			//     lisibilité — SANS toucher la distribution normale, philo #7) ;
			//  2. le PONT (D73 ⑦) : la ceinture du moteur, vérité du jeu ;
			//  3. le repli local par seed (binaire ancien, monde sans périphérie).
			_profile = _banc ? BancProfile()
					 : _ceinture != null ? BuildFromBridge(_ceinture, seed)
					 : BuildProfile(seed);
			TracerSource();   // console F5 : d'où vient le profil (DecorLayer.Banc.cs)
			InvaliderMailles();   // LEVIERS ③ : profil/rotation/banc changés → mailles à refaire
			_built = true;
			QueueRedraw();
		}

		private bool _lastZoomOk;
		private float _lastZoom;

		public override void _Process(double delta)
		{
			if (!Visible || !_built) return;
			// Inerte : on ne redessine qu'au basculement de LOD (apparition au dézoom,
			// MaxZoom) et, tant qu'il est visible, au CHANGEMENT DE PALIER — depuis
			// FLUIDITÉ PC ③ les pièces du kit gardent leurs px internes, leur semis
			// dépend donc du palier (et la bascule DetailZoom en fait partie).
			bool zoomOk = WorldView.CurrentZoom <= MaxZoom;
			if (zoomOk != _lastZoomOk || (zoomOk && WorldView.CurrentZoom != _lastZoom))
			{
				_lastZoomOk = zoomOk;
				_lastZoom = WorldView.CurrentZoom;
				QueueRedraw();
			}
			// LEVIERS ③ : les mailles des autres paliers se préparent par tranches
			// (DecorLayer.Mailles.cs) — le prochain cran de molette n'aura qu'à permuter.
			AvancerFond();
			MajUniformes();   // ⑥ : soleil, palier, vent → shader (DecorLayer.Vent.cs)
		}

		public override void _Draw()
		{
			if (!_built || WorldView.CurrentZoom > MaxZoom) { PublierDevant(null); return; }
			// 2 passes. Passe 1 : l'ASSISE de chaque secteur (aplats volumés T4) —
			// le fond sur lequel les motifs se détachent. Passe 2 : le MOTIF détaillé
			// (T5) peint par-dessus. On sépare les passes pour que les aplats voisins
			// ne recouvrent jamais un motif déjà tracé (les bandes se touchent aux coins).
			// PLANTE ASSEMBLÉE ① : tout part en UN lot (LotTriangles) — les triangles
			// gardent l'ordre des anciens appels, donc l'ordre des passes (~1 100 draw
			// calls → 1 à ×4 [VM]). On ne change que COMMENT, pas QUAND on redessine.
			// FLUIDITÉ PC LEVIERS ③ : le lot n'est plus reconstruit à chaque palier —
			// une maille FIGÉE par palier (DecorLayer.Mailles.cs) ; changer de palier =
			// redessiner la maille prête (un DrawMesh). Construite d'un bloc ici
			// seulement si elle manque encore (1er dessin, juste après Build).
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			Maille m = MailleImmediate(WorldView.CurrentZoom, out bool construite);
			TeleverserKit();   // ⑥ : texels-codes neufs / vidage de LUT → atlas au GPU
			if (m.Mesh != null) DrawMesh(m.Mesh, KitTexture);
			PublierDevant(m);   // LEVIERS ⑤ : pièces hautes côté caméra, couche au-dessus du jardin
			PublierEau(m);      // étincelles de CE palier (couche animée, DecorLayer.Eau.cs)
			TracerDessin(t0, m.Sommets, construite);   // console : coût (DecorLayer.Banc.cs)
		}

		// ⚠️ CONSERVÉ, plus appelé depuis LEVIERS ③ (remplacé par la maille par
		// palier) : l'ancien redessin complet du décor à chaque palier, référence.
		private void DessinerToutLot()
		{
			ZoomConstr = WorldView.CurrentZoom;   // le semis lit le palier construit
			_lot.Vider();
			_lot.UvUni = UvBlanc;   // aplats = texel blanc de l'atlas (DecorLayer.Kit.cs)
			_scintille?.Vider();    // FLUIDITÉ PC ④ : DrawReflets y range les étincelles
			foreach (var s in _profile.Secteurs)
				DrawAssise(s);      // FLUIDITÉ PC ③ : patchwork (DecorLayer.Patchwork.cs)
			foreach (var s in _profile.Secteurs)
				DrawMotif(s);
			_lot.Dessiner(this, KitTexture);
			_scintille?.Publier();  // couche animée à part (DecorLayer.Eau.cs)
		}

		// Lot de travail : réaffecté le temps d'une tranche de fond (Mailles.cs).
		private LotTriangles _lot = new();

		// Dispatch du MOTIF détaillé d'un secteur (T5), peint sur son assise.
		private void DrawMotif(Secteur s)
		{
			switch (s.Motif)
			{
				// FLUIDITÉ PC ③ : tapis du kit (DecorLayer.Patchwork.cs) sous les arbres.
				// LEVIERS ⑤ : EnHaut = pièces hautes, devant le jardin si le bord est côté
				// caméra (DecorLayer.Devant.cs) ; le tapis reste au sol, derrière.
				case Motif.Foret:   DrawTapis(s, Tapis.OurletForet); EnHaut(s, () => DrawForet(s)); break;
				case Motif.Riviere: DrawRiviere(s);     break;
				case Motif.Falaise: DrawTapis(s, Tapis.Pierrier); EnHaut(s, () => DrawFalaise(s)); break;
				// FRICHE (D73 ⑦) : l'ourlet fleuri de la prairie PLUS les ligneux
				// épars (DrawForet, dont la densité et la taille viennent du moteur —
				// une friche à 0.20 de densité et sans canopée donne des ronciers
				// rabougris, pas une futaie).
				case Motif.Friche:  DrawTapis(s, Tapis.Friche); EnHaut(s, () => DrawForet(s)); break;
				default:            DrawTapis(s, Tapis.Prairie); break;
			}
		}

		// ⚠️ CONSERVÉ, plus appelé depuis FLUIDITÉ PC ③ (remplacé par DrawAssise,
		// DecorLayer.Patchwork.cs) : l'assise en 3 aplats par pas, référence.
		// Un secteur : une bande extérieure le long d'un bord cardinal du jardin,
		// bornée côté jardin par une frontière SINUEUSE. On construit un ruban de
		// quads (le long du bord) rempli en aplat volumé (2 valeurs, hue-shift sud).
		private void DrawSecteur(Secteur s)
		{
			(Color near, Color far) = MotifColors(s.Motif);
			// Repère local du bord : `u` court le long du bord (0..WorldCm),
			// `depth` s'éloigne du jardin. On mappe (u, depth) → cm monde selon le
			// côté, puis WorldToScreen (⇒ la bande suit la rotation D35).
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm;
				float u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				// Frontière sinueuse : la bande commence à `edge + ondulation`
				// (mord de ±AmplitudeCm), s'étend vers l'extérieur sur DepthCm.
				float b0 = AmplitudeCm * Ondulation(s.SeedSecteur, u0 / 200f);
				float b1 = AmplitudeCm * Ondulation(s.SeedSecteur, u1 / 200f);
				Vector2 p0 = EdgePoint(s.Cote, u0, b0);
				Vector2 p1 = EdgePoint(s.Cote, u1, b1);
				Vector2 p2 = EdgePoint(s.Cote, u1, DepthCm);
				Vector2 p3 = EdgePoint(s.Cote, u0, DepthCm);
				// Volume : la lisière (près du jardin) plus claire, le fond plus
				// sombre → 2 valeurs sur la profondeur. Grain déterministe léger.
				float jitter = (Ondulation(s.SeedSecteur * 2654435761u, u0 / 90f)) * 0.05f;
				Color inner = near; inner = Assombrir(inner, -jitter);
				Color outer = far;  outer = Assombrir(outer, jitter);
				// Trois bandes JOINTIVES sur la profondeur, du bord jardin vers le fond :
				// seuil sombre | frange claire | fond. Frange de lisière ≈ 1/3 de la
				// profondeur ; LISIÈRE NETTE (T4) : un seuil SOMBRE franc collé au tracé
				// sinueux, côté décor, sur les 4 motifs → la frontière jardin/décor se
				// LIT au lieu de fondre. Rivière/falaise ont déjà leur bord franc
				// (berge/éboulis peints en passe 2), ce seuil passe dessous.
				// 📖 FLUIDITÉ PC ② — POURQUOI jointives et plus EMPILÉES : avant, le fond
				// couvrait tout le pas et la frange puis le seuil se peignaient
				// par-dessus. Leurs bords latéraux étaient alors COLINÉAIRES mais avec
				// des extrémités différentes (p3 pour le fond, m3 pour la frange). Le
				// SubViewport arrondit chaque sommet au pixel (snap_2d_vertices_to_pixel)
				// → m3 quitte la droite p0-p3 d'un demi-pixel, et le liseré du fond qui
				// dépasse se lit en POINTILLÉ sombre le long des pentes iso (les « fils
				// de couture »). Jointives, deux bandes voisines partagent EXACTEMENT
				// leurs sommets → aucune arête à demi recouverte, rien ne transparaît.
				float seuilW = DepthCm * 0.06f;
				Vector2 e2 = EdgePoint(s.Cote, u1, b1 + seuilW);
				Vector2 e3 = EdgePoint(s.Cote, u0, b0 + seuilW);
				Vector2 m2 = EdgePoint(s.Cote, u1, DepthCm * 0.34f + b1 * 0.66f);
				Vector2 m3 = EdgePoint(s.Cote, u0, DepthCm * 0.34f + b0 * 0.66f);
				_lot.Polygone(new[] { m3, m2, p2, p3 }, outer);
				_lot.Polygone(new[] { e3, e2, m2, m3 }, inner);
				_lot.Polygone(new[] { p0, p1, e2, e3 }, Assombrir(near, -0.24f));
			}
		}

		// -----------------------------------------------------------------------
		// MOTIFS DÉTAILLÉS (T5) — rivière (eau + reflets), falaise (redans étagés),
		// prairie (semis de fleurs). Tout en polygones/points cm MONDE → écran, donc
		// suit la rotation D35. Statique, cullé par le LOD global (comme l'ossature).
		// -----------------------------------------------------------------------

		// FLUIDITÉ PC ④ : DrawRiviere → DecorLayer.Eau.cs, DrawFalaise →
		// DecorLayer.Roche.cs (pièces du kit) ; les versions en aplats d'avant sont
		// CONSERVÉES dans DecorLayer.Aplats.cs (référence, plus appelées).

		// Un quad-bande le long d'un bord entre deux profondeurs, par pas de `u`
		// (near→far). Facteur commun des rubans de la rivière (berges, eau, liserés)
		// — garde DrawRiviere lisible sans dupliquer 4 EdgePoint à chaque bande.
		private void Bande(int cote, float u0, float u1,
						   float dNear0, float dNear1, float dFar0, float dFar1, Color col)
		{
			Vector2 p0 = EdgePoint(cote, u0, dNear0);
			Vector2 p1 = EdgePoint(cote, u1, dNear1);
			Vector2 p2 = EdgePoint(cote, u1, dFar1);
			Vector2 p3 = EdgePoint(cote, u0, dFar0);
			_lot.Polygone(new[] { p0, p1, p2, p3 }, col);
		}

		// ⚠️ CONSERVÉ, plus appelé depuis FLUIDITÉ PC ③ (fleurettes du kit, DrawTapis).
		// PRAIRIE : sur l'assise verte, un SEMIS déterministe de petites fleurs
		// (points blancs/jaunes), densité modérée, échantillonnage stable par hash.
		private void DrawPrairie(Secteur s)
		{
			// La prairie n'a PAS d'autre motif que ses fleurs (l'assise verte est
			// peinte en passe 1 par DrawSecteur) : elles sont DÉTAIL FIN (points 1.5
			// px) → au dézoom, l'assise + la lisière suffisent, on saute le semis.
			if (!DetailsVisibles) return;
			const float cell = 110f;
			int nU = Mathf.CeilToInt(WorldView.WorldCm / cell);
			int nD = Mathf.CeilToInt(DepthCm / cell);
			for (int iu = 0; iu < nU; iu++)
			for (int id = 0; id < nD; id++)
			{
				uint h = HashKey($"fleur|{s.SeedSecteur}|{iu}|{id}");
				if (h % 100u >= 45u) continue;   // ~45 % des cases fleuries
				float u = (iu + 0.5f + ((h >> 4 & 0xff) / 255f - 0.5f)) * cell;
				float depth = AmplitudeCm + (id + 0.5f) * cell;
				if (u < 0f || u > WorldView.WorldCm) continue;
				Color c = (h & 1u) == 0u ? Palette16.FleurPrairieBlanc : Palette16.FleurPrairieJaune;
				_lot.Cercle(EdgePoint(s.Cote, u, depth), 1.5f, c);
			}
		}

		// (u, depth) du repère local d'un bord → point cm MONDE → écran. `u` court
		// le long du bord (0..WorldCm), `depth` s'éloigne du jardin vers l'extérieur
		// (depth peut être négatif = mordre DANS le jardin, pour la frontière).
		private static Vector2 EdgePoint(int cote, float u, float depth)
		{
			float W = WorldView.WorldCm;
			(float x, float y) = cote switch
			{
				0 => (u, -depth),        // nord : bord y=0, extérieur vers y<0
				1 => (W + depth, u),     // est  : bord x=W, extérieur vers x>W
				2 => (u, W + depth),     // sud  : bord y=W, extérieur vers y>W
				_ => (-depth, u),        // ouest: bord x=0, extérieur vers x<0
			};
			return WorldView.WorldToScreen(x, y);
		}

		// Teintes de base par motif : (près du jardin, fond). Le détail (arbres,
		// eau, roche) est peint PAR-DESSUS en T5 — ici on valide juste le placement.
		private static (Color, Color) MotifColors(Motif m) => m switch
		{
			Motif.Foret   => (Palette16.DecorForetLisiere, Palette16.DecorForetFond),
			// ④ : fond = PRAIRIE de l'autre rive (le bleu du fond se lisait comme de
			// l'eau partout au-delà du lit) ; le lit est peint par DrawRiviere.
			Motif.Riviere => (Palette16.DecorEauBerge, Palette16.DecorPrairie),
			Motif.Falaise => (Palette16.DecorRocheHaut, Palette16.DecorRoche),
			// Friche : assise de prairie CLAIRE devant, lisière de bois au fond —
			// l'entre-deux, ce qu'une friche EST (une prairie qui se referme).
			Motif.Friche  => (Palette16.DecorPrairieClair, Palette16.DecorForetLisiere),
			_             => (Palette16.DecorPrairieClair, Palette16.DecorPrairie),
		};

		// Module la valeur d'une couleur (éclaircit si f>0, assombrit sinon),
		// bornée — volume pixel-art à 2 valeurs, sans virer la teinte.
		private static Color Assombrir(Color c, float f)
		{
			float k = Mathf.Clamp(1f + f, 0.75f, 1.25f);
			return new Color(
				Mathf.Clamp(c.R * k, 0f, 1f),
				Mathf.Clamp(c.G * k, 0f, 1f),
				Mathf.Clamp(c.B * k, 0f, 1f),
				c.A);
		}
	}
}
