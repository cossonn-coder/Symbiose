// SYMBIOSE — DecorLayer.Saison.cs (AUTOMNE VISIBLE ⑥ — la lisière dit la saison et le temps)
// Partial de DecorLayer : classes de matière des texels (lues par decor_indexe.gdshader)
// et uniforms de saison et de météo. La maille n'est JAMAIS reconstruite pour ça : 1 draw
// call conservé. Le ciel, l'état et le manteau viennent du snapshot (SignesLisiere.cs).
//
// 📖 Pédagogie — c'est le principe de la palette tournante des jeux SNES : l'image garde
// ses indices, seule la table de lecture change. Ici la « table » est choisie dans le
// shader, par pied, selon la semaine : aucun pixel d'atlas n'est réécrit chaque semaine.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Classe de matière, 2 bits (contrat : en-tête de decor_indexe.gdshader).
		private const int ClasseInerte = 0, ClasseFeuillu = 1, ClassePrairie = 2, ClasseSansSaison = 3;
		private const int DecalageClasse = 32;   // bits de la classe dans une source de palette
		private const int OrientFleur = 13;      // orientation du shader : fleur de prairie

		private int _classeAplat = ClasseInerte;

		/// <summary>Classe de matière des aplats suivants.</summary>
		private void ClasseAplats(int classe) => _classeAplat = classe;

		private static int ClasseTeinte(Teinte t) => t switch
		{
			Teinte.Chene or Teinte.Hetre or Teinte.Bouleau or Teinte.Charme => ClasseFeuillu,
			Teinte.PrairieClair or Teinte.Prairie or Teinte.Paille or Teinte.Roncier
				or Teinte.SousBois or Teinte.Roseau => ClassePrairie,
			Teinte.Sapin or Teinte.Roche or Teinte.RocheClaire => ClasseSansSaison,
			_ => ClasseInerte,
		};

		// Rampes d'arrivée : uniform du shader → matière de RampesDa.Matieres. Des rampes
		// écrites à la main : une rampe dérivée vire au vert dans ses ombres, et un bois
		// d'hiver redevenait vert au palier ×1.
		private static readonly string[] Rampes =
		{
			"tendre", "jaune", "orange", "roux", "terne", "regain", "paille", "grille",
			"sombre", "givre", "neige", "brume_chaude", "brume_froide", "fleur_b", "fleur_j",
		};

		private const float TauSemaineS = 3f;   // la saison glisse d'une semaine à l'autre
		private const float TauMeteoS = 4f;     // le temps s'installe en quelques secondes
		private const float MeteoEps = 0.002f;

		private int _saisonGen = -1;
		private float _semaineCible = -1f, _semaine = -1f;
		private EffetLisiere _etat, _signes, _manteau, _meteo;
		private bool _meteoPosee;

		/// <summary>Semaine du snapshot (`week_in_year`, 1 = équinoxe de printemps).</summary>
		public void SetSemaine(int semaine) => _semaineCible = semaine;

		/// <summary>Bloc `weather` du snapshot, après les forçages des bancs.</summary>
		public void SetMeteo(GDict weather) => _etat = SignesLisiere.DeEtat(
			weather.ContainsKey("kind") ? weather["kind"].AsString() : null,
			weather.ContainsKey("intensity") ? (float)weather["intensity"].AsDouble() : 0f);

		/// <summary>Bloc `ciel` du snapshot.</summary>
		public void SetSignes(GDict ciel) => _signes = SignesLisiere.DeCiel(ciel);

		/// <summary>Bloc `temperature` : la ceinture n'a pas d'état de neige propre, le
		/// manteau moyen des tuiles (`snow`, vérité moteur) vaut pour la lisière.</summary>
		public void SetManteau(GDict temperature)
		{
			float somme = 0f;
			int n = 0;
			foreach (var kv in temperature)
			{
				var td = kv.Value.AsGodotDictionary();
				if (td.ContainsKey("snow")) somme += (float)td["snow"].AsDouble();
				n++;
			}
			_manteau = new EffetLisiere(Neige: n > 0 ? Mathf.Clamp(2f * somme / n, 0f, 1f) : 0f);
		}

		/// <summary>Chaque image : lisse puis écrit semaine et météo, au changement seulement.</summary>
		private void MajSaison(float dt)
		{
			var m = MateriauDecor;
			if (_saisonGen != PaletteIndexee.Generation)   // LUT vidée : les n° ont changé
			{
				_saisonGen = PaletteIndexee.Generation;
				foreach (string nom in Rampes)
					m.SetShaderParameter("r_" + nom, PaletteIndexee.PaletteNommee("lisiere_" + nom));
				m.SetShaderParameter("i_fleur_jaune", IdSource(SourceTeinte((int)Teinte.FleurJaune)));
			}
			// Bancs : pas de transition, la capture doit montrer l'état demandé.
			bool net = WorldView.CaptureActive;
			if (_semaineCible > 0f)
			{
				float ecart = _semaine < 0f ? 0f : Mathf.PosMod(_semaineCible - _semaine + 26f, 52f) - 26f;
				float suivante = _semaine < 0f || net ? _semaineCible
					: Mathf.PosMod(_semaine + ecart * (1f - Mathf.Exp(-dt / TauSemaineS)), 52f);
				if (Mathf.Abs(suivante - _semaine) > 0.001f)
				{
					_semaine = suivante;
					m.SetShaderParameter("semaine", _semaine);
				}
			}
			MajFloraison(m, net, dt);   // LISIÈRE NUE ② (DecorLayer.Colonies.cs)
			EffetLisiere cible = _etat.Max(_signes).Max(_manteau);
			float a = net || !_meteoPosee ? 1f : 1f - Mathf.Exp(-dt / TauMeteoS);
			if (_semaineCible > 0f) _meteoPosee = true;
			Uniforme(m, "m_seche", ref _meteo, _meteo.Seche, cible.Seche, a, (e, v) => e with { Seche = v });
			Uniforme(m, "m_humide", ref _meteo, _meteo.Humide, cible.Humide, a, (e, v) => e with { Humide = v });
			Uniforme(m, "m_givre", ref _meteo, _meteo.Givre, cible.Givre, a, (e, v) => e with { Givre = v });
			Uniforme(m, "m_neige", ref _meteo, _meteo.Neige, cible.Neige, a, (e, v) => e with { Neige = v });
			Uniforme(m, "m_brume_chaude", ref _meteo, _meteo.BrumeChaude, cible.BrumeChaude, a, (e, v) => e with { BrumeChaude = v });
			Uniforme(m, "m_brume_froide", ref _meteo, _meteo.BrumeFroide, cible.BrumeFroide, a, (e, v) => e with { BrumeFroide = v });
		}

		private static void Uniforme(ShaderMaterial m, string nom, ref EffetLisiere e, float actuel, float cible,
			float a, System.Func<EffetLisiere, float, EffetLisiere> poser)
		{
			if (actuel == cible) return;
			float v = Mathf.Abs(cible - actuel) < MeteoEps ? cible : Mathf.Lerp(actuel, cible, a);
			e = poser(e, v);
			m.SetShaderParameter(nom, v);
		}
	}
}
