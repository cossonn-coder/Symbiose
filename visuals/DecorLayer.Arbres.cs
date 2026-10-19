// SYMBIOSE — DecorLayer.Arbres.cs (T5 RENDU AMBIANCE — silhouettes d'arbres du décor)
// Le MOTIF « forêt » du backdrop (docs/rendu/ambiance/conception_rendu_ambiance.md §5.2).
// Partial de DecorLayer : sépare la RESPONSABILITÉ « arbres adultes » du reste du
// décor (eau/roche/prairie, dans DecorLayer.cs) — un fichier reste lisible d'un
// regard (garde-fou taille).
//
// 📖 Pédagogie — POURQUOI des silhouettes peintes et PAS la structure PlantRenderer :
// le décor peut compter des CENTAINES d'arbres ; les rendre en segments (branches
// individuelles, morphogénèse) écraserait le budget qu'on vient de gagner au sprint
// perf du 2026-07-09. Ici un arbre = tronc + houppier « nuage » = quelques
// primitives, dessinées UNE fois (statique, jamais re-_Draw par frame — le vent est
// exclu, dette D72), cullables. L'arbre est ADULTE par CONSTRUCTION : pas d'âge, pas
// de croissance — son rayon de houppier EST sa taille adulte (table TreeSilhouette).
//
// 📖 Pédagogie — le GRADIENT de lisière (bord clairsemé → cœur dense) :
// on échantillonne la bande de forêt en une grille (u le long du bord, depth vers le
// fond). Chaque cellule tire un hash stable ; la PROBABILITÉ de poser un arbre CROÎT
// avec la profondeur (bord = pionniers rares, cœur = futaie dense). Le CHOIX d'essence
// suit aussi la profondeur : bouleau (pionnier clair) au bord, chêne/hêtre au fond.
// Zéro Random (philo #3) — tout dérive de SeedSecteur.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Port d'arbre adulte — l'archétype de silhouette (table par essence).
		private enum TreePort { Etale, Ovoide, Elance, Sinueux, Conique }

		// Le gabarit d'une essence du décor : son port, ses teintes, sa taille
		// adulte (rayon de houppier en cm monde) et la hauteur de tronc.
		private readonly struct TreeSilhouette
		{
			public readonly TreePort Port;
			public readonly Color Feuillage;
			public readonly Color Ecorce;
			public readonly float CanopyRadiusCm;   // rayon de houppier ADULTE
			public readonly float TrunkHeightCm;    // hauteur de fût sous le houppier
			public TreeSilhouette(TreePort port, Color feuillage, Color ecorce,
								  float canopyCm, float trunkCm)
			{
				Port = port; Feuillage = feuillage; Ecorce = ecorce;
				CanopyRadiusCm = canopyCm; TrunkHeightCm = trunkCm;
			}
		}

		// Table C# des essences (clé = nom d'espèce, contrat partagé avec T1).
		// Chêne/sapin/noyer préexistants + hêtre/bouleau/charme ajoutés en T1.
		private static readonly System.Collections.Generic.Dictionary<string, TreeSilhouette> Silhouettes = new()
		{
			["chene"]   = new(TreePort.Etale,   Palette16.FeuillageChene,   Palette16.EcorceBrune,   340f, 220f),
			["hetre"]   = new(TreePort.Ovoide,  Palette16.FeuillageHetre,   Palette16.EcorceBrune,   300f, 300f),
			["bouleau"] = new(TreePort.Elance,  Palette16.FeuillageBouleau, Palette16.EcorceBouleau, 170f, 300f),
			["charme"]  = new(TreePort.Sinueux, Palette16.FeuillageCharme,  Palette16.EcorceBrune,   230f, 200f),
			["sapin"]   = new(TreePort.Conique, Palette16.FeuillageSapin,   Palette16.EcorceBrune,   210f, 120f),
			["noyer"]   = new(TreePort.Etale,   Palette16.FeuillageChene,   Palette16.EcorceBrune,   300f, 240f),
			// Essences de RIPISYLVE (D73 ①/⑥) : le moteur peut donner `aulne` ou
			// `saule` comme dominante d'une lisière qui touche une rivière. Sans
			// entrée ici, elles ne pourraient jamais être rendues. Teintes reprises
			// du registre existant (aucune couleur neuve à la palette) : l'aulne
			// dressé et sombre, le saule clair et sinueux (port pleureur, cf. son
			// `gravitropism_gain` côté moteur).
			["aulne"]   = new(TreePort.Ovoide,  Palette16.FeuillageCharme,  Palette16.EcorceBrune,   250f, 260f),
			["saule"]   = new(TreePort.Sinueux, Palette16.FeuillageBouleau, Palette16.EcorceBrune,   280f, 180f),
		};

		// Peuple un secteur « forêt » : scatter d'arbres en gradient de lisière,
		// trié par profondeur (les proches masquent les lointains). Chaque cellule
		// d'une grille (u × depth) tire son occupation et son essence par hash.
		private void DrawForet(Secteur s)
		{
			// Grille d'échantillonnage : pas assez fin pour une futaie crédible,
			// assez grossier pour rester quelques centaines d'arbres au plus.
			const float cellU = 130f, cellDepth = 150f;
			int nU = Mathf.CeilToInt(WorldView.WorldCm / cellU);
			int nD = Mathf.CeilToInt(DepthCm / cellDepth);
			// On collecte d'abord (base monde, essence, taille) pour trier par Y
			// ÉCRAN avant de peindre (peintre : lointain d'abord).
			var arbres = new System.Collections.Generic.List<(Vector2 basePos, TreeSilhouette sil, float scale)>();
			// État MOTEUR du secteur (D73 ⑦) : la densité règle COMBIEN d'arbres se
			// posent, la hauteur de canopée règle leur TAILLE. Hors pont, les deux
			// facteurs valent 1 → le semis d'avant, au pixel près. C'est ici que le
			// geste du joueur devient visible : une clairière abattue s'éclaircit,
			// une trogne étêtée garde ses arbres mais les rabat.
			float kDensite = FacteurDensite(s);
			float kTaille = FacteurTaille(s);
			if (kDensite <= 0f || kTaille <= 0f) return;   // secteur rase : rien à peindre
			for (int iu = 0; iu < nU; iu++)
			for (int id = 0; id < nD; id++)
			{
				uint h = HashKey($"tree|{s.SeedSecteur}|{iu}|{id}");
				// Profondeur normalisée 0 (bord jardin) → 1 (fond). La densité
				// CROÎT vers le fond : proba d'occupation = 0.25 au bord → 0.92 au cœur.
				float dn = nD > 1 ? id / (float)(nD - 1) : 0f;
				float proba = Mathf.Lerp(0.25f, 0.92f, dn) * kDensite;
				if (h % 1000u / 1000f > proba) continue;
				// Jitter de position DANS la cellule (déterministe, jamais aligné).
				float ju = (h >> 4 & 0xff) / 255f - 0.5f;
				float jd = (h >> 12 & 0xff) / 255f - 0.5f;
				float u = (iu + 0.5f + ju * 0.8f) * cellU;
				float depth = (id + 0.5f + jd * 0.8f) * cellDepth + AmplitudeCm;
				if (u < 0f || u > WorldView.WorldCm) continue;
				// Essence : la DOMINANTE du moteur (décision D-4, un secteur porte
				// une essence, pas une flore) sur les deux tiers du semis, le
				// gradient de profondeur historique pour le reste — une lisière
				// d'aulnes reste mêlée, elle n'est pas une plantation. Sans
				// dominante (friche, repli local) : gradient seul, inchangé.
				string esp = EssenceDominante(s, h) ?? PickEssence(h, dn);
				// Taille : ±20 % autour de l'adulte (hétérogénéité, philo #7),
				// mise à l'échelle de la canopée réelle du secteur.
				float scale = (0.8f + (h >> 20 & 0xff) / 255f * 0.4f) * kTaille;
				arbres.Add((EdgePoint(s.Cote, u, depth), Silhouettes[esp], scale));
			}
			arbres.Sort((a, b) => a.basePos.Y.CompareTo(b.basePos.Y));
			foreach (var (basePos, sil, scale) in arbres)
				DrawArbre(basePos, sil, scale);
		}

		// L'essence DOMINANTE du secteur (moteur), ou null s'il n'y en a pas / si le
		// gabarit est inconnu de la table (moteur plus récent que la vue → on ne
		// crashe pas, on retombe sur le gradient). Deux tiers des sujets la portent :
		// une dominante n'est pas une monoculture.
		private static string EssenceDominante(Secteur s, uint h)
		{
			if (!s.DuPont || s.Essence == null) return null;
			if ((h >> 28 & 3u) == 0u) return null;            // ~25 % de mélange
			return Silhouettes.ContainsKey(s.Essence) ? s.Essence : null;
		}

		// Choix d'essence pondéré par la profondeur normalisée dn ∈ [0,1].
		private static string PickEssence(uint h, float dn)
		{
			int roll = (int)(h >> 24 & 0xff);   // 0..255, indépendant de l'occupation
			// Accents constants (~20 %) : sapin + charme, partout.
			if (roll < 12) return "sapin";
			if (roll < 30) return "charme";
			// Le reste : bouleau dominant au bord, chêne/hêtre au fond.
			float pBouleau = Mathf.Lerp(0.75f, 0.10f, dn);
			float r = (roll - 30) / 225f;
			if (r < pBouleau) return "bouleau";
			return (roll & 1) == 0 ? "chene" : "hetre";
		}

		// Un arbre = tronc fuselé + houppier (amas d'ellipses volumées). Tout en
		// px ÉCRAN : la base vient de WorldToScreen (suit la rotation D35), la
		// hauteur/rayon montent en px via PxPerCmZ (échelle iso verticale).
		private void DrawArbre(Vector2 basePos, TreeSilhouette sil, float scale)
		{
			float trunkH = sil.TrunkHeightCm * WorldView.PxPerCmZ * scale;
			float canopyR = sil.CanopyRadiusCm * WorldView.PxPerCmX * scale;
			Vector2 apex = basePos + Vector2.Up * trunkH;   // collet du houppier
			// -- Ombre portée au pied : ellipse aplatie au sol (T1). Décolle la
			// masse du plan-sol. Peinte AVANT tronc/houppier de CET arbre ; le tri
			// par Y de DrawForet fait que le proche recouvre proprement.
			DrawOmbrePied(basePos, canopyR);
			// -- Tronc : fuseau brun (2 quads triangulaires), largeur ~ rayon/6.
			float wTrunk = Mathf.Max(2f, canopyR * 0.16f);
			DrawTronc(basePos, apex, wTrunk, sil);
			// -- Houppier par port (les blobs sont hashés sur la base de l'arbre).
			uint hb = HashKey($"canopy|{Mathf.RoundToInt(basePos.X)}|{Mathf.RoundToInt(basePos.Y)}");
			DrawHouppier(apex, canopyR, sil, hb);
		}

		// Tronc fuselé : un trapèze (large au sol, fin au houppier). Écorce du
		// bouleau = blanche + chevrons sombres (lenticelles), sinon brun uni.
		private void DrawTronc(Vector2 basePos, Vector2 apex, float w, TreeSilhouette sil)
		{
			Vector2 bl = basePos + Vector2.Left * w;
			Vector2 br = basePos + Vector2.Right * w;
			Vector2 al = apex + Vector2.Left * w * 0.5f;
			Vector2 ar = apex + Vector2.Right * w * 0.5f;
			_lot.Polygone(new[] { bl, br, ar, al }, sil.Ecorce);
			// Chevrons (lenticelles) = DÉTAIL FIN (traits 1.5 px) → seulement à zoom
			// ≥ DetailZoom ; au dézoom le tronc blanc du bouleau suffit à le distinguer.
			if (sil.Port == TreePort.Elance && DetailsVisibles)   // bouleau : chevrons sombres
			{
				int chevrons = Mathf.Max(2, (int)((basePos.Y - apex.Y) / 14f));
				for (int k = 1; k < chevrons; k++)
				{
					float t = k / (float)chevrons;
					Vector2 c = basePos.Lerp(apex, t);
					_lot.Ligne(c + Vector2.Left * w * 0.6f, c + Vector2.Right * w * 0.2f,
							 Palette16.EcorceLenticelle, 1.5f);
				}
			}
		}

		// Houppier « nuage » : amas d'ellipses volumées (2 valeurs) selon le port.
		// Le port règle la forme de l'enveloppe (dôme large, œuf, cône étagé…).
		private void DrawHouppier(Vector2 apex, float r, TreeSilhouette sil, uint hb)
		{
			var col = sil.Feuillage;
			switch (sil.Port)
			{
				case TreePort.Conique:   // sapin : étages triangulaires décroissants
					for (int e = 0; e < 4; e++)
					{
						float t = e / 4f;
						Vector2 c = apex + Vector2.Up * (r * 1.4f * t);
						DrawVolumeBlob(c, r * (1f - t * 0.7f), r * 0.45f, col, hb + (uint)e);
					}
					break;
				case TreePort.Elance:    // bouleau : houppier léger, ouvert, haut
					DrawBlobCloud(apex + Vector2.Up * r * 0.5f, r * 0.85f, r * 1.1f, 5, col, hb);
					break;
				case TreePort.Ovoide:    // hêtre : œuf dense, dressé
					DrawBlobCloud(apex + Vector2.Up * r * 0.7f, r * 0.9f, r * 1.25f, 8, col, hb);
					break;
				case TreePort.Sinueux:   // charme : masse moyenne irrégulière
					DrawBlobCloud(apex + Vector2.Up * r * 0.4f, r * 1.0f, r * 0.9f, 7, col, hb);
					break;
				default:                 // Etale (chêne/noyer) : dôme large et bas
					DrawBlobCloud(apex + Vector2.Up * r * 0.35f, r * 1.25f, r * 0.85f, 9, col, hb);
					break;
			}
			// Silhouette de cime : UN accent clair au sommet de l'enveloppe (T1)
			// — bord bosselé lisible contre le jardin. Hauteur du sommet par port.
			float cimeUp = sil.Port switch
			{
				TreePort.Conique => 1.55f,   // pointe du sapin
				TreePort.Elance  => 1.35f,   // bouleau haut et ouvert
				TreePort.Ovoide  => 1.55f,   // hêtre dressé
				TreePort.Sinueux => 1.05f,   // charme
				_                => 0.95f,   // étalé (chêne/noyer)
			};
			DrawCimeAccent(apex + Vector2.Up * r * cimeUp, r * 0.42f, col);
		}

		// Un « nuage » de N blobs volumés répartis dans une enveloppe (rx, ry)
		// autour d'un centre. Placement/rayon par hash (jamais Random).
		private void DrawBlobCloud(Vector2 center, float rx, float ry, int n, Color col, uint seed)
		{
			for (int i = 0; i < n; i++)
			{
				uint h = seed * 2654435761u + (uint)i * 40503u;
				float ang = (h & 0xffff) / 65535f * Mathf.Tau;
				float rad = ((h >> 16 & 0xff) / 255f) * 0.7f;
				Vector2 c = center + new Vector2(Mathf.Cos(ang) * rx * rad,
												 -Mathf.Sin(ang) * ry * rad);
				float br = rx * (0.42f + (h >> 24 & 0xff) / 255f * 0.28f);
				DrawVolumeBlob(c, br, br * 0.82f, col, h);
			}
		}

		// Ellipse volumée LOCALE (2 valeurs) — masse d'ombre froide + calotte
		// éclairée décalée vers le bas (sud iso). Réplique l'invariant pixel-art de
		// PlantRenderer.DrawVolumeEllipse, en STATIC (le décor n'a pas d'instance
		// PlantRenderer). `h` ne sert qu'à un micro-jitter de valeur (grain).
		private void DrawVolumeBlob(Vector2 c, float rx, float ry, Color col, uint h)
		{
			float grain = ((h & 0x3f) / 63f - 0.5f) * 0.08f;
			// Marches FRANCHES (T1) : masse ×0.75 / calotte ×1.25 (bornes Assombrir)
			// au lieu de ±15 % — le volume se lit. Calotte décalée vers le SO
			// (bas+ouest écran = soleil commun aux plantes et à la maison).
			_lot.Ellipse(c, rx, ry, Assombrir(col, -0.25f + grain));
			_lot.Ellipse(c + Vector2.Down * ry * 0.32f + Vector2.Left * rx * 0.18f,
						rx * 0.66f, ry * 0.66f, Assombrir(col, 0.30f + grain));
		}

		// Ombre portée au sol d'un arbre : ellipse très aplatie et sombre au
		// pied (T1). Teinte = fond forêt fortement assombri (bornée par Assombrir).
		// Légèrement décalée vers le NE (soleil au SO) pour lire le sens de lumière.
		private void DrawOmbrePied(Vector2 basePos, float canopyR)
		{
			Vector2 c = basePos + Vector2.Up * canopyR * 0.06f + Vector2.Right * canopyR * 0.10f;
			_lot.Ellipse(c, canopyR * 0.70f, canopyR * 0.22f,
						Assombrir(Palette16.DecorForetFond, -0.30f));
		}

		// Accent de cime : petite calotte très claire au sommet du houppier (T1).
		// La calotte du volume plafonne à ×1.25 (Assombrir borné) ; pour une VRAIE
		// skyline on tire le feuillage vers DecorForetCime (vert au soleil), en
		// gardant un reste de la teinte d'essence (Lerp 0.7). Un seul par houppier.
		private void DrawCimeAccent(Vector2 sommet, float rc, Color col)
		{
			_lot.Ellipse(sommet, rc, rc * 0.70f, col.Lerp(Palette16.DecorForetCime, 0.70f));
		}
	}
}
