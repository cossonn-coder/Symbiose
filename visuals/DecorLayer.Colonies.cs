// SYMBIOSE — DecorLayer.Colonies.cs (LISIÈRE NUE ② — les taches de fleurs, vérité moteur)
// Partial de DecorLayer : lit les colonies du bloc `ceinture` (pont 0.6.4), sème leurs
// fleurs dans le tapis et transmet la floraison au shader. Python décide où et quand
// (`fields/fleurs_lisiere.py`) ; ici, seulement la façon de les peindre.
//
// 📖 Pédagogie — deux vitesses, comme une table en ROM et un registre de gain :
//  • la GÉOMÉTRIE ne change qu'avec la ceinture : les fleurs entrent dans la maille à
//    sa construction, et `MemesColonies` empêche toute reconstruction hebdomadaire ;
//  • la FLORAISON change chaque semaine : deux uniforms suffisent, le shader allume ou
//    éteint chaque fleur selon son hash. Aucun sommet n'est réécrit.
//
// 📖 Pédagogie — une ellipse lisse ne fait pas une tache de prairie. Le rayon normalisé
// est déformé par un bruit basse fréquence (la graine de la colonie), d'où des lobes ;
// la probabilité décroît du centre au bord, avec quelques fleurs isolées au-delà.

using Godot;
using GDict = Godot.Collections.Dictionary;
using GArray = Godot.Collections.Array;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		/// <summary>Géométrie d'une colonie, en cm dans le repère d'EdgePoint. Le compte de
		/// butineurs n'y figure pas : il change par semaine, pas le décor.</summary>
		public readonly record struct ColonieBord(float U, float Depth, float Ru, float Rd, bool Jaune, uint Graine);

		private const float PasFleurPx = 5f;      // px internes entre deux places de fleur
		private const float PasFleurMinCm = 17f;  // borne au gros plan : nombre de pièces fini
		private const float LobeCm = 130f;        // taille des lobes du contour
		private const float LobeAmp = 0.75f;      // déformation du rayon par le bruit
		private const float DensiteCentre = 0.9f, DensiteBord = 0.18f;
		private const float RayonEgare = 1.35f;   // au-delà du contour : fleurs isolées
		private const float DensiteEgaree = 0.05f;
		private const float TauFloraisonS = 3f;   // comme la semaine : pas de saut au snapshot

		private float _floraisonB, _floraisonJ;   // cibles, lues du pont
		private float _floraisonBVue = -1f, _floraisonJVue = -1f;   // écrites au shader

		private static ColonieBord[] LireColonies(GDict d)
		{
			if (!d.ContainsKey("colonies") || d["colonies"].VariantType != Variant.Type.Array) return null;
			var a = d["colonies"].AsGodotArray();
			var out_ = new ColonieBord[a.Count];
			for (int i = 0; i < a.Count; i++)
			{
				var c = a[i].AsGodotDictionary();
				out_[i] = new ColonieBord(Reel(c, "u"), Reel(c, "depth"), Reel(c, "ru"), Reel(c, "rd"),
					c["couleur"].AsString() == "jaune", (uint)c["graine"].AsInt64());
			}
			return out_;
		}

		// Compare la géométrie seule : `butineurs` et `floraison` ne reconstruisent rien.
		private static bool MemesColonies(ColonieBord[] a, ColonieBord[] b)
		{
			if (a == null || b == null) return a == b;
			if (a.Length != b.Length) return false;
			for (int i = 0; i < a.Length; i++)
				if (!a[i].Equals(b[i])) return false;
			return true;
		}

		// Floraison par couleur : identique sur les 4 secteurs (pont), lue sur le premier.
		private void LireFloraison(GArray ceinture)
		{
			_floraisonB = _floraisonJ = 0f;
			if (ceinture == null || ceinture.Count == 0) return;
			var d = ceinture[0].AsGodotDictionary();
			if (!d.ContainsKey("floraison")) return;
			var f = d["floraison"].AsGodotDictionary();
			_floraisonB = Reel(f, "blanc");
			_floraisonJ = Reel(f, "jaune");
		}

		// Écrit la floraison au shader, lissée. Appelée chaque image par MajSaison.
		private void MajFloraison(ShaderMaterial m, bool net, float dt)
		{
			float cibleB = _floraisonB, cibleJ = _floraisonJ;
			if (_ceinture == null && _banc)
			{
				cibleB = FloraisonBanc(6f, 8f, 17f, 20f);
				cibleJ = FloraisonBanc(3f, 5f, 12f, 15f);
			}
			float a = net || _floraisonBVue < 0f ? 1f : 1f - Mathf.Exp(-dt / TauFloraisonS);
			Floraison(m, "f_blanc", ref _floraisonBVue, cibleB, a);
			Floraison(m, "f_jaune", ref _floraisonJVue, cibleJ, a);
		}

		private static void Floraison(ShaderMaterial m, string nom, ref float vue, float cible, float a)
		{
			if (vue == cible) return;
			vue = vue < 0f || Mathf.Abs(cible - vue) < 0.002f ? cible : Mathf.Lerp(vue, cible, a);
			m.SetShaderParameter(nom, vue);
		}

		// Banc F10 sans pont : même fenêtres que `fleurs_lisiere.FENETRES`, pour que les
		// captures de saison du banc restent lisibles. Jamais utilisé en jeu.
		private float FloraisonBanc(float debut, float plein, float finPlein, float fin)
		{
			float w = _semaineCible;
			if (w <= debut || w >= fin) return 0f;
			return w < plein ? (w - debut) / (plein - debut)
				: w > finPlein ? (fin - w) / (fin - finPlein) : 1f;
		}

		// Colonies du banc F10 (aucun pont) : un jeu fixe, le temps de juger le rendu.
		private static readonly ColonieBord[] ColoniesBancPrairie =
		{
			new(400f, 380f, 190f, 170f, false, 11u),
			new(1050f, 300f, 160f, 200f, true, 22u),
			new(1650f, 450f, 210f, 150f, false, 33u),
		};
		private static readonly ColonieBord[] ColoniesBancRiviere = { new(900f, 85f, 180f, 60f, true, 44u) };

		// Ajoute aux poses du tapis les fleurs des colonies du secteur. Sur une rivière, le
		// lit est peint ensuite : ce qui déborde sur l'eau est recouvert.
		private void SemerColonies(Secteur s)
		{
			if (s.Colonies == null) return;
			float z = ZoomConstr;
			float pas = Mathf.Max(PasFleurMinCm, PasFleurPx / (z * WorldView.PxPerCmX));
			float seuilW = DepthCm * 0.06f;
			int taille = TailleZoom(Piece.Fleur);
			foreach (ColonieBord c in s.Colonies)
			{
				Teinte t = c.Jaune ? Teinte.FleurJaune : Teinte.FleurBlanc;
				int nU = Mathf.CeilToInt(c.Ru * RayonEgare / pas), nD = Mathf.CeilToInt(c.Rd * RayonEgare / pas);
				for (int iu = -nU; iu <= nU; iu++)
					for (int id = -nD; id <= nD; id++)
					{
						uint h = HashCase(c.Graine, iu, id, 61u);
						float du = (iu + ((h >> 8 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
						float dd = (id + ((h >> 16 & 0xff) / 255f - 0.5f) * 0.9f) * pas;
						float u = c.U + du, d = c.Depth + dd;
						if (Melange(h) % 1024u / 1024f >= DensiteFleur(c, du, dd, u, d)) continue;
						if (u < 0f || u > WorldView.WorldCm) continue;
						float b = AmplitudeCm * Ondulation(s.SeedSecteur, u / 200f);
						if (d < b + seuilW * 0.4f || d > DepthCm - 10f) continue;
						float m = 1f - 0.20f * Mathf.Clamp(d / DepthCm, 0f, 1f);
						_poses.Add(new Pose(EdgePoint(s.Cote, u, d), Piece.Fleur, taille, Melange(h ^ 0x5bd1e995u), t, new Color(m, m, m)));
					}
			}
		}

		// Probabilité d'une fleur : dense au centre, éparse au bord, rare au-delà.
		private static float DensiteFleur(ColonieBord c, float du, float dd, float u, float d)
		{
			float x = du / c.Ru, y = dd / c.Rd;
			float r2 = x * x + y * y;
			if (r2 > 4f) return 0f;
			float lobes = BruitValeur(c.Graine, u / LobeCm, d / LobeCm, 63u) - 0.5f;
			float r = Mathf.Sqrt(r2) * (1f + LobeAmp * lobes);
			if (r > RayonEgare) return 0f;
			if (r > 1f) return DensiteEgaree;
			return Mathf.Lerp(DensiteCentre, DensiteBord, r * r);
		}
	}
}
