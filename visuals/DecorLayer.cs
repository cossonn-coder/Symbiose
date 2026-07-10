// SYMBIOSE — DecorLayer.cs (T4 RENDU AMBIANCE — décor d'ambiance : OSSATURE)
// Le BACKDROP cosmétique AUTOUR du jardin (docs/conception/CONCEPTION_RENDU_AMBIANCE.md
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
// 📖 Pédagogie — la COUTURE d'extensibilité (SurroundingsProfile) :
// aujourd'hui le profil est calculé C#-depuis-seed (repli par défaut). Demain le
// pont pourra livrer la friche périphérique / les extensions par maîtrise : il
// suffira d'un second constructeur BuildFromBridge(...) alimentant la MÊME struct,
// sans toucher au rendu. Le point d'entrée unique est BuildProfile(seed). On ne
// câble PAS le pont ici (cosmétique — dette D73 terraforming).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Les 4 motifs possibles d'un secteur autour du jardin. Prairie = défaut.
		public enum Motif { Prairie, Foret, Riviere, Falaise }
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

		private SurroundingsProfile _profile;
		private bool _built;

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
			_profile = BuildProfile(seed);
			_built = true;
			QueueRedraw();
		}

		private bool _lastZoomOk;

		public override void _Process(double delta)
		{
			if (!Visible || !_built) return;
			// Inerte : on ne redessine qu'au basculement du LOD (apparaît au dézoom).
			bool zoomOk = WorldView.CurrentZoom <= MaxZoom;
			if (zoomOk != _lastZoomOk)
			{
				_lastZoomOk = zoomOk;
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
			}
		}

		// -----------------------------------------------------------------------
		// MOTIFS DÉTAILLÉS (T5) — rivière (eau + reflets), falaise (redans étagés),
		// prairie (semis de fleurs). Tout en polygones/points cm MONDE → écran, donc
		// suit la rotation D35. Statique, cullé par le LOD global (comme l'ossature).
		// -----------------------------------------------------------------------

		// RIVIÈRE : une bande d'eau sinueuse au CŒUR de la bande (bordée de berges
		// herbeuses déjà posées par l'assise), semée de reflets clairs par un
		// dithering ORDONNÉ (damier hashé) — 2 teintes de palette, pas de dégradé.
		private void DrawRiviere(Secteur s)
		{
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			// Le lit occupe la moitié médiane de la profondeur (berges de part et
			// d'autre) ; son axe serpente d'un tracé sinueux propre (déphasé).
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				float ax0 = DepthCm * 0.5f + AmplitudeCm * Ondulation(s.SeedSecteur ^ 0x9e37u, u0 / 230f);
				float ax1 = DepthCm * 0.5f + AmplitudeCm * Ondulation(s.SeedSecteur ^ 0x9e37u, u1 / 230f);
				float half = DepthCm * 0.22f;
				Vector2 a0 = EdgePoint(s.Cote, u0, ax0 - half);
				Vector2 a1 = EdgePoint(s.Cote, u1, ax1 - half);
				Vector2 b1 = EdgePoint(s.Cote, u1, ax1 + half);
				Vector2 b0 = EdgePoint(s.Cote, u0, ax0 + half);
				DrawColoredPolygon(new[] { a0, a1, b1, b0 }, Palette16.EauProfonde);
				// Reflets : un point clair 1 case sur 2 (damier hashé) au fil de l'eau.
				uint hd = (uint)i * 2654435761u ^ s.SeedSecteur;
				if ((hd & 1u) == 0u)
				{
					float d = ax0 + (((hd >> 8) & 0xff) / 255f - 0.5f) * half;
					DrawCircle(EdgePoint(s.Cote, u0 + StepCm * 0.5f, d),
							   2f, Palette16.EauReflet);
				}
			}
		}

		// FALAISE : paroi ÉTAGÉE en redans (3 valeurs) ; le NOMBRE de redans traduit
		// la PENTE issue du profil (douce = large & peu étagée, déversante = serrée).
		// Sommet végétalisé déjà donné par l'assise (RocheHaut). Adjacente à la rivière.
		private void DrawFalaise(Secteur s)
		{
			int redans = s.Pente switch
			{
				PenteFalaise.Douce      => 3,
				PenteFalaise.Verticale  => 5,
				_                       => 7,   // déversante : gradins serrés
			};
			Color[] rampe = { Palette16.RocheOmbre, Palette16.RocheMedian, Palette16.RocheClair };
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			// Chaque redan = une bande le long de la profondeur, à sa valeur, avec un
			// front sinueux (jamais une droite) qui suit le tracé du secteur.
			for (int r = 0; r < redans; r++)
			{
				float d0 = AmplitudeCm + DepthCm * (0.15f + 0.7f * r / redans);
				float d1 = AmplitudeCm + DepthCm * (0.15f + 0.7f * (r + 1) / redans);
				Color col = rampe[r % 3];
				for (int i = 0; i < steps; i++)
				{
					float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
					float w0 = AmplitudeCm * 0.4f * Ondulation(s.SeedSecteur + (uint)r * 131u, u0 / 120f);
					float w1 = AmplitudeCm * 0.4f * Ondulation(s.SeedSecteur + (uint)r * 131u, u1 / 120f);
					Vector2 p0 = EdgePoint(s.Cote, u0, d0 + w0);
					Vector2 p1 = EdgePoint(s.Cote, u1, d0 + w1);
					Vector2 p2 = EdgePoint(s.Cote, u1, d1 + w1);
					Vector2 p3 = EdgePoint(s.Cote, u0, d1 + w0);
					DrawColoredPolygon(new[] { p0, p1, p2, p3 }, col);
				}
			}
		}

		// PRAIRIE : sur l'assise verte, un SEMIS déterministe de petites fleurs
		// (points blancs/jaunes), densité modérée, échantillonnage stable par hash.
		private void DrawPrairie(Secteur s)
		{
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
