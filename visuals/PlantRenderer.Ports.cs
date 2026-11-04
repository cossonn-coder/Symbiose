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
			AvecTaille((f.RayonCm * CroissancePort(f), HampeLevee(f) ? _hauteurLisseeCm : HauteurFeuilles(f)));

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
				default: DessinerRosette(f, col); break;   // ④⑥ : chaumes, tapis…
			}
			PoserFruitsPort(f);
			_lotPrairie.DessinerSansMaille(this);
			PoserDetailsPrairie(col);
			return true;
		}

		// ---------------------------------------------------------------------------
		// FRUITS — ceux du moteur, placés sur le port au hash de leur index
		// ---------------------------------------------------------------------------

		// Point d'un fruit (cm, repère de la tuile, comme FruitPoint). Index = celui du moteur,
		// donc la récolte au clic (FindFruitNear) vise ce qui est dessiné ici. Les fruits
		// pendent dans le bas du port : le haut de la fiche porte la tête ou les fleurs.
		private Vector3 PointFruitPort(int i)
		{
			var (rayon, h) = MesurePort(FicheDeLaPlante);
			int ig = GraineIndividu;
			float a = Mathf.Tau * Hash01(351, ig, i), d = rayon * Mathf.Lerp(0.3f, 0.8f, Hash01(353, ig, i));
			return _structure.ColletCm + new Vector3(d * Mathf.Cos(a), d * Mathf.Sin(a),
				h * Mathf.Lerp(0.15f, 0.55f, Hash01(355, ig, i)));
		}

		private void PoserFruitsPort(FichePort f)
		{
			if (_structure.Fruits.Count == 0) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Vector3 collet = _structure.ColletCm;
			for (int i = 0; i < _structure.Fruits.Count; i++)
			{
				var fruit = _structure.Fruits[i];
				Vector3 p = PointFruitPort(i);
				Vector2 c = Iso(p.X - collet.X, p.Y - collet.Y, p.Z);
				// masse → rayon, comme DrawFruits (FRUIT_MASSE 0,15 → ~4,5 px ; borné).
				float rad = 3f + Mathf.Min(fruit.Masse, 0.3f) * 10f;
				PoserDisque(c, rad + PixelInterne, Ton(FruitColor(pal, fruit.Maturite), 0));
				PoserDisque(c, rad, Ton(FruitColor(pal, fruit.Maturite), PaletteIndexee.TonBase));
			}
		}

		// ---------------------------------------------------------------------------
		// RECUISSON — seulement si ce qui est dessiné a changé
		// ---------------------------------------------------------------------------

		private readonly record struct ClePort(int HauteurCm, int Densite, int Floraison, int Automne,
			int Rabattu, int Pince, int Fruits, int Segments, bool QuatreFeuilles, string Stade, string Organe);
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
				FicheDeLaPlante != null ? 0 : s.Segments.Count,   // le trèfle lit son nombre de segments
				s.QuatreFeuilles, s.StageName, s.Organ);
		}

		/// <summary>Appelé par SetStructure : vrai si la plante à port a déjà une image ou une
		/// cuisson en attente de ce même dessin. Tout autre état passe par Invalidate.</summary>
		private bool DessinInchange()
		{
			if (!TailleAuPied) return false;
			ClePort cle = CleDuPort();
			if (cle == _clePort) return true;
			_clePort = cle;
			return false;
		}

		private bool MemesSymptomes(IReadOnlyList<(string Cause, float Intensite)> symptomes)
		{
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
			if (FicheDeLaPlante is not { } f || (f.Forme != FormePort.Tige && !HampeLevee(f))) return false;
			float demi = Mathf.Max(4f / WorldView.CurrentZoom, f.EpaisseurTigeCm * WorldView.PxPerCmX);
			return Mathf.Abs(local.X) <= demi && local.Y <= 0f
				&& local.Y >= -_hauteurReelCm * WorldView.PxPerCmZ - f.TeteCm * WorldView.PxPerCmX;
		}
	}
}
