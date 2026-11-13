// SYMBIOSE — ReglagePastille.cs (sprint PALETTE & TIROIR ②)
// UNE PASTILLE DE RÉGLAGE : un des choix qu'un geste demande avant d'agir (quelle
// graine planter, quel substrat mettre dans le pot, quel paillis étaler). Muette
// comme les icônes de gestes (philo #5) : une forme et une couleur, le nom au
// survol, jamais de quantité.
//
// Trois formes, pour qu'on reconnaisse la NATURE du choix d'un coup d'œil :
//  - Graine   : un disque à la couleur du feuillage, un point à celle du fruit ;
//  - Substrat : un carré plein (une motte vue de dessus) ;
//  - Paillis  : trois brins couchés ;
//  - Vide     : un cadre seul (banque vide — rien à choisir).
//
// 📖 Pédagogie Godot/C# :
//  - Même patron que GesteIcon : on hérite de Button (clic + info-bulle gratuits)
//    et on peint tout dans _Draw. `QueueRedraw()` demande à Godot de rappeler
//    _Draw à la prochaine image ; on ne le fait que si un état a changé.
//  - Estomper = baisser l'alpha du MOTIF seulement (pas via `Modulate`, qui pâlirait
//    aussi le cadre du choix courant : on doit toujours voir ce qui est choisi).

using Godot;

namespace Symbiose
{
	public partial class ReglagePastille : Button
	{
		public enum Forme { Graine, Substrat, Paillis, Vide }

		public const int Taille = 32;      // côté (px écran) — plus petit qu'une case de geste

		private Forme _forme;
		private Color _fond, _accent;
		private bool _courant;
		private bool _estompe;

		/// <summary>Choix courant → cadre clair (comme le geste actif de la barre).</summary>
		public bool Courant
		{
			get => _courant;
			set { if (_courant == value) return; _courant = value; QueueRedraw(); }
		}

		/// <summary>Stock vide : la pastille reste là, pâlie. Elle reste CLIQUABLE —
		/// c'est le moteur qui refuse le geste, pas la vue.</summary>
		public bool Estompe
		{
			get => _estompe;
			set { if (_estompe == value) return; _estompe = value; QueueRedraw(); }
		}

		public void Init(Forme forme, string nom, Color fond, Color accent)
		{
			_forme = forme;
			_fond = fond;
			_accent = accent;
			TooltipText = nom;
			Flat = true;
			CustomMinimumSize = new Vector2(Taille, Taille);
			FocusMode = FocusModeEnum.None;
			foreach (var etat in new[] { "normal", "hover", "pressed", "disabled", "focus" })
				AddThemeStyleboxOverride(etat, new StyleBoxEmpty());
		}

		public override void _Draw()
		{
			float t = Taille, mid = Taille / 2f;
			var rect = new Rect2(0f, 0f, t, t);
			DrawRect(rect, new Color(0.14f, 0.16f, 0.18f, 0.85f), filled: true);
			float a = _estompe ? 0.3f : 1f;
			Color fond = new Color(_fond, _fond.A * a), accent = new Color(_accent, _accent.A * a);
			switch (_forme)
			{
				case Forme.Graine:
					DrawCircle(new Vector2(mid, mid), 10f, fond);
					DrawCircle(new Vector2(mid + 3f, mid - 3f), 4f, accent);
					break;
				case Forme.Substrat:
					DrawRect(new Rect2(7f, 7f, t - 14f, t - 14f), fond);
					// Deux grains d'accent : la texture du mélange.
					DrawRect(new Rect2(11f, 12f, 3f, 3f), accent);
					DrawRect(new Rect2(18f, 18f, 3f, 3f), accent);
					break;
				case Forme.Paillis:
					for (int i = 0; i < 3; i++)
					{
						float y = 10f + i * 6f;
						DrawLine(new Vector2(6f, y + 2f), new Vector2(t - 6f, y - 2f), fond, 3f);
					}
					break;
				case Forme.Vide:
					DrawRect(new Rect2(8f, 8f, t - 16f, t - 16f),
							 new Color(0.6f, 0.6f, 0.6f, 0.5f), filled: false, width: 1f);
					break;
			}
			if (_courant)
				DrawRect(rect, new Color(0.9f, 0.9f, 0.7f), filled: false, width: 2f);
		}
	}
}
