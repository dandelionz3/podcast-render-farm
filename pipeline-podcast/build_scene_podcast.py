# build_scene_podcast.py — PODCAST ANIMASI 3D "Masa Depan AI" (FASE 1).
# Builder karakter BARU (bukan copas builder zombie/NEXUS/GTA 6):
#   builder lama: kepala ~40% tinggi, hip_z 0.48*s, sho_z 1.12*s, head_r 0.275*s.
#   NARA (host, 1.62 m): bahu 0.78x builder lama, kepala head_r 0.20 (kecil),
#     mata besar + jarak lebar, rambut panjang bergelombang, blazer krem.
#   BIMO (tamu, 1.85 m): bahu 1.25x builder lama, lengan tebal, kepala 0.25,
#     rambut pendek rapi + jenggot tipis, kemeja lengan panjang.
# Gaya tetap vinyl-toy (konsisten dengan NEXUS) tapi proporsi + muka beda.
# Pose: duduk di kursi podcast, lengan bawah di meja, kaki ditekuk (rig 2 segmen).
# Usage still:
#   blender -b --factory-startup -P build_scene_podcast.py -- <out.png> --mode MODE [--res X Y]
#   MODE: front-nara | front-bimo | compare | twoshot
# Run:
#   blender -b --factory-startup -P build_scene_podcast.py -- out/stills/nara-front.png --mode front-nara --res 540 960
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//podcast_preview.png"
MODE = args[args.index("--mode") + 1] if "--mode" in args else "twoshot"
RES_X, RES_Y = (540, 960)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"
_set = lambda o, a, v: setattr(o, a, v) if hasattr(o, a) else None
_set(scene.eevee, "use_raytracing", False)
_set(scene.eevee, "use_shadows", True)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "8"))
scene.render.use_motion_blur = False

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.06, 0.02, 0.03, 1.0)  # v2: merah-hitam
bg.inputs["Strength"].default_value = 0.6


def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


