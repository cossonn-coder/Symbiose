// SYMBIOSE — HouseNode.cs (T3 RENDU AMBIANCE, sprint D58)
// RENDU PROCÉDURAL de la maison normande de granite + ardoise (réf. Nico,
// maçon-couvreur du Cotentin). Remplace le placeholder gris pyramidal de
// WorldView.Monde : ici on PEINT la pierre (moellons + joints chaux + chaînages
// d'angle + encadrements de baies), le PIGNON essenté d'ardoise, le TOIT en 2
// pans pentus d'ardoise (rangs d'écailles + lucarne à bâtière), les OUVERTURES
// (porte + fenêtres à petits carreaux) et la souche de CHEMINÉE en brique.
//
// 📖 POURQUOI un Node2D dédié à _Draw (et non 40 Polygon2D enfants) : le détail
// (grain de moellon, écailles d'ardoise, croisillons de fenêtre) se compte en
// centaines de primitives. Un `_Draw` immédiat les émet en UNE passe (un seul
// DrawMesh depuis PLANTE ASSEMBLÉE ②), statique
// (jamais rejoué par frame — cohérent avec l'exclusion du vent, D72), et se
// re-cuit seulement à la rotation D35 (WorldView.RebuildWorld). WorldView.Maison
// calcule la GÉOMÉTRIE (coins projetés, faîte, murs visibles + leur index
// mur-monde pour l'éclairement) et la POSE ici via Setup() ; ce nœud ne fait que
// rasteriser — aucune logique moteur, aucun RNG (philo #3), golden non concerné.
//
// 📖 PARAMÉTRAGE D'UNE FAÇADE (quad iso arbitraire) : une façade est un
// quadrilatère (bas-gauche B0, bas-droite B1, haut-droite B1+up, haut-gauche
// B0+up). On y peint en coordonnées (u,v) : u ∈ [0,1] le long du sol B0→B1, v
// ∈ [0,1] du sol vers le haut. QuadPoint(u,v) interpole → tout motif (assises de
// moellons, baies, essentage) se pose dans ce repère sans géométrie ad hoc, et
// suit donc la rotation D35 (les coins sont déjà projetés-orientés).

using Godot;

namespace Symbiose
{
	public partial class HouseNode : Node2D
	{
		// Géométrie posée par WorldView.Maison (coordonnées LOCALES au nœud,
		// ancré au coin avant). Les 4 coins bas + le vecteur "haut de mur" + le
		// faîte, plus l'index mur-monde de chaque arête (éclairement D35) et le
		// mur-monde OUEST (pignon essenté d'ardoise).
		private Vector2[] _corners;     // 4 coins au sol, cycle monde nw→ne→se→sw
		private Vector2 _upWall;        // vecteur vertical écran : sol → haut de mur
		private Vector2 _apexA, _apexB; // extrémités du FAÎTE (toit 2 pans + croupe)
		private int _front;             // coin avant (le plus bas écran) = ancrage
		private int _westWall;          // mur-monde ouest (0..3) → pignon essenté

		// Setup : appelé une fois par build (et par rotation). Déclenche _Draw.
		public void Setup(Vector2[] corners, Vector2 upWall, Vector2 apexA,
						  Vector2 apexB, int front, int westWall)
		{
			_corners = corners; _upWall = upWall;
			_apexA = apexA; _apexB = apexB;
			_front = front; _westWall = westWall;
			QueueRedraw();
		}

		// Hash déterministe → [0,1) : même mix xorshift que SolTexture/PlantRenderer
		// (un seul langage de bruit dans le rendu). Sert le grain des moellons et le
		// décalage des écailles d'ardoise — stable inter-frames et inter-sessions.
		private static float Hash01(int channel, int i, int j)
		{
			uint h = (uint)channel * 0x9E3779B1u
				   ^ (uint)i * 0x85EBCA77u ^ (uint)j * 0xC2B2AE3Du;
			h ^= h >> 15; h *= 0x2C1B3C6Du;
			h ^= h >> 12; h *= 0x297A2D39u;
			h ^= h >> 15;
			return (h & 0xFFFFFF) / 16777216f;
		}

