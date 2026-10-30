// SYMBIOSE — eau_mare.gdshader (sprint MARE VIVANTE ② — l'eau de la mare en DA 16 bits)
// Shader de la couche PuddleLayer (UN seul lot, UN seul draw call). Deux familles de
// triangles passent dans le MÊME envoi, distinguées par leur UV :
//   · UV.x < 1  → triangle LITTÉRAL (flaque, voile de tourbe, berge, rive) : la
//                 couleur de sommet est affichée telle quelle (texture blanche 1×1) ;
//   · UV.x ≥ 1  → triangle CODÉ de la MARE : la couleur de sommet n'est PAS une
//                 couleur mais trois paramètres lus du snapshot (interpolés d'un sommet
//                 à l'autre → le marnage est CONTINU, jamais une bascule par plot) :
//       R = lame d'eau / LAME_MAX (bloc `marais` 0.6.2, 5ᵉ champ)
//       G = glace ∈ [0,1]           (6ᵉ champ ; ≥ 0,5 = prise)
//       B = « bord » ∈ [0,1]        (1 aux coins qui touchent la terre, 0 au cœur)
//
// Le shader en tire, pixel par pixel (grille du PIXEL INTERNE, calée au monde) :
//   1. eau profonde / eau peu profonde / vase luisante / vase sèche, mêlées par un
//      tramage Bayer 4×4 (la convention SNES du dégradé : pas de demi-teinte, des
//      pixels purs de la rampe alternés) ;
//   2. le SCINTILLEMENT au repos : des reflets en courts traits (5×2 px internes)
//      placés au hash, qui s'allument et s'éteignent LENTEMENT (TIME, déphasés) ;
//   3. la GLACE : blanc-bleuté tramé, fêlures en diagonale iso, scintillement coupé ;
//      glace partielle = bords gelés d'abord (seuil abaissé par B).
// Les couleurs viennent de RampesDa.Matieres (eau_mare / vase / glace), posées en
// uniforms par PuddleLayer.Eau.cs : une seule source de vérité chromatique.
//
// 📖 Pédagogie : c'est le registre multiplexé du décor (decor_indexe.gdshader) — les
// 4 octets « couleur » d'un sommet ont un SENS fixé par contrat (cet en-tête). Le GPU
// interpole des nombres ; c'est nous qui décidons que ce sont une lame et une glace.

shader_type canvas_item;

uniform float zoom = 1.0;      // palier affiché (1 px interne = 1/zoom_px px canvas)
uniform vec3 eau[6];           // creux → éclat isolé
uniform vec3 vase[4];          // sombre → clair (sèche)
uniform vec3 glace[4];         // ombre → blanc

const float LAME_MAX = 3.0;    // = PuddleLayer.LameMax (HUM_CAP du moteur)
const float VIF = 0.9;         // pulsation du scintillement (rad/s → ~7 s par cycle)

varying vec4 v_mod;
varying vec2 v_pos;
varying float v_code;

void vertex() {
	v_mod = COLOR;
	v_pos = VERTEX;
	v_code = UV.x;
}

uint hache(int x, int y) {
	uint h = uint(x) * 0x9e3779b1u ^ uint(y) * 0x85ebca77u;
	h ^= h >> 15u; h *= 0x2c1b3c6du; h ^= h >> 12u;
	return h;
}

// Seuil de Bayer 4×4 ∈ ]0,1[ : comparer une proportion à ce seuil = tramage ordonné.
float bayer(ivec2 p) {
	int m[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };
	return (float(m[(p.y & 3) * 4 + (p.x & 3)]) + 0.5) / 16.0;
}

