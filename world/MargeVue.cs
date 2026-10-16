// SYMBIOSE — MargeVue.cs (sprint RENDU VISIBLE T4 — une seule notion de « près de l'écran »)
// Le rectangle de MARGE partagé par toutes les couches du monde : ce qui y tombe
// est tenu à jour (appliqué, cuit, dessiné) ; ce qui est au-delà attend sans rien
// coûter. Avant T4, chaque couche avait sa marge à elle (400 cm fixes pour les
// plantes — énorme à ×32, ridicule à ×0,5 — et 48-160 px pour les couches au sol).
//
// Marge PROPORTIONNELLE au cadre : visible agrandi de 25 % de sa taille de chaque
// côté pour ENTRER, de 50 % pour SORTIR. 📖 Pédagogie (côté embarqué) : c'est un
// comparateur à HYSTÉRÉSIS (trigger de Schmitt) — deux seuils au lieu d'un, sinon
// un objet posé pile au bord basculerait dedans/dehors à chaque pixel de pan.
//
// Deux usages :
//  · par OBJET (plantes, WorldView.CullPlants) : Garde(dedans, emprise) teste la
//    boîte projetée de l'objet (plus son centre) contre le seuil qui s'applique ;
//  · par COUCHE inerte (litière, paillis, flaques…) : Cadre = un rectangle STABLE
//    (la zone de sortie au moment du dernier ré-ancrage) dans lequel la couche
//    dessine. Il n'est ré-ancré (Version++) que quand la zone d'entrée en déborde
//    ou que le zoom change sa taille : la couche se redessine alors une fois, au
//    lieu de chaque frame de pan. Avant T4 elle ne se redessinait jamais au pan
//    et ce qui était hors de son cadre de départ manquait (trou au bord).
//
// Réévalué UNIQUEMENT au pan / zoom / rotation / snapshot (Mettre, appelé par
// CullPlants) — jamais en boucle par frame sans mouvement.

using Godot;

namespace Symbiose
{
	public static class MargeVue
	{
		private const float Entree = 0.25f;   // fraction de la taille, par côté
		private const float Sortie = 0.50f;

		/// <summary>Rectangle visible (canvas du monde) au dernier Mettre.</summary>
		public static Rect2 Visible { get; private set; }
		private static Rect2 _entree, _sortie;

		/// <summary>Cadre stable des couches inertes (vide tant que la caméra n'a
		/// pas été posée → CadreCouche dessine tout).</summary>
		public static Rect2 Cadre { get; private set; }
		/// <summary>Incrémenté à chaque ré-ancrage du Cadre : une couche qui a vu
		/// une autre version se redessine.</summary>
		public static int Version { get; private set; }

		/// <summary>Nouveau cadre visible (canvas). Ré-ancre le Cadre si besoin.</summary>
		public static void Mettre(Rect2 visible)
		{
			Visible = visible;
			_entree = Agrandir(visible, Entree);
			_sortie = Agrandir(visible, Sortie);
			if (Cadre.Size == Vector2.Zero || !Cadre.Encloses(_entree)
				|| !Cadre.Size.IsEqualApprox(_sortie.Size))
			{
				Cadre = _sortie;
				Version++;
			}
		}

		/// <summary>L'objet d'emprise `emprise` (canvas) est-il dans la marge ?
		/// `dedans` = son état précédent (hystérésis).</summary>
		public static bool Garde(bool dedans, Rect2 emprise)
		{
			Rect2 seuil = dedans ? _sortie : _entree;
			return emprise.Size == Vector2.Zero
				? seuil.HasPoint(emprise.Position) : seuil.Intersects(emprise);
		}

		/// <summary>Rectangle de dessin d'une couche inerte : le Cadre commun
		/// agrandi de sa propre marge d'objet (`margePx` : jitter, étalement).</summary>
		public static Rect2 CadreCouche(float margePx) =>
			Cadre.Size == Vector2.Zero
				? new Rect2(-1e6f, -1e6f, 2e6f, 2e6f)   // caméra pas encore posée : tout
				: Cadre.Grow(margePx);

		private static Rect2 Agrandir(Rect2 r, float f) =>
			r.GrowIndividual(r.Size.X * f, r.Size.Y * f, r.Size.X * f, r.Size.Y * f);
	}
}
