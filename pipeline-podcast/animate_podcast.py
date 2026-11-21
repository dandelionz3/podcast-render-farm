# animate_podcast.py — Animasi PODCAST "Masa Depan AI" (FASE 2, final; v2 21 Nov 2026).
# v2: KAMERA TENANG (user: gerakan kamera v1 "terlalu muter", bikin pusing).
# Semua line = SATU twoshot statis, tanpa close-up, tanpa cut kamera selama
# dialog; satu-satunya cut: ke twoshot-wide-endcard di outro (51.153 dtk).
# Gap antar line = ilustrasi bergerak (frame gap diganti frame ilustrasi di
# assembly pasca-render — di render ini gap tetap twoshot, tidak dipakai).
# Pola: animate_nexus_ep3.py — exec build_scene_podcast.py (tanpa still),
# keyframe rig + kamera + mulut tiap frame dari audio/timing.json +
# audio/podcast-words.json (lip-sync per kata), lalu render per rentang.
# Usage:
#   blender -b --factory-startup -P animate_podcast.py -- <out_dir> --start N --end N [--res 540 960] [--engine eevee|cycles]
#   9:16 Eevee: --res 540 960 ; 16:9 Cycles: --res 960 540 --engine cycles
#   Frame Blender = f + 1 (timing.json f 0-based). --start/--end = nomor frame Blender.
#   Cycles: device GPU, samples 32, denoise OPENIMAGEDENOISE (pola Nexus Ep 3).
# Aturan shot v2 (dari timing.json):
#   line  -> twoshot (SATU kamera statis untuk semua dialog)
#   gap   -> illustration (di assembly diganti ilustrasi bergerak)
#   outro 51.153-60 -> twoshot-wide-endcard (SATU cut keras di 51.153, tanpa gerak)
# Gerakan: anggukan kepala PELAN saat bicara (amplitudo + frekuensi kecil),
# mulut buka saat kata aktif (skala Z mulut), listener menoleh SEDIKIT +
# angguk pelan saat gap, gestur tangan kanan Bimo pelan di awal line-nya.
# Lip-sync: pembicara mulut ditentukan dari podcast-words.json (kata aktif),
# BUKAN batas line timing.json — timestamp kata Whisper melebar ~0.3-0.45 dtk
# melewati batas line, jadi mulut mengikuti kata langsung (peta kata->line
# dengan toleransi +-0.6 dtk). Kata outro "Terima kasih" (58.58-59.98, di luar
# semua line) dipetakan ke Nara (host menutup acara).
import bpy
import json
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = args[0] if args else PROJ + "/frames"
START = int(args[args.index("--start") + 1]) if "--start" in args else 1
END = int(args[args.index("--end") + 1]) if "--end" in args else 1440
ENGINE = args[args.index("--engine") + 1] if "--engine" in args else "eevee"
assert ENGINE in ("eevee", "cycles"), "--engine harus eevee|cycles, dapat %r" % ENGINE
FPS = 24

# Build the scene without its still render
sys.argv = [sys.argv[0], "--", OUT_DIR + "/unused.png", "--mode", "twoshot"] + (
    ["--res"] + args[args.index("--res") + 1:args.index("--res") + 3] if "--res" in args else [])
src = open(os.path.join(HERE, "build_scene_podcast.py"), encoding="utf-8").read().split(
    "scene.render.filepath = OUT")[0]
exec(src)
# build_scene sudah pose_seated + kamera twoshot default
if ENGINE == "cycles":
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    _cprefs = bpy.context.preferences.addons["cycles"].preferences
    _cprefs.compute_device_type = "CUDA"
    for _d in _cprefs.devices:
        _d.use = _d.type == "CUDA"
    print("CYCLES DEVICES:", [(d.name, d.type, d.use) for d in _cprefs.devices], flush=True)
    print("CYCLES SETTINGS: device=%s samples=%s denoiser=%s" % (
        scene.cycles.device, scene.cycles.samples, scene.cycles.denoiser), flush=True)
