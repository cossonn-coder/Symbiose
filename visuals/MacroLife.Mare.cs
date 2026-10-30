// SYMBIOSE — MacroLife.Mare.cs (sprint MARE VIVANTE ③ — la faune de mare lisible)
// Ce que la vie macro dit à la MARE, et la nuée de moustiques :
//   · ProiesDeMare : un point MONDE par plot où un moustique ou une libellule est
//     PEINT (vivant, pas en fondu de sortie). PuddleLayer.Signaux.cs en fait les
//     ronds de gobage de l'eau — ce qui est peint = ce qui gobe (règle « dit = peint »
//     du sprint, posée côté moteur au ①). VersionMare change à chaque snapshot :
//     l'eau ne relit la liste qu'alors (pas de recalcul par image).
//   · la libellule a une taille plancher (PlancherPx) : lisible de ×1 à ×4 ;
//   · les moustiques ne sont plus dessinés à leur taille réelle (0,6 cm → un point
//     à ×8 seulement) mais en NUÉE (NueeMoustiques), lisible dès ×4.
//
// 📖 Pédagogie — `partial` : MacroLife.cs garde le peintre des bêtes ; ce fichier
// regroupe le seul concept « mare ». Même classe, même état (_entries), deux fichiers.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class MacroLife
	{
		private static readonly HashSet<string> FauneDeMare = new() { "moustique", "libellule" };
		private readonly List<Vector2> _proies = new();
		private NueeMoustiques _nuee;

		/// <summary>Points MONDE (cm) où la faune de mare est peinte, un par plot.</summary>
		public IReadOnlyList<Vector2> ProiesDeMare => _proies;
		/// <summary>Incrémentée à chaque mise à jour de ProiesDeMare.</summary>
		public int VersionMare { get; private set; }

		// Taille PLANCHER (px internes) : à taille réelle (7 cm) la libellule fait 2,7 px
		// à ×1 et 11 px à ×4 — ses ailes claires s'y réduisent à un bâtonnet gris, son
		// abdomen d'1 px se noie dans l'eau (vu au banc ③, même à 16 px). Plancher
		// CROISSANT avec le palier : 8 px à ×1 (une tache claire, à l'échelle des autres
		// bêtes du ×1), 12 à ×2, 20 à ×4 (le portrait — ailes en croix sur l'abdomen —
		// se reconnaît) ; au-delà de ×4 la taille réelle (22 px à ×8) reprend la main.
		private static float PlancherPx(string guilde, float zoom) => guilde != "libellule" ? 0f
			: Mathf.Lerp(8f, 20f, Mathf.Clamp((zoom - 1f) / 3f, 0f, 1f));

		// Le moustique est confié à la nuée : le peintre principal le saute.
		private static bool EnNuee(string guilde) => guilde == "moustique";

		// Fin de diff d'un snapshot (StepSprites) : relit la faune de mare vivante.
		private void MajMare()
		{
			_proies.Clear();
			var plots = new HashSet<string>();
			var moustiques = new List<(Vector2, uint)>();
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f || !FauneDeMare.Contains(e.Guild)) continue;
				var w = new Vector2(e.Wx, e.Wy);
				if (EnNuee(e.Guild)) moustiques.Add((w, e.Phase));
				if (plots.Add(e.Plot)) _proies.Add(w);
			}
			VersionMare++;
			if (_nuee == null) { _nuee = new NueeMoustiques { Name = "Nuee" }; AddChild(_nuee); }
			_nuee.Poser(moustiques);
		}
	}
}
