// SYMBIOSE — CompostStructure.cs
// Le PLACEHOLDER procédural d'une structure posable (décompo·compost ⑤, vue
// 03·C) : un bac à compost (caisse ouverte) ou une pile à bois (tas de rondins),
// distincts d'un coup d'œil. Posé sur un plot, il VIT dans la couche YSort des
// objets (`_objects`) — donc il s'occulte correctement avec les plantes et la
// maison, comme tout volume au sol. La jauge `compost_mur` (matière mûre,
// épandable) est rendue en REMPLISSAGE VISUEL (philo : pas de chiffre en HUD) :
// le bac se remplit de compost sombre, la pile prend une assise d'humus. Le
// remplissage suit la masse TOTALE (`contenu` brut + `compost_mur` mûr, 0.3.8)
// → la structure se remplit DÈS le compostage (avant maturation) et se vide à
// l'épandage. Échelle réelle mesurée : un plot bien fourni ≈ 1-6 de litière.
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
		// Masse de référence pour saturer le remplissage (la masse n'a pas de borne
		// dure) : au-delà, structure « pleine ». Couvre ≈ un plot bien fourni
		// (1-6) à quelques plots compostés. Calibrage post-F5 (« toujours plein /
		// toujours vide » → ajuster cette seule constante).
		private const float MasseRef = 6f;

		// Teintes bois — caisse claire (planches), arêtes sombres, compost mûr.
		private static readonly Color BoisClair  = new Color("9a6f44");
		private static readonly Color BoisOmbre  = new Color("6f4d2c");
		private static readonly Color BoisFonce  = new Color("523619");
		private static readonly Color CompostCol = new Color("3c2c1c");
		private static readonly Color HumusCol   = new Color("4a3a22");
		// Rondins de la pile : sections claires (aubier) cernées.
		private static readonly Color RondinCol  = new Color("a9855c");

		// Ruche (⑥ apiculture, vue piqûre) : demi-empreinte + hauteur d'une hausse
		// extrudée. `MielMaxRef` = MIEL_MAX moteur (10) → la jauge miel sature à
		// pleine réserve ; `essaim` arrive déjà borné [0,1] (pas de ref à diviser).
		private const float RucheHalfCm = 15f;
		private const float RucheBoxCm  = 13f;   // hauteur d'une hausse
		private const float MielMaxRef  = 10f;
		// Teintes ruche : bois pâle des hausses, miel ambré, abeilles (= MacroLife).
		private static readonly Color RucheBois = new Color("c9a86a");
		private static readonly Color RucheBord = new Color("7a5a30");
		private static readonly Color MielCol   = new Color("e6a92a");
		private static readonly Color AbeilleCol = new Color("e9c83c");

		// Voile fongique (mycélium ⑥, §3.3) : filaments blancs/mycéliens à la surface
		// du tas colonisé, densité ∝ colonisation. Teinte blanc cassé légèrement
		// bleuté (mycélium au sol, pas une moisissure verte de pathogène — distinct).
		private static readonly Color VoileCol = new Color("e6e9e0");
		private const int VoileBrins = 9;       // filaments à pleine colonisation

		private readonly string _kind;   // "bac" | "pile" | "ruche"
		private readonly float _masse;   // contenu + compost_mur (saturé à MasseRef)
		private readonly float _essaim;  // [0,1] peuplement de la ruche (⑥)
		private readonly float _miel;    // [0, MIEL_MAX] réserve de miel (⑥)
		private readonly float _colonisation;  // [0,1] habitation fongique (⑥, voile)

		public CompostStructure(string kind, float compostMur, float contenu,
								float essaim = 0f, float miel = 0f,
								float colonisation = 0f)
		{
			_kind = kind;
			_masse = compostMur + contenu;   // remplissage = matière TOTALE présente
			_essaim = essaim;
			_miel = miel;
			_colonisation = colonisation;
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
			if (_kind == "ruche") { DrawRuche(); return; }
			float sat = Mathf.Clamp(_masse / MasseRef, 0f, 1f);
			float half;
			if (_kind == "pile") { DrawPile(sat); half = PileHalfCm; }
			else { DrawBac(sat); half = BacHalfCm; }
			// Voile fongique PAR-DESSUS le tas (mycélium ⑥, §3.3) : on voit le
			// réseau HABITER la structure (indice diégétique direct, philo #5).
			if (_colonisation > 0.01f) DrawVoile(half);
		}

		// VOILE FONGIQUE : des brins blancs mycéliens posés sur le dessus du tas,
		// densité/longueur ∝ colonisation. Déterministe (positions par index, zéro
		// Random — comme MacroLife) : le même tas porte toujours le même voile. Les
		// brins partent du centre du plot et rayonnent ; ils s'allongent et se
		// densifient à mesure que le réseau s'installe. Posés en OFFSET monde
		// (WorldToScreenOffset) → ils tournent avec la vue comme l'empreinte.
		private void DrawVoile(float halfCm)
		{
			float col = Mathf.Clamp(_colonisation, 0f, 1f);
			int n = Mathf.RoundToInt(VoileBrins * col);
			if (n <= 0) return;
			// Le voile « monte » un peu au-dessus de l'assise du tas (sa croûte
			// fongique de surface) — léger lift vertical écran.
			Vector2 lift = new Vector2(0f, -6f * WorldView.PxPerCmZ);
			var c = VoileCol; c.A = 0.35f + 0.45f * col;
			for (int i = 0; i < n; i++)
			{
				// Angle réparti + longueur ∝ colonisation, dans l'empreinte.
				float a = i * 2.39996f;                 // angle d'or → étalement régulier
				float len = halfCm * (0.35f + 0.55f * col);
				Vector2 dir = WorldView.WorldToScreenOffset(
					Mathf.Cos(a) * len, Mathf.Sin(a) * len);
				Vector2 baseP = lift;
				DrawLine(baseP, baseP + dir, c, 1.2f);
				// Petit point au bout = jeune carpophore naissant sur la croûte.
				DrawCircle(baseP + dir, 1.0f, c);
			}
		}

		// RUCHE : une pile de 3 hausses vue en iso (mêmes 2 faces avant + dessus
		// que le bac). Le REMPLISSAGE des faces ∝ miel/MIEL_MAX (la réserve « monte »
		// dans les hausses, philo : pas de chiffre). Le peuplement (`essaim`) se
		// lit en abeilles posées au trou de vol — densité ∝ essaim, sans nom (vie
		// macro). Posée en couche YSort → s'occulte avec plantes et maison.
		private void DrawRuche()
		{
			float miel = Mathf.Clamp(_miel / MielMaxRef, 0f, 1f);
			Vector2[] g = Footprint(RucheHalfCm);
			int front = 0;
			for (int i = 1; i < 4; i++) if (g[i].Y > g[front].Y) front = i;
			int right = (front + 3) % 4, left = front;

			// 3 hausses empilées : on extrude chaque caisson par RucheBoxCm. Les
			// faces se remplissent de miel du BAS vers le haut (jauge globale).
			for (int box = 0; box < 3; box++)
			{
				Vector2 dn = new Vector2(0f, -box * RucheBoxCm * WorldView.PxPerCmZ);
				Vector2 upBox = new Vector2(0f, -RucheBoxCm * WorldView.PxPerCmZ);
				Vector2[] baseR = { g[0] + dn, g[1] + dn, g[2] + dn, g[3] + dn };
				Vector2[] topR = { baseR[0] + upBox, baseR[1] + upBox,
								   baseR[2] + upBox, baseR[3] + upBox };
				// Part de miel revenant à CETTE hausse (remplissage du bas) : la
				// jauge globale × 3 hausses, la part de chacune saturée à 1.
				float boxMiel = Mathf.Clamp(miel * 3f - box, 0f, 1f);
				foreach (int w in new[] { right, left })
				{
					var face = new[] { baseR[w], baseR[(w + 1) % 4],
									   topR[(w + 1) % 4], topR[w] };
					Color bois = w == left ? RucheBois : RucheBord;
					DrawColoredPolygon(face, bois.Lerp(MielCol, 0.7f * boxMiel));
					DrawPolyline(new[] { baseR[w], topR[w], topR[(w + 1) % 4] },
								 RucheBord, 1.5f);
				}
			}
			// Trou de vol + abeilles : au pied de la face avant, densité ∝ essaim.
			Vector2 vol = (g[left] + g[(left + 1) % 4]) * 0.5f;
			int nAbeilles = Mathf.RoundToInt(_essaim * 6f);
			for (int i = 0; i < nAbeilles; i++)
			{
				float a = i * 1.3f;
				Vector2 p = vol + new Vector2(Mathf.Cos(a) * 5f,
											  -2f - Mathf.Sin(a) * 4f);
				DrawCircle(p, 1.4f, AbeilleCol);
			}
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

			// GESTES LISIBLES ③ : le bac montre son VOLUME — intérieur sombre (vide),
			// puis la surface du compost à une hauteur ∝ jauge : il se remplit à l'œil.
			DrawColoredPolygon(top, BoisFonce);
			if (sat > 0.01f)
			{
				Vector2 niveau = up * Mathf.Max(0.12f, sat);
				DrawColoredPolygon(new[] { g[0] + niveau, g[1] + niveau, g[2] + niveau, g[3] + niveau },
					CompostCol);
			}

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

			// GESTES LISIBLES ③ : la pile GROSSIT avec sa quantité — 1 à 10 rondins,
			// rangés en pyramide (4, 3, 2, 1) du bas vers le haut, côte à côte sur l'axe
			// nord-sud. Rondin = l'axe est-ouest projeté en offset → pivote avec la vue.
			Vector2 ew = WorldView.WorldToScreenOffset(PileHalfCm * 0.9f, 0f);
			float lift = 9f * WorldView.PxPerCmZ;
			int n = 1 + Mathf.RoundToInt(9f * sat);
			for (int k = 0, rang = 0; k < n; rang++)
				for (int i = 0; i < 4 - rang && k < n; i++, k++)
				{
					float v = (i - (3 - rang) * 0.5f) * 9f;   // cm, centré sur le rang
					Vector2 cen = WorldView.WorldToScreenOffset(0f, v)
						+ new Vector2(0f, -rang * lift - lift * 0.4f);
					DrawLine(cen - ew, cen + ew, RondinCol, 5f);
					DrawLine(cen - ew, cen + ew, BoisFonce, 1f);   // cœur cerné
				}
		}
	}
}
