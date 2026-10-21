// SYMBIOSE — WorldView.InfoBulle.cs (partial de WorldView, PLANTE ASSEMBLÉE ⑦)
// L'INFO-BULLE À DEUX NIVEAUX au survol (plantes ET bêtes) + l'observation d'un
// SIGNE. Spec : docs/rendu/pixelart/conception_plante_assemblee.md §3 (décision 4)
// et §4.4.
//
// 📖 Pédagogie — deux niveaux, une seule bascule :
//   - par DÉFAUT, l'info-bulle dit ce qu'on VOIT (le `vu` du corpus Python : « liseré
//     brun-noir au bord des feuilles », « petit coléoptère rouge à points noirs »),
//     jamais la cause ni le nom ;
//   - une fois APPRIS (liste `player.appris` du snapshot — c'est Python qui décide,
//     la vue LIT), elle ajoute la cause du signe / le nom de la bête. Même seuil que
//     le carnet interprétatif : la note se comprend, la fiche « signe » s'ouvre et
//     l'info-bulle nomme la cause AU MÊME MOMENT.
//   - Maj+F3 = AFFICHAGE TECHNIQUE (comme F6) : cause brute + intensité, clé
//     d'espèce. Seul endroit avec des chiffres (philo #5), étiqueté comme tel.
//
// Pas de 4ᵉ système de survol : même picking (FindPlant / BeteSousSouris), même
// clé de survol (`_survolSale`), même couche nette que les étiquettes. Le texte
// n'est recalculé que quand la clé change ; la légende statique (`vu`, `cause`)
// est demandée UNE fois au pont, au démarrage.
//
// « Visible au palier » = ce que le DESSIN montre (PlantRenderer.SigneVisible) :
// teinte de santé dès ×2, marques foliaires fines dès ×16 ; la vie macro dès ×4.
// INFO-BULLE DU VIVANT ② : visible = au palier ET au-dessus du SEUIL MESURÉ au rendu
// (banc WorldView.BancSeuil.cs) — un symptôme qui ne change aucun pixel se tait,
// le carnet ne le note pas non plus. Sans signe visible, la VOIX SAINE décrit le
// feuillage (vert franc / couleurs d'automne / terne), textes de la légende Python.