// Reflet scintillant : cellules 6×2 px (rangs décalés de 3), 1 sur `rarete` porte un
// trait (rang haut 5 px, rang bas 3 px). Rend 0 (rien), 1 (clair) ou 2 (éclat).
int reflet(ivec2 ip, uint rarete) {
	int row = ip.y >> 1;
	int x = ip.x + (row & 1) * 3;
	int col = int(floor(float(x) / 6.0));
	int lx = x - col * 6, ly = ip.y - row * 2;
	uint h = hache(col, row);
	if (h % rarete != 0u) return 0;
	bool dans = ly == 0 ? (lx >= 0 && lx <= 4) : (lx >= 1 && lx <= 3);
	if (!dans) return 0;
	float s = 0.5 + 0.5 * sin(TIME * VIF + float((h >> 8u) & 255u) * 0.0246);
	if (s > 0.78) return (ly == 0 && lx >= 1 && lx <= 3) ? 2 : 1;
	return s > 0.45 ? 1 : 0;
}

// Fêlure : dans des cellules 16×8 px, 1 sur 3 porte une diagonale iso (pente 1/2).
bool felure(ivec2 ip) {
	int cx = int(floor(float(ip.x) / 16.0)), cy = int(floor(float(ip.y) / 8.0));
	uint h = hache(cx + 7919, cy);
	if (h % 3u != 0u) return false;
	int lx = ip.x - cx * 16, ly = ip.y - cy * 8;
	int sens = (h & 8u) == 0u ? 1 : -1;
	int d = sens > 0 ? lx - 2 * ly : (15 - lx) - 2 * ly;
	return d == int((h >> 4u) & 3u) - 1 && ly >= 1 && ly <= 6;
}

vec3 couleur_glace(ivec2 ip, float b, float g) {
	if (felure(ip)) return glace[0];
	// Glace mince (g proche de la prise) plus grise, épaisse plus blanche ; de
	// larges bandes diagonales (le ciel qui se mire, ~40 px) tramées entre 2 tons
	// cassent l'aplat — immobiles : la glace ne scintille pas.
	float bande = sin(float(ip.x + 2 * ip.y) * 0.075) + 0.5 * sin(float(ip.x - ip.y) * 0.031);
	float t = 1.4 + 0.9 * clamp(g, 0.0, 1.0) + 0.45 * bande;
	int ton = int(floor(t + b - 0.5));
	return glace[clamp(ton, 0, 3)];
}

void fragment() {
	if (v_code >= 1.0) {
		float lame = v_mod.r * LAME_MAX;
		float gl = v_mod.g, bord = v_mod.b;
		float zp = clamp(zoom, 1.0, 4.0);   // grain borné : lisible de ×1 à ×32
		ivec2 ip = ivec2(floor(v_pos * zp));
		float b = bayer(ip);
		float b2 = bayer(ip + ivec2(2, 1));
		vec3 col;
		// 1. Glace : la prise abaisse son seuil près de la rive (bords gelés d'abord).
		if (lame > 0.05 && 2.0 * gl + 0.3 * (b - 0.5) > 1.0 - 0.8 * bord) {
			col = couleur_glace(ip, b2, gl);
		} else {
			// 2. Part d'eau libre : 0 sous 0,03 de lame, 1 au-delà de ~0,5.
			float m = clamp((lame - 0.03) / 0.45, 0.0, 1.0);
			if (b < m) {
				float prof = clamp((lame - 0.1) / 2.2, 0.0, 1.0);
				int ton = clamp(int(floor(mix(2.5, 0.3, prof) + b2 - 0.5)), 0, 2);
				int r = reflet(ip, lame > 0.3 ? 17u : 37u);
				col = r == 2 ? eau[5] : (r == 1 ? eau[4] : eau[ton]);
			} else {
				// 3. Vase : mouillée (sombre, éclats humides) → sèche (claire, grain).
				float hum = clamp(lame / 0.12, 0.0, 1.0);
				int ton = clamp(int(floor(mix(2.6, 1.0, hum) + b2 - 0.5)), 0, 3);
				col = vase[ton];
				if (hum > 0.25 && reflet(ip + ivec2(3, 0), 29u) > 0) col = eau[4];
			}
		}
		COLOR = vec4(col, 1.0);
	}
}
