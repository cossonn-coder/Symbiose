// SYMBIOSE — decor_indexe.gdshader (sprint CASSÉ À L'ÉCRAN ⑥ — lisière : dialecte 2, soleil, vent)
// Shader UNIQUE du décor de lisière (DecorLayer + sa couche « devant »). Trois rôles :
//  1. LECTURE de la palette indexée (même encodage que palette_indexee.gdshader, cf.
//     visuals/PaletteIndexee.cs) : le texel porte n° de palette + ton + orientation de
//     face, le soleil réel monte/descend le ton → l'éclat suit le soleil, 0 recuisson.
//  2. GRAINS procéduraux du DIALECTE 2 (Chrono Trigger forêt) sur les aplats, calés au
//     PIXEL INTERNE du palier (« même recette, plus de motifs en zoomant ») :
//       orientation 9  = TISSAGE en chevrons 2×3 px (sol, couvert, plateau) ;
//       orientation 10 = ROCHE en blocs 8×4 px à joints (face de falaise) — la face
//                        réelle vient de la couleur de sommet (canal B), donc s'éclaire
//                        au soleil comme une pièce ;
//       orientation 11 / 12 = ÉCORCE, flanc gauche / droit d'un tronc : stries
//                        verticales au hash, puis éclairée comme une face 4 / 0.
//  3. VENT : déformation des sommets (aucun redessin CPU), même onde que les plantes
//     (visuals/WindWave.cs PoseFor) : front qui avance dans le sens du vent, risées,
//     balancement propre ; amplitude par sommet (canal G, px canvas) posée à la
//     construction (houppiers > sous-bois > roseaux ; roche = 0), phase au hash (B).
//
// COULEUR DE SOMMET (posée par DecorLayer.Indexe.cs) — ce n'est plus une couleur :
//   R = valeur (plan du rideau, 1 devant → plus sombre au fond)   G = amplitude du vent
//   B = phase au hash (ou orientation de la face pour la roche)  A = alpha (touche H)
//
// 📖 Pédagogie : c'est la même astuce qu'un registre de configuration multiplexé en
// embarqué — 4 octets par sommet, dont le SENS est fixé par un contrat (en-tête), pas
// par leur nom (« color »). Le GPU s'en moque : ce sont 4 nombres interpolés.

shader_type canvas_item;

uniform sampler2D lut : filter_nearest;
uniform vec2 soleil = vec2(0.0, -1.0);   // direction ÉCRAN vers le soleil (normalisée)
uniform float zoom = 1.0;                // palier affiché : 1 px interne = 1/zoom px canvas
// --- vent (posés chaque image par DecorLayer.Vent.cs ; force 0 = immobile) ---
uniform float vent_force = 0.0;
uniform vec2 vent_dir = vec2(1.0, 0.0);  // direction ÉCRAN aval (normalisée)
uniform vec2 onde_k = vec2(0.0);         // cycles par px canvas (projection inverse incluse)
uniform float onde_c = 0.0;              // terme constant (origine du monde)
uniform float onde_f = 0.2;              // fréquence × échelle de force (Hz)
uniform float temps = 0.0;               // WindWave.Temps (s)
uniform vec4 risees = vec4(1.0);         // risées normées (cycle n → risees[n mod 4])

const float AMP_MAX = 32.0;              // px canvas pour G = 1
const float SEUIL = 0.3;
const float SEUIL_ECLAT = 0.8;
const int PALETTES_PAR_LIGNE = 64;
const int TEXELS_PAR_PALETTE = 8;

varying vec4 v_mod;
varying vec2 v_pos;

// Front asymétrique de WindWave.Envelope (montée 12 %, retour jusqu'à 65 %, repos).
float enveloppe(float u) {
	if (u < 0.12) { float x = u / 0.12; return x * x * (3.0 - 2.0 * x); }
	if (u < 0.65) { float x = (0.65 - u) / 0.53; return x * x; }
	return 0.0;
}

float risee(float n) {
	int i = int(mod(n, 4.0));
	return i == 0 ? risees.x : (i == 1 ? risees.y : (i == 2 ? risees.z : risees.w));
}

void vertex() {
	v_mod = COLOR;
	float amp = COLOR.g * AMP_MAX;
	if (vent_force > 0.0 && amp > 0.0) {
		float ph = COLOR.b;
		float f = vent_force;
		float cyc = onde_f * temps - (dot(VERTEX, onde_k) + onde_c) - ph * 0.15;
		float n = floor(cyc);
		float fond = 0.6 * min(f, 1.2);
		float sway = 0.08 * f * sin(2.6 * (0.8 + 0.4 * ph) * temps + ph * 6.2831853);
		float flex = clamp(f * (fond + 0.8 * enveloppe(cyc - n) * risee(n)) + sway, 0.0, 1.0);
		// Calé au pixel INTERNE : la pièce glisse d'un nombre entier de px (Nearest net).
		VERTEX += round(vent_dir * amp * flex * zoom) / zoom;
	}
	v_pos = VERTEX;   // après le vent : le grain d'un houppier suit le houppier
}

