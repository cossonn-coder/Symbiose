// SYMBIOSE — PlantRenderer.Lianes.cs (partial, sprint FORMES DES PLANTES ⑥)
// Tomate, lierre, jasmin gardent leurs segments et leur taille au segment (croissance
// procédurale, conception §2). Seuls changent ce qui les habille : des tiges fines de la couleur
// de la fiche, et leurs vraies feuilles, à tous les paliers. Fini le « bonsaï » : un bois brun
// de 4 px minimum à ×4 portant des ovales en paquets.
// Les fiches : docs/vegetal/croissance/fiches_herbacees.md, §Segments conservés.
//
// 📖 Pédagogie : réutiliser sans dupliquer. Une feuille de liane se pose sur un point d'un segment
// exactement comme une feuille de port tige sur un point d'axe : on remplit les mêmes listes
// (`_axesTige`, `_feuillesPort`, `_tetesTige`) et le même peintre fait l'ordre du fond vers
// l'avant. Le squelette moteur remplace seulement la géométrie calculée de l'axe.
//
// Le fruit reste celui du moteur, posé au bout de son segment porteur (FruitPoint, que lit aussi la
// récolte au clic) ; les fruits arrivent à la taille de la fiche, plus au disque de 11 cm de rayon.
// Zéro Random (philo #3).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>L'habillage d'une liane. `Organes` : feuille, marque, tête, fruit et couleur de
		/// tige, lus par les fonctions des ports (`Feuilles` = folioles). `LongCm` : feuille adulte ;
		/// `EspaceCm` : une feuille tous les… ; `TigeMaxCm` : plafond de l'épaisseur montrée (lierre = `girth_max_cm` du moteur, sinon il ne grossit pas à l'écran) ;
		/// `Nappe` : le feuillage serré ferme une plaque sombre (lierre) ; `Crampons` : son accroche.</summary>
		private sealed record FicheLiane(FichePort Organes, float LongCm, float EspaceCm, bool Opposees, float TigeMaxCm,
			bool Nappe = false, bool Crampons = false, int FleursSite = 1);

		private static readonly Dictionary<string, FicheLiane> FichesLiane = new()
		{
			["Tomato"] = new(new FichePort(FormePort.Tige, 0f, 0f, 1f, Feuilles: 7, FormeFeuille.Composee, LargeurFeuille: 0.62f, Dressee: 0f,
				FormeTete.Etoile, TeteCm: 1f, Hampes: 0, EpaisseurTigeCm: 1f, Marque: MarqueFeuille.Gaufre,
				Tige: new(1, 0f, 0f, 0f, 0f, false, 0f, 0f, -0.25f, new Color("6a9a50")), Fruit: new(2.6f)),
				LongCm: 22f, EspaceCm: 9f, Opposees: false, TigeMaxCm: 1.2f, FleursSite: 3),
			["Ivy"] = new(new FichePort(FormePort.Tige, 0f, 0f, 1f, Feuilles: 0, FormeFeuille.Lierre, LargeurFeuille: 0.9f, Dressee: 0f,
				FormeTete.Boule, TeteCm: 1.6f, Hampes: 0, EpaisseurTigeCm: 1f, Marque: MarqueFeuille.Nervures,
				Tige: new(1, 0f, 0f, 0f, 0f, false, 0f, 0f, -0.1f, new Color("6a5a3e"))),
				LongCm: 7f, EspaceCm: 5f, Opposees: false, TigeMaxCm: 6f, Nappe: true, Crampons: true),
			["Jasmine"] = new(new FichePort(FormePort.Tige, 0f, 0f, 1f, Feuilles: 7, FormeFeuille.Composee, LargeurFeuille: 0.42f, Dressee: 0f,
				FormeTete.Etoile, TeteCm: 1f, Hampes: 0, EpaisseurTigeCm: 0.4f,
				Tige: new(1, 0f, 0f, 0f, 0f, false, 0f, 0f, -0.3f, new Color("5f9a48"))),
				LongCm: 7f, EspaceCm: 7f, Opposees: true, TigeMaxCm: 2f, FleursSite: 3),
		};

		// Lierre : 5 lobes en triangle, base échancrée. Étoilé depuis la base, comme la paume.
		private static readonly Vector2[] ContourLierre = Symetrique(new(0f, 0f), new(-0.08f, 0.5f), new(0.12f, 1f),
			new(0.3f, 0.42f), new(0.52f, 0.68f), new(0.62f, 0.22f), new(1f, 0f));

		private FicheLiane LianeDeLaPlante =>
			_structure != null && FichesLiane.TryGetValue(_structure.SpeciesName, out var l) ? l : null;

		/// <summary>Appelé par DrawVector : une liane vivante, à tous les paliers. Mort et
		/// caduc nu gardent le chemin commun du bois (false pour la mort).</summary>
		private bool DessinerLiane()
		{
			if (LianeDeLaPlante is not { } l || !string.IsNullOrEmpty(_deadStade)) return false;
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			_sitesPrairie.Clear();
			_axesTige.Clear();
			_tetesTige.Clear();
			_feuillesPort.Clear();
			Vector3 collet = _structure.ColletCm;
			Color col = TeintePrairie();
			FichePort f = l.Organes;
			CollecterLiane(l, collet, col);
			_feuillesPort.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			PeindreFeuillesEtAxes(f, col, f.Tige.Tige);
			PoserAccroche(l, collet);
			CollecterSitesFleur(l, collet);
			PoserTetesPort(f, col, 0f);
			PoserFruitsLiane(f, collet);
			_lotPrairie.DessinerSansMaille(this);
			PoserDetailsPrairie(col);
			DrawHighlight(collet);   // la taille au segment reste
			return true;
		}

		private void CollecterLiane(FicheLiane l, Vector3 collet, Color col)
		{
			float pix = PixelInterne, density = _structure.DensiteVisible;
			bool loin = !AuPalier(PaliersHautsMinZoom);
			float espace = l.EspaceCm * (loin ? 1.6f : 1f);
			FicheTige t = l.Organes.Tige;
			var segs = _structure.Segments;
			foreach (var s in segs)
			{
				int i = CleSegment(s);   // stable : une coupe ailleurs ne déplace rien (HOUPPIER ④)
				Vector3 a = s.Base - new Vector3(collet.X, collet.Y, 0f);
				Vector3 b = a + s.Dir * s.LengthCm;
				float large = Mathf.Clamp(s.ThicknessCm, 0.1f, l.TigeMaxCm) * WorldView.PxPerCmX;
				_axesTige.Add((a, b, Mathf.Max(large, pix * 1.25f)));
				if (!IsLeafy(s) || density <= 0f) continue;
				if (l.Nappe)
					_lotPrairie.Ligne(Iso(a.X, a.Y, a.Z), Iso(b.X, b.Y, b.Z), Ton(col, 1), l.LongCm * 1.1f * WorldView.PxPerCmX);
				float g = LeafGrowthFactor(s);
				// Arrondi, pas troncature : à emit 20 (HOUPPIER ①) la troncature perdait jusqu'à une
				// feuille par segment, le jasmin à ×4 passait d'une feuille tous les 8 cm à 20.
				int n = Mathf.Max(1, Mathf.RoundToInt(s.LengthCm / espace));
				float az = Mathf.Atan2(PerpFeuilles(s).Y, PerpFeuilles(s).X);
				for (int j = 0; j < n; j++)
				{
					if (Hash01(17, i, j) >= density) continue;
					Vector3 p = a.Lerp(b, (j + 0.5f) / n);
					p.Z = Mathf.Max(p.Z - LeafDropCm(p.Z), 0.5f);
					float cote = (i + j) % 2 == 0 ? 1f : -1f;
					float ang = az + (cote < 0f ? Mathf.Pi : 0f) + (Hash01(421, i, j) - 0.5f) * 1.1f;
					float lg = Mathf.Max(l.LongCm * g * Mathf.Lerp(0.7f, 1f, Hash01(423, i, j)), 1f);
					int k = (i & 0xFFFFF) * 41 + j * 2;   // i = clé stable : borné, jamais négatif
					// Rayon infini : une liane n'a pas de rayon de port, sa feuille garde sa taille. Densité déjà tirée.
					AjouterFeuilleTige(l.Organes, p, ang, lg, Hash01(13, i, j), float.MaxValue, 1f, k, t.Penche);
					if (l.Opposees) AjouterFeuilleTige(l.Organes, p, ang + Mathf.Pi, lg, Hash01(13, i, j + 7), float.MaxValue, 1f, k + 1, t.Penche);
				}
			}
		}

		// Lierre : crampons le long de la tige ; jasmin palissé : un lien clair par rameau. Dès ×8.
		private void PoserAccroche(FicheLiane l, Vector3 collet)
		{
			if (!AuPalier(PalierOrganesZoom)) return;
			if (!l.Crampons && string.IsNullOrEmpty(_supportKind)) return;
			float pix = PixelInterne;
			var segs = _structure.Segments;
			for (int i = 0; i < segs.Count; i++)
			{
				var s = segs[i];
				Vector3 a = s.Base - new Vector3(collet.X, collet.Y, 0f);
				Vector3 b = a + s.Dir * s.LengthCm;
				if (!l.Crampons)
				{
					Vector2 q = Iso(a.X, a.Y, a.Z);
					_lotPrairie.Ligne(q + new Vector2(-pix * 2f, 0f), q + new Vector2(pix * 2f, -pix), Ton(BoisLien, 3), pix * 2f);
					continue;
				}
				int n = Mathf.Max(1, (int)(s.LengthCm / 3f));
				Color c = Ton(l.Organes.Tige.Tige, 1);
				for (int j = 0; j < n; j++)
				{
					Vector3 p = a.Lerp(b, (j + 0.5f) / n);
					Vector2 q = Iso(p.X, p.Y, p.Z);
					float sens = j % 2 == 0 ? 1f : -1f;
					_lotPrairie.Ligne(q, q + new Vector2(sens * pix * 3f, pix * 2f), c, pix);
				}
			}
		}
		private static readonly Color BoisLien = new Color("c8b888");

		// Apex = fleurs. Plusieurs fleurs par site, au hash : grappe de tomate, bouquet de jasmin.
		private void CollecterSitesFleur(FicheLiane l, Vector3 collet)
		{
			var sites = OrganSites();
			float e = l.Organes.TeteCm * 2.5f;
			for (int k = 0; k < sites.Count; k++)
			{
				Vector3 p = sites[k] - new Vector3(collet.X, collet.Y, 0f);
				for (int m = 0; m < l.FleursSite; m++)
				{
					var d = m == 0 ? Vector3.Zero : new Vector3((Hash01(431, k, m) - 0.5f) * e * 2f, (Hash01(433, k, m) - 0.5f) * e * 2f, -e * Hash01(435, k, m));
					_tetesTige.Add((p + d, Vector2.Right, GraineIndividu + k * 13 + m));
				}
			}
		}

		// Fruits du moteur au bout de leur segment : le même point que la récolte au clic.
		private void PoserFruitsLiane(FichePort f, Vector3 collet)
		{
			if (f.Fruit == null || _structure.Fruits.Count == 0) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			for (int i = 0; i < _structure.Fruits.Count; i++)
			{
				var fr = _structure.Fruits[i];
				Vector3 p = FruitPoint(fr);
				Vector2 c = Iso(p.X - collet.X, p.Y - collet.Y, p.Z);
				PoserFruit(c, RayonFruit(f.Fruit, fr.Masse), f.Fruit.Allonge, FruitColor(pal, fr.Maturite), i);
			}
		}

		// Les nervures pâles, motif de l'espèce (fiche) : une par lobe, depuis la base.
		private void PoserNervuresLierre(FeuillePosee fe, Color col)
		{
			Color pale = Ton(col, 4);
			Vector2 baseF = PointFeuille(fe, 0.05f, 0f);
			foreach (float cote in new[] { 1f, -1f })
			{
				_lotPrairie.Ligne(baseF, PointFeuille(fe, 0.12f, 0.9f * cote), pale, PixelInterne);
				_lotPrairie.Ligne(baseF, PointFeuille(fe, 0.5f, 0.62f * cote), pale, PixelInterne);
			}
		}
	}
}
