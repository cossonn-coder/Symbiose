// SYMBIOSE — PlantRenderer.FruitMur.cs (partial de PlantRenderer, GESTES LISIBLES ④)
// RÉCOLTER EN CLIQUANT LE FRUIT (conception §6) : sous `recolter`, la désignation vise
// l'ORGANE MÛR dessiné, pas le tronc. Ce fichier répond à une seule question : « un
// fruit MÛR de cette plante est-il dessiné sous le clic ? ».
//
// La maturité vient du moteur (`fruits[i].maturite`, 0→1 = mûr, > 1 = sur-mûr) ; la vue
// ne la calcule pas, elle la lit — c'est le seuil où DrawFruits atteint la teinte mûre.
// La POSITION est celle du dessin, par les mêmes chemins que `manger` : un port (fraise,
// framboise) ou un arbre (cohortes du verger) se mesurent au fruit dessiné
// (DistanceFruitPort) ; une herbacée ordinaire au bout de son segment porteur.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Maturité moteur à partir de laquelle un fruit se récolte (teinte mûre).</summary>
		internal const float MaturiteMure = 1f;
		// Rayon de clic (canvas) d'un fruit d'herbacée ordinaire : un fruit y fait quelques px.
		private const float RayonFruitHerbacee = 2f;

		/// <summary>La plante porte-t-elle au moins un fruit mûr ? (mots du refus)</summary>
		internal bool AFruitMur
		{
			get
			{
				if (_structure == null) return false;
				foreach (var f in _structure.Fruits)
					if (f.Maturite >= MaturiteMure) return true;
				return false;
			}
		}

		/// <summary>Distance² (canvas) au fruit MÛR dessiné sous le clic, l'infini sinon.
		/// Le fruit le plus proche du clic doit être mûr : un clic sur un fruit vert ne
		/// glisse pas vers un mûr voisin (on récolte ce qu'on vise).</summary>
		internal float DistanceFruitMur(Vector2 canvasPos)
		{
			int i = FindFruitNear(canvasPos);
			if (i < 0 || _structure.Fruits[i].Maturite < MaturiteMure) return float.PositiveInfinity;
			if (FicheDeLaPlante != null || Houppier) return DistanceFruitPort(canvasPos);
			// Herbacée ordinaire : le fruit est au bout de son segment porteur.
			float d2 = PointFruitLocal(i).DistanceSquaredTo(ToLocal(canvasPos));
			float tol = Mathf.Max(ToleranceFruitPx / WorldView.CurrentZoom, RayonFruitHerbacee);
			return d2 <= tol * tol ? d2 : float.PositiveInfinity;
		}
	}
}