		// Éclairement mur-monde (D35, cf. WorldView.Monde d'origine) : sud plein
		// soleil (clair), nord jamais éclairé (sombre), est/ouest intermédiaires et
		// distincts. On MODULE la valeur d'un matériau (granite/ardoise) au lieu de
		// dédoubler la palette par orientation. Index = mur monde : 0 N, 1 E, 2 S, 3 O.
		private static float WallLight(int worldWall) => worldWall switch
		{
			2 => 1.10f,   // sud : plein soleil
			1 => 0.92f,   // est
			3 => 0.84f,   // ouest
			_ => 0.72f,   // nord : à l'ombre
		};

		private static Color Lit(Color c, float f) => new Color(
			Mathf.Clamp(c.R * f, 0f, 1f), Mathf.Clamp(c.G * f, 0f, 1f),
			Mathf.Clamp(c.B * f, 0f, 1f), c.A);

		// PLANTE ASSEMBLÉE ② : chaque DrawColoredPolygon était UN draw call (~345 à
		// ×4 banc E s45 [VM, n=1] — l'essentiel de « Objects »). Les primitives vont
		// désormais dans un lot de triangles, dans le même ordre peintre, envoyé en
		// un seul DrawMesh (recette de LotTriangles.cs, ①).
		private readonly LotTriangles _lot = new();

		public override void _Draw()
		{
			if (_corners == null) return;
			_lot.Vider();

			int rightWall = (_front + 3) % 4;   // mur côté droit écran
			int leftWall  = _front;             // mur côté gauche écran

			// Ordre peintre : pans de toit ARRIÈRE d'abord (leur crête dépasse au
			// dessus des pans avant), puis les 2 murs visibles, puis pans avant +
			// faîtage + lucarne + cheminée par-dessus.
			DrawRoof(back: true);
			DrawWall(rightWall);
			DrawWall(leftWall);
			DrawRoof(back: false);
			DrawRidgeAndDormer();
			DrawChimney();
			_lot.Dessiner(this);
		}

		// Point d'une façade en coordonnées (u,v) : u le long du sol du mur w
		// (coin w → coin w+1), v du sol (0) vers le haut de mur (1).
		private Vector2 QuadPoint(int w, float u, float v)
		{
			Vector2 b0 = _corners[w], b1 = _corners[(w + 1) % 4];
			return b0.Lerp(b1, u) + _upWall * v;
		}

		// -------------------------------------------------------------------
		// MURS — moellons de granite + joints chaux + chaînages + baies
		// -------------------------------------------------------------------
		private void DrawWall(int w)
		{
			float light = WallLight(w);
			// Aplat de fond = joint chaux (les moellons se posent dessus → les
			// interstices restent clairs, lecture d'appareil de pierre).
			DrawQuad(w, 0f, 1f, 0f, 1f, Lit(Palette16.JointChaux, light));

			// Assises de moellons : ~5 rangs, moellons décalés d'un rang à l'autre
			// (appareil à joints croisés). Chaque moellon = un quad légèrement
			// rétréci (le joint chaux transparaît au pourtour). 2 valeurs + variété
			// rousse au hash → jamais d'aplat (E4).
			const int rows = 5, cols = 6;
			for (int r = 0; r < rows; r++)
			{
				float v0 = r / (float)rows, v1 = (r + 1) / (float)rows;
				float shift = (r % 2) * 0.5f / cols;   // décalage 1 rang sur 2
				for (int cc = -1; cc < cols; cc++)
				{
					float u0 = cc / (float)cols + shift;
					float u1 = u0 + 1f / cols;
					u0 = Mathf.Clamp(u0, 0f, 1f); u1 = Mathf.Clamp(u1, 0f, 1f);
					if (u1 - u0 < 0.02f) continue;
					float t = Hash01(1, r, cc + 2);
					Color stone = t < 0.28f ? Palette16.GraniteRoux
							   : t < 0.6f  ? Palette16.GraniteMurClair
										   : Palette16.GraniteMur;
					// Léger retrait (joint) : on rentre de ~6 % en u et v.
					DrawQuad(w, u0 + 0.02f, u1 - 0.02f, v0 + 0.03f, v1 - 0.03f,
							 Lit(stone, light));
				}
			}

			// Chaînages d'angle : bandes verticales de pierres harpées plus claires
			// aux DEUX arêtes du mur (granite clair, léger sur-éclairement).
			DrawQuad(w, 0f, 0.13f, 0f, 1f, Lit(Palette16.GraniteClair, light * 1.02f));
			DrawQuad(w, 0.87f, 1f, 0f, 1f, Lit(Palette16.GraniteClair, light * 1.02f));

			// Pignon ouest-monde : essentage d'ardoise (bardage d'écailles) jusqu'à
			// mi-hauteur, distinct du reste du mur (protège du vent d'ouest).
			if (w == _westWall)
				DrawGableCladding(w, light);
			else
				DrawOpenings(w, light);
		}

