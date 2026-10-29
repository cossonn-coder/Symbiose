// SYMBIOSE — palette_indexee.gdshader (sprint CASSÉ À L'ÉCRAN ③)
// Shader de LECTURE de la palette indexée (cf. visuals/PaletteIndexee.cs pour
// l'encodage). Chaque pixel de l'image cuite porte un n° de palette, un ton et
// une orientation de face ; on monte/descend le ton selon le soleil, puis on lit
// la couleur dans la LUT. Le modulate du nœud (fondu d'apparition, flash d'action,
// teinte de debug LOD) s'applique PAR-DESSUS, comme avant.
//
// 📖 Pédagogie : texelFetch lit UN texel par coordonnées ENTIÈRES, sans filtrage
// ni normalisation — l'équivalent d'un accès tableau `lut[y][x]` en C.

shader_type canvas_item;

uniform sampler2D lut : filter_nearest;
// Direction ÉCRAN vers le soleil (normalisée), posée par PaletteIndexee.MajSoleil.
uniform vec2 soleil = vec2(0.0, -1.0);

// Seuils du modelé sur cos(face, soleil) : au-delà de 0,3 la face est « au soleil »
// (+1 ton), au-delà de 0,8 franchement en face (+2 = éclat), sous −0,3 à l'ombre.
// Avec 8 orientations à 45°, ~3 directions montent, 1 passe à l'éclat, 3 descendent.
const float SEUIL = 0.3;
const float SEUIL_ECLAT = 0.8;
const int PALETTES_PAR_LIGNE = 64;
const int TEXELS_PAR_PALETTE = 8;

varying vec4 v_mod;

void vertex() {
	// COLOR (sommet) = couleur de dessin × modulate × self_modulate du nœud.
	v_mod = COLOR;
}

void fragment() {
	vec4 t = texture(TEXTURE, UV);
	if (t.a < 0.5) {
		COLOR = vec4(0.0);
	} else {
		ivec3 o = ivec3(round(t.rgb * 255.0));
		int id = o.r + 256 * o.g;
		int ton = (o.b >> 4) & 7;
		int orient = o.b & 15;
		if (orient < 8) {
			float a = float(orient) * 0.78539816;
			float d = dot(vec2(cos(a), sin(a)), soleil);
			ton += d > SEUIL_ECLAT ? 2 : (d > SEUIL ? 1 : (d < -SEUIL ? -1 : 0));
		}
		ton = clamp(ton, 0, 4);
		ivec2 px = ivec2((id % PALETTES_PAR_LIGNE) * TEXELS_PAR_PALETTE + ton, id / PALETTES_PAR_LIGNE);
		COLOR = vec4(texelFetch(lut, px, 0).rgb, 1.0) * v_mod;
	}
}
