// SYMBIOSE — PlantRenderer.Sapin.cs (partial, sprint BOIS & ARBRES ⑤)
// LE CÔNE DU SAPIN, par la VUE (arbitrage B3 de Nico). Le moteur donne au sapin une flèche droite
// et quelques latéraux courts, un tous les 50 cm : en jeu, un poteau à touffes éparses. La vue
// ajoute des ÉTAGES de rameaux le long du tronc, réguliers, du bas du fût (sapin non élagué)
// jusqu'à la flèche, de plus en plus courts vers le haut : le cône se lit à tous les paliers,
// puisque gerbes (×1-×4), petit bois, aiguilles et cônes se posent tous sur `BoisDuHouppier`.
//
// 📖 Pédagogie — pourquoi la longueur suit la HAUTEUR et pas l'âge. Un vrai verticille s'allonge
// chaque année, l'âge serait donc le plus juste. Mais au banc `houppiers_25` la flèche du moteur
// cale à 6 m : le haut du tronc a 13 ans, le bas 25, et un cône « à l'âge » devenait un cylindre
// tronqué [mesuré, n=1 pied]. On prend donc la distance à la cime : L = R × (Hcime − z) / Hcime,
// R = rayon réel `_rayonReelCm`. La vue densifie, elle n'élargit jamais l'arbre (DansLaCouronne).
//
// Clé stable : chaque étage tire tout de la clé du segment de TRONC qui le porte et de sa hauteur
// absolue sur le tronc. Couper un latéral ne touche ni le tronc ni la cime → aucun étage ne bouge.
// Limite assumée : étêter le sapin (couper la flèche) raccourcit tous les étages, comme si le cône
// se refaisait sur la nouvelle cime ; et couper LE latéral le plus long change R.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Espèces au port conique : étages dérivés sur le tronc. Une donnée, pas une branche de code.
		private static readonly HashSet<string> PortsConiques = new() { "FirTree" };

		private const float EtagePasCm = 30f;      // un étage tous les 30 cm de tronc [choix, F5]
		private const float EtageBasCm = 25f;      // premier étage presque au sol (non élagué) [choix]
		private const int EtageRameaux = 5;        // verticille de 5 rameaux [choix]
		private const float EtageCimeMinCm = 8f;   // en dessous, l'étage n'est qu'un bourgeon : pas posé
		private const float BrinPasCm = 8f;        // une brindille latérale par 8 cm de rameau [choix]
		private const int RangEtages = 1 << 16;    // rangs des étages, loin de ceux des rameaux des segments

		private const float ConeBoutCm = 10f;      // rayon permis à la cime : la flèche garde ses aiguilles
		private float _cimeConeCm;                 // hauteur de la cime du tronc ; 0 = pas un port conique
		private readonly List<Segment> _troncCone = new();

		/// <summary>Rayon horizontal permis au petit bois à la hauteur `z` (cm au-dessus du collet) :
		/// le disque réel pour tous, réduit au cône pour un port conique. Les rameaux que la vue dérive
		/// des latéraux et de la flèche du moteur y sont ramenés aussi : sinon la flèche, qui porte des
		/// rameaux de 50-70 cm, écrasait la pointe du cône.</summary>
		private float RayonPermis(float z)
		{
			if (_cimeConeCm <= 0f) return _rayonReelCm;
			return Mathf.Clamp(_rayonReelCm * (_cimeConeCm - z) / _cimeConeCm, ConeBoutCm, _rayonReelCm);
		}

		/// <summary>Hauteur de la cime du tronc (cm au-dessus du collet), le tronc rangé dans `_troncCone`.</summary>
		private float CimeDuTronc()
		{
			TroncDresse(_troncCone);
			if (_troncCone.Count == 0) return 0f;
			Segment haut = _troncCone[^1];
			float cime = haut.Base.Z + haut.Dir.Z * haut.LengthCm - _structure.ColletCm.Z;
			return cime > EtageBasCm ? cime : 0f;
		}

		/// <summary>Le tronc : du collet, l'enfant le plus vertical à chaque nœud, tant qu'il monte.</summary>
		private void TroncDresse(List<Segment> tronc)
		{
			var segs = _structure.Segments;
			tronc.Clear();
			int courant = segs.FindIndex(static s => s.Parent < 0);
			while (courant >= 0)
			{
				tronc.Add(segs[courant]);
				int suivant = -1;
				float meilleur = 0.7f;   // au-delà de ~45° de la verticale, ce n'est plus la flèche
				for (int i = 0; i < segs.Count; i++)
					if (segs[i].Parent == courant && segs[i].Dir.Z > meilleur) { meilleur = segs[i].Dir.Z; suivant = i; }
				courant = suivant;
			}
		}

		/// <summary>Étages réguliers sur le tronc, longueur décroissante vers la cime (cône).</summary>
		private void DeriverEtages(in RecetteRameaux r)
		{
			Vector3 c = _structure.ColletCm;
			float cime = _cimeConeCm;
			foreach (var s in _troncCone)
			{
				float z0 = s.Base.Z - c.Z, z1 = z0 + s.Dir.Z * s.LengthCm;
				if (z1 <= z0) continue;
				int cle = CleSegment(s);
				float g = LeafGrowthFactor(s);
				// Étages aux hauteurs ABSOLUES EtageBasCm + k × pas : un segment qui s'allonge n'en déplace aucun.
				int k0 = Mathf.Max(0, Mathf.CeilToInt((z0 - EtageBasCm) / EtagePasCm));
				for (int k = k0; ; k++)
				{
					float z = EtageBasCm + k * EtagePasCm;
					if (z >= z1) break;
					float lon = _rayonReelCm * (cime - z) / cime * g;
					if (lon < EtageCimeMinCm) continue;
					PoserEtage(s, (z - z0) / (z1 - z0), lon, r, cle, k, g);
				}
			}
		}

		private void PoserEtage(in Segment s, float t, float lon, in RecetteRameaux r, int cle, int k, float g)
		{
			Vector3 a = PointDuBois(s, t);   // sur la courbe du tronc (BOIS & ARBRES ①)
			float tour = Mathf.Tau * Hash01(621, cle, k);
			for (int i = 0; i < EtageRameaux; i++)
			{
				int rang = RangEtages + (k * EtageRameaux + i) * 8;
				float az = tour + Mathf.Tau * (i + 0.35f * Hash01(623, cle, rang)) / EtageRameaux;
				float ouv = r.Ouverture * Mathf.Lerp(0.9f, 1.1f, Hash01(625, cle, rang));
				Vector3 d = Bifurcation(s.Dir, az, ouv, r.Port);
				float l = lon * Mathf.Lerp(0.85f, 1.1f, Hash01(627, cle, rang));
				Vector3 b = DansLaCouronne(a + d * l);
				AjouterBois(a, b, cle, rang, true, g);
				// Rameau aplati du sapin : brindilles alternées à gauche et à droite, dans le plan du rameau.
				int nb = Mathf.Clamp(Mathf.RoundToInt(l / BrinPasCm), 1, 7);
				for (int j = 0; j < nb; j++)
				{
					int rb = rang + j + 1;
					Vector3 p = a.Lerp(b, 0.2f + 0.75f * (j + Hash01(629, cle, rb)) / nb);
					float cote = (j & 1) == 0 ? 0f : Mathf.Pi;
					Vector3 db = Bifurcation(d, cote + 0.3f * (Hash01(631, cle, rb) - 0.5f), Mathf.Lerp(0.6f, 0.9f, Hash01(633, cle, rb)), 0f);
					float lb = Mathf.Min(l * 0.45f, 22f) * Mathf.Lerp(0.6f, 1f, Hash01(635, cle, rb)) * (1f - 0.5f * j / nb);
					AjouterBois(p, DansLaCouronne(p + db * lb), cle, rb, false, g);
				}
			}
		}
	}
}
