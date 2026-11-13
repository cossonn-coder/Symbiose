// SYMBIOSE — PlantRenderer.Clic.cs (partial de PlantRenderer, PALETTE & TIROIR ③)
// LE CLIC SUR UNE PLANTE : « le curseur touche-t-il ce qui est dessiné ? ». Sorti de
// PlantRenderer.cs le 2026-11-13 (le fichier passait 300 lignes de code avec le
// correctif D118 c) : un concept, un fichier. Sert la priorité de clic plante >
// maison (WorldView.PointeUnePlante) et la visée d'un port (WorldView.FindPortSous).
// Voisins : HampeSous (Ports.cs), Couronne (Paliers.cs), FindSegmentNear
// (PlantRenderer.cs — la visée d'UNE branche pour tailler).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// D118 (c), cause isolée au banc `-M` (verger_mur, 2026-11-13) : la couronne d'un
		// ARBRE est une ellipse posée HAUT (centre aux deux tiers de la hauteur) — le tronc
		// et les charpentières basses sont dessinés mais HORS de l'ellipse. Cliquer le
		// tronc d'un arbre devant la maison n'était donc « pas une plante » → le clic
		// partait à la maison. On teste maintenant le bois DESSINÉ, avec la géométrie
		// exacte de DrawSegments (même Iso, comme FindSegmentNear), collet compris.
		// Réservé aux plantes SANS fiche de port : celles-là dessinent leurs segments ;
		// une herbacée à fiche dessine un port, ses segments ne sont pas à l'écran.
		private bool BoisSous(Vector2 local)
		{
			if (FicheDeLaPlante != null) return false;
			Vector3 collet = _structure.ColletCm;
			float marge = 4f / WorldView.CurrentZoom;          // 4 px d'écran de tolérance
			foreach (var s in _structure.Segments)
			{
				Vector3 tip = s.Base + s.Dir * s.LengthCm;
				Vector2 p1 = Iso(s.Base.X - collet.X, s.Base.Y - collet.Y, s.Base.Z);
				Vector2 p2 = Iso(tip.X - collet.X, tip.Y - collet.Y, tip.Z);
				float demi = s.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor / 2f;
				if (local.DistanceTo(Geometry2D.GetClosestPointToSegment(local, p1, p2)) <= demi + marge)
					return true;
			}
			return false;
		}

		/// <summary>Le curseur (canvas) touche-t-il le corps visible de la plante ?
		/// Test de l'ellipse de couronne des paliers bas (Couronne, D106 T5 — même
		/// géométrie que la tache / le port dessinés) → forgiving, cohérent à tout
		/// zoom. Sert la priorité de clic plante > maison (WorldView.PointeUnePlante).
		/// NB T5 : l'ancienne silhouette lisait CanopyRadiusCm, que le snapshot ne
		/// porte pas (0) → ellipse vide, le test rendait toujours faux.</summary>
		public bool ContientCurseur(Vector2 canvasPos)
		{
			if (_structure == null) return false;
			Vector2 local = ToLocal(canvasPos);
			if (HampeSous(local)) return true;   // un port se vise aussi à sa hampe (Ports.cs)
			if (BoisSous(local)) return true;    // un ligneux se vise aussi à son bois (D118 c)
			var (center, rx, ry) = Couronne();   // PlantRenderer.Paliers.cs (T5)
			if (rx <= 0f || ry <= 0f) return false;
			Vector2 d = local - center;
			return d.X * d.X / (rx * rx) + d.Y * d.Y / (ry * ry) <= 1f;  // dans l'ellipse
		}
	}
}
