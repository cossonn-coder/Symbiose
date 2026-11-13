// SYMBIOSE — TiroirPanel.cs (sprint PALETTE & TIROIR ①)
// LE TIROIR DES GESTES : un panneau qui montre TOUS les gestes ouverts, rangés
// par familles (une rangée par famille, dans l'ordre que donne le pont). La barre
// de gauche n'a que dix cases ; le tiroir, lui, n'oublie aucun geste. Ce fichier
// ne fait que l'AFFICHAGE : il ne sait rien du pont, des cases ni de la
// persistance — il reçoit des rangées toutes prêtes et rappelle deux actions
// (clic gauche = choisir, clic droit = mettre en case), branchées par
// `WorldView.Tiroir.cs`.
//
// Philo #5 : aucun texte permanent. Le nom du geste et celui de sa famille
// n'apparaissent qu'au SURVOL (info-bulle native de Godot).
//
// 📖 Pédagogie Godot/C# :
//  - PanelContainer = un conteneur qui peint un fond (StyleBox) derrière son
//    unique enfant et l'entoure de marges. Son MouseFilter vaut `Stop` par
//    défaut : un clic sur le fond du tiroir est AVALÉ ici et n'atteint jamais
//    `_UnhandledInput` de WorldView — c'est ce qui permet à « clic hors du
//    tiroir = fermer » de ne pas se déclencher quand on clique DANS le tiroir.
//  - VBoxContainer (rangées) > HBoxContainer (les icônes d'une famille) : les
//    conteneurs calculent seuls la taille du panneau, rien à mesurer à la main.
//  - `readonly record struct` = un petit n-uplet nommé, copié par valeur, sans
//    allocation : idéal pour passer des lignes de données à un afficheur.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class TiroirPanel : PanelContainer
	{
		/// <summary>Un geste à montrer : son index dans `Gestes[]` et de quoi
		/// fabriquer son pictogramme (mêmes trois champs que la barre).</summary>
		public readonly record struct Entree(int Geste, string Verb, string Nom, char Kind);

		/// <summary>Clic gauche sur un geste (index dans `Gestes[]`).</summary>
		public System.Action<int> OnChoisi;
		/// <summary>Clic droit sur un geste : l'icône sert d'ancre au menu.</summary>
		public System.Action<int, GesteIcon> OnClicDroit;

		private readonly VBoxContainer _rangees = new();
		// Les icônes posées, pour déplacer le cadre « actif » sans tout refaire.
		private readonly List<(int Geste, GesteIcon Icone)> _icones = new();

		public TiroirPanel()
		{
			// Même plaque sombre que les cases de la barre, un ton plus opaque pour
			// rester lisible par-dessus le jardin.
			var fond = new StyleBoxFlat
			{
				BgColor = new Color(0.09f, 0.11f, 0.13f, 0.93f),
				BorderColor = new Color(0.45f, 0.55f, 0.45f, 0.9f),
			};
			fond.SetBorderWidthAll(1);
			fond.SetContentMarginAll(6f);
			AddThemeStyleboxOverride("panel", fond);
			_rangees.AddThemeConstantOverride("separation", 4);
			AddChild(_rangees);
		}

		/// <summary>Remplace tout le contenu. `rangees` = (nom de famille, ses
		/// gestes ouverts) dans l'ordre d'affichage ; une famille vide n'est pas
		/// transmise. À n'appeler que lorsque l'ensemble des gestes ouverts change.</summary>
		public void Remplir(IList<(string Famille, List<Entree> Gestes)> rangees, int gesteActif)
		{
			foreach (var c in _rangees.GetChildren())
			{
				_rangees.RemoveChild(c);
				c.QueueFree();
			}
			_icones.Clear();
			foreach (var (famille, gestes) in rangees)
			{
				var ligne = new HBoxContainer { TooltipText = famille };
				ligne.AddThemeConstantOverride("separation", 4);
				// Repère de famille : un simple liseré en tête de rangée. Il ne dit
				// rien par lui-même ; survolé, il donne le nom de la famille.
				ligne.AddChild(new ColorRect
				{
					Color = new Color(0.45f, 0.55f, 0.45f, 0.7f),
					CustomMinimumSize = new Vector2(3f, GesteIcon.Taille),
					TooltipText = famille,
				});
				foreach (var e in gestes)
				{
					var icone = new GesteIcon();
					icone.Init(e.Verb, e.Nom, e.Kind);
					icone.TooltipText = $"{e.Nom} · {famille}";   // survol : geste + famille
					icone.Actif = e.Geste == gesteActif;
					int g = e.Geste;                     // capture par valeur
					icone.Pressed += () => OnChoisi?.Invoke(g);
					icone.OnRightClick = () => OnClicDroit?.Invoke(g, icone);
					_icones.Add((g, icone));
					ligne.AddChild(icone);
				}
				_rangees.AddChild(ligne);
			}
			// Le panneau a pu rétrécir : repartir de la taille minimale.
			ResetSize();
		}

		/// <summary>Déplace le cadre lumineux sur le geste actif (−1 = aucun).</summary>
		public void MarquerActif(int gesteActif)
		{
			foreach (var (g, icone) in _icones) icone.Actif = g == gesteActif;
		}
	}
}