		// Essentage d'ardoise sur la moitié BASSE du pignon (petit motif d'écailles
		// 2 valeurs, rangs décalés) — signature du pignon exposé au vent d'ouest.
		private void DrawGableCladding(int w, float light)
		{
			const int rows = 6, cols = 10;
			DrawQuad(w, 0.13f, 0.87f, 0f, 0.5f, Lit(Palette16.ArdoiseSombre, light));
			for (int r = 0; r < rows; r++)
			{
				float v0 = 0.5f * r / rows, v1 = 0.5f * (r + 1) / rows;
				float shift = (r % 2) * 0.5f / cols;
				for (int cc = 0; cc < cols; cc++)
				{
					float u0 = 0.13f + 0.74f * (cc / (float)cols + shift);
					float u1 = u0 + 0.74f / cols;
					if (u1 > 0.87f) continue;
					Color a = Hash01(2, r, cc) < 0.5f
						? Palette16.Ardoise : Palette16.ArdoiseClair;
					DrawQuad(w, u0, u1 - 0.01f, v1 - 0.06f, v1, Lit(a, light));
				}
			}
		}

		// Ouvertures d'un mur : sur le mur SUD-monde une porte centrale + 2 fenêtres ;
		// sur les autres murs visibles, une paire de fenêtres. Petits carreaux
		// (croisillons), encadrement granite clair (jambages/linteau/appui à larmier).
		private void DrawOpenings(int w, float light)
		{
			if (w == 2)   // sud : porte + fenêtres
			{
				DrawDoor(w, 0.44f, 0.56f, 0.02f, 0.62f, light);
				DrawWindow(w, 0.16f, 0.30f, 0.28f, 0.66f, light);
				DrawWindow(w, 0.70f, 0.84f, 0.28f, 0.66f, light);
			}
			else
			{
				DrawWindow(w, 0.22f, 0.36f, 0.30f, 0.66f, light);
				DrawWindow(w, 0.64f, 0.78f, 0.30f, 0.66f, light);
			}
		}

		private void DrawWindow(int w, float u0, float u1, float v0, float v1, float light)
		{
			Color frame = Lit(Palette16.GraniteClair, light * 1.05f);
			DrawQuad(w, u0 - 0.02f, u1 + 0.02f, v0 - 0.03f, v1 + 0.03f, frame); // encadrement
			DrawQuad(w, u0, u1, v0, v1, Palette16.VitreSombre);                 // verre
			// Croisillons : 1 meneau + 1 traverse (petits carreaux), menuiserie sombre.
			float um = (u0 + u1) / 2f, vm = (v0 + v1) / 2f;
			DrawQuad(w, um - 0.006f, um + 0.006f, v0, v1, Palette16.MenuiserieSombre);
			DrawQuad(w, u0, u1, vm - 0.008f, vm + 0.008f, Palette16.MenuiserieSombre);
			// Appui débordant à larmier (bandeau clair sous la baie).
			DrawQuad(w, u0 - 0.03f, u1 + 0.03f, v0 - 0.05f, v0 - 0.02f, frame);
		}

		private void DrawDoor(int w, float u0, float u1, float v0, float v1, float light)
		{
			Color frame = Lit(Palette16.GraniteClair, light * 1.05f);
			DrawQuad(w, u0 - 0.025f, u1 + 0.025f, v0, v1 + 0.03f, frame); // encadrement
			DrawQuad(w, u0, u1, v0, v1, Palette16.MenuiserieSombre);      // vantail sombre
			// Planches verticales suggérées par 2 rainures claires.
			float ua = Mathf.Lerp(u0, u1, 0.35f), ub = Mathf.Lerp(u0, u1, 0.65f);
			DrawQuad(w, ua - 0.004f, ua + 0.004f, v0, v1, Lit(Palette16.MenuiserieSombre, 1.4f));
			DrawQuad(w, ub - 0.004f, ub + 0.004f, v0, v1, Lit(Palette16.MenuiserieSombre, 1.4f));
		}

