// SYMBIOSE — PiqureFlash.cs
// L'éclat éphémère d'UNE piqûre (vue pure, §J — couche joueur temps réel) : un
// petit anneau jaune qui enfle et s'efface au point de piqûre, surmonté d'un
// dard central qui rétrécit. Posé en coord CANVAS (projection du point monde
// sous le curseur au moment de la piqûre) ; s'auto-détruit en fin d'animation.
//
// 📖 Pédagogie — un nœud jetable plutôt qu'un layer batché (l'inverse de
// MacroLife) : les piqûres sont RARES et brèves (quelques-unes par seconde au
// plus, 0,35 s chacune). Le nœud qui s'anime seul et se QueueFree est le modèle
// le plus simple ici — pas de liste à entretenir côté WorldView, pas de diff.
// Si un jour il en pleuvait des centaines, on basculerait au batch (comme la
// vie macro) ; tant que c'est une poignée, ce serait de l'optimisation aveugle.

using Godot;

namespace Symbiose
{
	public partial class PiqureFlash : Node2D
	{
		private const float DureeSec = 0.35f;
		private static readonly Color Col = new Color("ffe24a");
		private float _t;

		public override void _Process(double delta)
		{
			_t += (float)delta;
			if (_t >= DureeSec) { QueueFree(); return; }
			QueueRedraw();
		}

		public override void _Draw()
		{
			float p = _t / DureeSec;                 // 0 → 1
			var ring = Col; ring.A = 1f - p;          // anneau qui enfle et s'efface
			DrawArc(Vector2.Zero, 3f + 11f * p, 0f, Mathf.Tau, 16, ring, 2f, true);
			var dard = Col; dard.A = (1f - p) * 0.9f; // dard central qui rétrécit
			DrawCircle(Vector2.Zero, 2.5f * (1f - p), dard);
		}
	}
}
