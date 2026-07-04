// SYMBIOSE — SupportRenderer.cs
// Le PLACEHOLDER procédural d'un support de GRIMPE posable (sprint grimpantes ⑥,
// D49 volet A, vue). Un tuteur (pieu fin), un treillis (grille) ou une pergola
// (portique) posé sur un plot — ils vivent dans la couche YSort des objets
// (`_objects`), donc s'occultent correctement avec les plantes et la maison,
// comme tout volume au sol (même modèle que CompostStructure : un nœud chacun,
// peu nombreux, reconstruits à chaque snapshot).
//
// 📖 Pédagogie — pourquoi si peu de code pour « la grimpe » ? La grimpe elle-même
// est GRATUITE côté vue : par décision A (géométrique), la hauteur d'une grimpante
// est la vraie max_z de ses segments — une accrochée a déjà ses segments montés le
// long du support DANS le snapshot, une affalée les a au sol. PlantRenderer les
// dessine sans rien de spécial. Ce nœud ne peint donc QUE le support inerte (le
// tuteur/treillis/pergola), sur lequel la plante grimpe « toute seule ».
//
// La hauteur (Z) projette en vertical écran (comme la maison, le bac et les
// plantes) ; l'empreinte au sol tourne avec la vue (WorldToScreenOffset) → le
// placeholder reste cohérent sous les 4 orientations.

using Godot;

namespace Symbiose
{
	public partial class SupportRenderer : Node2D
	{
		// Teintes bois — piquet clair, arêtes sombres (mêmes bois que le bac compost
		// pour l'unité visuelle du « bois posé par le joueur »).
		private static readonly Color BoisClair = new Color("9a6f44");
		private static readonly Color BoisOmbre = new Color("6f4d2c");
		private static readonly Color BoisFonce = new Color("523619");

		// Demi-largeurs d'empreinte au sol (cm) — un plot fait 50 cm.
		private const float TuteurHalfCm  = 3f;    // pieu fin
		private const float TreillisHalfCm = 18f;  // panneau large
		private const float PergolaHalfCm = 22f;   // portique enjambant le plot

		private readonly string _kind;       // "tuteur" | "treillis" | "pergola"
		private readonly float _heightCm;    // hauteur d'appui (extrusion verticale)

		public SupportRenderer(string kind, float heightCm)
		{
			_kind = kind;
			_heightCm = heightCm;
		}

		// Vecteur vertical écran d'une hauteur en cm (Z tire vers le HAUT : +Y écran
		// vers le bas → on SOUSTRAIT, comme partout dans la vue).
		private Vector2 Up(float cm) => new Vector2(0f, -cm * WorldView.PxPerCmZ);

		public override void _Draw()
		{
			switch (_kind)
			{
				case "treillis": DrawTreillis(); break;
				case "pergola":  DrawPergola();  break;
				default:         DrawTuteur();   break;   // "tuteur" (défaut sobre)
			}
		}

		// TUTEUR : un simple pieu vertical planté au centre du plot, avec une légère
		// épaisseur iso (deux montants) pour ne pas être un trait plat.
		private void DrawTuteur()
		{
			Vector2 top = Up(_heightCm);
			Vector2 e = WorldView.WorldToScreenOffset(TuteurHalfCm, 0f);
			// Face du pieu (quadrilatère mince) + arête avant marquée.
			DrawColoredPolygon(new[] { -e, e, e + top, -e + top }, BoisClair);
			DrawLine(Vector2.Zero, top, BoisFonce, 1.5f);
			// Petite pointe en haut (repère d'appui maximal).
			DrawCircle(top, 1.6f, BoisOmbre);
		}

		// TREILLIS : un panneau-grille dressé face à la caméra. Deux montants + des
		// barreaux horizontaux régulièrement espacés (la vrille s'y enroule au F5).
		private void DrawTreillis()
		{
			Vector2 half = WorldView.WorldToScreenOffset(TreillisHalfCm, 0f);
			Vector2 top = Up(_heightCm);
			Vector2 lo = -half, hi = half;                     // pieds gauche/droit au sol
			// Cadre : 2 montants + traverse haute.
			DrawLine(lo, lo + top, BoisOmbre, 2f);
			DrawLine(hi, hi + top, BoisOmbre, 2f);
			DrawLine(lo + top, hi + top, BoisOmbre, 2f);
			// Barreaux horizontaux (5 niveaux) → la grille où s'accroche la plante.
			for (int i = 1; i <= 5; i++)
			{
				Vector2 lvl = Up(_heightCm * i / 6f);
				DrawLine(lo + lvl, hi + lvl, BoisClair, 1.3f);
			}
			// Deux montants verticaux internes (maille).
			foreach (float f in new[] { -0.33f, 0.33f })
			{
				Vector2 m = half * f;
				DrawLine(m, m + top, BoisClair, 1.1f);
			}
		}

		// PERGOLA : un portique qui ENJAMBE le plot (2 poteaux + une poutre faîtière
		// projetée en offset → elle tourne avec la vue). Elle projette une ombre au
		// sol (rectangle sombre translucide) : indice diégétique de l'occultation.
		private void DrawPergola()
		{
			Vector2 span = WorldView.WorldToScreenOffset(PergolaHalfCm, 0f);
			Vector2 top = Up(_heightCm);
			Vector2 lo = -span, hi = span;
			// Ombre portée au sol (léger losange sombre sous la poutre).
			var ombre = new Color(0f, 0f, 0f, 0.18f);
			Vector2 depth = WorldView.WorldToScreenOffset(0f, PergolaHalfCm);
			DrawColoredPolygon(new[] { lo - depth, hi - depth, hi + depth, lo + depth },
							   ombre);
			// 2 poteaux + poutre faîtière.
			DrawLine(lo, lo + top, BoisOmbre, 2.5f);
			DrawLine(hi, hi + top, BoisOmbre, 2.5f);
			DrawLine(lo + top, hi + top, BoisClair, 3f);
			// Chevrons de la poutre (petits débords) → lecture « toit ouvert ».
			for (int i = -1; i <= 1; i++)
			{
				Vector2 c = span * (i * 0.5f) + top;
				DrawLine(c, c + Up(-5f), BoisFonce, 1.2f);   // léger débord vers le bas
			}
		}
	}
}
