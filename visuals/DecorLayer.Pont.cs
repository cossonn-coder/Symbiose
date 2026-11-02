// SYMBIOSE — DecorLayer.Pont.cs (PÉRIPHÉRIE D73 ⑦ — le décor consomme le moteur)
// Partial de DecorLayer : la SOURCE de données du décor quand elle vient du pont
// (bloc `ceinture` du snapshot, protocole 0.5.41). Un fichier = une responsabilité :
// ici on TRADUIT l'état moteur d'un secteur en la struct `Secteur` que les tracés
// (DecorLayer.cs, DecorLayer.Arbres.cs) savent déjà dessiner. Aucun tracé ici,
// aucune règle : Python décide, la vue lit et met en forme (invariant « Godot bête »).
//
// 📖 Pédagogie — POURQUOI la vue cesse de générer son décor :
// jusqu'ici le décor était cosmétique et s'inventait depuis le seed. Le sprint
// PÉRIPHÉRIE en fait un ACTEUR ÉCOLOGIQUE : la lisière du sud ombre réellement le
// jardin, sa porosité y règle la rafale, la rivière de l'est gorge ou assèche la
// berge, et les gestes du joueur (abattre/recéper/étêter/endiguer/dériver/entailler)
// changent ces valeurs. Un décor qui continuerait de s'inventer MENTIRAIT : on
// verrait une forêt là où le moteur n'a qu'une prairie, et une clairière ouverte à
// la hache ne se verrait pas. D'où la règle : ce qui a un effet écologique se LIT
// du snapshot, jamais ne se devine (cf. D47, « les menus qui mentent »).
//
// 📖 Pédagogie — le repli, et pourquoi il RESTE :
// un monde peut légitimement n'avoir pas de périphérie (fixture smoke, banc
// thématique, binaire antérieur à 0.5.41). Dans ce cas le bloc est ABSENT et
// `BuildProfile(seed)` reprend la main — le décor d'avant, au pixel près, parce que
// `DuPont` reste false et que tous les facteurs ci-dessous rendent alors 1.

