// SYMBIOSE — PlantRenderer.Ports.cs (partial, sprint FORMES DES PLANTES ②)
// Le SOCLE des ports dessinés. Une espèce à port ne dessine plus ses segments : la vue
// garde ce que dit le moteur (hauteur, stade, floraison, fruits, santé, mort, coupe) et
// dessine sa forme depuis une ligne de table (PlantRenderer.PortsFiches.cs), qui traduit
// docs/vegetal/croissance/fiches_herbacees.md. Conception : docs/rendu/pixelart/
// conception_formes_plantes.md §4. Même chemin que la prairie (PlantRenderer.Prairie.cs),
// dont ce socle réutilise le lot, la teinte et les détails.
//
// Ce fichier : le dispatch, la taille du port, sa boîte de cuisson, le lissage de hauteur,
// la clé de recuisson, le clic. Zéro écologie, zéro Random (philo #3).
//
// 📖 Pédagogie : pourquoi une CLÉ de recuisson. Le pont envoie chaque semaine une structure
// neuve pour chaque plante. Une image cuite coûte cher à refaire. Comme un port dessine peu
// de choses, on les résume en un petit enregistrement, comparé à celui de la semaine d'avant :
// même contenu, l'image reste bonne. Un `record struct` compare ses champs un à un, c'est le
// `memcmp` d'un struct en C, sans qu'on ait à l'écrire.
//
// 📖 Pédagogie : pourquoi LISSER. Le moteur donne une hauteur par stade : la molène passe de
// 20 à 150 cm en une semaine [catalogue, à growth_factor et gène neutres]. Vrai pour l'ombre
// et la lumière, faux à l'œil. La vue rejoint donc `height_cm` par pas, et rien côté moteur.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private FichePort FicheDeLaPlante =>
			_structure != null && FichesPort.TryGetValue(_structure.SpeciesName, out var f) ? f : null;

		/// <summary>La taille vise toute la plante : ni `target.segment` ni surlignage. Prairie
		/// comprise (conception §4.4).</summary>
		internal bool TailleAuPied => FicheDeLaPlante != null || PortDeLaPlante != PortPrairie.Aucun;

		// Coupe et pincement sur la mesure du port, tous ports confondus (conception §4.4).
		private (float R, float H) AvecTaille((float R, float H) m) =>
			(m.R * (1f + 0.2f * _structure.Pince),
			 Mathf.Max(1f, m.H * (1f - 0.6f * _structure.Rabattu) * (1f - 0.15f * _structure.Pince)));

		// ---------------------------------------------------------------------------
		// HAUTEUR LISSÉE
		// ---------------------------------------------------------------------------

		// Hauteur montrée, cm ; < 0 = première semaine de ce nœud, posée d'emblée.
		private float _hauteurLisseeCm = -1f;
		// Part de l'écart comblée par semaine : ~6 semaines, la durée des stades qui sautent.
		private const float PasLissage = 1f / 6f;
		private const float PasLissageMinCm = 2f;

		private void LisserHauteur()
		{
			float cible = _structure.HeightCm;
			if (_hauteurLisseeCm < 0f) { _hauteurLisseeCm = cible; return; }
			float pas = Mathf.Max(PasLissageMinCm, Mathf.Abs(cible) * PasLissage);
			_hauteurLisseeCm = Mathf.MoveToward(_hauteurLisseeCm, cible, pas);
		}

		// ---------------------------------------------------------------------------
		// MESURE ET BOÎTE
		// ---------------------------------------------------------------------------

		// Taille d'un pied (0..1) : la hauteur moteur rapportée à celle de son feuillage adulte.
		private float CroissancePort(FichePort f) =>
			Mathf.Clamp(_hauteurLisseeCm / f.HauteurAdulteCm, 0.2f, 1f);

		// Hampe levée : par le stade (bisannuelle, ail) ou par la floraison (pissenlit).
		private bool HampeLevee(FichePort f)
		{
			if (MortPrairie || f.Hampes == 0) return false;
			if (f.StadesHampe != null && System.Array.IndexOf(f.StadesHampe, _structure.StageName) >= 0)
				return true;
			return _structure.Floraison >= FloraisonHampe;
		}

		private float HauteurFeuilles(FichePort f) =>
			Mathf.Min(f.HautFeuillesCm * CroissancePort(f), _hauteurLisseeCm);

		// (rayon, hauteur) du port dessiné, en cm, comme MesurePrairie.
		private (float R, float H) MesurePort(FichePort f) =>
			AvecTaille((f.RayonCm * CroissancePort(f),
				f.Forme == FormePort.Volubile ? HauteurVolubile(f) : HampeLevee(f) ? _hauteurLisseeCm : HauteurFeuilles(f)));

		/// <summary>Appelé par MesurerPort (Paliers.cs) : tapis, ombre, picking et vent suivent
		/// le port dessiné, plus les segments. L'ombre retrouve la vraie hauteur.</summary>
		private void MesurerPortDessine()
		{
			if (FicheDeLaPlante is not { } f) return;
			LisserHauteur();
			(_rayonReelCm, _hauteurReelCm) = MesurePort(f);
			_spreadCm = _rayonReelCm;
			_heightCm = _hauteurReelCm;
		}

		// Plaqué au sol, sans hampe : ne se couche pas au vent, deux poses suffisent.
		private bool PortPlaque => FicheDeLaPlante is { } f && !HampeLevee(f) && f.Dressee < 0.5f;

		private bool BoitePort(out Rect2 r)
		{
			r = default;
			if (FicheDeLaPlante is not { } f) return false;
			var (rayon, h) = MesurePort(f);
			r = new Rect2(Vector2.Zero, Vector2.Zero);
			// Le haut de la boîte : hauteur + tête. Les feuilles arquées et les têtes restent
			// sous le rayon du port, dont les coins passent par Iso, donc par la flexion.
			foreach (float z in new[] { 0f, h + f.TeteCm * 1.5f })
			{
				r = r.Expand(Iso(rayon, -rayon, z)).Expand(Iso(-rayon, rayon, z))
					 .Expand(Iso(rayon, rayon, z)).Expand(Iso(-rayon, -rayon, z));
			}
			if (f.Forme == FormePort.Volubile) r = EtendreBoiteVolubile(r, f, rayon, h);
			r = r.Grow(MargePrairiePx + f.TeteCm * WorldView.PxPerCmX);
			return true;
		}

		// ---------------------------------------------------------------------------
		// DISPATCH
		// ---------------------------------------------------------------------------

		private bool DessinerPort()
		{
			if (FicheDeLaPlante is not { } f) return false;
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			_sitesPrairie.Clear();
			Color col = TeintePrairie();
			switch (f.Forme)
			{
				case FormePort.Tige: DessinerTige(f, col); break;
				case FormePort.Chaume: DessinerChaume(f, col); break;
				case FormePort.Tapis: DessinerTapis(f, col); break;
				case FormePort.Buisson: DessinerBuisson(f, col); break;
				case FormePort.Rampante: DessinerRampante(f, col); break;
				case FormePort.Volubile: DessinerVolubile(f, col); break;
				default: DessinerRosette(f, col); break;
			}
			PoserFruitsPort(f);
			_lotPrairie.DessinerSansMaille(this);
			PoserDetailsPrairie(col);
			return true;
		}

		// ---------------------------------------------------------------------------
		// FRUITS — ceux du moteur, placés sur le port au hash de leur index
		// ---------------------------------------------------------------------------

		// Espèce sans ligne de fruit (repli : le moteur en poserait sur une espèce imprévue).
		private static readonly FicheFruit FruitParDefaut = new(1.5f);
		// Masse d'un fruit nominal (FRUIT_MASSE du moteur) : le rayon de la fiche vaut à cette masse.
		private const float FruitMasseNominale = 0.15f;

		// Point d'un fruit (cm, repère de la tuile, comme FruitPoint). Index = celui du moteur,
		// donc la récolte au clic (FindFruitNear) vise ce qui est dessiné ici. Sur une canne s'il y
		// en a, sinon au hash dans le volume que la fiche lui donne.
		private Vector3 PointFruitPort(int i)
		{
			FichePort f = FicheDeLaPlante;
			var (rayon, h) = MesurePort(f);
			if (f.Buisson is { Cannes: > 0 } b) return _structure.ColletCm + PointFruitCanne(f, b, i, rayon, h);
			FicheFruit fr = f.Fruit ?? FruitParDefaut;
			int ig = GraineIndividu;
			float a = Mathf.Tau * Hash01(351, ig, i), d = rayon * Mathf.Lerp(fr.DBas, fr.DHaut, Hash01(353, ig, i));
			return _structure.ColletCm + new Vector3(d * Mathf.Cos(a), d * Mathf.Sin(a),
				h * Mathf.Lerp(fr.ZBas, fr.ZHaut, Hash01(355, ig, i)));
		}

		private void PoserFruitsPort(FichePort f)
		{
			if (_structure.Fruits.Count == 0) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			FicheFruit fr = f.Fruit ?? FruitParDefaut;
			Vector3 collet = _structure.ColletCm;
			for (int i = 0; i < _structure.Fruits.Count; i++)
			{
				var fruit = _structure.Fruits[i];
				Vector3 p = PointFruitPort(i);
				Vector2 c = Iso(p.X - collet.X, p.Y - collet.Y, p.Z);
				PoserFruit(c, RayonFruit(fr, fruit.Masse), fr.Allonge, FruitColor(pal, fruit.Maturite), i);
			}
		}

		// Au moins un pixel : à ×1, c'est le point rouge qui fait reconnaître le fraisier (fiche).
		// La racine carrée garde l'échelle entre un fruit qui grossit et le port qui le porte.
		private static float RayonFruit(FicheFruit fr, float masse) =>
			Mathf.Max(fr.RayonCm * WorldView.PxPerCmX * Mathf.Sqrt(Mathf.Min(masse, 0.3f) / FruitMasseNominale), PixelInterne);

		// Rond, ou long et couché (courgette), avec son contour sombre, un éclat dès ×4.
		private void PoserFruit(Vector2 c, float r, float allonge, Color col, int i)
		{
			Color base_ = Ton(col, PaletteIndexee.TonBase), bord = Ton(col, 0), eclat = Ton(col, 4);
			float pix = PixelInterne;
			if (allonge <= 1f)
			{
				PoserDisque(c, r + pix, bord);
				PoserDisque(c, r, base_);
				if (AuPalier(PaliersHautsMinZoom)) PoserDisque(c - new Vector2(r, r) * 0.3f, Mathf.Max(r * 0.3f, pix), eclat);
				return;
			}
			float a = Mathf.Tau * Hash01(359, GraineIndividu, i);
			Vector2 demi = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.5f) * r * allonge * 0.5f;
			_lotPrairie.Ligne(c - demi, c + demi, bord, (r + pix) * 2f);
			_lotPrairie.Ligne(c - demi, c + demi, base_, r * 2f);
			PoserDisque(c - demi, r, base_);
			PoserDisque(c + demi, r, base_);
			if (AuPalier(PaliersHautsMinZoom))
				_lotPrairie.Ligne(c - demi * 0.7f - new Vector2(0f, r * 0.4f), c + demi * 0.7f - new Vector2(0f, r * 0.4f), eclat, Mathf.Max(r * 0.3f, pix));
		}

		// ---------------------------------------------------------------------------
		// RECUISSON — seulement si ce qui est dessiné a changé
		// ---------------------------------------------------------------------------

		// Une bouture de trèfle ne couvre pas tout de suite : sa taille suit l'âge du collet, seul
		// segment du moteur depuis FORMES ⑤. 25 semaines : ce que mettait le squelette à pousser
		// ses 6 segments d'alors [`grow_plant` isolé, gf 0,6 à 1, 20 à 35 semaines].
		private const float SemainesPiedEtabli = 25f;
		private const float PartPiedNeuf = 1f / 6f;

		// 1/6 pour un pied neuf, 1 pour un pied établi, comme le comptage de segments d'avant.
		private float EtablissementTrefle()
		{
			int age = _structure.Segments.Count > 0 ? _structure.Segments[0].AgeWeeks : 0;
			return Mathf.Lerp(PartPiedNeuf, 1f, Mathf.Min(age / SemainesPiedEtabli, 1f));
		}

		private readonly record struct ClePort(int HauteurCm, int Densite, int Floraison, int Automne,
			int Rabattu, int Pince, int Fruits, int Etablissement, bool QuatreFeuilles, string Stade, string Organe);
		private ClePort _clePort;

		private ClePort CleDuPort()
		{
			var s = _structure;
			int fruits = s.Fruits.Count;
			foreach (var fr in s.Fruits) fruits = fruits * 31 + Mathf.RoundToInt(fr.Maturite * 20f);
			float h = FicheDeLaPlante != null ? _hauteurLisseeCm : s.HeightCm;
			return new ClePort(Mathf.RoundToInt(h), Mathf.RoundToInt(s.DensiteVisible * 40f),
				Mathf.RoundToInt(s.Floraison * 20f), Mathf.RoundToInt(s.Automne * 20f),
				Mathf.RoundToInt(s.Rabattu * 16f), Mathf.RoundToInt(s.Pince * 24f), fruits,
				PortDeLaPlante == PortPrairie.Trefle ? Mathf.RoundToInt(EtablissementTrefle() * 20f) : 0,   // le trèfle lit l'âge
				s.QuatreFeuilles, s.StageName, s.Organ);
		}

		/// <summary>Appelé par SetStructure : vrai si la plante à port a déjà une image ou une
		/// cuisson en attente de ce même dessin. Tout autre état passe par Invalidate.</summary>
		private bool DessinInchange()
		{
			if (RecetteDeLaPlante(out _)) return ArbreInchange();   // PlantRenderer.CleStable.cs (HOUPPIER ④)
			if (!TailleAuPied) return false;
			ClePort cle = CleDuPort();
			if (cle == _clePort) return true;
			_clePort = cle;
			return false;
		}

		private bool MemesSymptomes(IReadOnlyList<(string Cause, float Intensite)> symptomes)
		{
			if (symptomes != null && RecetteDeLaPlante(out _)) return MemesSymptomesArbre(symptomes);   // HOUPPIER ④
			if (symptomes == null || symptomes.Count != _symptomes.Count) return false;
			for (int i = 0; i < symptomes.Count; i++)
				if (symptomes[i] != _symptomes[i]) return false;
			return true;
		}

		// ---------------------------------------------------------------------------
		// CLIC
		// ---------------------------------------------------------------------------

		// La tige fine d'un port haut se vise aussi : bande verticale au-dessus du collet.
		private bool HampeSous(Vector2 local)
		{
			if (FicheDeLaPlante is not { } f) return false;
			if (f.Forme is not (FormePort.Tige or FormePort.Chaume or FormePort.Buisson or FormePort.Volubile) && !HampeLevee(f)) return false;
			float demi = Mathf.Max(4f / WorldView.CurrentZoom, f.EpaisseurTigeCm * WorldView.PxPerCmX);
			return Mathf.Abs(local.X - AxeVolubileEcranX(f)) <= demi + RayonSpireEcran(f) && local.Y <= 0f
				&& local.Y >= -_hauteurReelCm * WorldView.PxPerCmZ - f.TeteCm * WorldView.PxPerCmX;
		}

		// Tolérance d'un clic sur un fruit, en px d'écran.
		private const float ToleranceFruitPx = 6f;

		/// <summary>Distance² (canvas) au fruit de port le plus proche, s'il est sous le clic ;
		/// l'infini sinon. Le clic re-projeté au sol tombe loin du pied dès que le fruit est haut,
		/// et sur le pied d'un voisin : pour manger, ce qui est dessiné sous la souris passe avant.</summary>
		internal float DistanceFruitPort(Vector2 canvasPos)
		{
			// HOUPPIER ⑤ : un fruit d'arbre est haut, le collet n'est pas sous le clic non plus.
			// VERGER VIVANT ④ : une cohorte est dessinée en plusieurs fruits, on mesure au plus proche.
			if (FicheDeLaPlante == null && Houppier) return DistanceFruitArbre(canvasPos);
			FicheFruit fr = FicheDeLaPlante is { } f ? f.Fruit ?? FruitParDefaut : Houppier ? FicheFruitArbre : null;
			if (fr == null || _structure.Fruits.Count == 0) return float.PositiveInfinity;
			int i = FindFruitNear(canvasPos);
			float d2 = PointFruitLocal(i).DistanceSquaredTo(ToLocal(canvasPos));
			float r = RayonFruit(fr, _structure.Fruits[i].Masse) * fr.Allonge;
			float tol = Mathf.Max(ToleranceFruitPx / WorldView.CurrentZoom, r);
			return d2 <= tol * tol ? d2 : float.PositiveInfinity;
		}

		private Vector2 PointFruitLocal(int i)
		{
			Vector3 p = PointDuFruit(i), collet = _structure.ColletCm;
			return Iso(p.X - collet.X, p.Y - collet.Y, p.Z);
		}

		internal int NombreFruits => _structure?.Fruits.Count ?? 0;
		internal string Espece => _structure?.SpeciesName;

		/// <summary>Banc de cueillette : là où le fruit `i` est dessiné, en canvas.</summary>
		internal Vector2 PointFruitCanvas(int i) => ToGlobal(PointFruitLocal(i));
	}
}
