// SYMBIOSE — DecorLayer.Aplats.cs (FLUIDITÉ PC ④ — rivière et falaise d'AVANT, conservées)
// Partial de DecorLayer : les tracés en APLATS de la rivière (T2) et de la falaise
// (T3), remplacés au tronçon ④ par leurs versions en pièces du kit
// (DecorLayer.Eau.cs, DecorLayer.Roche.cs). ⚠️ CONSERVÉS, plus appelés : référence
// de comparaison (règle « on ne jette pas de code »), comme DrawSecteur/DrawPrairie.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// RIVIÈRE : une surface d'eau CREUSÉE dans le terrain (T2). Berges franches
		// de galets de part et d'autre du lit, eau à 2 valeurs par damier hashé
		// ORDONNÉ (frémissement, jamais de dégradé), liseré d'ombre le long des deux
		// rives (creuse le lit, décolle la surface du plan-sol comme l'ombre T1), et
		// reflets = STREAKS clairs orientés dans le sens du COURANT (la tangente de
		// l'axe sinueux du lit). Zéro Random (hash + 3-sinus, philo #3).
		private void DrawRiviereAplats(Secteur s)
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
				// -- Ombre de berge : liseré d'eau plus sombre le long des deux rives.
				// Liserés et eau JOINTIFS, jamais empilés (FLUIDITÉ PC ② : un bord à
				// demi recouvert se lit en pointillé une fois les sommets arrondis au
				// pixel — cf. DrawSecteur).
				Bande(s.Cote, u0, u1, ax0 - half + liseré, ax1 - half + liseré, ax0, ax1, eauA);
				Bande(s.Cote, u0, u1, ax0, ax1, ax0 + half - liseré, ax1 + half - liseré, eauB);
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
					_lot.Ligne(mid - flow, mid + flow, Palette16.EauReflet, 2.5f);
				}
			}
		}

		// FALAISE : un ressaut rocheux qui SURPLOMBE le jardin (T3). Plus des redans
		// à plat : une vraie FACE VERTICALE montée en −Y écran (comme un mur de
		// maison, cf. WorldView.Maison upWall), STRATIFIÉE en 3 valeurs de roche
		// dures, coiffée d'un PLATEAU végétalisé lui aussi élevé, avec une ombre
		// portée au pied (le surplomb) et un semis d'ÉBOULIS clairs à la base. La
		// hauteur de la face dérive de la PENTE (Douce basse → Déversante haute).
		// NON forcée : le seed décide de sa présence (philo #7) — on la rend juste
		// lisible quand elle paraît. Déterministe (hash + 3-sinus, zéro Random, #3).
		private void DrawFalaiseAplats(Secteur s)
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
				_lot.Polygone(new[] { p0, p1, p2, p3 }, Palette16.DecorRocheHaut);
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
					_lot.Polygone(new[] { g0 + upA, g1 + upA, g1 + upB, g0 + upB }, col);
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
				_lot.Cercle(EdgePoint(s.Cote, u, d + Wob(u)), 1.5f + (hh & 1u), Palette16.RocheClair);
			}
		}
	}
}
