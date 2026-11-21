# podcast-render-farm

Render farm GitHub Actions untuk PODCAST ANIMASI 3D "Masa Depan AI" (60 dtk, 24 fps, 1440 frame).

- **Eevee 9:16** — workflow `render-podcast-full.yml`: 20 job paralel x 72 frame (540x960, samples 8), frame Blender 1–1440. Tiap job upload zip chunk ke GitHub Release.
- **Cycles 16:9** — via Kaggle (4 kernel T4 x 360 frame), job di `../kaggle/job-a..d` (bukan di repo ini).

## Isi

- `pipeline-podcast/build_scene_podcast.py` — builder karakter BARU Nara & Bimo + studio + kamera.
- `pipeline-podcast/animate_podcast.py` — animasi dari `audio/timing.json` + `audio/podcast-words.json` (cut kamera per shot, lip-sync per kata, anggukan, gestur, visibilitas mic per shot).
- `audio/timing.json`, `audio/podcast-words.json` — timing line/gap + kata (Whisper).

## Cara pakai (full run Eevee)

```bash
gh release create podcast-full-run-20261121 --title "Podcast full run 20261121" --notes "Eevee 9:16, 20 chunk x 72 frame"
gh workflow run render-podcast-full.yml --ref main -f release_tag=podcast-full-run-20261121
```

Tiap job menilai sukses dari FILE FRAME (bukan exit code Blender — Mesa bisa segfault saat teardown setelah semua frame tersimpan).
Download chunk: `gh release download podcast-full-run-20261121 -p '9x16-*.zip'`.
