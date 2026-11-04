// SYMBIOSE — PlantRenderer.Wind.cs (partial, sprint JARDIN VIVANT T3 — vent)
// Côté PLANTE du vent en onde : (1) la FLEXION géométrique, appliquée dans la
// projection Iso (peu au collet, fort à l'apex, dans la direction du vent
// projetée à l'écran) ; (2) les paramètres propres à la plante que l'onde lit
// (position monde, abri local, raideur de son port, retard, phase propre) ;
// (3) la pose affichée (index dans l'atlas de poses cuit par PlantBaker).
//
// 📖 Pédagogie : la flexion n'est PAS une rotation d'image. Chaque point du
// dessin à la hauteur z glisse dans le sens du vent de ∝ z²/H et s'abaisse un
// peu : le collet ne bouge pas, l'apex se couche — comme une tige réelle. Les
// feuilles/fleurs/fruits suivent car ils sont placés par la même projection.
//
// Raideur par PORT (kickoff §5) : dérivée de l'épaisseur max des segments, déjà
// au snapshot — aucun champ moteur neuf. Une herbacée (tige ≈ 0,5 cm) plie fort
// et tout de suite ; un arbre (collet ≈ 15 cm) plie peu, et en RETARD ∝ hauteur.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// Déplacement horizontal de l'apex à flexion 1, en fraction de la hauteur,
		// et abaissement relatif de l'apex (la plante couchée est moins haute).
		private const float BendReach = 0.55f;
		private const float BendDrop = 0.30f;
		// Raideur = 1 / (1 + épaisseur / ThickRefCm), bornée [RaideurMin, 1].
		// Tige 0,5 cm → 0,86 ; arbuste 4 cm → 0,43 ; tronc 15 cm → 0,17.
		private const float ThickRefCm = 3f;
		private const float RaideurMin = 0.12f;
		// Pose maximale cuite = ceil(7 × raideur × FlexCap) : un arbre n'atteint
		// jamais les poses couchées → on ne les cuit pas (mémoire vidéo).
		private const float FlexCap = 1.5f;
		// Retard de l'onde dans le port (s par cm de hauteur) : grand = en retard.
		private const float LagPerCm = 0.002f;

		/// <summary>Nombre de degrés de flexion d'un atlas complet (0..7).</summary>
		public const int MaxPoses = 8;

		// Flexion DESSINÉE (0 = droite). Pinceau : celle de sa cellule ; plante du
		// monde : celle de la pose affichée (dessin direct, surbrillance, picking).
		private float _bendFlex;
		private int _pose;
		private float _windX, _windY, _abri = 1f, _raideur = 1f, _lagSec, _swayPhase;
		private int _maxPoseLive;

		/// <summary>Cellules de l'atlas : 1 au calme ou pour un squelette.</summary>
		internal int BakePoseCount =>
			WindWave.Active && string.IsNullOrEmpty(_deadStade) ? _maxPoseLive + 1 : 1;

		/// <summary>Cellules réellement PEINTES (D109 c, PERF VUE ④) : jusqu'à la pose
		/// la plus couchée que le vent courant peut demander. L'atlas garde sa taille
		/// (BakePoseCount cellules) : même géométrie, mêmes UV, même image au pixel
		/// près ; seules les poses inatteignables ne sont plus dessinées.</summary>
		internal int BakePosesUtiles =>
			Mathf.Min(BakePoseCount, WindWave.PoseMaxAtteignable(_abri, _raideur) + 1);

		/// <summary>Position MONDE (cm) et facteur d'abri local (clé `abri` du
		/// snapshot, 1.0 si absente). La phase propre = hash de la position, qui
		/// EST l'identité d'une plante côté pont (pas d'id inventé).</summary>
		public void SetWindAnchor(float wx, float wy, float abri)
		{
			_windX = wx;
			_windY = wy;
			_abri = Mathf.Max(0f, abri);
			uint h = (uint)Mathf.RoundToInt(wx * 10f) * 73856093u
					 ^ (uint)Mathf.RoundToInt(wy * 10f) * 19349663u;
			h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
			_swayPhase = (h & 0xffff) / 65536f;
		}

		// Appelé par SetStructure : raideur, retard et pose max suivent la croissance.
		private void ComputeStiffness()
		{
			float thick = 0f;
			if (_structure != null)
				foreach (var s in _structure.Segments)
					if (s.ThicknessCm > thick) thick = s.ThicknessCm;
			_raideur = Mathf.Clamp(1f / (1f + thick / ThickRefCm), RaideurMin, 1f);
			_lagSec = LagPerCm * _heightCm;
			_maxPoseLive = Mathf.Clamp(Mathf.CeilToInt(7f * _raideur * FlexCap), 1, MaxPoses - 1);
			// Le tapis de trèfle ne se couche pas : deux poses de frémissement suffisent,
			// et une colonie ne cuit pas 8 cellules par pied (TRÈFLE DOMINANT ④).
			if (PortDeLaPlante == PortPrairie.Trefle) _maxPoseLive = Mathf.Min(_maxPoseLive, PosesMaxTapis);
		}

		/// <summary>Une frame d'onde (WindWave, plantes près de l'écran seulement).</summary>
		internal void UpdateWind()
		{
			int max = string.IsNullOrEmpty(_deadStade) ? _maxPoseLive : 0;
			// Sous la neige la plante est RAIDIE (T5, SnowStiffness) : elle plie moins.
			ApplyWindPose(WindWave.PoseFor(_windX, _windY, _abri, _raideur * SnowStiffness, _lagSec,
										   _swayPhase, max));
		}

		/// <summary>Affiche la pose `pose` : simple changement d'index d'image si
		/// la plante est cuite, sinon redessin direct (naissance, très grand arbre).</summary>
		internal void ApplyWindPose(int pose)
		{
			if (pose == _pose) return;
			_pose = pose;
			_bendFlex = pose / (float)(MaxPoses - 1);
			QueueRedraw();
		}

		/// <summary>Pinceau de la cellule `pose` de l'atlas.</summary>
		internal void SetBrushPose(int pose) => _bendFlex = pose / (float)(MaxPoses - 1);

		/// <summary>Flexion d'un point (offset au collet, cm). Tirée vers l'aval
		/// de ∝ z²/H, abaissée de ∝ z/H. dz > 0 garanti par l'appelant.</summary>
		private void Bend(ref float dx, ref float dy, ref float dz)
		{
			float t = Mathf.Min(dz / _heightCm, 1f);
			float push = _bendFlex * BendReach * dz * t;
			Vector2 u = WindWave.BakedDir;
			dx += u.X * push;
			dy += u.Y * push;
			dz *= 1f - BendDrop * _bendFlex * t;
		}

		/// <summary>Boîte englobante LOCALE de la pose `pose` seule (cellule
		/// serrée de l'atlas, D106 T6) : la flexion de la pose, puis la boîte.</summary>
		internal Rect2 PoseBounds(int pose)
		{
			float keep = _bendFlex;
			_bendFlex = pose / (float)(MaxPoses - 1);
			Rect2 r = StraightBounds();
			_bendFlex = keep;
			return r;
		}
	}
}
