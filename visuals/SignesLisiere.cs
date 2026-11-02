// SYMBIOSE — SignesLisiere.cs (AUTOMNE VISIBLE ⑥ — ce que le temps fait à la lisière)
// La TABLE libellé → effet : état météo du snapshot (`weather.kind`) et signes annoncés
// du bloc `ciel`. Aucune écologie ici : la vue traduit ce que le moteur a émis, et un
// libellé absent de la table ne fait rien. Un signe non annoncé (`signed` faux) ne se
// montre pas : les événements imprévisibles le restent (conception §3.5).
//
// 📖 Pédagogie : c'est une table de décodage, comme une table de codes d'erreur en
// embarqué. Ajouter un signe = ajouter une ligne, sans toucher au shader.

using System.Collections.Generic;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	/// <summary>Effets macro sur la lisière, chacun dans [0,1].</summary>
	internal readonly record struct EffetLisiere(
		float Seche = 0f, float Humide = 0f, float Givre = 0f, float Neige = 0f,
		float BrumeChaude = 0f, float BrumeFroide = 0f)
	{
		public EffetLisiere Fois(float k) =>
			new(Seche * k, Humide * k, Givre * k, Neige * k, BrumeChaude * k, BrumeFroide * k);

		public EffetLisiere Max(EffetLisiere o) => new(
			Mathf.Max(Seche, o.Seche), Mathf.Max(Humide, o.Humide), Mathf.Max(Givre, o.Givre),
			Mathf.Max(Neige, o.Neige), Mathf.Max(BrumeChaude, o.BrumeChaude), Mathf.Max(BrumeFroide, o.BrumeFroide));
	}

	internal static class SignesLisiere
	{
		// Mêmes libellés que les événements de sim/weather.py.
		private static readonly Dictionary<string, EffetLisiere> Etats = new()
		{
			["Canicule"] = new(Seche: 1f, BrumeChaude: 1f),
			["Sécheresse"] = new(Seche: 0.9f, BrumeChaude: 0.4f),
			["Gelée tardive"] = new(Givre: 1f, BrumeFroide: 1f),
			["Pluie prolongée"] = new(Humide: 1f),
			["Neige"] = new(Neige: 0.5f),   // le manteau moteur prend le relais (SetManteau)
		};

		// Mêmes libellés que SIGN_TABLE de sim/weather.py. Un préavis reste discret.
		private static readonly Dictionary<string, EffetLisiere> Signes = new()
		{
			["ciel blanc laiteux"] = new(BrumeChaude: 0.4f),
			["sol qui craquelle"] = new(Seche: 0.25f),
			["feuilles qui se recroquevillent"] = new(Seche: 0.15f),
			["brume rasante au petit matin"] = new(BrumeFroide: 0.6f),
			["ciel bas et gris constant"] = new(Humide: 0.25f),
		};

		// Intensité d'un événement (hash_gauss, en σ) → force à l'écran.
		private const float ForceMin = 0.6f;
		// Un signe à 2 semaines pèse moins qu'un signe à 1 semaine.
		private const float SigneLointain = 0.6f;

		/// <summary>Effet de l'état météo (`weather.kind`, `weather.intensity`).</summary>
		public static EffetLisiere DeEtat(string kind, float intensite) =>
			kind != null && Etats.TryGetValue(kind, out EffetLisiere e)
				? e.Fois(Mathf.Lerp(ForceMin, 1f, Mathf.Clamp(intensite, 0f, 1f)))
				: default;

		/// <summary>Effet des signes annoncés du bloc `ciel`.</summary>
		public static EffetLisiere DeCiel(GDict ciel)
		{
			EffetLisiere total = default;
			if (ciel == null || !ciel.ContainsKey("signes")) return total;
			foreach (var v in ciel["signes"].AsGodotArray())
			{
				var ev = v.AsGodotDictionary();
				if (!ev.ContainsKey("signed") || !ev["signed"].AsBool()) continue;
				float k = ev.ContainsKey("in_weeks") && ev["in_weeks"].AsInt32() > 1 ? SigneLointain : 1f;
				foreach (var libelle in ev["signs"].AsGodotArray())
					if (Signes.TryGetValue(libelle.AsString(), out EffetLisiere e))
						total = total.Max(e.Fois(k));
			}
			return total;
		}
	}
}