# --- materials ---
SKIN_NARA = mat("SkinNara", (0.86, 0.68, 0.55), 0.5)
SKIN_BIMO = mat("SkinBimo", (0.72, 0.55, 0.42), 0.5)
HAIR_NARA = mat("HairNara", (0.16, 0.09, 0.05), 0.55)   # cokelat gelap
HAIR_BIMO = mat("HairBimo", (0.07, 0.06, 0.05), 0.6)
BLAZER = mat("BlazerNara", (0.88, 0.82, 0.68), 0.6)     # krem
BLOUSE = mat("BlouseNara", (0.94, 0.93, 0.90), 0.6)
SKIRT = mat("SkirtNara", (0.22, 0.20, 0.24), 0.65)
SHIRT_BIMO = mat("ShirtBimo", (0.16, 0.38, 0.42), 0.6)  # teal gelap, lengan panjang
PANTS_BIMO = mat("PantsBimo", (0.13, 0.14, 0.17), 0.65)
EYE_DARK = mat("EyeDark", (0.05, 0.03, 0.02), 0.2)
EYE_BIMO = mat("EyeBimo", (0.04, 0.04, 0.03), 0.2)
MOUTH_M = mat("MouthM", (0.45, 0.15, 0.18), 0.4)
WOOD = mat("Wood", (0.32, 0.20, 0.11), 0.6)
WOOD_DARK = mat("WoodDark", (0.20, 0.13, 0.08), 0.6)
FLOOR_M = mat("Floor", (0.13, 0.05, 0.06), 0.7)          # v2: lantai merah-hitam
WALL_M = mat("Wall", (0.09, 0.04, 0.05), 0.9)            # v2: dinding merah-hitam
PANEL_M = mat("Panel", (0.30, 0.04, 0.05), 0.95)        # v2: panel akustik merah gelap
PANEL_M2 = mat("Panel2", (0.07, 0.05, 0.06), 0.95)      # v2: panel hampir hitam
CHAIR_M = mat("Chair", (0.12, 0.05, 0.06), 0.6)         # v2: kursi merah-hitam
CARPET_M = mat("Carpet", (0.30, 0.03, 0.04), 0.95)      # v2: karpet merah gelap
METAL = mat("Metal", (0.15, 0.15, 0.16), 0.35, metal=0.8)
MIC_M = mat("Mic", (0.08, 0.08, 0.09), 0.4, metal=0.6)
FOAM_M = mat("MicFoam", (0.05, 0.05, 0.06), 0.9)
POT_M = mat("Pot", (0.55, 0.30, 0.15), 0.7)
LEAF_M = mat("Leaf", (0.12, 0.35, 0.16), 0.7)
MUG_M = mat("Mug", (0.85, 0.55, 0.20), 0.5)
SIGN_M = emissive("SignGlow", (1.0, 0.10, 0.08), 2.2)   # v2: sign merah menyala
SIGN_M2 = emissive("SignGlow2", (1.0, 0.08, 0.08), 1.8)  # v2: bar merah
REDGLOW_M = emissive("RedGlow", (1.0, 0.08, 0.08), 1.6)  # v2: strip cahaya merah
HALO_M = emissive("HaloRed", (0.7, 0.04, 0.04), 0.9)     # v2: halo merah di balik sign
PAPER_M = mat("Paper", (0.92, 0.90, 0.84), 0.7)


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def ball(name, loc, size, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def cylinder(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def text_obj(name, body, loc, size, m, rot):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.extrude = 0.02
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.resolution_u = 16
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(m)
    return t


# ---------- KARAKTER BARU ----------
# Params terukur (vs builder lama s=1: hip 0.48, sho 1.12, sho_x 0.38, head_r 0.275):
#   NARA: tinggi total ~1.62, sho_x 0.27 (=0.78x lama pd s=0.9), head_r 0.20, mata r 0.05 gap +-0.09
#   BIMO: tinggi total ~1.85, sho_x 0.49 (=1.25x lama pd s=1.03), head_r 0.25, mata r 0.05 gap +-0.10
CHARS = {}


def make_character(prefix, P):
    """P: dict proporsi. Karakter BERDIRI di base, menghadap -Y. Kaki & lengan
    2 segmen (paha/betis, lengan atas/bawah) supaya bisa duduk via rig."""
    bx, by, bz = P["base"]
    s = P["s"]
    hip_z, sho_z, sho_x = P["hip_z"], P["sho_z"], P["sho_x"]
    head_z, head_r = P["head_z"], P["head_r"]
    skin, hair_m = P["skin"], P["hair"]
    torso_m, leg_m = P["torso"], P["legs"]

    def Q(x, y, z):
        return (bx + x, by + y, bz + z)

    body, head = [], []
    armU_L, armU_R, armF_L, armF_R = [], [], [], []
    legT_L, legT_R, legS_L, legS_R = [], [], [], []
    # torso: dada + pinggang (Nara: pinggang lebih ramping dari dada)
    body.append(block(f"{prefix}_Torso", Q(0, 0, P["torso_z"]),
                      (P["torso_w"], P["torso_d"], P["torso_h"]), torso_m))
    body.append(block(f"{prefix}_Waist", Q(0, 0, P["waist_z"]),
                      (P["waist_w"], P["torso_d"] * 0.92, P["waist_h"]), P["waist_m"]))
    if P.get("skirt"):
        body.append(block(f"{prefix}_Skirt", Q(0, 0.02, hip_z + 0.02),
                          (P["waist_w"] + 0.06, 0.34, 0.16), SKIRT))
    # bahu: blok trapesium menutup celah leher-dagu di atas torso
    body.append(block(f"{prefix}_Shoulder", Q(0, 0, sho_z - 0.08),
                      (P["torso_w"] + 0.08, P["torso_d"] * 0.9, 0.12), torso_m))
    # kerah / detail dada
    if P.get("collar"):
        body.append(block(f"{prefix}_Collar", Q(0, -0.14, sho_z - 0.02),
                          (0.30 * s, 0.06, 0.10), P["collar_m"]))
    # kaki 2 segmen: paha (hip->knee) + betis+sepatu (knee->ankle)
    knee_z = P["knee_z"]
    for side, sx in (("L", -1), ("R", 1)):
        legT = block(f"{prefix}_Thigh{side}", Q(0.14 * sx * s, 0, (hip_z + knee_z) / 2),
                     (P["thigh_w"], P["thigh_w"] * 1.05, hip_z - knee_z), leg_m)
        (legT_L if side == "L" else legT_R).append(legT)
        # betis dibuat SEPANJANG hip_z (bukan knee_z): saat duduk, lutut ada di
        # ketinggian pinggul, jadi betis harus mencapai lantai dari sana.
        # Saat berdiri, betis menumpang-tindih paha (lebih tipis, tersembunyi).
        shin = block(f"{prefix}_Shin{side}", Q(0.14 * sx * s, 0, hip_z / 2),
                     (P["shin_w"], P["shin_w"] * 1.05, hip_z), leg_m)
        shoe = block(f"{prefix}_Shoe{side}", Q(0.14 * sx * s, -0.05, 0.05),
                     (P["shin_w"] + 0.03, 0.26, 0.09), P["shoe_m"])
        (legS_L if side == "L" else legS_R).extend([shin, shoe])
    # lengan 2 segmen: atas (bahu->siku) + bawah+telapak (siku->tangan)
    elb_z = sho_z - P["upper_len"]
    for side, sx in (("L", -1), ("R", 1)):
        up = block(f"{prefix}_ArmU{side}", Q(sho_x * sx, 0, (sho_z + elb_z) / 2),
                   (P["arm_w"], P["arm_w"] * 1.05, P["upper_len"]), torso_m)
        (armU_L if side == "L" else armU_R).append(up)
        fo = block(f"{prefix}_ArmF{side}", Q(sho_x * sx, 0, elb_z - P["fore_len"] / 2),
                   (P["arm_w"] * 0.9, P["arm_w"] * 0.95, P["fore_len"]), torso_m)
        hand = ball(f"{prefix}_Hand{side}", Q(sho_x * sx, 0, elb_z - P["fore_len"]),
                    (P["arm_w"] * 0.62,) * 3, skin)
        (armF_L if side == "L" else armF_R).extend([fo, hand])
    # kepala + wajah (mata di depan permukaan: y = -head_r*0.92 - 0.01)
    head.append(ball(f"{prefix}_Head", Q(0, 0, head_z),
                     (head_r, head_r * 0.92, head_r * 1.02), skin))
    # leher: tebal + tinggi supaya kepala tidak melayang (torso atas harus bertemu dagu)
    body.append(cylinder(f"{prefix}_Neck", Q(0, 0, head_z - head_r - 0.02),
                         head_r * 0.45, 0.16, skin))
    # pinggul: jembatan torso -> paha (subsurf membuat celah terlihat menganga)
    body.append(block(f"{prefix}_Hips", Q(0, 0, hip_z + 0.02),
                      (P["waist_w"] + 0.04, P["torso_d"] * 0.95, 0.14), P["waist_m"]))
    eye_y = -head_r * 0.92
    for side, sx in (("L", -1), ("R", 1)):
        head.append(ball(f"{prefix}_Eye{side}",
                         Q(P["eye_gap"] * sx, eye_y, head_z + P["eye_dz"]),
                         (P["eye_r"], 0.028, P["eye_r"] * 1.25), P["eye_m"]))
        # alis menempel dahi (y sedikit ke belakang dari mata — dahi melengkung)
        head.append(block(f"{prefix}_Brow{side}",
                          Q(P["eye_gap"] * sx, eye_y + 0.015, head_z + P["brow_dz"]),
                          (P["brow_w"], 0.02, 0.022), hair_m,
                          rot=(0, 0, math.radians(P.get("brow_tilt", -8) * sx))))
    # hidung kecil + mulut (mulut diskala di animate untuk lip-sync)
    head.append(ball(f"{prefix}_Nose", Q(0, -head_r * 0.98, head_z - 0.02),
                     (0.022, 0.02, 0.03), skin))
    mouth = block(f"{prefix}_Mouth", Q(0, -head_r * 0.94, head_z - P["mouth_dz"]),
                  (P["mouth_w"], 0.02, 0.018), MOUTH_M)
    head.append(mouth)
    # rambut
    if P["kind"] == "nara":
        # panjang bergelombang: cap atas + massa belakang + 2 jambul samping
        head.append(ball(f"{prefix}_HairTop", Q(0, 0.05, head_z + head_r * 0.55),
                         (head_r * 1.06, head_r * 1.0, head_r * 0.72), hair_m))
        head.append(ball(f"{prefix}_HairBack", Q(0, 0.10, head_z - head_r * 0.15),
                         (head_r * 1.02, head_r * 0.85, head_r * 1.25), hair_m))
        for side, sx in (("L", -1), ("R", 1)):
            head.append(ball(f"{prefix}_HairSide{side}",
                             Q(0.16 * sx, 0.02, head_z - head_r * 0.55),
                             (0.075, 0.07, 0.22), hair_m))
            head.append(ball(f"{prefix}_HairWave{side}",
                             Q(0.17 * sx, -0.02, head_z - head_r * 1.05),
                             (0.06, 0.055, 0.12), hair_m))
    else:
        # pendek rapi: cap membungkus ubun-ubun (bukan pelat mengambang) + jenggot + kumis
        head.append(ball(f"{prefix}_HairTop", Q(0, 0.02, head_z + head_r * 0.32),
                         (head_r * 1.06, head_r * 1.0, head_r * 0.78), hair_m))
        # jenggot: bola pipih melengkung mengikuti dagu (poles Fase 2 — dulu balok
        # datar seperti pita; bola ini menempel permukaan dagu, menonjol ~0.05)
        head.append(ball(f"{prefix}_Beard", Q(0, -head_r * 0.55, head_z - head_r * 0.80),
                         (head_r * 0.62, 0.055, head_r * 0.42), hair_m))
        head.append(block(f"{prefix}_Moustache", Q(0, -head_r * 0.80, head_z - head_r * 0.38),
                          (head_r * 0.55, 0.04, 0.035), hair_m))
    info = {"base": Vector(P["base"]), "scale": s, "kind": P["kind"],
            "hip_z": hip_z, "sho_z": sho_z, "sho_x": sho_x, "head_z": head_z,
            "head_r": head_r, "knee_z": knee_z, "elb_z": elb_z,
            "head_pivot_z": head_z - head_r - 0.06,
            "body": body, "head": head, "armU_L": armU_L, "armU_R": armU_R,
            "armF_L": armF_L, "armF_R": armF_R,
            "legT_L": legT_L, "legT_R": legT_R, "legS_L": legS_L, "legS_R": legS_R,
            "mouth": mouth, "params": P}
    CHARS[prefix] = info
    return info


NARA_P = {"kind": "nara", "s": 0.90, "base": (0, 0.55, 0),
          "hip_z": 0.42, "sho_z": 1.02, "sho_x": 0.27, "head_z": 1.38, "head_r": 0.20,
          "knee_z": 0.21, "torso_z": 0.80, "torso_w": 0.50, "torso_d": 0.30, "torso_h": 0.62,
          "waist_z": 0.58, "waist_w": 0.38, "waist_h": 0.20, "waist_m": BLOUSE,
          "skin": SKIN_NARA, "hair": HAIR_NARA, "torso": BLAZER, "legs": SKIN_NARA,
          "thigh_w": 0.13, "shin_w": 0.11, "shoe_m": SKIRT,
          "upper_len": 0.30, "fore_len": 0.28, "arm_w": 0.11,
          "eye_gap": 0.09, "eye_r": 0.05, "eye_dz": 0.02, "eye_m": EYE_DARK,
          "brow_dz": 0.11, "brow_w": 0.11, "brow_tilt": -8,
          "mouth_dz": 0.11, "mouth_w": 0.09, "skirt": True, "collar": True, "collar_m": BLOUSE}
BIMO_P = {"kind": "bimo", "s": 1.03, "base": (0, -0.55, 0),
          "hip_z": 0.50, "sho_z": 1.16, "sho_x": 0.49, "head_z": 1.55, "head_r": 0.25,
          "knee_z": 0.25, "torso_z": 0.89, "torso_w": 0.86, "torso_d": 0.42, "torso_h": 0.74,
          "waist_z": 0.64, "waist_w": 0.76, "waist_h": 0.22, "waist_m": SHIRT_BIMO,
          "skin": SKIN_BIMO, "hair": HAIR_BIMO, "torso": SHIRT_BIMO, "legs": PANTS_BIMO,
          "thigh_w": 0.22, "shin_w": 0.19, "shoe_m": METAL,
          "upper_len": 0.34, "fore_len": 0.32, "arm_w": 0.20,
          "eye_gap": 0.10, "eye_r": 0.05, "eye_dz": 0.03, "eye_m": EYE_BIMO,
          "brow_dz": 0.10, "brow_w": 0.13, "brow_tilt": 0,
          "mouth_dz": 0.13, "mouth_w": 0.11, "skirt": False, "collar": True, "collar_m": SHIRT_BIMO}
make_character("NARA", NARA_P)
make_character("BIMO", BIMO_P)

# ---------- rig (empty pivot, pola NEXUS) ----------
RIGS = {}


def empty(name, loc, parent=None):
    """loc SELALU dalam ruang parent (root: world; anak rig: relatif parent).
    Jangan campur koordinat world dengan lokasi parent."""
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
    e.location = loc
    bpy.context.view_layer.update()
    return e


def attach(obj, rig):
    m = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = m


def rig_character(prefix, info):
    base = info["base"]
    root = empty(f"{prefix}_RootRig", (base.x, base.y, base.z))
    head_rig = empty(f"{prefix}_HeadRig", (0, 0, info["head_pivot_z"]), root)
    arm_r = empty(f"{prefix}_ArmRigR", (info["sho_x"], 0, info["sho_z"]), root)
    arm_l = empty(f"{prefix}_ArmRigL", (-info["sho_x"], 0, info["sho_z"]), root)
    elb_r = empty(f"{prefix}_ElbRigR", (0, 0, info["elb_z"] - info["sho_z"]), arm_r)
    elb_l = empty(f"{prefix}_ElbRigL", (0, 0, info["elb_z"] - info["sho_z"]), arm_l)
    leg_r = empty(f"{prefix}_LegRigR", (0.14 * info["scale"], 0, info["hip_z"]), root)
    leg_l = empty(f"{prefix}_LegRigL", (-0.14 * info["scale"], 0, info["hip_z"]), root)
    knee_r = empty(f"{prefix}_KneeRigR", (0, 0, info["knee_z"] - info["hip_z"]), leg_r)
    knee_l = empty(f"{prefix}_KneeRigL", (0, 0, info["knee_z"] - info["hip_z"]), leg_l)
    for o in info["body"]:
        attach(o, root)
    for o in info["head"]:
        attach(o, head_rig)
    for o in info["armU_R"]:
        attach(o, arm_r)
    for o in info["armU_L"]:
        attach(o, arm_l)
    for o in info["armF_R"]:
        attach(o, elb_r)
    for o in info["armF_L"]:
        attach(o, elb_l)
    for o in info["legT_R"]:
        attach(o, leg_r)
    for o in info["legT_L"]:
        attach(o, leg_l)
    for o in info["legS_R"]:
        attach(o, knee_r)
    for o in info["legS_L"]:
        attach(o, knee_l)
    RIGS[prefix] = {"root": root, "head": head_rig, "armR": arm_r, "armL": arm_l,
                    "elbR": elb_r, "elbL": elb_l, "legR": leg_r, "legL": leg_l,
                    "kneeR": knee_r, "kneeL": knee_l, "info": info}
    return RIGS[prefix]


rig_character("NARA", CHARS["NARA"])
rig_character("BIMO", CHARS["BIMO"])
# Bimo menghadap +Y (ke Nara): putar root 180 derajat
RIGS["BIMO"]["root"].rotation_euler = (0, 0, math.radians(180))


def pose_seated(prefix, facing):
    """Pose duduk — sudut dalam RUANG LOKAL karakter (keduanya dibangun
    menghadap -Y lokal; rotasi root 180 Bimo yang menangani arah dunia).
    Jadi sudutnya SAMA untuk Nara & Bimo: paha ke depan, betis ke bawah,
    lengan bawah ke depan di meja."""
    R = RIGS[prefix]
    R["legR"].rotation_euler = (-math.pi / 2, 0, 0)
    R["legL"].rotation_euler = (-math.pi / 2, 0, 0)
    R["kneeR"].rotation_euler = (math.pi / 2, 0, 0)
    R["kneeL"].rotation_euler = (math.pi / 2, 0, 0)
    R["elbR"].rotation_euler = (-math.pi / 2 * 0.9, 0, 0)
    R["elbL"].rotation_euler = (-math.pi / 2 * 0.9, 0, 0)
    # lengan sedikit ke dalam (ke arah meja tengah)
    R["armR"].rotation_euler = (0, 0.12, 0)
    R["armL"].rotation_euler = (0, -0.12, 0)


STUDIO_OBJS = []


def reg(o):
    STUDIO_OBJS.append(o)
    return o


# ---------- STUDIO ----------
reg(block("Floor", (0, 0, -0.05), (7, 6, 0.1), FLOOR_M))
# v2: karpet merah gelap di bawah meja (tipis — sepatu karakter tetap di atasnya)
reg(block("Carpet", (0.6, 0, 0.006), (2.6, 1.7, 0.012), CARPET_M))
# backdrop wall di -X (latar twoshot dari kamera +X) + panel akustik — v2 LEBIH TINGGI (4.4 m)
reg(block("Backdrop", (-2.2, 0, 2.2), (0.15, 5.6, 4.4), WALL_M))
for i, py in enumerate((-1.8, -0.9, 0.0, 0.9, 1.8)):
    reg(block(f"Panel{i}", (-2.11, py, 2.0), (0.06, 0.80, 3.2),
              PANEL_M if i % 2 == 0 else PANEL_M2))
# dinding samping (belakang Nara / belakang Bimo) — v2 lebih tinggi
reg(block("WallNara", (0, 1.9, 2.2), (5.6, 0.15, 4.4), WALL_M))
reg(block("WallBimo", (0, -1.9, 2.2), (5.6, 0.15, 4.4), WALL_M))
# v2: kolom megah mengapit backdrop + strip cahaya merah di sisinya
for _sy in (-2.5, 2.5):
    reg(block(f"Column{_sy}", (-2.05, _sy, 2.0), (0.22, 0.4, 4.0), PANEL_M2))
    reg(block(f"ColumnGlow{_sy}", (-1.92, _sy, 2.0), (0.04, 0.08, 3.6), REDGLOW_M))
# sign "MASA DEPAN AI" di backdrop (menghadap +X), + garis merah di bawahnya
reg(text_obj("SignTitle", "MASA DEPAN AI", (-2.05, 0, 2.35), 0.34, SIGN_M,
             (math.radians(90), 0, math.radians(90))))
reg(block("SignBar", (-2.08, 0, 2.02), (0.04, 1.7, 0.06), SIGN_M2))
# v2: halo merah di balik sign + bar cahaya vertikal mengapit sign + garis cahaya lantai
reg(cylinder("SignHalo", (-2.09, 0, 2.35), 0.85, 0.03, HALO_M,
             rot=(0, math.radians(90), 0)))
reg(block("LightBarL", (-2.07, -1.15, 2.35), (0.04, 0.07, 1.5), REDGLOW_M))
reg(block("LightBarR", (-2.07, 1.15, 2.35), (0.04, 0.07, 1.5), REDGLOW_M))
reg(block("FloorGlow", (-2.05, 0, 0.12), (0.04, 3.6, 0.05), REDGLOW_M))
# meja bundar kayu di tengah (radius 0.62: tepi tepat di dada pembicara)
reg(cylinder("TableTop", (0, 0, 0.72), 0.62, 0.06, WOOD))
reg(cylinder("TableLeg", (0, 0, 0.36), 0.09, 0.72, WOOD_DARK))
reg(cylinder("TableBase", (0, 0, 0.03), 0.35, 0.06, WOOD_DARK))
# kursi: dudukan TEPAT di bawah pinggul (y = posisi karakter), sandaran di belakang
for cx, cy in ((0, 0.55), (0, -0.55)):
    reg(block(f"ChairSeat{cy}", (cx, cy, 0.40), (0.55, 0.5, 0.08), CHAIR_M))
    reg(block(f"ChairBack{cy}", (cx, cy + (0.28 if cy > 0 else -0.28), 0.85),
              (0.55, 0.08, 0.8), CHAIR_M))
    reg(cylinder(f"ChairPole{cy}", (cx, cy, 0.20), 0.05, 0.40, METAL))
# mic podcast di boom arm (satu per pembicara, di depan mulut)
for prefix, my in (("NARA", 0.55), ("BIMO", -0.55)):
    sgn = 1 if my > 0 else -1
    # mic digeser ke SISI (x) supaya di close-up tidak menutupi muka:
    # kamera closeup Nara dari +X -> mic di x -0.44; Bimo dari -X -> mic di +0.44
    # (poles Fase 2: dulu -0.30 masih menutupi tepi muka Nara; mic juga dikecilkan)
    mx = -0.44 if my > 0 else 0.44
    reg(cylinder(f"{prefix}_BoomBase", (0.40, my - sgn * 0.25, 0.75),
                 0.05, 0.06, METAL))
    reg(cylinder(f"{prefix}_BoomArm", (mx * 0.5, my - sgn * 0.30, 1.05), 0.025, 0.75, METAL,
                 rot=(math.radians(50 * sgn), 0, math.radians(90))))
    reg(cylinder(f"{prefix}_Mic", (mx, my - sgn * 0.22, 1.18), 0.045, 0.13, MIC_M,
                 rot=(math.radians(35 * sgn), 0, 0)))
    reg(ball(f"{prefix}_MicTop", (mx, my - sgn * 0.25, 1.24), (0.05, 0.05, 0.05), FOAM_M))
    reg(cylinder(f"{prefix}_PopFilter", (mx, my - sgn * 0.16, 1.20), 0.075, 0.015, FOAM_M,
                 rot=(math.radians(90), 0, 0)))
# tanaman kecil + mug + kertas di meja
reg(cylinder("Pot", (-0.42, 0.38, 0.80), 0.09, 0.14, POT_M))
for i, (lx, ly, lz) in enumerate(((-0.42, 0.38, 1.05), (-0.49, 0.33, 0.98),
                                  (-0.35, 0.43, 0.98), (-0.42, 0.45, 1.02), (-0.47, 0.43, 1.08))):
    reg(ball(f"Leaf{i}", (lx, ly, lz), (0.05, 0.05, 0.09), LEAF_M))
reg(cylinder("Mug", (0.42, -0.38, 0.79), 0.05, 0.12, MUG_M))
reg(block("Notes", (0.45, 0.35, 0.76), (0.28, 0.20, 0.015), PAPER_M))

# ---------- lampu ----------
def point_light(name, loc, color, energy, shadow=False):
    bpy.ops.object.light_add(type="POINT", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.use_shadow = shadow
    return o


def area_light(name, loc, color, energy, size, rot, shadow=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.size = size
    o.data.use_shadow = shadow
    o.rotation_euler = rot
    return o


# key hangat dari arah kamera twoshot (+X), fill hangat dari atas, rim MERAH dari backdrop
area_light("KeyWarm", (2.2, 0, 2.2), (1.0, 0.82, 0.60), 220.0, 1.6, (math.radians(55), 0, math.radians(-90)))
area_light("FillTop", (0, 0, 3.0), (0.95, 0.75, 0.72), 80.0, 2.0, (math.radians(10), 0, 0))
point_light("RimRed", (-1.6, 0, 2.0), (1.0, 0.10, 0.12), 220.0)
point_light("FaceWarm", (1.2, 0, 1.4), (1.0, 0.85, 0.65), 60.0)
# v2: semburan merah dari kolom — membasuh backdrop
point_light("WashL", (-1.7, -2.2, 2.4), (1.0, 0.08, 0.08), 90.0)
point_light("WashR", (-1.7, 2.2, 2.4), (1.0, 0.08, 0.08), 90.0)
# softbox panel emissive (terlihat di frame pinggir) — v2 merah
reg(block("SoftboxL", (2.4, -1.4, 2.0), (0.08, 0.9, 1.2), emissive("SoftboxM", (1.0, 0.22, 0.18), 2.0)))
reg(block("SoftboxR", (2.4, 1.4, 2.0), (0.08, 0.9, 1.2), emissive("SoftboxM2", (1.0, 0.22, 0.18), 2.0)))

# subsurf 1 karakter (bukan detail pipih)
for _info in CHARS.values():
    for _part in (_info["body"] + _info["head"] + _info["armU_L"] + _info["armU_R"]
                  + _info["armF_L"] + _info["armF_R"] + _info["legT_L"] + _info["legT_R"]
                  + _info["legS_L"] + _info["legS_R"]):
        if _part.type == "MESH" and not any(k in _part.name for k in ("Brow", "Beard", "Moustache", "Mouth", "Neck")):
            _s = _part.modifiers.new("Subdiv", "SUBSURF")
            _s.levels = 0
            _s.render_levels = 1
for _m, _coat in ((SKIN_NARA, 0.5), (SKIN_BIMO, 0.5), (BLAZER, 0.3)):
    _b = _m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in _b.inputs:
        _b.inputs["Coat Weight"].default_value = _coat
        _b.inputs["Coat Roughness"].default_value = 0.15

# ---------- kamera per mode ----------
bpy.ops.object.camera_add(location=(2.8, 0.1, 1.35))
cam = bpy.context.object
cam.data.lens = 40
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 2.8
cam.data.dof.aperture_fstop = 2.8
scene.camera = cam


def look_at(cam_obj, target, lens=None):
    if lens:
        cam_obj.data.lens = lens
    look = Vector(target) - cam_obj.location
    cam_obj.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()


def hide_mic_set(prefix):
    """Sembunyikan seluruh rangkaian mic satu pembicara (Mic/MicTop/
    PopFilter/BoomArm/BoomBase). Dipakai di still close-up: mic lawan bicara
    yang dekat kamera akan membesar di foreground dan menutupi muka."""
    for suffix in ("Mic", "MicTop", "PopFilter", "BoomArm", "BoomBase"):
        o = bpy.data.objects.get(f"{prefix}_{suffix}")
        if o is not None:
            o.hide_render = True


if MODE == "compare":
    # keduanya BERDIRI berdampingan, skala sama, kamera sama — bukti cetakan beda
    for o in STUDIO_OBJS:
        o.hide_render = True
    RIGS["NARA"]["root"].location = (-0.62, 0, 0)
    RIGS["BIMO"]["root"].location = (0.62, 0, 0)
    RIGS["BIMO"]["root"].rotation_euler = (0, 0, 0)  # sama-sama menghadap kamera (-Y)
    cam.location = (0, -3.4, 1.25)
    look_at(cam, (0, 0, 1.0), lens=40)
    cam.data.dof.focus_distance = 3.4
elif MODE == "front-nara":
    pose_seated("NARA", +1)
    pose_seated("BIMO", -1)
    hide_mic_set("BIMO")  # mic Bimo dekat kamera close-up Nara -> foreground raksasa
    cam.data.dof.use_dof = False  # still depan: tanpa DOF (mic di depan lensa bikin blur)
    cam.location = (0.9, -0.9, 1.40)
    look_at(cam, (0, 0.55, 1.32), lens=50)
elif MODE == "front-bimo":
    pose_seated("NARA", +1)
    pose_seated("BIMO", -1)
    hide_mic_set("NARA")  # mic Nara dekat kamera close-up Bimo -> foreground raksasa
    cam.data.dof.use_dof = False
    cam.location = (-0.9, 0.9, 1.50)
    look_at(cam, (0, -0.55, 1.45), lens=50)
else:  # twoshot
    pose_seated("NARA", +1)
    pose_seated("BIMO", -1)
    cam.location = (3.3, 0.1, 1.25)
    look_at(cam, (0, 0, 0.95), lens=40)
    cam.data.dof.focus_distance = 3.3

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
