// SYMBIOSE — TiroirBouton.cs (sprint PALETTE & TIROIR ①)
// LE BOUTON DU TIROIR, posé en bas de la barre de gestes. Deux visages :
//  - au repos, une petite GRILLE de points (« il y en a d'autres ») ;
//  - quand le geste actif n'a PAS de case dans la barre, il PORTE le pictogramme
//    de ce geste — sinon rien à l'écran ne dirait quel outil on tient.
// Un clic ouvre ou ferme le tiroir (branché par `WorldView.Tiroir.cs`).
//
// 📖 Pédagogie Godot/C# :
//  - Comme GesteIcon, on hérite de Button pour le clic et l'info-bulle, et on
//    peint tout nous-mêmes dans _Draw (fond natif rendu transparent).
//  - Le pictogramme porté est un GesteIcon ENFANT avec MouseFilter = Ignore :
//    il se dessine par-dessus (un enfant est peint après son parent) mais laisse
//    passer la souris, donc c'est bien CE bouton qui reçoit le clic.

using Godot;

namespace Symbiose
{
	public partial class TiroirBouton : Button
	{
		private GesteIcon _porte;      // pictogramme du geste actif hors barre (ou null)
		private string _verbPorte;
		private bool _ouvert;
		private Tween _battement;      // signal en cours (ou null)

		/// <summary>Tiroir ouvert → cadre clair (le bouton « reste enfoncé »).</summary>
		public bool Ouvert
		{
			get => _ouvert;
			set { if (_ouvert == value) return; _ouvert = value; QueueRedraw(); }
		}

		public TiroirBouton()
		{
			Flat = true;
			CustomMinimumSize = new Vector2(GesteIcon.Taille, GesteIcon.Taille);
			FocusMode = FocusModeEnum.None;
			foreach (var etat in new[] { "normal", "hover", "pressed", "disabled", "focus" })
				AddThemeStyleboxOverride(etat, new StyleBoxEmpty());
			TooltipText = "tous les gestes";
		}

		/// <summary>SIGNAL : le bouton bat ~3 s (un geste vient de s'ouvrir, ou un
		/// pressenti neuf est apparu dans le tiroir). Immobile le reste du temps —
		/// l'animation est un signal, pas un décor.
		/// 📖 Un Tween anime une propriété dans le temps sans code par image ;
		/// SetLoops(4) rejoue la séquence aller-retour quatre fois puis s'arrête.</summary>
		public void Battre()
		{
			_battement?.Kill();            // un signal en cours repart de zéro
			Modulate = Colors.White;
			_battement = CreateTween().SetLoops(4);
			_battement.TweenProperty(this, "modulate", new Color(0.45f, 1f, 0.45f), 0.4f);
			_battement.TweenProperty(this, "modulate", Colors.White, 0.4f);
		}

		/// <summary>Montre le geste actif sur le bouton (il n'a pas de case).</summary>
		public void Porter(string verb, string nom, char kind)
		{
			if (_verbPorte == verb) return;
			Vider();
			_verbPorte = verb;
			_porte = new GesteIcon { MouseFilter = MouseFilterEnum.Ignore };
			_porte.Init(verb, nom, kind);
			_porte.Actif = true;
			AddChild(_porte);
			TooltipText = $"tous les gestes · en main : {nom}";
		}

		/// <summary>Retour à la grille de points (le geste actif est dans la barre,
		/// ou il n'y a pas de geste actif).</summary>
		public void Vider()
		{
			if (_porte == null) return;
			RemoveChild(_porte);
			_porte.QueueFree();
			_porte = null;
			_verbPorte = null;
			TooltipText = "tous les gestes";
		}

		public override void _Draw()
		{
			float t = GesteIcon.Taille;
			var rect = new Rect2(0f, 0f, t, t);
			DrawRect(rect, new Color(0.14f, 0.16f, 0.18f, 0.85f), filled: true);
			// Grille 3×3 : le signe muet « d'autres gestes par ici ». Masquée par le
			// pictogramme porté quand il y en a un (l'enfant est peint par-dessus).
			var point = new Color(0.75f, 0.80f, 0.75f);
			const float cote = 6f, pas = 10f;
			float debut = (t - (2f * pas + cote)) / 2f;
			for (int l = 0; l < 3; l++)
				for (int c = 0; c < 3; c++)
					DrawRect(new Rect2(debut + c * pas, debut + l * pas, cote, cote), point);
			if (_ouvert)
				DrawRect(rect, new Color(0.9f, 0.9f, 0.7f), filled: false, width: 2f);
		}
	}
}
