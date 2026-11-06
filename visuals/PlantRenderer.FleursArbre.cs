// SYMBIOSE — PlantRenderer.FleursArbre.cs (partial, sprint VERGER VIVANT ④)
// Les FLEURS D'UN ARBRE, en bouquets sur les brindilles, à tous les paliers.
//  · Densité CONTINUE avec le scalaire moteur `floraison` : des premières fleurs (~0,15) au plein
//    (~0,85), puis la même courbe à la descente. Plus de tout ou rien à 0,5.
//  · Bouquets : un cerisier porte ses fleurs par 2 à 4, un pommier par 3 à 5 (corymbes [odg]).
//  · Boutons : à la montée, une part des fleurs est encore en bouton (rose franc chez le pommier,
//    blanc verdâtre chez le cerisier) ; au pic tout est ouvert ; à la descente, plus de bouton.
//  · ×0,5 à ×4 : gerbes de fleurs, un bouquet par tracé (GerbesFleurs.cs) ; ×8 et plus : fleurs une
//    à une en pièces (PiecesFleur.cs), cinq pétales, liseré rosé chez le pommier, étamines dès ×16.
// Les pétales qui tombent au sol sont dans PetalLayer.cs (vue seule).
//
// 📖 Pédagogie — montée ou descente ? Le moteur n'exporte qu'un scalaire. 0,47 peut être une
// floraison qui monte ou qui fane. La vue garde donc le PIC vu depuis le début de la floraison,
// comme un détecteur de crête en électronique : sous le pic, ça descend. Limite : un jeu chargé en
// pleine descente montre une semaine de boutons, la suivante le corrige.
//
// 📖 Pourquoi un plafond APPLIQUÉ AU HASH et pas un `break`. Le bois est trié du fond vers l'avant :
// s'arrêter à N fleurs vidait l'avant de l'arbre. On calcule plutôt la part à garder et on la
// tire au hash sur toutes les brindilles : la couronne reste uniformément fleurie.
//
// Zéro Random (philo #3) : canaux 543, 571-581 ; golden non concerné (vue seule).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Seuils de la densité de fleurs [choix, à juger au F5] : première fleur, couronne pleine.
		private const float FloraisonApparition = 0.15f, FloraisonPleine = 0.85f;
		// Part des brindilles fleuries au plein (le reste porte des feuilles seules) [choix].
		private const float PartBrindillesFleuries = 0.85f;
		// Boutons : tous fermés sous 0,5 à la montée, tous ouverts à 0,9 [choix].
		private const float BoutonsOuverts0 = 0.5f, BoutonsOuverts1 = 0.9f;
		// Pic oublié sous ce seuil : la floraison suivante repart de zéro.
		private const float FloraisonFinie = 0.005f;
		// Plafond de dessin par arbre à ×8 et plus [choix, mesuré au bilan ④] ; en dessous, gerbes de fleurs.
		private const int FleursArbreMax = 1500;

		/// <summary>Bouquet (fleurs par brindille), écart des fleurs du bouquet, couleur du bouton.</summary>
		private readonly record struct FicheFleurArbre(int BouquetMin, int BouquetMax, float BouquetCm, Color Bouton, Color Bord);

		// Cerisier : blanc pur, bouton blanc verdâtre ; pommier : bouton rose franc, fleur blanc rosé
		// au bord rose [odg, fiches_arbres.md].
		private static readonly Dictionary<string, FicheFleurArbre> FleursArbres = new()
		{
			["CherryTree"] = new(3, 5, 3f, new Color("dfe6c8"), new Color("c8c4c0")),
			["AppleTree"] = new(3, 5, 3.5f, new Color("d8708e"), new Color("e08ca6")),
		};

		/// <summary>Une fleur posée : point (cm, repère tuile), bouton ou ouverte, graine de variation.</summary>
		private readonly record struct FleurArbre(Vector3 P, bool Bouton, int K);

		private readonly List<FleurArbre> _fleursArbre = new();
		private float _floraisonPic;

		/// <summary>Au snapshot : retient le pic de la floraison en cours (détecteur de crête).</summary>
		private void NoterFloraison()
		{
			float f = _structure?.Floraison ?? 0f;
			_floraisonPic = f < FloraisonFinie ? 0f : Mathf.Max(_floraisonPic, f);
		}

		/// <summary>Vrai quand la floraison est passée par son pic et redescend.</summary>
		private bool FloraisonFane => _structure != null && _structure.Floraison < _floraisonPic - 0.02f;

		private bool FleursCachees => _structure.SpeciesName == "Fig";   // la fleur est dans la figue (fiche)

		/// <summary>Pétales au sol sous la couronne, 0..1 (PetalLayer) : ils s'accumulent à la descente,
		/// puis fondent avec la fin de la floraison. Pas de pétale chez les arbres à chatons.</summary>
		internal float PetalesAuSol
		{
			get
			{
				if (!Houppier || FleursCachees || Chatons.Contains(_structure.SpeciesName) || !FloraisonFane) return 0f;
				float f = _structure.Floraison;
				return (1f - f / _floraisonPic) * Mathf.Clamp(f / 0.05f, 0f, 1f);
			}
		}

		internal Color TonPetale =>
			Palettes.TryGetValue(_structure.SpeciesName, out var pal) ? pal.Flower : DefaultPalette.Flower;

		private FicheFleurArbre FicheFleurs(in OrganPalette pal) =>
			FleursArbres.TryGetValue(_structure.SpeciesName, out var f) ? f : new(1, 2, 2.5f, pal.Flower.Darkened(0.1f), pal.Flower.Darkened(0.25f));

		/// <summary>Part des brindilles fleuries, continue de 0 (≤ 0,15) à 1 (≥ 0,85).</summary>
		private float PartFleursArbre() =>
			Mathf.Clamp((_structure.Floraison - FloraisonApparition) / (FloraisonPleine - FloraisonApparition), 0f, 1f);

		private float PartBoutons() =>
			FloraisonFane ? 0f : 1f - Mathf.SmoothStep(BoutonsOuverts0, BoutonsOuverts1, _structure.Floraison);

		/// <summary>Les fleurs de l'arbre une à une, en bouquets (×8 et plus) : au bout de chaque bout de bois
		/// et au milieu des brindilles (éperons). Le bout suit le même tirage (canal 543) que les gerbes de
		/// fleurs des paliers bas : la même brindille fleurit à tous les paliers.</summary>
		private List<FleurArbre> FleursHouppier(in OrganPalette pal)
		{
			_fleursArbre.Clear();
			float part = PartFleursArbre() * PartBrindillesFleuries;
			if (part <= 0f || FleursCachees) return _fleursArbre;
			FicheFleurArbre fiche = FicheFleurs(pal);
			var bois = BoisDuHouppier();
			int sites = 0;
			foreach (var e in bois) sites += e.EstRameau ? 1 : 2;
			float parBouquet = (fiche.BouquetMin + fiche.BouquetMax) * 0.5f;
			part *= Mathf.Min(1f, FleursArbreMax / Mathf.Max(sites * part * parBouquet, 1f));
			float boutons = PartBoutons();
			foreach (var e in bois)
				for (int site = 0; site < (e.EstRameau ? 1 : 2); site++)
				{
					int rang = e.Rang + site * 4096;
					if (Hash01(543, e.Cle, rang) >= part) continue;
					int n = fiche.BouquetMin + (int)(Hash01(571, e.Cle, rang) * (fiche.BouquetMax - fiche.BouquetMin + 1));
					Vector3 recul = (e.A - e.B).Normalized(), bout = site == 0 ? e.B : e.B.Lerp(e.A, 0.45f);
					int k0 = (Melange(e.Cle, rang) & 0xFFFFF) * 8;
					for (int j = 0; j < n; j++)
					{
						// La première au bout, les autres en couronne un peu en retrait, sur le même éperon.
						float a = Mathf.Tau * (j / (float)n + Hash01(573, e.Cle, rang));
						float d = j == 0 ? 0f : fiche.BouquetCm * Mathf.Lerp(0.7f, 1.1f, Hash01(575, k0, j));
						Vector3 p = bout + recul * (j * 0.8f) + new Vector3(d * Mathf.Cos(a), d * Mathf.Sin(a), (Hash01(577, k0, j) - 0.5f) * d);
						_fleursArbre.Add(new FleurArbre(p, Hash01(579, k0, j) < boutons, k0 + j));
					}
				}
			return _fleursArbre;
		}

		/// <summary>Paliers bas (×0,5 à ×2) : gerbes de fleurs (GerbesFleurs.cs).</summary>
		private void DrawFleuronsHouppier()
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			DrawGerbesFleurs(pal);
		}

		// ---------------------------------------------------------------------------
		// ×4 ET PLUS
		// ---------------------------------------------------------------------------

		// Fleur d'arbre relevée d'un tiers comme ses limbes (Rameaux.cs), sinon perdue entre eux [choix] :
		// 4 cm de diamètre, d'où les côtés des pièces de PiecesFleur.cs.
		private const float FleurArbreRayonCm = 2f;

		/// <summary>×4 : gerbes de fleurs ; ×8+ : chaque fleur des bouquets en pièce ; chatons pour le noyer et ses pareils.</summary>
		private void DrawFleursHouppier(Vector3 c, OrganPalette pal)
		{
			if (!AuPalier(PalierOrganesZoom)) { DrawGerbesFleurs(pal); return; }
			if (_structure.Floraison < FloraisonApparition || FleursCachees) return;
			FicheFleurArbre fiche = FicheFleurs(pal);
			if (!Chatons.Contains(_structure.SpeciesName)) { DrawPiecesFleurs(c, pal, fiche); return; }
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			foreach (var f in FleursHouppier(pal))
				PoserChaton(Iso(f.P.X - c.X, f.P.Y - c.Y, f.P.Z), f.Bouton ? fiche.Bouton : pal.Flower, f.K);
			_lotPrairie.DessinerSansMaille(this);
		}
	}
}