		// Quad plein dans le repère (u,v) d'une façade (voir QuadPoint).
		private void DrawQuad(int w, float u0, float u1, float v0, float v1, Color col)
		{
			var poly = new Vector2[]
			{
				QuadPoint(w, u0, v0), QuadPoint(w, u1, v0),
				QuadPoint(w, u1, v1), QuadPoint(w, u0, v1),
			};
			_lot.Polygone(poly, col);
		}

		// -------------------------------------------------------------------
		// TOIT — 2 pans d'ardoise pentus (rangs d'écailles), croupe
		// -------------------------------------------------------------------
		// Un pan = du haut de mur w au segment de faîte. La forte pente vient de ce
		// que le faîte est nettement au-dessus des hauts de mur (WorldView calcule
		// apex à height_cm, murs à ~0.62·height). Rangs d'écailles peints en (s,t) :
		// s le long du bas de pan (haut de mur), t du bas vers le faîte.
		private void DrawRoof(bool back)
		{
			int rightWall = (_front + 3) % 4, leftWall = _front;
			int[] walls = back
				? new[] { (_front + 1) % 4, (_front + 2) % 4 }
				: new[] { rightWall, leftWall };
			foreach (int w in walls)
				DrawRoofPane(w);
		}

		private void DrawRoofPane(int w)
		{
			// Bas du pan = arête haute du mur w ; haut du pan = faîte. Le faîte est un
			// SEGMENT (_apexA..B) : on choisit l'extrémité de faîte la plus proche de
			// chaque coin bas pour que les 4 pans (2 grands + 2 croupes) se ferment.
			Vector2 b0 = _corners[w] + _upWall, b1 = _corners[(w + 1) % 4] + _upWall;
			Vector2 r0 = b0.DistanceSquaredTo(_apexA) <= b0.DistanceSquaredTo(_apexB) ? _apexA : _apexB;
			Vector2 r1 = b1.DistanceSquaredTo(_apexA) <= b1.DistanceSquaredTo(_apexB) ? _apexA : _apexB;
			float light = WallLight(w) * 0.9f;   // le toit est plus incliné → un peu plus sombre

			_lot.Polygone(new[] { b0, b1, r1, r0 }, Lit(Palette16.ArdoiseSombre, light));

			// Rangs d'écailles : ~7 rangs du bas (t=0) au faîte (t=1). Chaque rang =
			// une bande de petites écailles décalées (pureau serré). 2 valeurs au hash.
			const int rows = 7, cols = 9;
			for (int rr = 0; rr < rows; rr++)
			{
				float t0 = rr / (float)rows, t1 = (rr + 1) / (float)rows;
				// Bords bas/haut du rang (interpolation vers les points de faîte).
				Vector2 e0a = b0.Lerp(r0, t0), e1a = b1.Lerp(r1, t0);
				Vector2 e0b = b0.Lerp(r0, t1), e1b = b1.Lerp(r1, t1);
				float shift = (rr % 2) * 0.5f / cols;
				for (int cc = 0; cc < cols; cc++)
				{
					float s0 = cc / (float)cols + shift, s1 = s0 + 1f / cols;
					if (s1 > 1f) continue;
					Vector2 p0 = e0a.Lerp(e1a, s0), p1 = e0a.Lerp(e1a, s1);
					Vector2 p2 = e0b.Lerp(e1b, s1), p3 = e0b.Lerp(e1b, s0);
					Color a = Hash01(3, rr, cc) < 0.5f
						? Palette16.Ardoise : Palette16.ArdoiseClair;
					// Écaille = 85 % du rang (le recouvrement sombre transparaît en bas).
					Vector2 q0 = p0.Lerp(p3, 0.15f), q1 = p1.Lerp(p2, 0.15f);
					_lot.Polygone(new[] { q0, q1, p2, p3 }, Lit(a, light));
				}
			}
		}

