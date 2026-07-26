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
		private static bool DetailsVisibles => WorldView.CurrentZoom >= DetailZoom;

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
					 : _ceinture != null ? BuildFromBridge(_ceinture)
					 : BuildProfile(seed);
			_built = true;
			QueueRedraw();
		}

		private bool _lastZoomOk;
		private bool _lastDetailOk;

		public override void _Process(double delta)
		{
			if (!Visible || !_built) return;
			// Inerte : on ne redessine qu'aux DEUX basculements de LOD — apparition au
			// dézoom (MaxZoom) et bascule masse↔détails fins (DetailZoom).
			bool zoomOk = WorldView.CurrentZoom <= MaxZoom;
			bool detailOk = DetailsVisibles;
			if (zoomOk != _lastZoomOk || detailOk != _lastDetailOk)
			{
				_lastZoomOk = zoomOk;
				_lastDetailOk = detailOk;
				QueueRedraw();
			}
		}

		public override void _Draw()
		{
			if (!_built || WorldView.CurrentZoom > MaxZoom) return;
			// 2 passes. Passe 1 : l'ASSISE de chaque secteur (aplats volumés T4) —
			// le fond sur lequel les motifs se détachent. Passe 2 : le MOTIF détaillé
			// (T5) peint par-dessus. On sépare les passes pour que les aplats voisins
			// ne recouvrent jamais un motif déjà tracé (les bandes se touchent aux coins).
			foreach (var s in _profile.Secteurs)
				DrawSecteur(s);
			foreach (var s in _profile.Secteurs)
				DrawMotif(s);
		}

		// Dispatch du MOTIF détaillé d'un secteur (T5), peint sur son assise.
		private void DrawMotif(Secteur s)
		{
			switch (s.Motif)
			{
				case Motif.Foret:   DrawForet(s);       break;   // DecorLayer.Arbres.cs
				case Motif.Riviere: DrawRiviere(s);     break;
				case Motif.Falaise: DrawFalaise(s);     break;
				// FRICHE (D73 ⑦) : l'ourlet fleuri de la prairie PLUS les ligneux
				// épars (DrawForet, dont la densité et la taille viennent du moteur —
				// une friche à 0.20 de densité et sans canopée donne des ronciers
				// rabougris, pas une futaie).
				case Motif.Friche:  DrawPrairie(s); DrawForet(s); break;
				default:            DrawPrairie(s);     break;
			}
		}

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
				// Deux triangles remplis (quad). L'inner sur le bord jardin, l'outer
				// au fond : on peint le fond puis la frange claire par-dessus.
				DrawColoredPolygon(new[] { p0, p1, p2, p3 }, outer);
				// Frange de lisière (bande claire côté jardin), 1/3 de la profondeur.
				Vector2 m2 = EdgePoint(s.Cote, u1, DepthCm * 0.34f + b1 * 0.66f);
				Vector2 m3 = EdgePoint(s.Cote, u0, DepthCm * 0.34f + b0 * 0.66f);
				DrawColoredPolygon(new[] { p0, p1, m2, m3 }, inner);
				// LISIÈRE NETTE (T4) : un seuil SOMBRE franc collé au tracé sinueux,
				// côté décor, sur les 4 motifs → la frontière jardin/décor se LIT au
				// lieu de fondre (rang d'ombre bas en forêt, ourlet de prairie, etc.).
				// Rivière/falaise ont déjà leur bord franc (berge/éboulis peints en
				// passe 2), ce seuil passe dessous sans les gêner. Suit la sinuosité.
				float seuilW = DepthCm * 0.06f;
				Vector2 e2 = EdgePoint(s.Cote, u1, b1 + seuilW);
				Vector2 e3 = EdgePoint(s.Cote, u0, b0 + seuilW);
				DrawColoredPolygon(new[] { p0, p1, e2, e3 }, Assombrir(near, -0.24f));
			}
		}

		// -----------------------------------------------------------------------
		// MOTIFS DÉTAILLÉS (T5) — rivière (eau + reflets), falaise (redans étagés),
		// prairie (semis de fleurs). Tout en polygones/points cm MONDE → écran, donc
		// suit la rotation D35. Statique, cullé par le LOD global (comme l'ossature).
		// -----------------------------------------------------------------------

		// RIVIÈRE : une surface d'eau CREUSÉE dans le terrain (T2). Berges franches
		// de galets de part et d'autre du lit, eau à 2 valeurs par damier hashé
		// ORDONNÉ (frémissement, jamais de dégradé), liseré d'ombre le long des deux
		// rives (creuse le lit, décolle la surface du plan-sol comme l'ombre T1), et
		// reflets = STREAKS clairs orientés dans le sens du COURANT (la tangente de
		// l'axe sinueux du lit). Zéro Random (hash + 3-sinus, philo #3).
		private void DrawRiviere(Secteur s)
		{
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			// Demi-largeur du lit MODULÉE par la ligne d'eau du moteur (pont) : un
			// bord endigué s'élargit, un bord dérivé se réduit à un filet — c'est
			// le retour visuel d'`endiguer`/`deriver` et de la mare creusée.
			float half         = DepthCm * 0.22f * FacteurLit(s);
			const float berge  = DepthCm * 0.11f;   // largeur de berge sur chaque rive
			float liseré = half * 0.18f;             // ombre de berge (bord d'eau)
			Color eauSombre = Assombrir(Palette16.EauProfonde, -0.18f);
			// L'axe du lit serpente d'un tracé sinueux propre (déphasé du secteur).
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				float ax0 = DepthCm * 0.5f + AmplitudeCm * Ondulation(s.SeedSecteur ^ 0x9e37u, u0 / 230f);
				float ax1 = DepthCm * 0.5f + AmplitudeCm * Ondulation(s.SeedSecteur ^ 0x9e37u, u1 / 230f);
				// -- Berges franches : bande de galets clairs sur chaque rive (au lieu
				// de laisser l'assise nue) → bord net entre terre et eau.
				Bande(s.Cote, u0, u1, ax0 - half - berge, ax1 - half - berge, ax0 - half, ax1 - half, Palette16.BergeGalet);
				Bande(s.Cote, u0, u1, ax0 + half, ax1 + half, ax0 + half + berge, ax1 + half + berge, Palette16.BergeGalet);
				// -- Surface d'eau : 2 valeurs en damier (parité du pas × moitié du
				// lit) → frémissement lisible à distance, sans dégradé continu.
				uint hd = (uint)i * 2654435761u ^ s.SeedSecteur;
				Color eauA = (hd & 1u) == 0u ? Palette16.EauProfonde : Palette16.EauSurface;
				Color eauB = (hd & 1u) == 0u ? Palette16.EauSurface  : Palette16.EauProfonde;
				Bande(s.Cote, u0, u1, ax0 - half, ax1 - half, ax0, ax1, eauA);
				Bande(s.Cote, u0, u1, ax0, ax1, ax0 + half, ax1 + half, eauB);
				// -- Ombre de berge : liseré d'eau plus sombre le long des deux rives.
				Bande(s.Cote, u0, u1, ax0 - half, ax1 - half, ax0 - half + liseré, ax1 - half + liseré, eauSombre);
				Bande(s.Cote, u0, u1, ax0 + half - liseré, ax1 + half - liseré, ax0 + half, ax1 + half, eauSombre);
				// -- Reflet orienté courant : un streak clair 1 case sur 2, tracé le
				// long du COURS (direction = le segment d'axe lui-même = tangente du
				// lit). Longueur ∝ pas monde → suit zoom/rotation, jamais 2 px morts.
				// DÉTAIL FIN : seulement à zoom ≥ DetailZoom (la surface d'eau et les
				// berges portent déjà la lisibilité de masse au dézoom).
				if (DetailsVisibles && (hd & 2u) == 0u)
				{
					float dOff = (((hd >> 8) & 0xff) / 255f - 0.5f) * half * 1.1f;
					Vector2 pa = EdgePoint(s.Cote, u0, ax0 + dOff);
					Vector2 pb = EdgePoint(s.Cote, u1, ax1 + dOff);
					Vector2 mid = pa.Lerp(pb, 0.5f);
					Vector2 flow = (pb - pa) * 0.42f;
					DrawLine(mid - flow, mid + flow, Palette16.EauReflet, 2.5f);
				}
			}
		}

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
			DrawColoredPolygon(new[] { p0, p1, p2, p3 }, col);
		}

		// FALAISE : un ressaut rocheux qui SURPLOMBE le jardin (T3). Plus des redans
		// à plat : une vraie FACE VERTICALE montée en −Y écran (comme un mur de
		// maison, cf. WorldView.Maison upWall), STRATIFIÉE en 3 valeurs de roche
		// dures, coiffée d'un PLATEAU végétalisé lui aussi élevé, avec une ombre
		// portée au pied (le surplomb) et un semis d'ÉBOULIS clairs à la base. La
		// hauteur de la face dérive de la PENTE (Douce basse → Déversante haute).
		// NON forcée : le seed décide de sa présence (philo #7) — on la rend juste
		// lisible quand elle paraît. Déterministe (hash + 3-sinus, zéro Random, #3).
		private void DrawFalaise(Secteur s)
		{
			// Hauteur de la face (cm monde) élevée en −Y écran : la ROCHE RESTANTE du
			// moteur si le pont l'a fournie (⇒ chaque coup de pioche d'`entailler`
			// abaisse la falaise à l'écran, et c'est le seul retour visuel de
			// l'irréversible), sinon la pente du profil local. Cf. HauteurFaceCm.
			float facePx = HauteurFaceCm(s) * WorldView.PxPerCmZ;
			// Nombre de strates de roche empilées sur la face (pente serrée = plus).
			int strates = s.Pente switch
			{
				PenteFalaise.Douce      => 3,
				PenteFalaise.Verticale  => 4,
				_                       => 5,
			};
			Color[] rampe = { Palette16.RocheOmbre, Palette16.RocheMedian, Palette16.RocheClair };
			float dFront  = AmplitudeCm + DepthCm * 0.15f;   // pied de la face (bord jardin)
			float ombreW  = DepthCm * 0.08f;                 // largeur d'ombre au pied
			Color ombreCol = Assombrir(Palette16.RocheOmbre, -0.25f);
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			// Front SINUEUX partagé (jamais une droite) : même ondulation pour l'ombre,
			// la face et le plateau → un seul bord cohérent qui serpente.
			float Wob(float u) => AmplitudeCm * 0.4f * Ondulation(s.SeedSecteur, u / 120f);

			// 1) OMBRE PORTÉE au pied, côté jardin (depth < dFront) : le surplomb.
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				Bande(s.Cote, u0, u1, dFront - ombreW + Wob(u0), dFront - ombreW + Wob(u1),
					  dFront + Wob(u0), dFront + Wob(u1), ombreCol);
			}
			// 2) PLATEAU VÉGÉTALISÉ élevé de la hauteur de face : recule en profondeur
			//    (DecorRocheHaut). C'est le SOMMET — il coiffe la face plus haut à l'écran.
			Vector2 up = new Vector2(0f, -facePx);
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				Vector2 p0 = EdgePoint(s.Cote, u0, dFront + Wob(u0)) + up;
				Vector2 p1 = EdgePoint(s.Cote, u1, dFront + Wob(u1)) + up;
				Vector2 p2 = EdgePoint(s.Cote, u1, dFront + DepthCm * 0.55f + Wob(u1)) + up;
				Vector2 p3 = EdgePoint(s.Cote, u0, dFront + DepthCm * 0.55f + Wob(u0)) + up;
				DrawColoredPolygon(new[] { p0, p1, p2, p3 }, Palette16.DecorRocheHaut);
			}
			// 3) FACE VERTICALE stratifiée : chaque strate = une tranche de hauteur du
			//    pied (dFront, au sol) vers le sommet (dFront + up), teinte alternée →
			//    bandes de roche contrastées qui font lire le relief (base la + sombre).
			for (int k = 0; k < strates; k++)
			{
				Vector2 upA = new Vector2(0f, -facePx * k / strates);
				Vector2 upB = new Vector2(0f, -facePx * (k + 1) / strates);
				Color col = rampe[k % 3];
				for (int i = 0; i < steps; i++)
				{
					float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
					Vector2 g0 = EdgePoint(s.Cote, u0, dFront + Wob(u0));
					Vector2 g1 = EdgePoint(s.Cote, u1, dFront + Wob(u1));
					DrawColoredPolygon(new[] { g0 + upA, g1 + upA, g1 + upB, g0 + upB }, col);
				}
			}
			// 4) ÉBOULIS : taches claires (RocheClair) jonchant le pied de la face,
			//    semis déterministe hashé (densité modérée, jamais de Random). DÉTAIL
			//    FIN (taches 1-2 px) → seulement à zoom ≥ DetailZoom ; la face
			//    stratifiée + l'ombre au pied portent le surplomb au dézoom.
			if (!DetailsVisibles) return;
			// Densité d'éboulis : ~42 % des pas au repos, jusqu'à ~82 % quand la
			// roche a été ENTAILLÉE (la cicatrice se lit au pied de la face, et
			// l'érosion qu'elle nourrit dans le sol du jardin en est la conséquence
			// moteur — cf. bordure.tick_erosion).
			uint seuilEboulis = SeuilEboulis(s);
			for (int i = 0; i < steps; i++)
			{
				uint hh = HashKey($"eboul|{s.SeedSecteur}|{i}");
				if (hh % 100u >= seuilEboulis) continue;
				float u = i * StepCm + ((hh >> 6 & 0xff) / 255f) * StepCm;
				if (u < 0f || u > WorldView.WorldCm) continue;
				float d = dFront - ombreW * ((hh >> 3 & 7u) / 7f);
				DrawCircle(EdgePoint(s.Cote, u, d + Wob(u)), 1.5f + (hh & 1u), Palette16.RocheClair);
			}
		}

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
				DrawCircle(EdgePoint(s.Cote, u, depth), 1.5f, c);
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
			Motif.Riviere => (Palette16.DecorEauBerge, Palette16.DecorEau),
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
