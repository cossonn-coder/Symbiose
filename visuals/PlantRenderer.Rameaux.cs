// SYMBIOSE — PlantRenderer.Rameaux.cs (partial, sprint HOUPPIER ⑤)
// LES RAMEAUX DÉRIVÉS d'un arbre : la vue ajoute au bois du moteur le petit bois qu'il ne porte
// pas. Un segment du moteur fait 40-50 cm, c'est la charpente ; rameaux et brindilles naissent ici,
// à la cuisson, des segments feuillés, à partir de la table par espèce ci-dessous.
//
// 📖 Pédagogie — pourquoi dans la vue. Mettre ce bois au moteur coûte : tick +16 %, JSON ×2,4, 11
// arbres à recalibrer et le golden qui bouge [plafond 400, `full` an 2, seed 42, n=1 run par côté,
// VM, charge 3 à 17]. Le prix à accepter : on ne taille pas une brindille, la taille reste sur la
// charpente. C'est de la géométrie PURE : même segment → mêmes rameaux, aucun Random, aucun champ
// de pont. Comme une table dérivée en embarqué : on la reconstruit quand la source change, et la
// source est ici la référence du snapshot (`_structure`), clé qui s'invalide toute seule.
//
// Tout est tiré de la CLÉ STABLE du segment (CleStable.cs) : couper une branche ne déplace pas les
// rameaux des autres. Tout reste DANS le rayon réel `_rayonReelCm` (le snapshot ne porte pas
// `CanopyRadiusCm`) : la vue densifie la couronne sans jamais l'élargir.
//
// Source unique : feuilles, fleurs et fruits des arbres se posent sur ce bois, et le clic `manger`
// relit le même point que le dessin (PointDuFruit, Organs.cs).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Le petit bois d'une espèce. `ParMetre` : rameaux par mètre de segment feuillé ;
		/// `LongCm` : longueur d'un rameau ; `Ouverture` : angle à l'axe porteur (radians) ;
		/// `Port` : −1 retombant, 0 étalé, +1 érigé ; `Brindilles` par rameau ; `FeuillesBrin` :
		/// feuilles par brindille à ×8 et plus ; `Limbe`, `LimbeCm`, `LimbeLarge` : forme, longueur, largeur
		/// relative. Limbes de la fiche, relevés d'environ un tiers pour rester lisibles. Valeurs [choix], à juger au F5.</summary>
		private readonly record struct RecetteRameaux(float ParMetre, float LongCm, float Ouverture, float Port, int Brindilles,
			int FeuillesBrin, FormeFeuille Limbe, float LimbeCm, float LimbeLarge);

		private static readonly Dictionary<string, RecetteRameaux> RecettesRameaux = new()
		{
			["AppleTree"]    = new(7f, 60f, 0.95f, -0.10f, 3, 7, FormeFeuille.Dentee, 10f, 0.5f),      // étalé ; ovale denté, 5-10 cm
			["CherryTree"]   = new(6f, 65f, 0.70f,  0.20f, 3, 6, FormeFeuille.Scie, 13f, 0.42f),       // ovoïde étagé ; pointue dentée, 7-14 cm
			["WalnutTree"]   = new(6f, 75f, 0.90f,  0.00f, 3, 2, FormeFeuille.Composee, 32f, 0.4f),    // composée, 20-40 cm : peu de feuilles
			["OakTree"]      = new(7f, 65f, 1.05f, -0.05f, 3, 6, FormeFeuille.Lobee, 13f, 0.5f),       // tortueux ; lobée, 7-14 cm
			["BeechTree"]    = new(8f, 60f, 1.15f, -0.15f, 3, 7, FormeFeuille.Ovale, 10f, 0.55f),      // plans horizontaux ; ovale, 5-10 cm
			["BirchTree"]    = new(8f, 75f, 0.55f, -0.85f, 3, 9, FormeFeuille.Scie, 7f, 0.6f),         // pendant ; triangulaire, 3-7 cm
			["HornbeamTree"] = new(7f, 60f, 0.80f,  0.15f, 3, 7, FormeFeuille.Scie, 10f, 0.5f),        // ovoïde ; doublement dentée, 5-10 cm
			["Alder"]        = new(7f, 50f, 0.70f,  0.20f, 3, 7, FormeFeuille.Coeur, 9f, 0.75f),       // ronde échancrée, 4-9 cm
			["Willow"]       = new(8f, 80f, 0.55f, -0.65f, 3, 8, FormeFeuille.Lanceolee, 10f, 0.2f),   // retombée ; étroite, 5-10 cm
			["Fig"]          = new(5f, 60f, 1.00f,  0.25f, 3, 2, FormeFeuille.Palmee, 22f, 0.9f),      // palmée, 10-25 cm : peu de feuilles
			["FirTree"]      = new(8f, 50f, 1.25f, -0.30f, 3, 12, FormeFeuille.Ruban, 4f, 0.15f),      // étages ; aiguille, 2-3 cm
		};

		private static readonly Dictionary<string, FichePort> FichesLimbe = new();

		// Ce que le peintre de limbes lit d'une fiche de port (forme, largeur, folioles), rien de plus.
		private FichePort FicheLimbe(in RecetteRameaux r)
		{
			if (!FichesLimbe.TryGetValue(_structure.SpeciesName, out var f))
				FichesLimbe[_structure.SpeciesName] = f = new FichePort(FormePort.Tige, 0f, 0f, 1f, Feuilles: 7, r.Limbe,
					LargeurFeuille: r.LimbeLarge, Dressee: 0f, FormeTete.Aucune, TeteCm: 0f, Hampes: 0, EpaisseurTigeCm: 1f);
			return f;
		}

		// Un rameau se limite à ce dépassement au-dessus du bois réel : la cime reste celle du moteur.
		private const float RameauMargeHautCm = 10f;
		private const float RameauSolCm = 15f;
		// Port sous lequel une gerbe pend au lieu de monter.
		private const float PortPendant = -0.4f;

		/// <summary>Un trait de petit bois (cm, repère de la tuile, comme `Segment`). `Rang` : son identité
		/// dans le segment de clé `Cle`, pour tous les tirages au hash.</summary>
		private readonly record struct BoisDerive(Vector3 A, Vector3 B, int Cle, int Rang, bool EstRameau, float Croissance, float Prof);

		private readonly List<BoisDerive> _boisDerive = new();
		private PlantStructure _boisDeriveDe;
		private Vector2 _boisDeriveAxe;

		/// <summary>Arbre vivant au port d'arbre, avec une table de rameaux. Le jeune plant sans tronc et
		/// le squelette gardent leur dessin.</summary>
		private bool Houppier =>
			_structure != null && string.IsNullOrEmpty(_deadStade)
			&& RecettesRameaux.ContainsKey(_structure.SpeciesName) && Port() == "arbre";

		// Rameaux et brindilles, du fond vers l'avant. Reconstruits si le snapshot change, ou si la
		// rotation D35 change l'ordre de profondeur.
		private List<BoisDerive> BoisDuHouppier()
		{
			Vector2 axe = WorldView.WorldToScreenOffset(1f, 1f);
			if (_boisDeriveDe == _structure && _boisDeriveAxe == axe) return _boisDerive;
			_boisDeriveDe = _structure;
			_boisDeriveAxe = axe;
			_boisDerive.Clear();
			RecetteRameaux r = RecettesRameaux[_structure.SpeciesName];
			foreach (var s in _structure.Segments)
				if (IsLeafy(s)) DeriverRameaux(s, r);
			_boisDerive.Sort(static (a, b) => a.Prof.CompareTo(b.Prof));
			return _boisDerive;
		}

		private void DeriverRameaux(in Segment s, in RecetteRameaux r)
		{
			int cle = CleSegment(s);
			float g = LeafGrowthFactor(s);   // un segment neuf a des rameaux courts : ils grandissent avec lui
			int n = Mathf.Max(1, Mathf.RoundToInt(s.LengthCm / 100f * r.ParMetre));
			for (int k = 0; k < n; k++)
			{
				Vector3 a = s.Base + s.Dir * (s.LengthCm * (k + Hash01(521, cle, k)) / n);
				float ouv = r.Ouverture * Mathf.Lerp(0.7f, 1.3f, Hash01(525, cle, k));
				Vector3 d = Bifurcation(s.Dir, Mathf.Tau * Hash01(523, cle, k), ouv, r.Port);
				float l = r.LongCm * Mathf.Lerp(0.6f, 1.4f, Hash01(527, cle, k)) * g;
				Vector3 b = DansLaCouronne(a + d * l);
				AjouterBois(a, b, cle, k * 8, true, g);
				for (int j = 0; j < r.Brindilles; j++)
				{
					int rang = k * 8 + j + 1;
					Vector3 p = a.Lerp(b, 0.3f + 0.65f * (j + Hash01(529, cle, rang)) / r.Brindilles);
					Vector3 db = Bifurcation(d, Mathf.Tau * Hash01(531, cle, rang), Mathf.Lerp(0.5f, 1f, Hash01(533, cle, rang)), r.Port * 0.5f);
					float lb = l * Mathf.Lerp(0.3f, 0.55f, Hash01(535, cle, rang));
					AjouterBois(p, DansLaCouronne(p + db * lb), cle, rang, false, g);
				}
			}
		}

		private void AjouterBois(Vector3 a, Vector3 b, int cle, int rang, bool rameau, float g)
		{
			Vector3 c = _structure.ColletCm;
			float prof = WorldView.WorldToScreenOffset(b.X - c.X, b.Y - c.Y).Y + (b.Z - c.Z) * 1e-3f;
			_boisDerive.Add(new BoisDerive(a, b, cle, rang, rameau, g, prof));
		}

		// S'écarte de `axe` de l'angle `ouv`, dans l'azimut `az` autour de l'axe, puis penche selon le port.
		private static Vector3 Bifurcation(Vector3 axe, float az, float ouv, float port)
		{
			Vector3 ref_ = Mathf.Abs(axe.Z) < 0.9f ? Vector3.Back : Vector3.Right;   // Back = (0,0,1) en Godot
			Vector3 e1 = axe.Cross(ref_).Normalized(), e2 = axe.Cross(e1);
			Vector3 d = axe * Mathf.Cos(ouv) + (e1 * Mathf.Cos(az) + e2 * Mathf.Sin(az)) * Mathf.Sin(ouv);
			d.Z += port;
			return d.Normalized();
		}

		// Ramené dans le rayon réel et sous la cime : un rameau densifie, il n'agrandit pas l'arbre.
		private Vector3 DansLaCouronne(Vector3 p)
		{
			Vector3 c = _structure.ColletCm;
			var h = new Vector2(p.X - c.X, p.Y - c.Y);
			if (h.Length() > _rayonReelCm) h = h.Normalized() * _rayonReelCm;
			return new Vector3(c.X + h.X, c.Y + h.Y,
				Mathf.Clamp(p.Z, RameauSolCm, _hauteurReelCm + c.Z + RameauMargeHautCm));
		}

		/// <summary>Boîte de cuisson d'un arbre : les vrais bouts du petit bois, pas tout le disque de couronne,
		/// qui gonflait l'image de chaque arbre. `BakePadPx` couvre ensuite la moitié d'une gerbe et une feuille.</summary>
		private Rect2 EtendreHouppier(Rect2 r)
		{
			Vector3 c = _structure.ColletCm;
			foreach (var e in BoisDuHouppier())
				r = r.Expand(Iso(e.B.X - c.X, e.B.Y - c.Y, e.B.Z));
			return r;
		}
	}
}