		// Faîtage (ligne de crête sombre) + lucarne à bâtière sur le versant sud.
		private void DrawRidgeAndDormer()
		{
			// Faîtage : trait épais le long du segment de faîte.
			_lot.Ligne(_apexA, _apexB, Lit(Palette16.ArdoiseSombre, 0.7f), 2.5f);

			// Lucarne à bâtière : petit volume saillant sur le pan SUD-monde (mur 2)
			// s'il est un des 2 pans avant visibles. Sinon on ne la dessine pas (elle
			// serait cachée) — cohérent avec la rotation D35.
			int rightWall = (_front + 3) % 4, leftWall = _front;
			if (rightWall != 2 && leftWall != 2) return;

			int w = 2;
			Vector2 b0 = _corners[w] + _upWall, b1 = _corners[(w + 1) % 4] + _upWall;
			Vector2 r0 = b0.DistanceSquaredTo(_apexA) <= b0.DistanceSquaredTo(_apexB) ? _apexA : _apexB;
			Vector2 r1 = b1.DistanceSquaredTo(_apexA) <= b1.DistanceSquaredTo(_apexB) ? _apexA : _apexB;
			// Centre du pan, à mi-pente : base de la lucarne.
			Vector2 baseL = b0.Lerp(b1, 0.5f).Lerp(r0.Lerp(r1, 0.5f), 0.42f);
			Vector2 up = (r0.Lerp(r1, 0.5f) - b0.Lerp(b1, 0.5f)).Normalized();
			float sz = _upWall.Length() * 0.28f;
			// Front de la lucarne (petite fenêtre encadrée) + mini-toit à 2 versants.
			Vector2 fl = baseL - _upWall.Normalized() * (sz * 0.55f);
			Vector2 fr = baseL + _upWall.Normalized() * (sz * 0.55f);
			Vector2 ft = baseL - up * sz;
			_lot.Polygone(new[] { fl, fr, fr - up * sz * 0.7f, fl - up * sz * 0.7f },
							   Lit(Palette16.GraniteClair, 1.0f));                 // joue/front clair
			_lot.Polygone(new[] { fl - up * sz * 0.7f, fr - up * sz * 0.7f, ft },
							   Lit(Palette16.Ardoise, 0.95f));                     // mini-toit
			_lot.Polygone(new[]
			{
				fl.Lerp(fr, 0.28f), fl.Lerp(fr, 0.72f),
				(fl.Lerp(fr, 0.72f)) - up * sz * 0.42f, (fl.Lerp(fr, 0.28f)) - up * sz * 0.42f,
			}, Palette16.VitreSombre);                                            // carreau
		}

		// -------------------------------------------------------------------
		// CHEMINÉE — souche de brique orangée émergeant du faîtage (statique,
		// PAS de fumée = animation différée D72).
		// -------------------------------------------------------------------
		private void DrawChimney()
		{
			// Souche posée à ~30 % du faîte (côté avant du toit pour être visible).
			Vector2 baseC = _apexA.Lerp(_apexB, 0.3f);
			float wCm = _upWall.Length();
			float half = wCm * 0.12f;
			float tall = wCm * 0.55f;
			Vector2 top = baseC - new Vector2(0f, tall);   // la souche monte à l'écran
			// Corps de brique (2 valeurs : face avant claire, côté sombre).
			var body = new Vector2[]
			{
				baseC + new Vector2(-half, 0f), baseC + new Vector2(half, 0f),
				top + new Vector2(half, 0f), top + new Vector2(-half, 0f),
			};
			_lot.Polygone(body, Palette16.BriqueOrange);
			// Assises de brique (traits sombres horizontaux) + un joint vertical.
			for (int r = 1; r < 5; r++)
			{
				float y = -tall * r / 5f;
				_lot.Ligne(baseC + new Vector2(-half, y), baseC + new Vector2(half, y),
						 Palette16.BriqueSombre, 1f);
			}
			// Couronnement (chapeau débordant plus sombre).
			_lot.Polygone(new[]
			{
				top + new Vector2(-half * 1.3f, 4f), top + new Vector2(half * 1.3f, 4f),
				top + new Vector2(half * 1.3f, -3f), top + new Vector2(-half * 1.3f, -3f),
			}, Palette16.BriqueSombre);
		}
	}
}