using Godot;
using System.Collections.Generic;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private Label _infoBulle;
		private bool _infoTechnique;   // Maj+F3

		// Légende statique du pont (commande `legende`) : signe → (vu, cause) ; bête → vu.
		private readonly Dictionary<string, (string Vu, string Cause)> _legendeSignes = new();
		private readonly Dictionary<string, string> _legendeFaune = new();
		// Voix saine (légende `voix_saine` ①) : franc / automne / terne → texte.
		private readonly Dictionary<string, string> _voixSaine = new();
		// Appris (snapshot `player.appris`), relus à chaque application de snapshot.
		private readonly HashSet<string> _signesAppris = new(), _fauneApprise = new();
		// Observations de signe déjà envoyées : "espèce|signe|saison" (dédup vue).
		private readonly HashSet<string> _signesObserves = new();

		private const string MentionTechnique =
			"affichage technique — déconseillé en première découverte";

		// Appelée par BuildPlantLabels (après l'init du pont) : label + légende.
		private void BuildInfoBulle()
		{
			_infoBulle = new Label { Visible = false };
			_infoBulle.AddThemeFontSizeOverride("font_size", 13);
			_infoBulle.AddThemeColorOverride("font_color", new Color(1f, 0.95f, 0.82f, 0.95f));
			_infoBulle.AddThemeColorOverride("font_outline_color", Colors.Black);
			_infoBulle.AddThemeConstantOverride("outline_size", 5);
			_plantLabels.AddChild(_infoBulle);
			ChargerLegende(_bridge?.Legende());
		}

		private void ChargerLegende(GDict lg)
		{
			if (lg == null) return;   // pont ancien / erreur : info-bulle muette, pas de crash
			if (lg.ContainsKey("signes"))
				foreach (var (k, v) in lg["signes"].AsGodotDictionary())
				{
					var d = v.AsGodotDictionary();
					_legendeSignes[k.AsString()] = (d["vu"].AsString(),
						d.ContainsKey("cause") ? d["cause"].AsString() : "");
				}
			if (lg.ContainsKey("faune"))
				foreach (var (k, v) in lg["faune"].AsGodotDictionary())
					_legendeFaune[k.AsString()] = v.AsString();
			if (lg.ContainsKey("voix_saine"))   // pont ≥ 0.5.47 ; absent → voix saine muette
				foreach (var (k, v) in lg["voix_saine"].AsGodotDictionary())
					_voixSaine[k.AsString()] = v.AsString();
		}

		// Appelée à l'application du bloc joueur (WorldView.Snapshot.cs). Tolérant à
		// un snapshot pré-0.5.46 (clé absente → rien d'appris).
		private void LireAppris(GDict pl)
		{
			_signesAppris.Clear();
			_fauneApprise.Clear();
			if (!pl.ContainsKey("appris")) return;
			var ap = pl["appris"].AsGodotDictionary();
			foreach (var s in ap["signes"].AsGodotArray()) _signesAppris.Add(s.AsString());
			foreach (var f in ap["faune"].AsGodotArray()) _fauneApprise.Add(f.AsString());
		}

		// Après un raccourci debug de maîtrise (P/V/R) : relire `appris` sans attendre
		// la semaine suivante (debug seulement — un snapshot complet, lecture pure).
		private void RelireAppris()
		{
			var snap = _bridge?.GetSnapshot();
			if (snap != null && snap.ContainsKey("player")) LireAppris(snap["player"].AsGodotDictionary());
			_cleVersion = -1;
		}

		// Maj+F3 : bascule défaut ↔ technique. Force le recalcul à la frame suivante.
		private void ToggleInfoTechnique()
		{
			_infoTechnique = !_infoTechnique;
			_cleVersion = -1;   // invalide la clé de survol (Survol.cs)
			GD.Print($"[WorldView] Maj+F3 → info-bulle {(_infoTechnique ? "TECHNIQUE" : "descriptive")}.");
		}

		// Appelée chaque frame (_Process), travail seulement si la clé de survol a changé.
		private void UpdateInfoBulle()
		{
			if (_infoBulle == null || !_survolSale) return;
			var plante = _plantNodes.Count > 0 ? FindPlant(_sourisMonde, HoverRadiusCm) : null;
			if (plante != null && !IsInstanceValid(plante)) plante = null;
			string signe = plante != null ? SigneDominant(plante) : null;
			// Observer le signe = regarder, comme l'espèce : indépendant du mode
			// d'étiquette (on observe même étiquettes coupées).
			if (signe != null) ObserverSigne(plante, signe);

			string bete = BeteSousSouris();
			var sb = new StringBuilder();
			if (_labelMode != LabelMode.Aucune)
			{
				if (_infoTechnique) sb.Append(MentionTechnique);
				if (plante != null) LignesPlante(sb, plante, signe);
				if (bete != null) LigneBete(sb, bete);
			}
			bool rien = sb.Length == 0 || (_infoTechnique && plante == null && bete == null);
			_infoBulle.Visible = !rien;
			if (rien) return;
			_infoBulle.Text = sb.ToString();
			// Sous l'étiquette « espèce · stade » de la plante ; sinon près du curseur.
			_infoBulle.Position = plante != null
				? WorldToWindow(plante.Position) + new Vector2(-24f, 28f)
				: _sourisPx + new Vector2(18f, 14f);
		}

		// Le signe le plus intense VISIBLE au palier courant ET au-dessus de son seuil
		// mesuré (liste déjà triée par le moteur), null si aucun ne se voit.
		private static string SigneDominant(PlantRenderer plante)
		{
			foreach (var (cause, it) in plante.Symptomes)
				if (PlantRenderer.SigneVisible(cause, it, CurrentZoom)) return cause;
			return null;
		}

		// Voix saine (aucun signe visible) : couleurs d'automne si elles se voient (dès
		// ×0,5, teinte de saison) ; sinon, dès ×2 seulement (sous ×2 la santé n'est pas
		// dessinée — on ne dit pas ce qu'on ne montre pas), vert franc ou terne selon
		// la vitalité, comparée à la borne où ApplyVitality ternit un pixel.
		private string VoixSaine(PlantRenderer plante)
		{
			string cle = plante.Automne >= PlantRenderer.SeuilAutomne ? "automne"
				: !PlantRenderer.SanteVisible(CurrentZoom) ? null
				: plante.Vitalite >= PlantRenderer.VitaliteFranche ? "franc" : "terne";
			return cle != null && _voixSaine.TryGetValue(cle, out var t) ? t : null;
		}

		private void LignesPlante(StringBuilder sb, PlantRenderer plante, string signe)
		{
			if (_infoTechnique)
			{
				var syms = plante.Symptomes;
				Ligne(sb, $"vitalité {plante.Vitalite:F2} · automne {plante.Automne:F2}");
				Ligne(sb, "symptômes : ");
				if (syms.Count == 0) sb.Append("aucun");
				for (int i = 0; i < syms.Count; i++)
				{
					var (c, it) = syms[i];
					sb.Append(i > 0 ? " · " : "").Append($"{c} {it:F2}");
					// Pourquoi il se tait ici : trop faible à tout palier, ou palier trop bas.
					if (!PlantRenderer.SigneVisible(c, it, CurrentZoom))
						sb.Append(PlantRenderer.SigneVisible(c, it, 32f) ? " (hors palier)" : " (sous seuil)");
				}
				if (signe != null) sb.Append($"  (visible ici : {signe})");
				return;
			}
			if (signe == null)
			{
				string voix = VoixSaine(plante);
				if (voix != null) Ligne(sb, voix);
				return;
			}
			if (!_legendeSignes.TryGetValue(signe, out var lg)) return;
			Ligne(sb, lg.Vu);
			if (_signesAppris.Contains(signe) && lg.Cause.Length > 0)
				sb.Append(" — ").Append(lg.Cause.ToLowerInvariant());
		}

		private void LigneBete(StringBuilder sb, string bete)
		{
			if (_infoTechnique) { Ligne(sb, $"espèce : {bete}"); return; }
			if (!_legendeFaune.TryGetValue(bete, out var vu)) return;   // carpophore : pas de `vu`
			Ligne(sb, _fauneApprise.Contains(bete)
				? char.ToUpperInvariant(bete[0]) + bete.Substring(1) + " : " + vu : vu);
		}

		private static void Ligne(StringBuilder sb, string texte)
		{
			if (sb.Length > 0) sb.Append('\n');
			sb.Append(texte);
		}

		// Envoie l'observation du signe au pont, une fois par (espèce, signe, saison)
		// côté vue — Python déduplique aussi (relu dans le ledger) ; on lui épargne
		// le spam, comme `_especesObservees`. Saison = celle de la note Python
		// (semaine consignée = semaine moteur − 1, saisons de 13 semaines).
		private void ObserverSigne(PlantRenderer plante, string signe)
		{
			if (_bridge == null) return;
			string species = plante.GetMeta(LectureSnap.Meta("species"), "").AsString();
			int saison = System.Math.Max(0, SemaineMoteur - 2) / 13;
			if (species.Length == 0 || !_signesObserves.Add($"{species}|{signe}|{saison}")) return;
			// Métas de lieu posées à la création (Snapshot.cs) ; absentes → nil → note sans lieu.
			_bridge.ObserverSigne(species, signe, plante.GetMeta(LectureSnap.Meta("tile"), default),
				plante.GetMeta(LectureSnap.Meta("lx"), default), plante.GetMeta(LectureSnap.Meta("ly"), default));
			GD.Print($"[WorldView] survol → signe observé : {signe} sur {species}.");
		}
	}
}