scene.frame_start = 1
scene.frame_end = 1440
print("EEVEE SETTINGS: samples=%s" % scene.eevee.taa_render_samples, flush=True)

timing = json.load(open(os.path.join(PROJ, "audio/timing.json"), encoding="utf-8"))
words = json.load(open(os.path.join(PROJ, "audio/podcast-words.json"), encoding="utf-8"))["words"]
lines = timing["lines"]
gaps = timing["gaps"]

# ---------- kamera per shot (posisi + target + lens) ----------
# v2: HANYA twoshot + wide-endcard. Tidak ada close-up (itulah yang bikin
# kamera v1 terasa "muter": cut keras antar sudut berlawanan tiap line).
CAM_SHOTS = {
    "twoshot": ((3.3, 0.1, 1.25), (0, 0, 0.95), 40),
    "twoshot-wide-endcard": ((4.2, 0.2, 1.45), (0, 0, 0.95), 36),
}
cam = scene.camera
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.8


def set_cam(shot):
    loc, tgt, lens = CAM_SHOTS[shot]
    cam.location = loc
    cam.data.lens = lens
    look = Vector(tgt) - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = (Vector(tgt) - cam.location).length


MIC_SETS = {}
for _prefix in ("NARA", "BIMO"):
    MIC_SETS[_prefix] = [bpy.data.objects.get(f"{_prefix}_{_s}")
                         for _s in ("Mic", "MicTop", "PopFilter", "BoomArm", "BoomBase")]
    MIC_SETS[_prefix] = [o for o in MIC_SETS[_prefix] if o is not None]


def set_mic_visibility(shot, frame):
    """v2: shot selalu twoshot/wide — kedua mic tampil. Fungsi dipertahankan
    (tidak ada close-up lagi, jadi hide selalu None)."""
    hide = {"closeup-nara": "BIMO", "closeup-bimo": "NARA"}.get(shot)
    for prefix, objs in MIC_SETS.items():
        for o in objs:
            o.hide_render = (prefix == hide)
            o.keyframe_insert(data_path="hide_render", frame=frame)


def shot_at(f):
    """f = frame 0-based. Kembalikan nama shot yang berlaku."""
    t = f / FPS
    for ln in lines:
        if ln["start_frame"] <= f <= ln["end_frame"]:
            return ln["shot"]
    for gp in gaps:
        if gp["start"] <= t < gp["end"]:
            return gp["shot"]
    if t < 2.0:
        return "twoshot"
    return "twoshot-wide-endcard"


def speaker_at(f):
    """Pembicara pada frame f (0-based) — untuk CUT KAMERA: batas line timing.json."""
    for ln in lines:
        if ln["start_frame"] <= f <= ln["end_frame"]:
            return ln["speaker"]
    return None


def word_speaker_at(t):
    """(pembicara, kata-aktif?) pada detik t — untuk MULUT + ANGGUKAN:
    kata aktif dari podcast-words.json, pembicara dari line yang titik
    tengah katanya jatuh di [start-0.6, end+0.6]. Kata outro di luar semua
    line (t>=51.153) = Nara (host menutup acara)."""
    for w in words:
        if w["s"] <= t <= w["e"]:
            mid = (w["s"] + w["e"]) / 2.0
            for ln in lines:
                if ln["start"] - 0.6 <= mid <= ln["end"] + 0.6:
                    return ln["speaker"], True
            if t >= 51.153:
                return "Nara", True
            return None, True
    return None, False


