// SYMBIOSE — DecorLayer.Charpente.cs (sprint LISIÈRE & CHARGEMENT ②, décision L1)
// Partial de DecorLayer : le BOIS des arbres de lisière sur celui du jardin (S2). La charpente —
// fût, axe dans la couronne, charpentières — n'est plus faite de trapèzes cernés mais de RUBANS
// lissés (RubanTexture, la primitive du bois des plantes) :
//   • deux flancs en aplats ORIENTÉS par la normale du ruban (le soleil réel éclaire l'un) ;
//   • par-dessus, la BANDE D'ÉCORCE cuite de l'essence (S2, `ecorces.json`), plaquée en u en
//     travers, v = longueur d'arc en cm → l'écorce garde son échelle à tous les paliers.
// Le fût a un PIED ÉVASÉ (contreforts) ; le sapin est monté en ÉTAGES (Houppiers.cs).
//
// UN SEUL ENVOI : les bandes d'écorce des essences de lisière sont RECOPIÉES dans l'atlas du décor
// (sous les étagères du kit, même encodage de codes que les pièces : palette de l'écorce, classe
// shader) ; les triangles du ruban se versent dans le lot du décor (`RubanTexture.Verser`) et
// passent par son encodeur de sommets (valeur du plan, vent, phase du pied) comme une pièce.
//
// 📖 Pédagogie — pourquoi recopier plutôt que lier la planche d'écorces : une maille Godot n'a
// qu'UNE texture. Lier une deuxième planche couperait la lisière en deux envois (et en deux
// mailles par palier). Recopier quelques bandes (≈ 0,1 Mo) dans l'atlas existant, c'est comme
// regrouper deux tables dans la même page mémoire pour ne faire qu'un accès DMA.
//
// Classes shader (DecorLayer.Saison.cs) inchangées : le fût reste inerte, les charpentières
// « sans saison » (neige et givre s'y posent). Tout reste dans l'ellipse de l'enveloppe
// (`DansCouronne`, Branches.cs) : la courbe d'une charpentière reste dans le triangle de ses trois
// points. Interrupteur Maj+F11 / SYMBIOSE_SPLATS=0 : l'ancien dessin (fuseaux, traits) intact.
// Déterministe (hash de la graine du secteur), purement visuel : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Âges d'écorce servis : la branche (charpentières) et le tronc (fût, axe). Le rameau, fin
		// d'un pixel en lisière, n'aurait jamais la largeur de se lire (EcorceMinPx).
		private static readonly int[] AgesLisiere = { Ecorces.Branche, Ecorces.Tronc };
		private const int PalierEcorces = 4;         // la maille la plus fine est ×4 (③ : paliers hauts)
		private const float EcorceMinPx = 4f;        // largeur interne sous laquelle la bande ne se lit plus (= jardin)
		private const int TraversMax = 3;            // bandes côte à côte au plus sur un fût large
		// Texels de bande par px interne au-delà desquels la bande, échantillonnée au plus proche,
		// tourne au sel (mesuré au ② : bouleau gris tacheté à ×1-×2, bande ×4 réduite 3 à 7 fois).
		// Au-delà, le fût garde ses stries procédurales (orientations 11/12 du shader).
		private const float EcorceReductionMax = 2f;
		private const float PiedEvase = 0.6f;        // surlargeur du pied (× demi-largeur du fût)
		private const float PiedHauteur = 0.15f;     // part du fût où l'évasement s'éteint
		private const float FlecheFut = 0.18f;       // flèche latérale du fût (× demi-largeur), au hash

		// Une bande recopiée : rectangle dans l'atlas du décor, période et diamètre de cuisson (cm).
		private readonly record struct BandeDecor(Rect2I Rect, float PeriodeCm, float DCm);
		private static readonly Dictionary<(string, int), BandeDecor> _bandesDecor = new();
		private static readonly List<(Rect2I r, byte[] codes, long src)> _codesEcorces = new();
		private static readonly System.Func<int, bool> Toujours = _ => true;

		// Maj+F11 change la GÉOMÉTRIE du bois (ruban ou fuseau) : les mailles se reconstruisent.
		private static int _versionBois;
		private int _versionMailles;

		/// <summary>Le bois de S2 sert-il ? Interrupteur des splats allumé et bandes rangées.</summary>
		private static bool BoisCuit => PlantRenderer.SplatsActifs && _bandesDecor.Count > 0;

		/// <summary>Range les bandes d'écorce des essences de la lisière à la suite des étagères du
		/// kit (`x`, `y`, `hRang` de AssurerKitDecor) et les ajoute aux codes de l'atlas. Bande
		/// absente (planche non cuite) : l'essence garde son fuseau uni.</summary>
		private static void RangerEcorces(ref int x, ref int y, ref int hRang)
		{
			_bandesDecor.Clear();
			_codesEcorces.Clear();
			foreach (var sil in Silhouettes.Values)
				foreach (int age in AgesLisiere)
				{
					if (_bandesDecor.ContainsKey((sil.Bois, age))
						|| !Ecorces.CodesBruts(sil.Bois, age, PalierEcorces, out byte[] codes, out Vector2I s, out float per, out float d))
						continue;
					if (x + s.X > AtlasW) { x = 0; y += hRang; hRang = 0; }
					var r = new Rect2I(x, y, s.X, s.Y);
					int classe = age == Ecorces.Tronc ? ClasseInerte : ClasseSansSaison;
					_codesEcorces.Add((r, codes, SourceCouleur(sil.Ecorce) | (long)classe << DecalageClasse));
					_bandesDecor[(sil.Bois, age)] = new BandeDecor(r, per, d);
					x += s.X + 1;
					hRang = Mathf.Max(hRang, s.Y + 1);
				}
			_kitCodes.AddRange(_codesEcorces);
		}

		/// <summary>Maj+F11 : la géométrie du bois change avec la source du kit.</summary>
		private static void BasculerBois()
		{
			_kitCodes.AddRange(_codesEcorces);   // l'atlas réécrit garde ses bandes
			_versionBois++;
		}

		/// <summary>Chaque image : mailles jetées si l'interrupteur a changé le bois.</summary>
		private void SuivreBois()
		{
			if (_versionMailles == _versionBois) return;
			_versionMailles = _versionBois;
			InvaliderMailles();
			QueueRedraw();
		}

		/// <summary>Fût en ruban, de `pied` à `apex` : pied évasé, légère flèche au hash, aminci
		/// de moitié sous la couronne (comme l'ancien fuseau). `w` = demi-largeur au sol.</summary>
		private void FutRuban(Vector2 pied, Vector2 apex, float w, TreeSilhouette sil, Color mod, uint hb)
		{
			float[] t = { 0f, 0.05f, 0.15f, 0.4f, 0.7f, 1f };
			var pts = new Vector2[t.Length];
			var demi = new float[t.Length];
			float fleche = ((hb >> 3 & 0xff) / 255f - 0.5f) * 2f * FlecheFut * w;
			for (int k = 0; k < t.Length; k++)
			{
				float evase = t[k] < PiedHauteur ? PiedEvase * Mathf.Pow(1f - t[k] / PiedHauteur, 2f) : 0f;
				demi[k] = w * (Mathf.Lerp(1f, 0.5f, t[k]) + evase);
				pts[k] = pied.Lerp(apex, t[k]) + Vector2.Right * fleche * Mathf.Sin(Mathf.Pi * t[k]);
			}
			bool cuite = Ruban(pts, demi, sil.Bois, Ecorces.Tronc, sil.Ecorce * mod, mod, hb);
			if (cuite || sil.Port != TreePort.Elance || !DetailsVisibles) return;
			for (float tl = 0.2f; tl < 0.95f; tl += 0.18f)   // bouleau sans bande : lenticelles d'avant
			{
				Vector2 c = pied.Lerp(apex, tl);
				float d = w * Mathf.Lerp(1f, 0.5f, tl);
				_lot.Ligne(c + Vector2.Left * d * 0.6f, c + Vector2.Right * d * 0.2f, Palette16.EcorceLenticelle, 1f / ZoomConstr);
			}
		}

		/// <summary>Charpentière lissée : courbe du 2ᵉ degré qui passe par `depart`, `coude` et
		/// `bout` (5 points), demi-largeur `racine` → `milieu` → `fin`.</summary>
		private void CharpentiereRuban(Vector2 depart, Vector2 coude, Vector2 bout, float racine, float milieu,
			float fin, string bois, Color col, Color mod, uint h)
		{
			Vector2 ctrl = 2f * coude - 0.5f * (depart + bout);   // la courbe passe par le coude à t = ½
			var pts = new Vector2[5];
			var demi = new float[5];
			for (int k = 0; k < 5; k++)
			{
				float s = k / 4f, u = 1f - s;
				pts[k] = u * u * depart + 2f * u * s * ctrl + s * s * bout;
				demi[k] = s < 0.5f ? Mathf.Lerp(racine, milieu, s * 2f) : Mathf.Lerp(milieu, fin, s * 2f - 1f);
			}
			Ruban(pts, demi, bois, Ecorces.Branche, col, mod, h);
		}

		/// <summary>Axe prolongé dans la couronne, en ruban (de l'apex du fût au sommet de l'axe).</summary>
		private void AxeRuban(Vector2 apex, Vector2 sommet, float w0, float w1, string bois, Color col, Color mod, uint hb) =>
			_ = Ruban(new[] { apex, apex.Lerp(sommet, 0.5f), sommet }, new[] { w0, Mathf.Lerp(w0, w1, 0.5f), w1 },
				  bois, Ecorces.Tronc, col, mod, hb);

		/// <summary>Un ruban de bois : flancs orientés (deux aplats par pas, un seul sous 1 px
		/// interne), puis la bande d'écorce `bois` × `age` versée dans le même lot si elle se lit à ce
		/// palier (largeur, réduction). Sans bande, un fût garde ses stries procédurales. `col` =
		/// écorce × plan (aplats), `mod` = plan (bande). Vrai si la bande est posée.</summary>
		private bool Ruban(Vector2[] pts, float[] demi, string bois, int age, Color col, Color mod, uint h)
		{
			Vector2[] nrm = RubanTexture.Normales(pts);
			int mi = pts.Length / 2;
			float largeurPx = 2f * demi[mi] * ZoomConstr;
			bool bande = _bandesDecor.TryGetValue((bois, age), out var b) && largeurPx >= EcorceMinPx;
			// Fût large : plusieurs bandes côte à côte, chacune à l'échelle de sa cuisson (diamètre
			// `DCm`), chacune décalée en hauteur — un rhytidome ne se répète pas d'une colonne à l'autre.
			// Jamais plus de colonnes que la réduction ne permet (sinon un fût étroit tournerait au sel).
			int n = bande ? Mathf.Clamp(Mathf.Min(Mathf.RoundToInt(2f * demi[mi] / WorldView.PxPerCmX / b.DCm),
				Mathf.FloorToInt(largeurPx * EcorceReductionMax / b.Rect.Size.X)), 1, TraversMax) : 1;
			bande &= b.Rect.Size.X * n / largeurPx <= EcorceReductionMax;
			bool stries = !bande && age == Ecorces.Tronc;
			for (int k = 0; k + 1 < pts.Length; k++)
			{
				Vector2 perp = RubanTexture.Perp(pts[k + 1] - pts[k]);
				if (perp == Vector2.Zero) continue;
				bool deux = demi[k] * ZoomConstr >= 1f;
				for (int c = 0; c < (deux ? 2 : 1); c++)
				{
					float u0 = deux && c == 1 ? 0f : -1f, u1 = deux && c == 0 ? 0f : 1f;
					// Côté u > 0 = côté de la normale : son orientation est celle de `perp`.
					Aplats(!deux ? OPlat : stries ? (c == 0 ? OrientEcorceG : OrientEcorceD) : OrientDe(c == 0 ? -perp : perp));
					_lot.PolygoneConvexe(new[] {
						pts[k] + nrm[k] * demi[k] * u0, pts[k] + nrm[k] * demi[k] * u1,
						pts[k + 1] + nrm[k + 1] * demi[k + 1] * u1, pts[k + 1] + nrm[k + 1] * demi[k + 1] * u0 }, col);
				}
			}
			Aplats(OPlat);
			if (!bande) return false;
			var v = new float[pts.Length];
			for (int k = 1; k < pts.Length; k++) v[k] = v[k - 1] + pts[k].DistanceTo(pts[k - 1]) / WorldView.PxPerCmZ;
			for (int i = 0; i < n; i++)
			{
				float dec = (h >> (4 + i * 5) & 31u) / 31f * b.PeriodeCm;
				RubanTexture.PoserBandePeriodique(pts, demi, nrm, v, -1f + 2f * i / n, -1f + 2f * (i + 1) / n,
					_kitTex, b.Rect, b.PeriodeCm, dec, mod, Toujours);
			}
			RubanTexture.Verser(_lot, _kitTex);
			return true;
		}

		/// <summary>SAPIN EN ÉTAGES : des rangs de bouquets conifères de plus en plus courts vers le
		/// haut (le cône), aux bouts un peu retombants ; l'enveloppe sombre se voit entre deux étages.
		/// Même règle que le sapin du jardin (S2 ⑤) : la longueur suit la distance à la cime.</summary>
		private void EtagesSapin(Vector2 c0, float rx, float ry, Piece f, int taille, Vector2 sz, Teinte t, Color mod, uint hb)
		{
			int etages = Mathf.Clamp(Mathf.RoundToInt(2f * ry / (sz.Y * 0.9f)), 3, 8);
			for (int e = 0; e < etages; e++)
			{
				float haut = (e + 0.5f) / etages;                       // 0 bas → 1 cime
				float y = ry - 2f * ry * (e + 0.3f) / etages;          // haut de l'étage (repère c0)
				float demiL = rx * (1f - haut) * (0.9f + 0.15f * ((hb >> (e * 3) & 7u) / 7f));
				int nb = Mathf.Clamp(Mathf.RoundToInt(2f * demiL / (sz.X * 0.75f)), 1, 8);
				for (int j = 0; j < nb && _bouquets.Count < BouquetsMax; j++)
				{
					uint h = HashCase(hb, e, j, 5u);
					float x = nb == 1 ? 0f : Mathf.Lerp(-demiL, demiL, j / (nb - 1f)) + ((h & 0xff) / 255f - 0.5f) * sz.X * 0.3f;
					float chute = Mathf.Abs(x) / Mathf.Max(demiL, 1f) * sz.Y * 0.35f;   // bouts retombants
					_bouquets.Add(new Pose(c0 + new Vector2(x, y + chute + sz.Y * 0.5f), f, taille, h, t, mod));
				}
			}
			// La flèche : un bouquet à la cime.
			_bouquets.Add(new Pose(c0 + new Vector2(0f, -ry + sz.Y), f, taille, HashCase(hb, etages, 0, 5u), t, mod));
		}
	}
}
