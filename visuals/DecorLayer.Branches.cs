// SYMBIOSE — DecorLayer.Branches.cs (LISIÈRE NUE ③ — la charpente des arbres de lisière)
// Partial de DecorLayer : l'axe et les charpentières d'un feuillu, posés dans
// DrawArbreKit AVANT l'enveloppe. Ce fichier ne sait RIEN de la saison : l'été, enveloppe
// et bouquets les recouvrent ; quand le shader dégarnit la couronne, elles apparaissent.
//
// 📖 Pédagogie — c'est le principe du décor de théâtre : tout est déjà sur scène, un rideau
// se lève. Aucune reconstruction de maille ni donnée de plus, donc 0 coût par semaine.
// Le prix se paie une fois, en sommets, à la construction de la maille.
//
// 📖 Pourquoi tout rester DANS l'ellipse de l'enveloppe (`DansCouronne`) : c'est la seule
// garantie que l'été n'en montre rien, quelle que soit la graine du pied.
//
// Classe `ClasseSansSaison` : le shader ne touche pas leur couleur, mais y pose neige et givre.
// Le vent les plie avec l'arbre (`VentArbre` est actif pendant ce tracé). Zéro Random (philo #3).

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Forme des charpentières d'un port. Angles en degrés depuis la verticale :
		// `AngleMin..AngleMax` au départ, `Courbe` ajouté au coude (< 0 redresse, > 0 retombe).
		// `DepartMin..DepartMax` = où elles naissent sur l'axe (0 = bas de couronne, 1 = sommet).
		private readonly record struct FormeBranches(float AngleMin, float AngleMax, float Courbe,
			float DepartMin, float DepartMax, float Longueur, float Epaisseur);

		private static FormeBranches FormeDe(TreePort port) => port switch
		{
			TreePort.Elance  => new(25f, 40f, 90f, 0.25f, 0.80f, 0.85f, 0.12f),    // bouleau : fin, retombant
			TreePort.Ovoide  => new(18f, 35f, -8f, 0.10f, 0.70f, 0.85f, 0.20f),    // hêtre : ascendant
			TreePort.Sinueux => new(35f, 60f, -55f, 0.05f, 0.60f, 0.85f, 0.18f),   // charme : sinueux
			_                => new(55f, 78f, -25f, 0.08f, 0.45f, 0.95f, 0.22f),   // chêne : étalé
		};

		private const float PartSommetAxe = 0.70f;   // l'axe monte à 70 % du demi-axe vertical
		private const float MargeCouronne = 0.85f;   // sous l'enveloppe, qui est à 0,92

		/// <summary>Axe prolongé dans la couronne puis 3 à 5 charpentières (`c0`, `rx`, `ry` =
		/// ellipse de l'enveloppe, `w` = largeur du tronc). Rameaux si `DetailsVisibles`.</summary>
		private void DrawBranches(Vector2 apex, Vector2 c0, float rx, float ry, float w,
								  TreePort port, Color col, uint hb)
		{
			float fin = 0.5f / ZoomConstr;   // demi-largeur minimale : 1 px interne en tout
			FormeBranches f = FormeDe(port);
			Vector2 sommet = c0 + Vector2.Up * ry * PartSommetAxe;
			ClasseAplats(ClasseSansSaison);
			// Palier le plus bas : moitié moins de sommets. La charpente y fait quelques
			// pixels et la maille y est petite, le surcoût relatif y serait le plus lourd.
			bool bas = ZoomConstr < 1f;
			float finAxe = Mathf.Max(fin, w * 0.12f);
			Aplats(OPlat);
			int n = bas ? 3 : 3 + (int)(hb >> 6 & 0xffu) % 3;
			for (int k = 0; k < n; k++)
			{
				uint h = HashCase(hb, k, 1, 41u);
				float cote = (k + (hb >> 14 & 1u)) % 2 == 0 ? -1f : 1f;   // alternes le long de l'axe
				float t = Mathf.Lerp(f.DepartMin, f.DepartMax, (k + 0.5f) / n);
				float angle = Mathf.Lerp(f.AngleMin, f.AngleMax, (h & 0xff) / 255f);
				Vector2 depart = apex.Lerp(sommet, t);
				Vector2 d1 = Direction(angle, cote);
				// Portée : rx à l'horizontale, ry à la verticale (le port donne la silhouette).
				float portee = f.Longueur * Mathf.Lerp(ry, rx, Mathf.Abs(d1.X));
				// Jamais plus large que l'axe à cet endroit : sinon le bout carré dépasse de l'autre côté.
				float racine = Mathf.Max(fin, Mathf.Min(w * f.Epaisseur, Mathf.Lerp(w * 0.5f, finAxe, t) * 0.9f));
				float milieu = Mathf.Max(fin, racine * 0.5f);
				Vector2 coude = DansCouronne(depart + d1 * portee * 0.55f, c0, rx, ry);
				Vector2 bout = DansCouronne(coude + Direction(angle + f.Courbe, cote) * portee * 0.45f, c0, rx, ry);
				Troncon(depart, coude, racine, milieu, col);
				Troncon(coude, bout, milieu, fin, col);
				if (bas) continue;
				// Une fourche au coude : sans elle, un arbre nu n'a que quelques traits.
				Vector2 fourche = coude + Direction(angle + f.Courbe - 45f, -cote) * portee * 0.35f;
				Troncon(coude, DansCouronne(fourche, c0, rx, ry), milieu * 0.7f, fin, col);
				if (DetailsVisibles) Rameaux(coude, bout, angle + f.Courbe, cote, portee, c0, rx, ry, fin, col, h);
			}
			// L'axe APRÈS les charpentières : il recouvre leurs racines carrées.
			if (bas)
			{
				Troncon(apex, sommet, w * 0.5f, finAxe, col);
			}
			else
			{
				// L'axe prolonge le fût : mêmes flancs orientés, sinon une couture se voit.
				Aplats(OrientEcorceG);
				Flanc(apex, sommet, w * 0.5f, finAxe, -1f, col);
				Aplats(OrientEcorceD);
				Flanc(apex, sommet, w * 0.5f, finAxe, 1f, col);
				Aplats(OPlat);
			}
			ClasseAplats(ClasseInerte);
		}

		// Trois brins d'un pixel le long du bout de la charpentière, de part et d'autre.
		private void Rameaux(Vector2 coude, Vector2 bout, float angle, float cote, float portee,
							 Vector2 c0, float rx, float ry, float fin, Color col, uint h)
		{
			for (int i = 0; i < 3; i++)
			{
				float t = 0.25f + i * 0.3f;
				float ecart = i % 2 == 0 ? 40f : -40f;
				float l = portee * (0.15f + (h >> (8 + i * 4) & 15u) / 15f * 0.15f);
				Vector2 p = coude.Lerp(bout, t);
				_lot.Ligne(p, DansCouronne(p + Direction(angle + ecart, cote) * l, c0, rx, ry), col, fin * 2f);
			}
		}

		// Direction ÉCRAN : `degres` depuis la verticale haute, vers le côté `cote` (−1 ou +1).
		private static Vector2 Direction(float degres, float cote)
		{
			float a = Mathf.DegToRad(degres);
			return new Vector2(Mathf.Sin(a) * cote, -Mathf.Cos(a));
		}

		// Ramène un point dans l'ellipse de l'enveloppe, marge comprise.
		private static Vector2 DansCouronne(Vector2 p, Vector2 c0, float rx, float ry)
		{
			var q = new Vector2((p.X - c0.X) / rx, (p.Y - c0.Y) / ry);
			float l = q.Length();
			return l <= MargeCouronne ? p : c0 + new Vector2(q.X * rx, q.Y * ry) * (MargeCouronne / l);
		}

		// Tronçon effilé : `ha`, `hb` = demi-largeurs à chaque bout.
		private void Troncon(Vector2 a, Vector2 b, float ha, float hb, Color col)
		{
			Vector2 n = (b - a).Orthogonal().Normalized();
			_lot.PolygoneConvexe(new[] { a + n * ha, a - n * ha, b - n * hb, b + n * hb }, col);
		}

		// Un flanc d'axe, de la ligne médiane au bord `cote`.
		private void Flanc(Vector2 a, Vector2 b, float ha, float hb, float cote, Color col) =>
			_lot.PolygoneConvexe(new[] { a, a + Vector2.Right * ha * cote, b + Vector2.Right * hb * cote, b }, col);
	}
}
