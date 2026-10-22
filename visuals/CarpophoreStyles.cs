// SYMBIOSE — CarpophoreStyles.cs (sprint « le sol qui respire » ⑧)
// Le PORTRAIT de chacun des 13 champignons du registre Python
// (`fields/fongique.REGISTRE_FONGIQUE`) : une silhouette + trois couleurs, assez
// pour qu'un joueur RECONNAISSE l'espèce à l'œil avant de savoir la nommer
// (posture naturaliste, philo #5-#6). Les sosies restent des sosies À DESSEIN :
// le rosé des prés et le clitocybe blanchâtre ne diffèrent que par la couleur des
// lames (rose / blanc) et un chapeau un peu creusé — exactement le piège réel.
//
// 📖 Pédagogie — la vue ne décide rien : l'espèce arrive du snapshot (7ᵉ champ du
// carpophore) ; ici on ne fait que lui associer un DESSIN (table de données,
// comme une LUT en embarqué). Tout se trace en triangles dans le lot partagé de
// la couche (LotTriangles → UN draw call pour tous les chapeaux), en basse
// définition : à 3-15 px internes, quatre triangles valent un cercle de 64.
// DA SNES mignon : chapeaux ronds et francs, un point de lumière, pas de détail
// qui grouille.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	internal enum FormeCarpo
	{
		Convexe,    // chapeau en dôme (rosé, amanites, collybie)
		Creuse,     // chapeau plat un peu creusé (clitocybe)
		Conique,    // petit cône pointu, pied long et fin (psilocybe)
		Coprin,     // haute cloche blanche à mèches, bord qui noircit
		Morille,    // cône alvéolé sur pied blanc
		Bouchon,    // pied ventru, chapeau brioche (cèpe)
		Console,    // éventail latéral sans pied (pleurote, polypore)
	}

	internal readonly record struct StyleCarpo(
		FormeCarpo Forme, Color Chapeau, Color Ombre, Color Pied,
		Color Detail, int Touffe, float Taille, bool Points = false);

	internal static class CarpophoreStyles
	{
		// Repli (clé absente / pont pré-0.5.52) : le champignon brun de sous-bois
		// d'avant ⑧, inchangé.
		public static readonly StyleCarpo Defaut = new(FormeCarpo.Convexe,
			new("8a5a36"), new("5e3c22"), new("e2d8c4"), new("5e3c22"), 1, 1f);

		// Touffe = nombre de chapeaux dessinés (espèces cespiteuses : hypholome,
		// armillaire, collybie). Taille = facteur sur le gabarit de densité.
		private static readonly Dictionary<string, StyleCarpo> Table = new()
		{
			["pleurote"] = new(FormeCarpo.Console, new("a4a294"), new("6e6c62"), new("d8d4c4"), new("e8e4d8"), 2, 1.1f),
			["hypholome"] = new(FormeCarpo.Convexe, new("d4b630"), new("9a7420"), new("c8b060"), new("b86a20"), 3, 0.7f),
			["collybie"] = new(FormeCarpo.Convexe, new("d0742a"), new("8a4418"), new("3e2a1c"), new("f0b060"), 2, 0.8f),
			["coprin"] = new(FormeCarpo.Coprin, new("f2eee4"), new("b8ad98"), new("f2eee4"), new("2a2622"), 1, 0.85f),
			["rose_des_pres"] = new(FormeCarpo.Convexe, new("f4f0e8"), new("c8c0b0"), new("f4f0e8"), new("e08a9a"), 1, 1f),
			["clitocybe"] = new(FormeCarpo.Creuse, new("ece8dc"), new("c4bcac"), new("ece8dc"), new("f8f6ee"), 1, 0.9f),
			["psilocybe"] = new(FormeCarpo.Conique, new("c0a060"), new("7a6034"), new("dcd2b4"), new("6a5a3c"), 1, 0.6f),
			["morille"] = new(FormeCarpo.Morille, new("9a7448"), new("5a4028"), new("ece2cc"), new("5a4028"), 1, 1f),
			["cepe"] = new(FormeCarpo.Bouchon, new("7a4a26"), new("4e2e16"), new("e4d8b8"), new("a87a4a"), 1, 1.3f),
			["amanite_phalloide"] = new(FormeCarpo.Convexe, new("a4ae6a"), new("6e7a40"), new("f2f0e6"), new("f2f0e6"), 1, 1.1f),
			["amanite_tue_mouches"] = new(FormeCarpo.Convexe, new("d83a2a"), new("901e16"), new("f4f0e6"), new("faf6ec"), 1, 1.2f, true),
			["armillaire"] = new(FormeCarpo.Convexe, new("c89a48"), new("8a6428"), new("d8c49a"), new("6a4a20"), 3, 0.8f, true),
			["polypore_bouleau"] = new(FormeCarpo.Console, new("eae0c8"), new("b89c70"), new("eae0c8"), new("c8a878"), 1, 1.4f),
		};

		public static StyleCarpo De(string espece)
			=> espece != null && Table.TryGetValue(espece, out var s) ? s : Defaut;

		/// <summary>Dessine UN carpophore de style `s` au pied `b` (px internes).
		/// `h` = hauteur du pied, `cap` = rayon du chapeau, `phase` = variété
		/// déterministe, `a` = alpha (fondus).</summary>
		public static void Dessiner(LotTriangles lot, StyleCarpo s, Vector2 b,
									float h, float cap, uint phase, float a)
		{
			h *= s.Taille; cap *= s.Taille;
			for (int i = 0; i < s.Touffe; i++)
			{
				// Touffe : chapeaux décalés et de tailles inégales autour du pied.
				float k = i == 0 ? 1f : 0.65f + 0.2f * ((phase >> (i * 3) & 7) / 7f);
				Vector2 o = i == 0 ? Vector2.Zero
					: new Vector2((i % 2 == 1 ? -1f : 1f) * cap * 1.1f, cap * 0.3f);
				Un(lot, s, b + o, h * k, cap * k, phase, a);
			}
		}

		private static Color A(Color c, float a) { c.A = a; return c; }

		private static void Un(LotTriangles lot, StyleCarpo s, Vector2 b, float h,
							   float cap, uint phase, float a)
		{
			Color ch = A(s.Chapeau, a), om = A(s.Ombre, a), pi = A(s.Pied, a), de = A(s.Detail, a);
			float pied = Mathf.Max(1f / WorldView.CurrentZoom, cap * 0.4f);
			Vector2 top = b - new Vector2(0f, h);
			switch (s.Forme)
			{
				case FormeCarpo.Console:   // éventail plaqué au sol/bois, pas de pied
					DemiDisque(lot, b - new Vector2(0f, cap * 0.2f), cap * 1.2f, cap * 0.7f, ch);
					lot.Ligne(b + new Vector2(-cap * 1.2f, 0f), b + new Vector2(cap * 1.2f, 0f), om, Mathf.Max(pied * 0.6f, cap * 0.25f));
					lot.Ligne(b + new Vector2(-cap * 0.6f, -cap * 0.45f), b + new Vector2(cap * 0.6f, -cap * 0.45f), de, pied * 0.5f);
					return;
				case FormeCarpo.Conique:   // pied long et fin, petit cône à mamelon
					top = b - new Vector2(cap * 0.3f, h * 1.6f);
					lot.Ligne(b, top, pi, pied * 0.6f);
					lot.Triangle(top + new Vector2(-cap, 0f), top + new Vector2(cap, 0f), top - new Vector2(0f, cap * 1.3f), ch);
					lot.Ligne(top + new Vector2(-cap, 0f), top + new Vector2(cap, 0f), om, pied * 0.5f);
					return;
				case FormeCarpo.Coprin:    // haute cloche à mèches, bord noir (encre)
					lot.Ligne(b, top, pi, pied);
					lot.Ligne(top + new Vector2(0f, cap * 0.4f), top - new Vector2(0f, cap * 1.6f), ch, cap * 1.3f);
					DemiDisque(lot, top - new Vector2(0f, cap * 1.6f), cap * 0.65f, cap * 0.5f, ch);
					lot.Ligne(top + new Vector2(-cap * 0.65f, cap * 0.4f), top + new Vector2(cap * 0.65f, cap * 0.4f), de, pied * 0.6f);
					for (int i = 0; i < 3; i++)   // mèches
						lot.Ligne(top - new Vector2(cap * (0.3f - 0.3f * i), cap * (0.3f + 0.4f * i)),
								  top - new Vector2(cap * (0.3f - 0.3f * i), cap * (0.1f + 0.4f * i)), om, pied * 0.4f);
					return;
				case FormeCarpo.Morille:   // cône alvéolé (damier sombre) sur pied blanc
					lot.Ligne(b, top, pi, pied * 1.4f);
					lot.Triangle(top + new Vector2(-cap * 0.8f, 0f), top + new Vector2(cap * 0.8f, 0f), top - new Vector2(0f, cap * 2.2f), ch);
					for (int i = 0; i < 4; i++)
					{
						Vector2 m = top - new Vector2((i % 2 == 0 ? -0.25f : 0.25f) * cap, cap * (0.35f + 0.45f * i));
						lot.Ligne(m, m + new Vector2(0f, cap * 0.2f), de, cap * 0.22f);
					}
					return;
				case FormeCarpo.Bouchon:   // pied ventru + brioche brune à bord clair
					lot.Ligne(b, top, pi, cap * 0.9f);
					DemiDisque(lot, b - new Vector2(0f, h * 0.35f), cap * 0.55f, cap * 0.45f, pi);
					DemiDisque(lot, top, cap, cap * 0.75f, ch);
					lot.Ligne(top + new Vector2(-cap, 0f), top + new Vector2(cap, 0f), de, pied * 0.5f);
					return;
			}
			// Convexe / Creuse : pied, chapeau, ligne des lames (Detail = couleur des
			// lames pour rosé/clitocybe, sinon une écaille ou des points).
			lot.Ligne(b, top, pi, pied);
			if (s.Forme == FormeCarpo.Creuse)
			{
				lot.Ligne(top + new Vector2(-cap, -cap * 0.15f), top + new Vector2(cap, -cap * 0.15f), ch, cap * 0.45f);
				lot.Triangle(top + new Vector2(-cap * 0.4f, -cap * 0.35f), top + new Vector2(cap * 0.4f, -cap * 0.35f), top, om);
			}
			else
				DemiDisque(lot, top, cap, cap * 0.8f, ch);
			// Ligne des lames : Detail (rose du rosé, blanc du clitocybe…), sauf pour
			// les chapeaux À POINTS où Detail colore les points (voile, écailles).
			lot.Ligne(top + new Vector2(-cap, 0f), top + new Vector2(cap, 0f), s.Points ? om : de, pied * 0.55f);
			if (s.Points)   // restes du voile (tue-mouches), écailles (armillaire)
				for (int i = 0; i < 3; i++)
				{
					float u = ((phase >> (i * 4) & 0xf) / 15f - 0.5f) * cap * 1.2f;
					Vector2 m = top + new Vector2(u, -cap * (0.3f + 0.15f * i));
					lot.Ligne(m, m + new Vector2(cap * 0.2f, 0f), de, cap * 0.2f);
				}
			else   // reflet : un trait d'ombre douce sur le dôme
				lot.Ligne(top + new Vector2(-cap * 0.35f, -cap * 0.55f), top + new Vector2(-cap * 0.05f, -cap * 0.6f), om, pied * 0.4f);
		}

		// Demi-disque supérieur (chapeau) en 6 triangles.
		private static void DemiDisque(LotTriangles lot, Vector2 c, float rx, float ry, Color col)
		{
			const int n = 6;
			Vector2 prec = c + new Vector2(-rx, 0f);
			for (int i = 1; i <= n; i++)
			{
				float ang = Mathf.Pi + i * Mathf.Pi / n;
				Vector2 cour = c + new Vector2(Mathf.Cos(ang) * rx, Mathf.Sin(ang) * ry);
				lot.Triangle(c, prec, cour, col);
				prec = cour;
			}
		}
	}
}