using Godot;
using GDict = Godot.Collections.Dictionary;
using GArray = Godot.Collections.Array;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Dernier bloc `ceinture` reçu (null = aucun ⇒ repli local par seed). On
		// garde la DONNÉE plutôt que le profil construit : la rotation D35 et le
		// toggle F10 rappellent Build(seed), qui reconstruit depuis la même source.
		private GArray _ceinture;

		// Références de NORMALISATION, miroirs des plages du générateur Python
		// (`fields/peripherie.py` : DENSITE_FORET[1] = 0.95, HAUTEUR_FORET_CM[1] =
		// 2000). Une lisière au maximum de ce que le terrain sait produire rend le
		// décor NOMINAL (celui d'avant le pont) ; en-dessous, ça s'éclaircit.
		private const float DensiteRef = 0.95f;
		private const float HauteurRefCm = 2000f;
		// Hauteur d'un ligneux de FRICHE : le moteur ne lui donne pas de canopée
		// (`hauteur_canopee` reste 0 — une friche n'ombre ni n'abrite, §②). Il faut
		// pourtant dessiner quelque chose : des ronciers et semis de 2,5 m.
		private const float HauteurFricheCm = 250f;
		// Plancher de taille : sous ce facteur un arbre devient un point illisible.
		// Un secteur rasé garde donc des repousses VISIBLES au ras du sol — ce qui
		// est exactement ce que le moteur simule (plancher pionnier, §④).
		private const float TailleMin = 0.28f;
		// Ligne d'eau qui DOUBLE la largeur du lit, en cm (bornes moteur : −150 à
		// +120). Placeholder de calibrage F5, comme le pas d'`endiguer`.
		private const float LigneEauPleineCm = 200f;
		// Entaille au-delà de laquelle le pied de falaise est jonché d'éboulis.
		// Miroir de `ENTAILLE_REFERENCE_CM` (2 × 150 cm) côté moteur.
		private const float EntailleRefCm = 300f;

		/// <summary>
		/// Le décor reçoit la ceinture du moteur (bloc `ceinture` du snapshot) et se
		/// redessine. Appelée à chaque snapshot : la coupe faite au clic précédent est
		/// donc visible au retour de l'action (le pont renvoie un snapshot frais).
		/// `null` (bloc absent) REND la main au repli local — on ne garde pas une
		/// ceinture périmée d'un monde qu'on a quitté.
		/// </summary>
		public void SetCeinture(GArray ceinture)
		{
			_ceinture = ceinture != null && ceinture.Count > 0 ? ceinture : null;
			LireFloraison(_ceinture);   // LISIÈRE NUE ② : par semaine, sans toucher la maille
			if (!_built) return;
			// FLUIDITÉ PC ③ : le snapshot arrive CHAQUE semaine, la ceinture change
			// rarement (un geste, une recolonisation lente). Avant, chaque snapshot
			// redessinait le décor entier ; avec le kit, un redessin coûte des
			// dizaines de ms [VM] → on ne reconstruit que si le profil a CHANGÉ.
			if (!_banc && _ceinture != null && MemeProfil(BuildFromBridge(_ceinture, _seed), _profile))
				return;
			Build(_seed);   // reconstruit le profil, puis QueueRedraw
		}

		// Deux profils dessinent-ils la même chose ? Champ à champ (struct avec une
		// chaîne : on n'utilise pas l'Equals par réflexion de ValueType).
		private static bool MemeProfil(SurroundingsProfile a, SurroundingsProfile b)
		{
			if (a.Secteurs == null || b.Secteurs == null) return false;
			for (int i = 0; i < 4; i++)
			{
				Secteur x = a.Secteurs[i], y = b.Secteurs[i];
				if (x.Motif != y.Motif || x.Pente != y.Pente || x.SeedSecteur != y.SeedSecteur
					|| x.DuPont != y.DuPont || x.DensiteLigneuse != y.DensiteLigneuse
					|| x.HauteurCanopeeCm != y.HauteurCanopeeCm || x.LigneEauCm != y.LigneEauCm
					|| x.AltitudeRelativeCm != y.AltitudeRelativeCm || x.EntailleCm != y.EntailleCm
					|| x.Essence != y.Essence || !MemesColonies(x.Colonies, y.Colonies))
					return false;
			}
			return true;
		}

		/// <summary>
		/// Le profil des alentours LU du pont : 4 secteurs, un par bord cardinal.
		/// Alimente la MÊME struct que `BuildProfile(seed)` — les tracés ne savent pas
		/// d'où vient le profil, et c'était toute l'intention de la couture D58·T4.
		/// </summary>
		private static SurroundingsProfile BuildFromBridge(GArray ceinture, int seed)
		{
			var secteurs = new Secteur[4];
			// Le repli sert de FOND : un bloc partiel (côté manquant) laisse une
			// prairie cohérente au lieu d'un trou. Seed 0 : la ceinture du pont écrase
			// tout ce qui compte, seul le tracé sinueux garde une graine.
			var defaut = BuildProfile(0);
			for (int i = 0; i < 4; i++) secteurs[i] = defaut.Secteurs[i];

			foreach (var sv in ceinture)
			{
				var d = sv.AsGodotDictionary();
				int cote = d["cote"].AsInt32();
				if (cote < 0 || cote > 3) continue;
				string type = d["type"].AsString();
				secteurs[cote] = new Secteur
				{
					Cote = cote,
					Motif = MotifDeType(type),
					// La PENTE ne vient pas du moteur (il n'a pas ce champ) : on la
					// dérive du seed du secteur, comme avant — c'est un détail de
					// tracé, pas une donnée écologique.
					// FLUIDITÉ PC ③ : la graine inclut le SEED DU TERRAIN (avant, deux
					// terrains au même type de bord avaient la même lisière — philo
					// #7) et passe par Melange (djb2 seul : bits hauts mal brassés).
					Pente = (PenteFalaise)(Melange(HashKey($"pente|{seed}|{cote}|{type}")) % 3u),
					SeedSecteur = Melange(HashKey($"ceinture|{seed}|{cote}|{type}")),
					DuPont = true,
					DensiteLigneuse = Reel(d, "densite_ligneuse"),
					HauteurCanopeeCm = Reel(d, "hauteur_canopee"),
					LigneEauCm = Reel(d, "ligne_eau"),
					AltitudeRelativeCm = Reel(d, "altitude_relative"),
					EntailleCm = Reel(d, "entaille_cm"),
					Essence = d.ContainsKey("essence")
						&& d["essence"].VariantType != Variant.Type.Nil
						? d["essence"].AsString() : null,
					Colonies = LireColonies(d),
				};
			}
			return new SurroundingsProfile { Secteurs = secteurs };
		}

		// Lecture TOLÉRANTE d'un réel : clé absente ou nulle → 0 (un binaire plus
		// vieux peut n'émettre qu'une partie des champs, cf. tous les bumps).
		private static float Reel(GDict d, string cle) =>
			d.ContainsKey(cle) && d[cle].VariantType != Variant.Type.Nil
				? (float)d[cle].AsDouble() : 0f;

		// Types du moteur (`fields/peripherie.TYPES`) → motifs de rendu. Un type
		// inconnu (moteur plus récent que la vue) retombe sur la prairie : neutre et
		// jamais un crash.
		private static Motif MotifDeType(string type) => type switch
		{
			"foret"   => Motif.Foret,
			"riviere" => Motif.Riviere,
			"falaise" => Motif.Falaise,
			"friche"  => Motif.Friche,
			_         => Motif.Prairie,
		};

		// -------------------------------------------------------------------
		// FACTEURS DE RENDU — l'état moteur devient de la masse dessinée.
		// Tous rendent 1 (ou la valeur nominale) hors pont : le décor de repli est
		// bit-pour-bit celui d'avant ce tronçon.
		// -------------------------------------------------------------------

		/// <summary>Facteur d'OCCUPATION du semis d'arbres ∝ densité ligneuse. Une
		/// clairière ouverte à la hache (densité 0.10) laisse ~10 % des arbres : le
		/// geste se VOIT, sans jauge ni chiffre (philo #5).</summary>
		private static float FacteurDensite(Secteur s) =>
			!s.DuPont ? 1f : Mathf.Clamp(s.DensiteLigneuse / DensiteRef, 0f, 1.05f);

		/// <summary>Facteur de TAILLE d'un arbre ∝ hauteur de canopée. Étêter (la
		/// trogne) rabat la hauteur SANS toucher la densité : autant d'arbres, plus
		/// courts — l'asymétrie des gestes du ④ se lit à l'œil.</summary>
		private static float FacteurTaille(Secteur s)
		{
			if (!s.DuPont) return 1f;
			float hCm = s.HauteurCanopeeCm > 0f ? s.HauteurCanopeeCm
					  : s.Motif == Motif.Friche ? HauteurFricheCm : 0f;
			return Mathf.Clamp(hCm / HauteurRefCm, TailleMin, 1.05f);
		}

		/// <summary>Hauteur de la FACE de falaise (cm monde) : la roche restante du
		/// moteur, ou la pente du profil local en repli. Entailler l'abaisse
		/// définitivement — le seul geste dont on ne revient pas.</summary>
		private static float HauteurFaceCm(Secteur s)
		{
			if (s.DuPont && s.AltitudeRelativeCm > 0f) return s.AltitudeRelativeCm;
			return s.Pente switch
			{
				PenteFalaise.Douce     => 190f,
				PenteFalaise.Verticale => 330f,
				_                      => 470f,   // déversante : surplomb haut
			};
		}

		/// <summary>Facteur de largeur du LIT ∝ ligne d'eau (endiguée = large,
		/// dérivée = filet). Borné pour que le lit reste dans la bande.</summary>
		private static float FacteurLit(Secteur s) =>
			!s.DuPont ? 1f
				: Mathf.Clamp(1f + s.LigneEauCm / LigneEauPleineCm, 0.35f, 1.8f);

		/// <summary>Part des pas jonchés d'ÉBOULIS au pied d'une falaise (0..100) :
		/// ~42 % au repos, jusqu'à ~82 % sur une roche entaillée.</summary>
		private static uint SeuilEboulis(Secteur s)
		{
			if (!s.DuPont || s.EntailleCm <= 0f) return 42u;
			float t = Mathf.Min(1f, s.EntailleCm / EntailleRefCm);
			return (uint)Mathf.RoundToInt(42f + 40f * t);
		}
	}
}
