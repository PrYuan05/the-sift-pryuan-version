#version 330
#extension GL_ARB_separate_shader_objects : require

// Soul Deprivation: every block looks like sculk (伏聆). The depth buffer and the camera (written every frame by
// PostPassMixin into SculkCamera) give the world position of each pixel; the face it lies on is found from the screen
// derivatives, and the sculk pattern is drawn on that face's 16x16 texel grid, so the specks stick to the blocks:
//   near-black navy body, teal mid-tones, a few dark teal dots that breathe and rare bright cyan texels that blink.
// The sky only gets the colour grade. Strength fades the whole effect in / out (SoulDeprivationVision).

#include <minecraft:globals.glsl>

uniform sampler2D InSampler;
uniform sampler2D DepthSampler;

layout(location = 0) in vec2 texCoord;

layout(std140) uniform SamplerInfo {
    vec2 OutSize;
    vec2 InSize;
};

layout(std140) uniform SculkCamera {
    vec4 InvViewProj0;      // columns of inverse(projection * view rotation)
    vec4 InvViewProj1;
    vec4 InvViewProj2;
    vec4 InvViewProj3;
    vec4 CameraStrength;    // xyz = camera position (mod 1024), w = strength 0..1
    vec4 Params;            // x = 1 when depth is 0..1 (else -1..1)
};

layout(location = 0) out vec4 fragColor;

const vec3 DEEP = vec3(0.035, 0.085, 0.105);   // sculk body, dark navy
const vec3 MID = vec3(0.090, 0.330, 0.350);    // teal
const vec3 HIGH = vec3(0.420, 0.850, 0.820);   // light teal (keeps the world readable)
const vec3 SPECK = vec3(0.330, 0.960, 0.910);  // bright cyan texels
const vec3 DOT = vec3(0.060, 0.420, 0.440);    // darker teal texels

float hash(vec3 p) {
    p = fract(p * vec3(0.1031, 0.1030, 0.0973));
    p += dot(p, p.yxz + 33.33);
    return fract((p.x + p.y) * p.z);
}

vec3 grade(vec3 c) {
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    vec3 g = l < 0.45 ? mix(DEEP, MID, l / 0.45) : mix(MID, HIGH, (l - 0.45) / 0.55);
    return g + (c - vec3(l)) * 0.2;
}

void main() {
    float strength = CameraStrength.w;
    vec3 c = texture(InSampler, texCoord).rgb;
    float depth = texture(DepthSampler, texCoord).r;
    vec3 sculk = grade(c);

    if (depth < 0.99999) {
        mat4 invViewProj = mat4(InvViewProj0, InvViewProj1, InvViewProj2, InvViewProj3);
        float ndcZ = Params.x > 0.5 ? depth : depth * 2.0 - 1.0;
        vec4 rel = invViewProj * vec4(texCoord * 2.0 - 1.0, ndcZ, 1.0);
        rel.xyz /= rel.w;
        vec3 world = rel.xyz + CameraStrength.xyz;
        vec3 n = cross(dFdx(world), dFdy(world));
        vec3 an = abs(n);

        // the face's own 2D texel grid (16 per block) + which block layer it is on
        vec2 uv;
        float layer;
        vec3 inside = world - normalize(n + 1e-6) * 0.001;
        if (an.y >= an.x && an.y >= an.z) {
            uv = world.xz; layer = floor(inside.y) * 3.0;
        } else if (an.x >= an.z) {
            uv = world.zy; layer = floor(inside.x) * 3.0 + 1.0;
        } else {
            uv = world.xy; layer = floor(inside.z) * 3.0 + 2.0;
        }
        vec2 texel = floor(uv * 16.0);
        float h = hash(vec3(texel, layer));

        float t = GameTime * 1200.0;                    // GameTime is the fraction of the day -> seconds
        float near = 1.0 - smoothstep(24.0, 56.0, length(rel.xyz));   // far texels would only be noise
        if (h > 0.98) {
            // ~2% of texels: bright cyan, blinking fully on / off, each with its own speed and phase
            float h2 = hash(vec3(texel.yx, layer + 17.0));
            float blink = smoothstep(0.35, 0.95, sin(t * (1.2 + 2.0 * h2) + h2 * 40.0));
            sculk = mix(sculk, SPECK * 1.15, blink * near);
        } else if (h > 0.94) {
            // ~4%: darker teal dots that slowly breathe
            float breathe = 0.5 + 0.5 * sin(t * 0.7 + h * 90.0);
            sculk = mix(sculk, DOT, (0.3 + 0.35 * breathe) * near);
        }
    }

    // darker edges
    vec2 d = (texCoord - 0.5) * vec2(OutSize.x / OutSize.y, 1.0);
    float vig = 1.0 - smoothstep(0.25, 0.95, length(d));
    sculk *= mix(0.7, 1.0, vig);

    fragColor = vec4(mix(c, sculk, strength), 1.0);
}
