// SYMBIOSE — WorldView.InfoBulleVivant.cs (partial de WorldView, INFO-BULLE DU VIVANT ③)
// La ligne d'info-bulle d'une BÊTE ou d'un CARPOPHORE survolé. Spec :
// docs/narration/semiologie/conception_infobulle_vivant.md §3.
//
// 📖 Pédagogie — ce que dit la ligne dépend de ce que le joueur SAIT :
//   - avant apprentissage, ce qu'on VOIT : « petit coléoptère rouge… · quelques-unes »
//     (le `vu` + combien on en voit dans le plot) ;
//   - une fois nommée (3 saisons d'observation, décidé par Python, lu dans
//     `player.appris`) : « Coccinelle — mange les pucerons · quelques-unes,
//     nourriture suffisante ». La nourriture n'est révélée qu'avec le nom : savoir
//     que la coccinelle a de quoi manger suppose de savoir ce qu'elle mange ;
//   - un carpophore : « petit chapeau pâle… · réseau dense », puis « Champignon —
//     décompose le bois mort · réseau dense » (rôle LU SUR PLACE par Python).
//   - Maj+F3 (technique) : nom dès le 1er survol + chiffres bruts.
// La vue ne décide RIEN : tous les textes ET toutes les bornes (abondance,
// nourriture mesurée, réseau dense) viennent de la légende Python (`legende`).
// Sans ces clés (pont pré-0.5.47), la ligne retombe sur le seul `vu`.

using Godot;
using System.Collections.Generic;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Légende ① : bête → rôle ; champignon (vu + rôles b/r/h) ; libellés et bornes.
		private readonly Dictionary<string, string> _roleFaune = new(), _roleChampignon = new();
		private readonly Dictionary<string, string> _libAbondance = new(), _libNourriture = new(),
			_libReseau = new();
		private string _vuChampignon;
		private int _abondQuelques = int.MaxValue, _abondNombreuses = int.MaxValue;
		private float _nourSuffisante, _nourAbondante, _reseauDense;

		// Appelée par ChargerLegende : clés ajoutées en 0.5.47, toutes optionnelles.
		private void ChargerLegendeVivant(GDict lg)
		{
			if (lg.ContainsKey("faune_role")) Copier(lg["faune_role"].AsGodotDictionary(), _roleFaune);
			if (lg.ContainsKey("champignon"))
			{
				var ch = lg["champignon"].AsGodotDictionary();
				_vuChampignon = ch["vu"].AsString();
				Copier(ch["roles"].AsGodotDictionary(), _roleChampignon);
			}
			if (lg.ContainsKey("abondance"))
			{
				var a = lg["abondance"].AsGodotDictionary();
				Copier(a["libelles"].AsGodotDictionary(), _libAbondance);
				_abondQuelques = a["quelques"].AsInt32();
				_abondNombreuses = a["nombreuses"].AsInt32();
			}
			if (lg.ContainsKey("nourriture"))
			{
				var n = lg["nourriture"].AsGodotDictionary();
				Copier(n["libelles"].AsGodotDictionary(), _libNourriture);
				_nourSuffisante = (float)n["suffisante"].AsDouble();
				_nourAbondante = (float)n["abondante"].AsDouble();
			}
			if (lg.ContainsKey("reseau"))
			{
				var r = lg["reseau"].AsGodotDictionary();
				Copier(r["libelles"].AsGodotDictionary(), _libReseau);
				_reseauDense = (float)r["dense"].AsDouble();
			}
		}

		private static void Copier(GDict src, Dictionary<string, string> dst)
		{
			foreach (var (k, v) in src) dst[k.AsString()] = v.AsString();
		}

		private void LigneBete(StringBuilder sb, MacroPick p)
		{
			bool champi = p.Cle == "champignon";
			string nom = char.ToUpperInvariant(p.Cle[0]) + p.Cle.Substring(1);
			string role = champi ? Lib(_roleChampignon, p.Role) : Lib(_roleFaune, p.Cle);
			if (_infoTechnique)
			{
				Ligne(sb, role != null ? $"{nom} — {role}" : nom);
				Ligne(sb, champi
					? $"clé {p.Cle} · rôle {p.Role ?? "?"} · densité {p.Densite:F2}"
					: $"clé {p.Cle} · abondance {p.Abondance} · activite "
					  + (p.Nourriture >= 0f ? p.Nourriture.ToString("F2") : "—"));
				return;
			}
			string vu = champi ? _vuChampignon : Lib(_legendeFaune, p.Cle);
			if (vu == null) return;   // clé hors corpus : on n'invente rien
			// État visible sans savoir : l'abondance (bête) / le réseau (carpophore).
			string etat = champi
				? Lib(_libReseau, p.Densite >= _reseauDense ? "dense" : "clairseme")
				: Lib(_libAbondance, p.Abondance < _abondQuelques ? "seule"
					: p.Abondance < _abondNombreuses ? "quelques" : "nombreuses");
			if (!_fauneApprise.Contains(p.Cle))
			{
				Ligne(sb, etat != null ? $"{vu} · {etat}" : vu);
				return;
			}
			Ligne(sb, role != null ? $"{nom} — {role}" : $"{nom} : {vu}");
			if (etat != null) sb.Append(" · ").Append(etat);
			// Nourriture : bête nommée seulement, si le snapshot la donne (bandes ①).
			string nour = champi || p.Nourriture < 0f ? null
				: Lib(_libNourriture, p.Nourriture < _nourSuffisante ? "rare"
					: p.Nourriture < _nourAbondante ? "suffisante" : "abondante");
			if (nour != null) sb.Append(etat != null ? ", " : " · ").Append(nour);
		}

		private static string Lib(Dictionary<string, string> d, string k)
			=> k != null && d.TryGetValue(k, out var v) ? v : null;
	}
}