# ---------- keyframe helpers ----------
def key(obj, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


# Semua keyframe LINEAR (potongan podcast = cut keras, gerakan halus antar key)
for ob in bpy.data.objects:
    if ob.animation_data is not None:
        for fc in ob.animation_data.action.fcurves if ob.animation_data.action else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"

# ---------- animasi per frame ----------
# HeadRig rotasi lokal: X = angguk (maju/mundur), Z = menoleh.
# Nara & Bimo dibangun menghadap -Y lokal; menoleh ke lawan = rotasi Z.
prev_shot = None
for f in range(START - 1, END):
    bf = f + 1  # frame Blender
    t = f / FPS
    shot = shot_at(f)
    # v2: gap "illustration" dirender sebagai twoshot (framenya diganti
    # ilustrasi di assembly) — kamera TIDAK PERNAH pindah dari twoshot
    # kecuali satu cut ke wide-endcard di outro.
    cam_shot = "twoshot" if shot == "illustration" else shot
    spk = speaker_at(f)        # cut kamera: batas line
    wspk, wactive = word_speaker_at(t)  # mulut/angguk: kata aktif
    if cam_shot != prev_shot:
        set_cam(cam_shot)
        # WAJIB keyframe lokasi+rotasi+lensa kamera (bukan cuma set nilai):
        # key(cam, bf) tanpa loc/rot tidak menyisipkan keyframe apa pun,
        # kamera diam di posisi set_cam terakhir untuk SEMUA frame.
        key(cam, bf, loc=cam.location.copy(), rot=cam.rotation_euler.copy())
        cam.data.keyframe_insert(data_path="lens", frame=bf)
        cam.data.keyframe_insert(data_path="dof.focus_distance", frame=bf)
        set_mic_visibility(cam_shot, bf)
        prev_shot = cam_shot
    # --- kepala: v2 PELAN — angguk kecil + lambat, menoleh sedikit ---
    for prefix, name in (("NARA", "Nara"), ("BIMO", "Bimo")):
        head = RIGS[prefix]["head"]
        if wspk == name and wactive:
            # angguk pelan selama kata aktif (dulu 0.10*sin(t*9) — terlalu cepat)
            nod = 0.06 * math.sin(t * 5.0)
            turn = 0.0
        elif spk is None:
            # gap: listener menoleh sedikit + angguk pelan
            turn = 0.15 if name == "Nara" else -0.15
            nod = 0.03 * math.sin(t * 2.0)
        else:
            # mendengarkan: menoleh sedikit + angguk pelan sesekali
            turn = 0.10 if name == "Nara" else -0.10
            nod = 0.02 * math.sin(t * 1.5)
        key(head, bf, rot=(nod, 0, turn))
        # --- mulut: buka (skala Z) saat kata aktif, tutup saat diam ---
        mouth = CHARS[prefix]["mouth"]
        if wspk == name and wactive:
            key(mouth, bf, scale=(1.0, 1.0, 2.6))
        else:
            key(mouth, bf, scale=(1.0, 1.0, 1.0))
    # --- gestur: tangan kanan Bimo terangkat PELAN di 0.5 dtk pertama tiap line-nya ---
    armR = RIGS["BIMO"]["elbR"]
    gesture = 0.0
    for ln in lines:
        if ln["speaker"] == "Bimo" and ln["start_frame"] <= f <= ln["start_frame"] + 12:
            gesture = -0.3 * math.sin(math.pi * (f - ln["start_frame"]) / 12.0)
    key(armR, bf, rot=(-math.pi / 2 * 0.9 + gesture, 0, 0))
    # lengan kiri Bimo & kedua lengan Nara: tetap di meja (pose_seated)
    key(RIGS["BIMO"]["elbL"], bf, rot=(-math.pi / 2 * 0.9, 0, 0))
    key(RIGS["NARA"]["elbR"], bf, rot=(-math.pi / 2 * 0.9, 0, 0))
    key(RIGS["NARA"]["elbL"], bf, rot=(-math.pi / 2 * 0.9, 0, 0))

# interpolasi LINEAR untuk semua fcurve yang baru dibuat
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"

# ---------- render rentang ----------
os.makedirs(OUT_DIR, exist_ok=True)
scene.render.filepath = os.path.join(OUT_DIR, "f_")
scene.frame_start = START
scene.frame_end = END
bpy.ops.render.render(animation=True)
print("RENDERED frames %d-%d to %s" % (START, END, OUT_DIR))
