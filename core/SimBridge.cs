// SYMBIOSE — SimBridge.cs
// Pont vivant vers le moteur Python (sprint Intégration, tranche 1 — Option B :
// Python = moteur source de vérité, Godot = vue). Lance data/code/tools/
// sim_server.py en SOUS-PROCESS et lui parle par les pipes stdin/stdout.
//
// 📖 Pédagogie — pourquoi un sous-process et pas un portage :
// c'est un UART logiciel. L'OS fournit deux tuyaux fiables et ordonnés entre
// Godot et Python (comme une liaison série carte-mère ↔ microcontrôleur).
// Framing par délimiteur : 1 ligne = 1 message JSON complet. Maître/esclave
// strict : Godot (maître) écrit une commande, lit LA réponse, continue —
// protocole requête/réponse synchrone, comme SPI. Python ne parle jamais
// spontanément → pas de concurrence, déterminisme préservé.
//
// Choix techniques (kickoff 01_pont_minimal.md) :
//  - System.Diagnostics.Process et PAS OS.Execute : OS.Execute est BLOQUANT
//    (lance, attend la fin, rend tout stdout d'un coup) — impossible de
//    dialoguer. Process + RedirectStandardInput/Output donne les deux pipes.
//  - stderr NON redirigé : il file directement dans la console Godot → les
//    tracebacks Python s'affichent là où Nico regarde déjà. (Le rediriger sans
//    le lire risquerait en plus de bloquer Python sur un buffer plein.)
//  - API SYNCHRONE pour cette tranche (Init/StepWeek bloquent quelques ms) :
//    un thread/await viendra quand l'UI devra rester fluide pendant la saison.
//  - Json natif de Godot (Json.ParseString/Stringify), cohérent avec
//    PlantStructure.cs : Variant/Dictionary manipulés nativement, zéro stack
//    de sérialisation .NET ajoutée.
//  - Chemin (tranche 7) : DEUX modes, résolus dans Start(). Mode DISTRIBUÉ =
//    binaire gelé PyInstaller `sim_server[.exe]` posé À CÔTÉ de l'exécutable
//    Godot (il ne peut pas vivre dans le .pck : un exécutable ne se lance pas
//    depuis une archive). Mode DEV (repli) = python3 + script sous res://,
//    inchangé — F5 dans l'éditeur marche toujours sans binaire. La console
//    affiche le mode choisi (témoin).
//  - Encodage des pipes : UTF-8 SANS BOM explicite des deux côtés C#. Sous
//    Windows, .NET prendrait sinon la codepage console (cp1252…) ; et un BOM
//    en tête de flux casserait le premier json.loads côté Python. Le protocole
//    est de toute façon ASCII par construction (json.dumps ensure_ascii côté
//    serveur, verbes sans accents) — ceinture et bretelles.

