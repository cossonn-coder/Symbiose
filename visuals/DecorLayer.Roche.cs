// SYMBIOSE — DecorLayer.Roche.cs (FLUIDITÉ PC ④ — la FALAISE de lisière en patchwork)
// Partial de DecorLayer : remplace la falaise en aplats (conservée dans
// DecorLayer.Aplats.cs) par une roche « en pièces » :
//   ombre portée au pied → PLATEAU élevé en parcelles → FACE en grille aux sommets
//   PARTAGÉS (strates × pas), chaque strate découpée en BLOCS (teinte par bloc +
//   joints verticaux sombres) → CONTOURS (pied sombre, lits de strate, lèvre
//   claire) → ÉBOULIS en pièces du kit (blocs anguleux, galets) au pied → touffes
//   sur la lèvre du plateau.
//
// 📖 Pédagogie — les 3 PENTES se lisent par la géométrie, pas par une couleur :
// chaque strate est décalée en profondeur de `recul` cm par rapport à celle du
// dessous. Douce : les strates RECULENT (gradins) ; verticale : aucun décalage ;
// déversante : elles AVANCENT vers le jardin (le haut surplombe le pied, et l'ombre
// portée s'élargit d'autant).
//
// 📖 Pédagogie — face CLAIRE / face d'OMBRE : le soleil vient du sud-ouest, dans le
// MONDE (il ne tourne pas avec la caméra D35). Une falaise au nord ou à l'est du
// jardin tourne sa face vers le sud / l'ouest → au soleil ; au sud ou à l'ouest,
// sa face regarde le nord / l'est → à l'ombre. Même rampe, décalée d'un cran.
//
// La hauteur (roche restante, `entailler`) et la densité d'éboulis (entaille
// cumulée, EntailleRefCm) viennent toujours du pont (DecorLayer.Pont.cs).

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private const float PasEboulisPx = 7f;   // px internes entre deux éboulis

		private void DrawFalaise(Secteur s)
		{
			float facePx = HauteurFaceCm(s) * WorldView.PxPerCmZ;
			(int strates, float recul) = s.Pente switch
			{
				PenteFalaise.Douce     => (3, 70f),
				PenteFalaise.Verticale => (4, 0f),
				_                      => (5, -35f),
			};
			bool claire = s.Cote == 0 || s.Cote == 1;
			Color[] rampe = claire
				? new[] { Palette16.RocheMedian, Palette16.RocheClair, Assombrir(Palette16.RocheClair, 0.06f) }
				: new[] { Palette16.RocheOmbre, Assombrir(Palette16.RocheMedian, -0.10f), Palette16.RocheMedian };
			float dFront = AmplitudeCm + DepthCm * 0.15f;
			float ombreW = DepthCm * 0.08f + Mathf.Max(0f, -recul * strates);
			float dTop = dFront + recul * strates;
			float Wob(float u) => AmplitudeCm * 0.4f * Ondulation(s.SeedSecteur, u / 120f);
			int steps = Mathf.CeilToInt(WorldView.WorldCm / StepCm);
			float z = ZoomConstr, trait = 1f / z;

			// 1) OMBRE PORTÉE au pied, côté jardin.
			Color ombreCol = Assombrir(Palette16.RocheOmbre, -0.25f);
			for (int i = 0; i < steps; i++)
			{
				float u0 = i * StepCm, u1 = Mathf.Min(u0 + StepCm, WorldView.WorldCm);
				Bande(s.Cote, u0, u1, dFront - ombreW + Wob(u0), dFront - ombreW + Wob(u1),
					  dFront + Wob(u0), dFront + Wob(u1), ombreCol);
			}
			// Grilles aux sommets partagés : face (strates + 1 rangs) et plateau (4 rangs).
			var face = new Vector2[steps + 1, strates + 1];
			var plat = new Vector2[steps + 1, 4];
			Vector2 up = new Vector2(0f, -facePx);
			for (int i = 0; i <= steps; i++)
			{
				float u = Mathf.Min(i * StepCm, WorldView.WorldCm), w = Wob(u);
				for (int k = 0; k <= strates; k++)
					face[i, k] = EdgePoint(s.Cote, u, dFront + w + recul * k) + up * k / strates;
				for (int r = 0; r < 4; r++)
					plat[i, r] = EdgePoint(s.Cote, u, dTop + w + DepthCm * 0.55f * r / 3f) + up;
			}
			float[] ecarts = { -0.06f, -0.02f, 0.02f, 0.06f };
			// 2) PLATEAU végétalisé, en parcelles (3 pas × 1 rang).
			for (int i = 0; i < steps; i++)
				for (int r = 0; r < 3; r++)
				{
					uint hp = HashCase(s.SeedSecteur, i / 3, r, 51u);
					_lot.PolygoneConvexe(new[] { plat[i, r], plat[i + 1, r], plat[i + 1, r + 1], plat[i, r + 1] },
										 Assombrir(Palette16.DecorRocheHaut, ecarts[hp & 3u]));
				}
			// 3) FACE : strate k = valeur de base (le pied le plus sombre), découpée
			//    en BLOCS de 1-3 pas, chaque bloc décalé d'un écart de valeur.
			for (int k = 0; k < strates; k++)
			{
				Color baseK = rampe[Mathf.Min(2, k * 3 / strates)];
				uint hb = HashCase(s.SeedSecteur, 0, k, 53u);
				int bloc = 1 + (int)(hb >> 8 & 1u) + (int)(hb >> 9 & 1u);
				for (int i = 0; i < steps; i++)
				{
					if (i > 0 && --bloc <= 0)
					{
						hb = HashCase(s.SeedSecteur, i, k, 53u);
						bloc = 1 + (int)(hb >> 8 & 1u) + (int)(hb >> 9 & 1u);
						// Joint vertical sombre entre deux blocs.
						_lot.Ligne(face[i, k], face[i, k + 1], Assombrir(rampe[0], -0.22f), trait);
					}
					_lot.PolygoneConvexe(new[] { face[i, k], face[i + 1, k], face[i + 1, k + 1], face[i, k + 1] },
										 Assombrir(baseK, ecarts[hb & 3u]));
				}
			}
			// 4) CONTOURS : pied sombre, lits de strate (trait d'ombre), lèvre claire.
			Color lit = Assombrir(rampe[0], -0.15f);
			for (int i = 0; i < steps; i++)
			{
				_lot.Ligne(face[i, 0], face[i + 1, 0], Assombrir(Palette16.RocheOmbre, -0.25f), trait);
				for (int k = 1; k < strates; k++)
					_lot.Ligne(face[i, k], face[i + 1, k], lit, trait);
				_lot.Ligne(face[i, strates], face[i + 1, strates], Palette16.RocheClair, trait);
			}
			DrawEboulis(s, dFront, ombreW, Wob);
			DrawLevre(s, dTop, up, Wob);
		}

		// ÉBOULIS : blocs anguleux près de la face, galets plus loin, en pièces du kit.
		// Part des pas jonchés = SeuilEboulis (42 % au repos → 82 % sur roche
		// entaillée) : la cicatrice d'`entailler` se lit au pied.
		private void DrawEboulis(Secteur s, float dFront, float ombreW, System.Func<float, float> wob)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm, PasEboulisPx / (z * WorldView.PxPerCmX));
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			uint seuil = SeuilEboulis(s);
			_poses.Clear();
			for (int iu = 0; iu < nU; iu++)
				for (int rang = 0; rang < 2; rang++)
				{
					uint h = HashCase(s.SeedSecteur, iu, rang, 55u);
					if (h % 100u >= seuil) continue;
					float u = (iu + 0.5f + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					if (u < 0f || u > WorldView.WorldCm) continue;
					float t = (h >> 16 & 0xff) / 255f;
					t = t * t;                                             // amassés contre la face
					float d = dFront - ombreW * 1.2f * (rang == 0 ? t * 0.5f : 0.4f + t * 0.6f);
					bool bloc = rang == 0 && (h >> 24 & 3u) != 0u;
					Piece f = bloc ? Piece.Bloc : Piece.Galet;
					Teinte te = (h >> 26 & 1u) == 0u ? Teinte.Roche : Teinte.RocheClaire;
					_poses.Add(new Pose(EdgePoint(s.Cote, u, d + wob(u)), f, TailleZoom(f, bloc ? 0 : -1),
										Melange(h), te, Colors.White));
				}
			PoserTriees(_poses);
		}

		// LÈVRE et DESSUS du plateau : herbe rase et quelques ronciers serrés sur la
		// lèvre (sa bordure se lit en silhouette), puis un semis plus lâche d'herbe
		// sèche et de cailloux sur le plateau — jamais d'aplat uni.
		private void DrawLevre(Secteur s, float dTop, Vector2 up, System.Func<float, float> wob)
		{
			float z = ZoomConstr;
			float pas = Mathf.Max(PasTouffeMinCm, 1.5f * PasTouffePx / (z * WorldView.PxPerCmX));
			int nU = Mathf.CeilToInt(WorldView.WorldCm / pas);
			_poses.Clear();
			int rang = 0;
			for (float dd = 10f; dd < DepthCm * 0.55f; rang++)
			{
				bool levre = dd < 100f;
				for (int iu = 0; iu < nU; iu++)
				{
					uint h = HashCase(s.SeedSecteur, iu, rang, 57u);
					if ((h & 0xff) > (levre ? 150u : 70u)) continue;
					float u = (iu + 0.5f + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
					if (u < 0f || u > WorldView.WorldCm) continue;
					float d = dTop + dd + ((h >> 16 & 0xff) / 255f) * pas;
					int roll = (int)(h >> 24 & 7u);
					Piece f = roll == 0 ? (levre ? Piece.Roncier : Piece.Galet) : Piece.Herbe;
					Teinte te = f == Piece.Roncier ? Teinte.Roncier : f == Piece.Galet ? Teinte.RocheClaire
							  : roll < 5 ? Teinte.Paille : Teinte.Prairie;
					_poses.Add(new Pose(EdgePoint(s.Cote, u, d + wob(u)) + up, f, TailleZoom(f, -1), Melange(h),
										te, Colors.White));
				}
				dd += levre ? pas : pas * 2.5f;
			}
			PoserTriees(_poses);
		}
	}
}
