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
//  - Chemin : python3 + script sous res:// — le binaire gelé (PyInstaller,
//    tranche 6) remplacera ce couple ICI, un seul point à changer.

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
			// GlobalizePath : res://… → chemin absolu disque (l'OS ne connaît
			// pas res://). Ne marche qu'en éditeur/dev — l'export PCK packagera
			// le binaire gelé autrement (tranche 6).
			string script = ProjectSettings.GlobalizePath(ServerScript);
			string cwd = ProjectSettings.GlobalizePath(CodeDir);

			var psi = new ProcessStartInfo
			{
				FileName = "python3",            // Linux/macOS ; Windows : "python" (tranche 6)
				Arguments = $"\"{script}\"",
				WorkingDirectory = cwd,
				UseShellExecute = false,         // requis pour rediriger les pipes
				RedirectStandardInput = true,    // Godot → Python
				RedirectStandardOutput = true,   // Python → Godot
				// stderr volontairement NON redirigé (cf. en-tête).
			};

			try
			{
				_proc = Process.Start(psi);
			}
			catch (System.Exception e)
			{
				GD.PrintErr($"[SimBridge] Échec du lancement de python3 : {e.Message}");
				_proc = null;
				return false;
			}
			GD.Print($"[SimBridge] Moteur Python lancé (pid {_proc.Id}).");
			return true;
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