using Godot;
using System.Diagnostics;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public sealed class SimBridge : System.IDisposable
	{
		// Le serveur s'importe depuis data/code/ (imports absolus du moteur) →
		// on lance python3 AVEC ce répertoire courant.
		public const string ServerScript = "res://data/code/tools/sim_server.py";
		public const string CodeDir = "res://data/code";

		private Process _proc;

		public bool IsAlive => _proc != null && !_proc.HasExited;

		// -------------------------------------------------------------------
		// CYCLE DE VIE DU SOUS-PROCESS
		// -------------------------------------------------------------------

		public bool Start()
		{
			// MODE DISTRIBUÉ (tranche 7) : binaire gelé à côté de l'exécutable
			// Godot. En éditeur, GetExecutablePath() pointe l'éditeur lui-même
			// → pas de binaire à côté → on tombe naturellement sur le repli dev.
			string exeDir = System.IO.Path.GetDirectoryName(OS.GetExecutablePath());
			string binName = OS.GetName() == "Windows" ? "sim_server.exe" : "sim_server";
			string binPath = System.IO.Path.Combine(exeDir, binName);
			if (System.IO.File.Exists(binPath) && TryLaunch(binPath, "", exeDir))
			{
				GD.Print($"[SimBridge] Mode BINAIRE — moteur gelé {binPath} (pid {_proc.Id}).");
				return true;
			}

			// MODE DEV (repli, inchangé) : python3 + script sous res://.
			// GlobalizePath : res://… → chemin absolu disque (l'OS ne connaît
			// pas res://). Ne marche qu'en éditeur/dev. Sous Windows dev,
			// l'interpréteur s'appelle souvent "python" — on tente les deux.
			string script = ProjectSettings.GlobalizePath(ServerScript);
			string cwd = ProjectSettings.GlobalizePath(CodeDir);
			foreach (string python in new[] { "python3", "python" })
			{
				if (TryLaunch(python, $"\"{script}\"", cwd))
				{
					GD.Print($"[SimBridge] Mode DEV — {python} + sim_server.py (pid {_proc.Id}).");
					return true;
				}
			}

			GD.PrintErr("[SimBridge] Aucun moteur lançable : ni binaire gelé "
				+ $"({binPath}), ni python3/python + script.");
			return false;
		}

		private bool TryLaunch(string fileName, string arguments, string cwd)
		{
			var psi = new ProcessStartInfo
			{
				FileName = fileName,
				Arguments = arguments,
				WorkingDirectory = cwd,
				UseShellExecute = false,         // requis pour rediriger les pipes
				RedirectStandardInput = true,    // Godot → Python
				RedirectStandardOutput = true,   // Python → Godot
				// stderr volontairement NON redirigé (cf. en-tête).
				// Sous Windows, une app GUI qui lance une app console ouvre
				// sinon une fenêtre cmd noire à côté du jeu (console parasite).
				// Le serveur reste une app console (il lui faut ses stdio) —
				// c'est au PARENT de ne pas lui créer de fenêtre.
				CreateNoWindow = true,
				// UTF-8 sans BOM (cf. en-tête — codepage Windows, BOM fatal).
				StandardInputEncoding = new System.Text.UTF8Encoding(false),
				StandardOutputEncoding = new System.Text.UTF8Encoding(false),
			};

			try
			{
				_proc = Process.Start(psi);
				return true;
			}
			catch (System.Exception e)
			{
				GD.Print($"[SimBridge] {fileName} : lancement impossible ({e.Message}).");
				_proc = null;
				return false;
			}
		}

		public void Quit()
		{
			if (!IsAlive) return;
			Request(new GDict { ["cmd"] = "quit" });
			_proc.WaitForExit(2000);             // EOF/quit → le serveur sort seul
			Dispose();
		}

		public void Dispose()
		{
			if (_proc == null) return;
			if (!_proc.HasExited) _proc.Kill();  // ceinture : jamais de Python zombie
			_proc.Dispose();
			_proc = null;
		}

		// -------------------------------------------------------------------
		// PROTOCOLE v0 — une commande = une réponse (cf. sim_server.py)
		// -------------------------------------------------------------------

		/// <summary>init(seed) → partie STATIQUE du monde (tuiles, maison), ou null.</summary>
		public GDict Init(int seed, string config = "smoke")
		{
			var resp = Request(new GDict { ["cmd"] = "init", ["seed"] = seed, ["config"] = config });
			return resp?["world"].AsGodotDictionary();
		}

		/// <summary>Avance la simulation d'une semaine → snapshot, ou null.</summary>
		public GDict StepWeek()
		{
			var resp = Request(new GDict { ["cmd"] = "step_week" });
			return resp?["snapshot"].AsGodotDictionary();
		}

		/// <summary>Relit l'état courant sans avancer → snapshot, ou null.</summary>
		public GDict GetSnapshot()
		{
			var resp = Request(new GDict { ["cmd"] = "snapshot" });
			return resp?["snapshot"].AsGodotDictionary();
		}

		/// <summary>
		/// Geste joueur (protocole v1, tranche 4) : verbe + cible + params.
		/// Renvoie la réponse COMPLÈTE (`result` = ACK/NAK métier + Vigueur,
		/// `snapshot` = état frais joint) — c'est le seul appel où l'appelant a
		/// besoin des deux. Un refus métier (Vigueur insuffisante, cible
		/// introuvable) arrive en `ok:true` + `result.applied=false` : Python
		/// possède les RÈGLES, la vue ne pré-valide rien.
		/// </summary>
		public GDict Action(string verb, GDict target = null, GDict prms = null)
		{
			var msg = new GDict { ["cmd"] = "action", ["verb"] = verb };
			if (target != null) msg["target"] = target;
			if (prms != null) msg["params"] = prms;
			return Request(msg);
		}

		/// <summary>
		/// Mode debug champs écologiques (t6·C) : sans argument → le REGISTRE
		/// (`fields` = liste de noms) ; avec un nom → les grilles par tuile
		/// (`tiles` = {id: {rows, cols, values row-major}}). L'appelant
		/// distingue les deux par la clé présente. Champ inconnu → null
		/// (erreur loggée par Request, le serveur survit).
		/// </summary>
		public GDict Fields(string field = null)
		{
			var msg = new GDict { ["cmd"] = "fields" };
			if (field != null) msg["field"] = field;
			return Request(msg);
		}

		/// <summary>
		/// Liste des bancs d'essai montables (`init config="<nom>"`), DEMANDÉE au
		/// serveur (commande `list_bancs`, pont 0.5.4) : la source reste le registre
		/// Python `BANCS` — le C# ne duplique pas les noms (un menu périmé = le piège
		/// D47). Appelable après Start() SANS Init (lecture du registre, pas du
		/// moteur). Renvoie [] si le serveur ne répond pas (vieux binaire gelé
		/// pré-0.5.4) → le sélecteur retombe sur full/smoke.
		/// </summary>
		public string[] ListBancs()
		{
			var resp = Request(new GDict { ["cmd"] = "list_bancs" });
			if (resp == null) return System.Array.Empty<string>();
			var arr = resp["bancs"].AsGodotArray();
			var noms = new string[arr.Count];
			for (int i = 0; i < arr.Count; i++) noms[i] = arr[i].AsString();
			return noms;
		}

		/// <summary>
		/// Cœur du pont : écrit 1 ligne JSON, lit 1 ligne JSON (bloquant).
		/// Retourne le message si ok:true, sinon null (+ erreur en console).
		/// </summary>
		private GDict Request(GDict msg)
		{
			if (!IsAlive)
			{
				GD.PrintErr("[SimBridge] Requête sur un moteur non démarré/mort.");
				return null;
			}
			_proc.StandardInput.WriteLine(Json.Stringify(msg));
			_proc.StandardInput.Flush();         // symétrique du flush=True Python

			string line = _proc.StandardOutput.ReadLine();
			if (line == null)                    // EOF = le serveur est mort
			{
				GD.PrintErr("[SimBridge] Le moteur Python s'est arrêté (EOF).");
				return null;
			}

			Variant parsed = Json.ParseString(line);
			if (parsed.VariantType != Variant.Type.Dictionary)
			{
				GD.PrintErr($"[SimBridge] Réponse non-JSON : {line}");
				return null;
			}
			var resp = parsed.AsGodotDictionary();
			if (!resp["ok"].AsBool())
			{
				GD.PrintErr($"[SimBridge] Erreur moteur : {resp["error"].AsString()}");
				return null;
			}
			return resp;
		}

		// -------------------------------------------------------------------
		// SMOKE TEST (preuve visible de la tranche 1 — appelé depuis TileGrid)
		// Init → StepWeek ×4 → GetSnapshot, résumé en console. Pas de rendu :
		// le tube d'abord (le monde dessiné = tranche 2).
		// -------------------------------------------------------------------

		public static void SmokeTest()
		{
			GD.Print("[SimBridge] — smoke test du pont Python —");
			using var bridge = new SimBridge();
			if (!bridge.Start()) return;

			var world = bridge.Init(seed: 42);
			if (world == null) { bridge.Quit(); return; }
			GD.Print($"[SimBridge] init ok : {world["tiles"].AsGodotArray().Count} tuiles + maison.");

			GDict snap = null;
			for (int i = 0; i < 4; i++)
				snap = bridge.StepWeek();
			if (snap == null) { bridge.Quit(); return; }

			var plants = snap["plants"].AsGodotArray();
			GD.Print($"[SimBridge] semaine {snap["week"].AsInt32()} "
					 + $"(an {snap["year"].AsInt32()}, {snap["season"].AsString()}) : "
					 + $"{plants.Count} plantes vivantes.");
			foreach (var pv in plants)
			{
				var p = pv.AsGodotDictionary();
				GD.Print($"    {p["tile"].AsString()} {p["name"].AsString(),-12} "
						 + $"stade={p["stage_name"].AsString()} "
						 + $"h={p["height_cm"].AsDouble():F1}cm "
						 + $"segments={p["segments"].AsGodotArray().Count}");
			}
			bridge.Quit();
			GD.Print("[SimBridge] — smoke test terminé, moteur arrêté proprement —");
		}
	}
}
