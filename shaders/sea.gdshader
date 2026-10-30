shader_type spatial;
// Stylized, cheap sea for the Compatibility renderer: two crossing sine swells,
// depth-free colour banding by wave height, and crest foam.

uniform vec4 deep : source_color = vec4(0.03, 0.20, 0.32, 1.0);
uniform vec4 shallow : source_color = vec4(0.08, 0.42, 0.50, 1.0);
uniform vec4 foam : source_color = vec4(0.85, 0.94, 0.95, 1.0);
uniform float amplitude = 0.18;
uniform float speed = 1.0;

varying float h;

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME * speed;
	h = sin(w.x * 0.45 + t * 1.3) * 0.6 + sin(w.z * 0.7 - t * 0.9 + w.x * 0.2) * 0.4;
	VERTEX.y += h * amplitude;
	float dx = cos(w.x * 0.45 + t * 1.3) * 0.27 + cos(w.z * 0.7 - t * 0.9 + w.x * 0.2) * 0.08;
	float dz = cos(w.z * 0.7 - t * 0.9 + w.x * 0.2) * 0.28;
	NORMAL = normalize(vec3(-dx * amplitude, 1.0, -dz * amplitude));
}

void fragment() {
	float k = smoothstep(-0.8, 0.9, h);
	vec3 col = mix(deep.rgb, shallow.rgb, k);
	col = mix(col, foam.rgb, smoothstep(0.78, 0.98, h) * 0.8);
	ALBEDO = col;
	ROUGHNESS = 0.55;
	SPECULAR = 0.35;
}
