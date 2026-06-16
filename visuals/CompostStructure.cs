// SYMBIOSE — CompostStructure.cs
// Le PLACEHOLDER procédural d'une structure posable (décompo·compost ⑤, vue
// 03·C) : un bac à compost (caisse ouverte) ou une pile à bois (tas de rondins),
// distincts d'un coup d'œil. Posé sur un plot, il VIT dans la couche YSort des
// objets (`_objects`) — donc il s'occulte correctement avec les plantes et la
// maison, comme tout volume au sol. La jauge `compost_mur` (matière mûre,
// épandable) est rendue en REMPLISSAGE VISUEL (philo : pas de chiffre en HUD) :
// le bac se remplit de compost sombre, la pile prend une assise d'humus.
//
// 📖 Pédagogie — un nœud par structure (l'inverse de la litière/macro) : elles
// sont PEU nombreuses, persistantes et doivent trier en profondeur (YSort) avec
// les plantes → le modèle « un CanvasItem chacune » (comme les plantes), pas le
// batch d'un layer. La hauteur (Z) projette toujours en vertical écran (comme la
// maison et les plantes) ; l'empreinte au sol, elle, tourne avec la vue
// (WorldToScreenOffset) → le placeholder reste cohérent sous les 4 orientations.

using Godot;

namespace Symbiose
{
	public partial class CompostStructure : Node2D
	{
		// Demi-empreinte au sol (cm) — un plot fait 50 cm ; la structure en occupe
		// le cœur sans déborder. La pile est un poil plus large que le bac.
		private const float BacHalfCm  = 17f;
		private const float PileHalfCm = 20f;
		// Hauteurs (cm) extrudées vers le haut de l'écran.
		private const float BacWallCm = 26f;
		// Référence de jauge pour saturer le remplissage (compost_mur n'a pas de
		// borne dure) : au-delà, structure « pleine ». Calibrage post-F5.
		private const float MurRef = 6f;

		// Teintes bois — caisse claire (planches), arêtes sombres, compost mûr.
		private static readonly Color BoisClair  = new Color("9a6f44");
		private static readonly Color BoisOmbre  = new Color("6f4d2c");
		private static readonly Color BoisFonce  = new Color("523619");
		private static readonly Color CompostCol = new Color("3c2c1c");
		private static readonly Color HumusCol   = new Color("4a3a22");
		// Rondins de la pile : sections claires (aubier) cernées.
		private static readonly Color RondinCol  = new Color("a9855c");

		private readonly string _kind;   // "bac" | "pile"
		private float _mur;              // jauge compost_mur (saturée à MurRef)

		public CompostStructure(string kind, float compostMur)
		{
			_kind = kind;
			_mur = compostMur;
		}

		// Les 4 coins de l'empreinte, projetés en OFFSET (vecteur) autour du
		// centre du plot — tournent avec la vue. Ordre nw→ne→se→sw.
		private static Vector2[] Footprint(float halfCm)
		{
			return new[]
			{
				WorldView.WorldToScreenOffset(-halfCm, -halfCm),
				WorldView.WorldToScreenOffset( halfCm, -halfCm),
				WorldView.WorldToScreenOffset( halfCm,  halfCm),
				WorldView.WorldToScreenOffset(-halfCm,  halfCm),
			};
		}

		public override void _Draw()
		{
			float sat = Mathf.Clamp(_mur / MurRef, 0f, 1f);
			if (_kind == "pile") DrawPile(sat);
			else DrawBac(sat);
		}

		// BAC : caisse ouverte vue en iso. Empreinte au sol → 2 faces visibles
		// (avant-gauche, avant-droite) extrudées, + rebord supérieur. Le compost
		// mûr est la teinte du fond vu d'en haut (alpha ∝ jauge).
		private void DrawBac(float sat)
		{
			Vector2[] g = Footprint(BacHalfCm);          // coins au sol
			Vector2 up = new Vector2(0f, -BacWallCm * WorldView.PxPerCmZ);
			Vector2[] top = { g[0] + up, g[1] + up, g[2] + up, g[3] + up };

			// Le coin « avant » = le plus bas à l'écran (le plus proche caméra) ;
			// ses deux faces adjacentes sont visibles. MÊME logique que la maison.
			int front = 0;
			for (int i = 1; i < 4; i++) if (g[i].Y > g[front].Y) front = i;
			int right = (front + 3) % 4, left = front;

			// Fond de caisse = top rhombus rempli de compost (alpha ∝ jauge) :
			// la matière mûre « remplit » le bac vue d'en haut.
			var fond = CompostCol; fond.A = 0.25f + 0.65f * sat;
			DrawColoredPolygon(top, fond);

			// 2 faces avant (planches claires), arêtes plus sombres.
			foreach (int w in new[] { right, left })
			{
				var face = new[] { g[w], g[(w + 1) % 4], top[(w + 1) % 4], top[w] };
				DrawColoredPolygon(face, w == left ? BoisClair : BoisOmbre);
				DrawPolyline(new[] { g[w], top[w], top[(w + 1) % 4] }, BoisFonce, 1.5f);
			}
			// Rebord du haut (le contour ouvert de la caisse).
			DrawPolyline(new[] { top[0], top[1], top[2], top[3], top[0] }, BoisFonce, 1.5f);
		}

		// PILE : un tas de rondins. Assise = empreinte teintée d'humus (∝ jauge,
		// la pile « digère » en humus forestier), surmontée de 3 sections de
		// rondins empilées en pyramide.
		private void DrawPile(float sat)
		{
			Vector2[] g = Footprint(PileHalfCm);
			var humus = HumusCol; humus.A = 0.30f + 0.55f * sat;
			DrawColoredPolygon(g, humus);

			// Largeur d'un rondin = l'axe est-ouest de l'empreinte, projeté en
			// offset → il pivote avec la vue. Trois assises décroissantes.
			Vector2 ew = WorldView.WorldToScreenOffset(PileHalfCm, 0f);
			float lift = 11f * WorldView.PxPerCmZ;
			(float w, float y)[] rangs = { (1.0f, 0f), (0.7f, 1f), (0.4f, 2f) };
			foreach (var (wf, yi) in rangs)
			{
				Vector2 cen = new Vector2(0f, -yi * lift - lift * 0.4f);
				Vector2 half = ew * wf;
				DrawLine(cen - half, cen + half, RondinCol, 7f);
				DrawLine(cen - half, cen + half, BoisFonce, 7f * 0.18f);  // cœur cerné
			}
		}
	}
}