uint hache(int x, int y) {
	uint h = uint(x) * 0x9e3779b1u ^ uint(y) * 0x85ebca77u;
	h ^= h >> 15u; h *= 0x2c1b3c6du; h ^= h >> 12u;
	return h;
}

// TISSAGE en chevrons : cellules de 2 px de large × 3 px de haut, décalées d'1 px par
// colonne (diagonale), sens inversé toutes les 3 colonnes (chevron). Dans une cellule :
// rang haut éclairé (+1, une cellule sur deux), rang bas dans l'ombre (−1) ; ~1 cellule
// sur 8 creusée (−1 de plus) = les « tuiles retirées » du brief, au hash.
int tissage(ivec2 ip) {
	int cx = ip.x >> 1;
	int sens = (int(floor(float(cx) / 3.0)) & 1) == 0 ? 1 : -1;
	int y = ip.y + sens * cx;
	int cy = int(floor(float(y) / 3.0));
	int ly = y - 3 * cy;
	uint h = hache(cx, cy);
	int d = ly == 2 ? -1 : (ly == 0 && (h & 1u) == 0u ? 1 : 0);
	if ((h >> 4u & 7u) == 0u) d -= 1;
	return d;
}

// ROCHE : blocs 8×4 px en appareil (rang sur deux décalé de 4), joint = −1 (bas et
// gauche du bloc), arête haute +1, ~1 bloc sur 4 plus sombre, 1 sur 8 plus clair.
int roche(ivec2 ip) {
	int row = ip.y >> 2;
	int x = ip.x + ((row & 1) << 2);
	int col = x >> 3;
	int lx = x - (col << 3), ly = ip.y - (row << 2);
	if (ly == 3 || lx == 0) return -1;
	uint h = hache(col, row);
	int d = ly == 0 ? 1 : 0;
	if ((h & 3u) == 0u) d -= 1; else if ((h >> 2u & 7u) == 0u) d += 1;
	return d;
}

// ÉCORCE : stries verticales d'1 px (une colonne sur 4 creusée, au hash de la colonne,
// rompues tous les 3 à 6 px) — le fût ne se lit plus comme un aplat.
int ecorce(ivec2 ip) {
	uint h = hache(ip.x, ip.y / 5);
	return (h & 3u) == 0u ? -1 : ((h >> 2u & 7u) == 0u ? 1 : 0);
}

void fragment() {
	// texelFetch (accès tableau, sans filtrage) : un code est un ENTIER, un texel
	// voisin mêlé par le filtrage le rendrait faux (n° de palette, ton décalés).
	vec4 t = texelFetch(TEXTURE, ivec2(floor(UV * vec2(textureSize(TEXTURE, 0)))), 0);
	if (t.a < 0.5) {
		COLOR = vec4(0.0);
	} else {
		ivec3 o = ivec3(round(t.rgb * 255.0));
		if (o.b < 128) {
			// Filet : texel littéral (aucun aujourd'hui) → tel quel.
			COLOR = vec4(t.rgb * v_mod.r, v_mod.a);
		} else {
			int id = o.r + 256 * o.g;
			int ton = (o.b >> 4) & 7;
			int orient = o.b & 15;
			ivec2 ip = ivec2(floor(v_pos * zoom));
			if (orient == 9) {
				ton += tissage(ip);
			} else if (orient == 10) {
				ton += roche(ip);
				orient = int(v_mod.b * 16.0);   // face réelle (0..7) ou 8 = plat
			} else if (orient == 11 || orient == 12) {
				ton += ecorce(ip);
				orient = orient == 11 ? 4 : 0;
			}
			if (orient < 8) {
				float a = float(orient) * 0.78539816;
				float d = dot(vec2(cos(a), sin(a)), soleil);
				ton += d > SEUIL_ECLAT ? 2 : (d > SEUIL ? 1 : (d < -SEUIL ? -1 : 0));
			}
			ton = clamp(ton, 0, 4);
			ivec2 px = ivec2((id % PALETTES_PAR_LIGNE) * TEXELS_PAR_PALETTE + ton, id / PALETTES_PAR_LIGNE);
			COLOR = vec4(texelFetch(lut, px, 0).rgb * v_mod.r, v_mod.a);
		}
	}
}
