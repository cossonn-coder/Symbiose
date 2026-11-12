// SYMBIOSE — PlantRenderer.FleurSnes.cs (partial, sprint FORMES DES PLANTES ⑥, D118 B)
// Les fleurs des plantes à segments en grammaire SNES, et le détail du limbe de près.
// Le brief : « aucune fleur n'a de pétales détaillés, elles se lisent comme des taches de couleur
// pure posées sur du vert », éclat en haut à gauche, ombre en bas à droite, trait fin d'une teinte
// plus sombre de leur propre couleur. Ici : 4 tons d'une rampe, taille en cm donc à l'échelle du
// port, et chatons pour les 7 arbres dont c'est la floraison (fiches_arbres.md).
//
// 📖 Pédagogie : avant, le rayon d'une corolle valait 4 px CANVAS, soit 10 cm de pétales. À ×32 une
// fleur de pommier couvrait 256 px. Un px canvas grandit avec le zoom : pour rester à l'échelle
// d'une plante, tout rayon se donne en cm, multiplié par `PxPerCmX`. Tout passe par le lot de
// triangles du port : un seul envoi par plante au lieu d'un par pétale.
//
// Zéro Random (philo #3) : variations au hash.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Rayon d'une fleur `[choix]` : 3 cm de diamètre, comme la fleur du pommier [odg].
		private const float FleurRayonCm = 1.5f;
		// Chaton `[choix]` : long de 6 cm [odg], fait de 5 grains.
		private const float ChatonCm = 6f;
		private const int GrainsChaton = 5;

		private static readonly System.Collections.Generic.HashSet<string> Chatons = new()
		{
			"WalnutTree", "OakTree", "BeechTree", "HornbeamTree", "BirchTree", "Alder", "Willow", "FirTree",
			"HazelTree",   // noisetier : chatons jaunes en fin d'hiver (zoochorie ⑧)
		};

		/// <summary>Une fleur d'arbre en `c` : chaton pendant, ou tache ronde à 5 lobes de près.</summary>
		private void PoserFleurSnes(Vector2 c, Color col, int k)
		{
			if (_structure.SpeciesName == "Fig") return;   // sa floraison est dans la figue (fiche)
			float pix = PixelInterne, r = Mathf.Max(FleurRayonCm * WorldView.PxPerCmX, pix * 2f);
			if (Chatons.Contains(_structure.SpeciesName)) { PoserChaton(c, col, k); return; }
			PoserDisque(c, r + pix, Ton(col, 0));   // contour sélectif
			if (AuPalier(PalierSymptomesZoom))
				for (int p = 0; p < 5; p++)
				{
					float a = Mathf.Tau * (p + Hash01(391, GraineIndividu, k)) / 5f;
					var q = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r * 0.62f;
					PoserDisque(q, r * 0.5f + pix, Ton(col, 0));
					PoserDisque(q, r * 0.5f, Ton(col, q.Y > c.Y ? PaletteIndexee.TonBase : 3));
				}
			else
			{
				PoserDisque(c, r, Ton(col, PaletteIndexee.TonBase));
				PoserDisque(c - new Vector2(r, r) * 0.18f, r * 0.68f, Ton(col, 3));
			}
			PoserDisque(c - new Vector2(r, r) * 0.42f, Mathf.Max(r * 0.2f, pix), Ton(col, 4));   // éclat en haut à gauche
			PoserDisque(c, Mathf.Max(r * 0.2f, pix), Ton(FlowerHeart, 1));                        // le point central
		}

		// Grains serrés sur un fil qui pend, du plus gros au plus fin.
		private void PoserChaton(Vector2 c, Color col, int k)
		{
			float pix = PixelInterne, pas = ChatonCm * WorldView.PxPerCmZ / GrainsChaton;
			float penche = (Hash01(393, GraineIndividu, k) - 0.5f) * pas;
			for (int g = 0; g < GrainsChaton; g++)
			{
				var q = c + new Vector2(penche * g, pas * g);
				float r = Mathf.Max(pas * Mathf.Lerp(0.75f, 0.4f, g / (GrainsChaton - 1f)), pix);
				PoserDisque(q, r + pix, Ton(col, 0));
				PoserDisque(q, r, Ton(col, g % 2 == 0 ? 3 : PaletteIndexee.TonBase));
			}
		}

		// ---------------------------------------------------------------------------
		// LIMBE DE PRÈS (D118 B) : plus d'ovale vert uni
		// ---------------------------------------------------------------------------

		// Largeur relative qui reste dans le limbe à la position `lg`, quelle que soit sa forme :
		// le contour s'effile aux deux bouts (sinon les nervures dépassent, comme des soies).
		private static float DansLimbe(float lg) => 0.6f * Mathf.Min(1f, 2.2f * (1f - lg)) * Mathf.Min(1f, 3f * lg);

		/// <summary>Sur un limbe de contour `_contourPrairie` (base, moitié gauche, bout, moitié
		/// droite) : dès ×16, une moitié dans l'ombre et les nervures secondaires à 1 px ; à ×32,
		/// le grain et l'éclat. À appeler juste après le remplissage du limbe.</summary>
		private void DetaillerLimbe(FeuillePosee fe, Color col)
		{
			if (!AuPalier(PalierSymptomesZoom)) return;
			float pix = PixelInterne;
			Color ombre = Ton(col, Mathf.Max(fe.Ton - 1, 0)), nervure = Ton(col, Mathf.Min(fe.Ton + 1, 4));
			int bout = _contourPrairie.Count / 2;
			for (int i = bout; i + 1 < _contourPrairie.Count; i++)
				_lotPrairie.Triangle(_contourPrairie[0], _contourPrairie[i], _contourPrairie[i + 1], ombre);
			bool intime = AuPalier(PalierIntimeZoom);
			int paires = intime ? 5 : 3;
			for (int i = 1; i <= paires; i++)
			{
				float t = 0.12f + 0.68f * i / paires;
				Vector2 axe = PointFeuille(fe, t, 0f);
				float lr = DansLimbe(t + 0.14f);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.14f, lr), nervure, pix);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.14f, -lr), nervure, pix);
			}
			if (!intime) return;
			int ig = GraineIndividu + fe.K;
			for (int i = 0; i < 8; i++)
			{
				float lg = Mathf.Lerp(0.2f, 0.85f, Hash01(395, ig, i)), lr = Mathf.Lerp(-1f, 1f, Hash01(397, ig, i)) * DansLimbe(lg);
				Vector2 q = PointFeuille(fe, lg, lr);
				_lotPrairie.Ligne(q, q + new Vector2(pix * 2f, pix), Ton(col, i % 3 == 0 ? Mathf.Max(fe.Ton - 1, 0) : Mathf.Min(fe.Ton + 1, 4)), pix);
			}
			_lotPrairie.Ligne(PointFeuille(fe, 0.3f, DansLimbe(0.3f)), PointFeuille(fe, 0.5f, DansLimbe(0.5f)), Ton(col, 4), pix);   // éclat
		}
	}
}
