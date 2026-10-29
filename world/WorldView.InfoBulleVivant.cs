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
		// Sol qui respire ⑤ (pont 0.5.53) : `vu` par ESPÈCE de champignon (légende), et
		// nom + comestibilité des seules espèces NOMMÉES (`player.appris.champignons`).
		private readonly Dictionary<string, string> _vuChampiEspece = new();
		private readonly Dictionary<string, (string Nom, string Comestibilite)> _champiNommes = new();
		private int _abondQuelques = int.MaxValue, _abondNombreuses = int.MaxValue;
		private float _nourSuffisante, _nourAbondante, _reseauDense;

		// Appelée par ChargerLegende : clés ajoutées en 0.5.47, toutes optionnelles.
		private void ChargerLegendeVivant(GDict lg)
		{
			if (lg.ContainsKey("faune_role")) Copier(lg["faune_role"].AsGodotDictionary(), _roleFaune);
			if (lg.ContainsKey("champignons")) Copier(lg["champignons"].AsGodotDictionary(), _vuChampiEspece);
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

		// Appelée par LireAppris : nom + comestibilité des champignons NOMMÉS (Python
		// ne les envoie qu'une fois le nom mérité — la vue ne peut rien révéler trop tôt).
		private void LireChampignonsNommes(GDict ap)
		{
			_champiNommes.Clear();
			if (!ap.ContainsKey("champignons")) return;
			foreach (var (k, v) in ap["champignons"].AsGodotDictionary())
			{
				var d = v.AsGodotDictionary();
				_champiNommes[k.AsString()] = (d["nom"].AsString(), d["comestibilite"].AsString());
			}
		}

		private void LigneBete(StringBuilder sb, MacroPick p)
		{
			bool champi = p.Cle == "champignon" || _vuChampiEspece.ContainsKey(p.Cle);
			bool champiNomme = _champiNommes.TryGetValue(p.Cle, out var cn);
			string nom = champiNomme ? cn.Nom
				: char.ToUpperInvariant(p.Cle[0]) + p.Cle.Substring(1).Replace('_', ' ');
			string role = champi ? Lib(_roleChampignon, p.Role) : Lib(_roleFaune, p.Cle);
			if (_infoTechnique)
			{
				Ligne(sb, role != null ? $"{nom} — {role}" : nom);
				Ligne(sb, champi ? $"clé {p.Cle} · rôle {p.Role ?? "?"}"
								 : $"clé {p.Cle} · abondance {p.Abondance}");
				// Jauges (D112 ②), sens par clé : réseau d'un carpophore → bon = dense
				// (mal = 1 − densité, seuil = « réseau dense », pastille F6 mycelium) ;
				// nourriture d'une bête → bon = abondante (mal = 1 − activité, seuil =
				// « suffisante », pastille = la heatmap F6 de l'espèce). L'abondance
				// reste un chiffre : son « bon » dépend du rôle (ravageur ou auxiliaire),
				// que la vue ne décide pas.
				if (champi)
					Jauge(sb, "réseau", 1f - p.Densite, 1f - _reseauDense, p.Densite,
						  JaugesInfoBulle.PastilleDe("mycelium"));
				else if (p.Nourriture >= 0f)
					Jauge(sb, "nourriture", 1f - p.Nourriture, 1f - _nourSuffisante, p.Nourriture,
						  JaugesInfoBulle.PastilleDe(p.Cle));
				return;
			}
			string vu = champi ? (Lib(_vuChampiEspece, p.Cle) ?? _vuChampignon)
				: Lib(_legendeFaune, p.Cle);
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
			if (champiNomme) Ligne(sb, cn.Comestibilite);   // dite seulement une fois nommé
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
