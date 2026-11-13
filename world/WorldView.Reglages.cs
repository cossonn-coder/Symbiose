// SYMBIOSE — WorldView.Reglages.cs (partial de WorldView, sprint PALETTE & TIROIR ②)
// LA RANGÉE DE RÉGLAGES du geste actif. Certains gestes demandent un CHOIX avant
// d'agir : quelle graine (`planter`, `planter_conteneur`), quel substrat
// (`poser_pot`, `poser_bac_culture`), quel paillis (`pailler`). Ce choix se faisait
// à l'aveugle par les touches S, B, N ; il devient une rangée de pastilles visibles
// et cliquables, posée à droite de la barre, À HAUTEUR du geste actif. Un geste
// sans réglage → pas de rangée.
//
// UNE SEULE SOURCE D'ÉTAT : la rangée lit et écrit les index qui existaient déjà
// (`_seedIndex`, `_substratIndex`, `_natureIndex`, dans WorldView.Actions.cs). Ce
// que le pont reçoit ne change pas d'un octet (`params.species`/`substrat`/`nature`).
//
// 📖 Pédagogie Godot/C# :
//  - HBoxContainer aligne ses enfants en ligne et calcule sa propre largeur.
//  - Reconstruire des nœuds a un coût : on compare d'abord une EMPREINTE (une
//    chaîne qui résume ce que la rangée doit montrer). Identique → on déplace
//    seulement le cadre du choix courant. C'est le même garde-fou que la barre.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private HBoxContainer _reglagesBox;
		private readonly List<ReglagePastille> _reglagesPastilles = new();
		private string _reglagesEmpreinte = "";
		// Natures de mulch dont le stock couvre un geste (`player.paillis_dispo`,
		// pont 0.6.13). null = clé absente (ancien serveur) → on n'estompe rien.
		private HashSet<string> _paillisDispo;
		private readonly Dictionary<string, string> _grainesEspece = new();
		// CATALOGUE DES GRAINES (GESTES LISIBLES ④) : ouvert à l'armement de `planter`, il
		// montre toute la banque ; il se REFERME au choix d'une graine et ne garde que la
		// graine choisie (un clic dessus le rouvre).
		private bool _catalogueOuvert;
		private Reglage _reglagePrecedent = Reglage.Aucun;

		// Teintes des substrats posables (fond, grain) — même ordre que `Substrats`.
		// Placeholders lisibles : sombre = organique, clair = minéral ou mycélien.
		private static readonly (Color Fond, Color Grain)[] TeintesSubstrat =
		{
			(new Color("4a3626"), new Color("6b5038")),   // terreau : brun
			(new Color("2c221a"), new Color("5a4a2e")),   // compost : presque noir
			(new Color("8f8a80"), new Color("c9c4b8")),   // drainant minéral : gris
			(new Color("7a5e38"), new Color("b89a52")),   // lasagnes : brun strié de paille
			(new Color("a89c86"), new Color("ece6d6")),   // mycélium usé : beige piqué de blanc
		};

		private enum Reglage { Aucun, Graine, Substrat, Paillis }

		// Quel réglage demande le geste actif ? (Table unique : c'est ICI qu'on
		// ajoute un geste à réglage.)
		private Reglage ReglageDuGesteActif()
		{
			if (_gesteIndex < 0) return Reglage.Aucun;
			return Gestes[_gesteIndex].Verb switch
			{
				"planter" or "planter_conteneur" => Reglage.Graine,
				"poser_pot" or "poser_bac_culture" => Reglage.Substrat,
				"pailler" => Reglage.Paillis,
				_ => Reglage.Aucun,
			};
		}

		// -------------------------------------------------------------------
		// DONNÉE — natures de mulch disponibles (snapshot).
		// -------------------------------------------------------------------

		// Clé de graine → nom d'espèce (`player.graines_espece`, 0.6.13) : les teintes
		// d'espèce sont rangées par NOM D'ESPÈCE (« Basil »), la banque par CLÉ de
		// catalogue (« basilic »). Clé inconnue → teinte par défaut.
		private void ApplyGrainesEspece(Godot.Collections.Dictionary noms)
		{
			if (noms == null) return;
			foreach (var k in noms.Keys) _grainesEspece[k.AsString()] = noms[k].AsString();
		}

		private void ApplyPaillisDispo(Godot.Collections.Array dispo)
		{
			_paillisDispo = dispo == null ? null : new HashSet<string>();
			if (dispo != null)
				foreach (var n in dispo) _paillisDispo.Add(n.AsString());
			SynchroniserReglages();
		}

		// -------------------------------------------------------------------
		// SYNCHRO — appelée quand le geste actif, la banque, le stock ou le tiroir
		// bougent. Ne reconstruit que si ce qu'il faut montrer a changé.
		// -------------------------------------------------------------------

		private void SynchroniserReglages()
		{
			if (_paletteLayer == null) return;
			var reglage = ReglageDuGesteActif();
			if (reglage == Reglage.Graine && _reglagePrecedent != Reglage.Graine) _catalogueOuvert = true;
			_reglagePrecedent = reglage;
			// Tiroir ouvert : il occupe la même place à droite de la barre → la
			// rangée s'efface le temps qu'on choisisse un geste.
			if (reglage == Reglage.Aucun || TiroirOuvert)
			{
				if (_reglagesBox != null) _reglagesBox.Visible = false;
				return;
			}
			if (_reglagesBox == null)
			{
				_reglagesBox = new HBoxContainer();
				_reglagesBox.AddThemeConstantOverride("separation", 4);
				_paletteLayer.AddChild(_reglagesBox);
			}
			string empreinte = EmpreinteReglages(reglage);
			if (empreinte != _reglagesEmpreinte)
			{
				_reglagesEmpreinte = empreinte;
				ConstruireReglages(reglage);
			}
			int courant = reglage switch
			{
				Reglage.Graine => _catalogueOuvert ? _seedIndex : 0,   // fermé : la seule pastille
				Reglage.Substrat => _substratIndex,
				_ => _natureIndex,
			};
			for (int i = 0; i < _reglagesPastilles.Count; i++)
				_reglagesPastilles[i].Courant = i == courant
					&& !(reglage == Reglage.Graine && _seeds.Count == 0);   // case vide : rien de choisi
			_reglagesBox.Position = PositionReglages();
			_reglagesBox.Visible = true;
		}

		// Résumé de ce que la rangée doit montrer (hors choix courant).
		private string EmpreinteReglages(Reglage reglage)
		{
			switch (reglage)
			{
				case Reglage.Graine:
					var cles = new List<string>(_seeds.Count);
					foreach (var (cle, _) in _seeds) cles.Add(cle);
					return (_catalogueOuvert ? "g+:" : $"g-{_seedIndex}:") + string.Join(",", cles);
				case Reglage.Paillis:
					return "p:" + (_paillisDispo == null ? "*" : string.Join(",", Sorted(_paillisDispo)));
				default:
					return "s";
			}
		}

		private void ConstruireReglages(Reglage reglage)
		{
			foreach (var c in _reglagesBox.GetChildren())
			{
				_reglagesBox.RemoveChild(c);
				c.QueueFree();
			}
			_reglagesPastilles.Clear();
			switch (reglage)
			{
				case Reglage.Graine:
					// Banque vide : une case vide estompée dit « rien à semer ». Le
					// geste reste sélectionnable ; le refus viendra du moteur.
					if (_seeds.Count == 0)
					{
						var vide = AjouterPastille(ReglagePastille.Forme.Vide, "aucune graine",
												   Colors.Transparent, Colors.Transparent, null);
						vide.Estompe = true;
						break;
					}
					// Fermé : la graine choisie seule, un clic rouvre le catalogue. Ouvert :
					// toute la banque (déjà triée, ApplySeeds), un clic choisit et referme.
					for (int i = _catalogueOuvert ? 0 : _seedIndex; i < _seeds.Count; i++)
					{
						int idx = i;                         // capture par valeur
						var (feuille, _, fruit) = PlantRenderer.TeintesEspece(
							_grainesEspece.TryGetValue(_seeds[i].Key, out var nom) ? nom : null);
						AjouterPastille(ReglagePastille.Forme.Graine, NomGraine(_seeds[i].Key), feuille, fruit,
										_catalogueOuvert ? () => { _seedIndex = idx; _catalogueOuvert = false; }
														 : () => { _catalogueOuvert = true; });
						if (!_catalogueOuvert) break;
					}
					break;
				case Reglage.Substrat:
					for (int i = 0; i < Substrats.Length; i++)
					{
						int idx = i;
						AjouterPastille(ReglagePastille.Forme.Substrat, Substrats[i].Replace('_', ' '),
										TeintesSubstrat[i].Fond, TeintesSubstrat[i].Grain,
										() => { _substratIndex = idx; });
					}
					break;
				case Reglage.Paillis:
					for (int i = 0; i < Natures.Length; i++)
					{
						int idx = i;
						var teinte = MulchLayer.CouleurNature(Natures[i]);
						var p = AjouterPastille(ReglagePastille.Forme.Paillis, Natures[i], teinte, teinte,
												() => { _natureIndex = idx; });
						// Stock qui ne couvre pas un geste → pâlie, sans chiffre.
						p.Estompe = _paillisDispo != null && !_paillisDispo.Contains(Natures[i]);
					}
					break;
			}
		}

		// Pose une pastille ; `choisir` écrit l'index concerné, puis on rafraîchit le
		// texte du HUD et le cadre de la rangée.
		private ReglagePastille AjouterPastille(ReglagePastille.Forme forme, string nom,
												Color fond, Color accent, System.Action choisir)
		{
			var p = new ReglagePastille();
			p.Init(forme, nom, fond, accent);
			if (choisir != null)
				p.Pressed += () =>
				{
					choisir();
					UpdateActionHud();
					SynchroniserReglages();
				};
			_reglagesPastilles.Add(p);
			_reglagesBox.AddChild(p);
			return p;
		}

		// Nom AFFICHÉ d'une graine (info-bulle) : la clé de catalogue, sans soulignés.
		private static string NomGraine(string cle) => cle.Replace('_', ' ');

		// Ordre du catalogue : alphabétique sur le nom affiché, accents ignorés (« épinard »
		// entre « endive » et « fenouil », pas après « z » comme en ordre ordinal).
		private static int OrdreGraines(string a, string b) =>
			string.CompareOrdinal(CleTri(NomGraine(a)), CleTri(NomGraine(b)));

		private static string CleTri(string nom)
		{
			var sb = new System.Text.StringBuilder(nom.Length);
			foreach (char ch in nom.Normalize(System.Text.NormalizationForm.FormD))
				if (System.Globalization.CharUnicodeInfo.GetUnicodeCategory(ch)
					!= System.Globalization.UnicodeCategory.NonSpacingMark)
					sb.Append(char.ToLowerInvariant(ch));
			return sb.ToString();
		}

		// À droite de la barre, à hauteur du geste actif : sa case s'il en a une,
		// sinon le bouton du tiroir (qui le porte). La barre empile ses cases
		// occupées tous les (Taille + 4) px à partir de y = 150.
		private Vector2 PositionReglages()
		{
			int rang = 0;
			for (int s = 0; s < SlotCount; s++)
			{
				if (_slots[s] == _gesteIndex) break;
				if (_slots[s] >= 0) rang++;
			}
			float y = 150f + rang * (GesteIcon.Taille + 4f)
					  + (GesteIcon.Taille - ReglagePastille.Taille) / 2f;
			return new Vector2(10f + GesteIcon.Taille + 8f, y);
		}
	}
}
