"""GIF/MP4 delle traiettorie U-Net + LAP di un video PINN sopra la sua illuminazione.

Sullo stile di ~/Scrivania/chlamy_sims/analysis/traj_gif.py (simulazioni):
- sfondo: l'illuminazione del video (illuminations/illumination<ill>.tiff), stessa geometria del fotogramma;
- ogni cellula e' un punto con una scia che sfuma (ultimi TAIL secondi). Il colore dice se, nell'ultimo
  secondo, la cellula si avvicina al centro vero dell'anello (blu) o se ne allontana (arancio);
- cerchio tratteggiato: disc_radius (luce al 5%, dal centro vero), lo stesso dell'analisi;
- sotto: rho_in/rho_out (dentro/fuori dal disco) per tutto il video, con il cursore sul fotogramma.
Le posizioni sono quelle di tracking/tAlgae<N>.txt (tutte le tracce, senza i filtri dell'analisi).
Scritte nella figura in inglese; nel fotogramma solo tempo, potenza della luce e barra di scala (niente nome
dell'esperimento ne' metodo di tracking).

Adapted from the laboratory `traj_gif.py` script: only hardcoded local paths
(`BASE`, `ring_geometry.csv`, `talgae_settings_PINN.txt`) and external `ffmpeg` calls
were parameterized to run inside the backend service using installed libraries.
"""
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

import imageio.v3 as iio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import tifffile  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from core import clamutils_exp as cu  # noqa: E402
from core.clam_pipeline.io import load_settings  # noqa: E402

# Default spatial/temporal conversion constants and color palette
PIX = 1 / 0.96                      # um per pixel spatial calibration (PINN register)
DT = 0.1                            # seconds per frame (10 fps video recording)
MAX_GAP = 4                         # max frame gap bridged by LAP linker (max_gap 3)
COL_IN = np.array([0.31, 0.76, 0.97])          # high-contrast blue: cell moving towards ring centre
COL_OUT = np.array([1.00, 0.44, 0.26])         # high-contrast orange: cell moving away from centre
MAP_CMAP = LinearSegmentedColormap.from_list("light", ["#000000", "#3a3a12", "#9a9a3a"])

# Shared rendering dictionary populated once by `init()` and reused by `draw()`
# to avoid re-parsing trajectories or re-computing geometry on every frame.
G = {}


# Precomputes physical coordinates, motion directions, and density ratios
def init(
    trajectories_txt,
    illumination_path,
    tail_frames,
    disc=130.0,
    pix=PIX,
    dt=DT,
    power=None,
    ctrp=0,
):
    """Load trajectories and illumination map, computing all physical metrics ahead of rendering."""
    # 1. Read illumination TIFF and find ring centre coordinates (cx, cy) in um using Speckle
    field = tifffile.imread(illumination_path).astype(float)
    if field.ndim == 3:
        field = field[..., 0]
    H, W = field.shape
    speckle = cu.Speckle(field, diam=15.0, pix=pix, ctrp=ctrp)
    cy, cx = float(speckle.center[1]), float(speckle.center[0])

    # 2. Load trajectory coordinates and normalize column names (supports both trackpy and legacy LAP)
    df = pd.read_csv(trajectories_txt)
    if {"snap", "tag"}.issubset(df.columns):
        df = df.rename(columns={"snap": "frame", "tag": "particle"})
    df = df.sort_values(["particle", "frame"], kind="stable")
    if df.empty:
        raise ValueError("Trajectories file is empty")
    f = df["frame"].to_numpy()
    p = df["particle"].to_numpy()
    # Convert pixel positions to micrometers (um)
    x, y = df["x"].to_numpy() * pix, df["y"].to_numpy() * pix
    # Radial distance of each cell from the illumination ring centre
    r = np.hypot(x - cx, y - cy)

    # 3. Identify consecutive detections belonging to the same particle track
    same = np.r_[False, (p[1:] == p[:-1]) & (f[1:] - f[:-1] <= MAX_GAP)]

    # 4. Determine motion direction (inward vs outward) over the preceding ~1 second
    # k is the number of frames corresponding to 1 second
    k = max(1, int(round(1.0 / dt)))
    r_back = np.full_like(r, np.nan)
    ok = np.r_[np.zeros(k, bool), p[k:] == p[:-k]]
    r_back[ok] = r[:-k][ok[k:]]
    first = pd.Series(r).groupby(p).transform("first").to_numpy()      # fallback for tracks < 1 s
    vr = r - np.where(np.isnan(r_back), first, r_back)
    inward = vr < 0  # True = moving towards the center (dr < 0); False = moving away

    # 5. Index trail segments and row indices sorted by frame for fast time slicing
    seg = np.flatnonzero(same)                  # segment (row-1 -> row), stamped at target frame
    order = np.argsort(f[seg], kind="stable")
    seg = seg[order]
    rows = np.argsort(f, kind="stable")

    # 6. Compute density ratio rho_in / rho_out:
    # (cells_inside / area_inside) divided by (cells_outside / area_outside)
    yy, xx = np.indices((H, W))
    in_px = np.hypot(xx * pix - cx, yy * pix - cy) < disc
    a_in, a_out = max(int(in_px.sum()), 1), max(int((~in_px).sum()), 1)
    n_frames = int(f.max()) + 1
    n_in = np.bincount(f[r < disc], minlength=n_frames)
    n_all = np.bincount(f, minlength=n_frames)
    ratio = (n_in / a_in) / np.maximum(n_all - n_in, 1) * a_out
    # Smooth ratio curve over a 10-frame rolling window for clean plotting
    ratio_s = pd.Series(ratio).rolling(10, center=True, min_periods=1).mean().to_numpy()

    field_max = float(field.max())
    norm_field = field / field_max if field_max > 0 else field

    # Store all computed state in global dict G for access during draw()
    G.update(
        power=power,
        field=norm_field,
        H=H,
        W=W,
        pix=pix,
        cx=cx,
        cy=cy,
        disc=float(disc),
        f=f,
        x=x,
        y=y,
        inward=inward,
        seg=seg,
        seg_f=f[seg],
        rows=rows,
        rows_f=f[rows],
        n_in=n_in,
        ratio=ratio_s,
        t=np.arange(n_frames) * dt,
        tail=tail_frames,
    )



# Render a single composite frame (illumination ring + trails + concentration plot) to PNG
# Renders a single composite frame to PNG:
# - Upper main panel: grayscale video frame + illumination ring + cell centroid dots + fading trails.
# - Lower panel: temporal evolution of inner/outer concentration ratio (rho_in / rho_out) with timeline cursor.
def draw(args):
    """Render a single frame snapshot to PNG with illumination overlay and trajectories."""
    i, path = args[:2]
    vid_frame = args[2] if len(args) > 2 else None
    g = G
    pix = g["pix"]
    Lx, Ly = g["W"] * pix, g["H"] * pix
    fig = plt.figure(figsize=(7.5, 6.4), dpi=90, facecolor="black")

    # Upper panel: microscope view (dimensions in micrometers, um)
    ax = fig.add_axes([0.01, 0.235, 0.98, 0.755])

    # 1. Background image:
    # If video frame is supplied, show grayscale video blended with false-color illumination ring.
    # If video is absent (e.g. running from trajectory txt alone), show illumination ring alone.
    if vid_frame is not None:
        vmax = float(vid_frame.max())
        norm_vid = vid_frame.astype(float) / vmax if vmax > 0 else vid_frame.astype(float)
        ax.imshow(norm_vid, cmap="gray", vmin=0, vmax=1, extent=[0, Lx, Ly, 0], alpha=0.85)
        ax.imshow(g["field"], cmap=MAP_CMAP, vmin=0, vmax=1, extent=[0, Lx, Ly, 0], alpha=0.45)
    else:
        ax.imshow(
            g["field"],
            cmap=MAP_CMAP,
            vmin=0,
            vmax=1,
            extent=[0, Lx, Ly, 0],
            interpolation="bilinear",
        )

    # 2. Illumination ring marker: dashed white circle drawn at `disc_radius`
    ax.add_patch(
        plt.Circle(
            (g["cx"], g["cy"]),
            g["disc"],
            fill=False,
            ls="--",
            lw=0.8,
            color="white",
            alpha=0.45,
        )
    )

    # 3. Draw fading trajectory tails over the last `tail` frames using LineCollection
    # Binary search (searchsorted) extracts only segments within [i - tail + 1, i + 1]
    lo, hi = np.searchsorted(g["seg_f"], [i - g["tail"] + 1, i + 1])
    s = g["seg"][lo:hi]
    if len(s):
        pts = np.stack(
            [
                np.stack([g["x"][s - 1], g["y"][s - 1]], -1),
                np.stack([g["x"][s], g["y"][s]], -1),
            ],
            1,
        )
        # Line opacity increases with recency (fading scia)
        age = (g["seg_f"][lo:hi] - (i - g["tail"])) / g["tail"]
        rgb = np.where(g["inward"][s][:, None], COL_IN, COL_OUT)
        ax.add_collection(
            LineCollection(pts, colors=np.column_stack([rgb, 0.08 + 0.6 * age]), linewidths=0.9)
        )

    # 4. Draw current cell centroids: blue if moving toward ring centre, orange if moving away
    lo, hi = np.searchsorted(g["rows_f"], [i, i + 1])
    now = g["rows"][lo:hi]
    inw = g["inward"][now]
    ax.scatter(
        g["x"][now],
        g["y"][now],
        s=9,
        c=np.where(inw[:, None], COL_IN, COL_OUT),
        edgecolors="black",
        linewidths=0.3,
        zorder=3,
    )
    ax.set_xlim(0, Lx)
    ax.set_ylim(Ly, 0)
    ax.set_axis_off()

    # 5. Overlays: 100 um scale bar, elapsed time timestamp, laser power, and directional legend
    ax.plot([Lx - 130, Lx - 30], [Ly - 35, Ly - 35], color="white", lw=2)
    ax.text(Lx - 80, Ly - 50, "100 µm", color="white", ha="center", va="bottom", fontsize=8)
    ax.text(
        20,
        25,
        f"t = {g['t'][i]:6.1f} s",
        color="white",
        ha="left",
        va="top",
        fontsize=11,
        family="monospace",
    )
    if g["power"] is not None:
        ax.text(
            20,
            Ly - 30,
            f"{g['power']:g} µW",
            color="white",
            ha="left",
            va="bottom",
            fontsize=8.5,
            bbox=dict(facecolor="black", alpha=0.6, edgecolor="none", pad=2),
        )
    n_in = int(inw.sum())
    ax.scatter([], [], s=12, c=[COL_IN], label=f"towards centre ({n_in})")
    ax.scatter([], [], s=12, c=[COL_OUT], label=f"away from centre ({len(now) - n_in})")
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 0.94),
        fontsize=8,
        labelcolor="white",
        handletextpad=0.2,
        facecolor="black",
        framealpha=0.6,
        edgecolor="none",
    )

    # 6. Lower panel: concentration ratio plot (rho_in / rho_out) as a function of time
    sx = fig.add_axes([0.10, 0.06, 0.86, 0.13], facecolor="black")
    t, ratio = g["t"], g["ratio"]
    sx.plot(t, ratio, color="#bbbbbb", lw=0.8)
    # Vertical white line and dot highlighting the exact timestamp of this frame
    sx.axvline(t[i], color="white", lw=1)
    sx.plot(t[i], ratio[i], "o", color="white", ms=4)
    if len(t) > 1:
        sx.set_xlim(t[0], t[-1])
    y_max = float(ratio.max()) if len(ratio) else 1.0
    sx.set_ylim(0, max(y_max * 1.1, 0.1))
    sx.set_ylabel(f"ρ in / out\nr < {g['disc']:.0f} µm", color="white", fontsize=7.5)
    sx.set_xlabel("t (s)", color="white", fontsize=8, labelpad=1)
    sx.tick_params(colors="white", labelsize=7)
    for sp in sx.spines.values():
        sp.set_color("#666666")

    # Save rendered figure to target PNG file and close to free memory
    fig.savefig(path, facecolor="black")
    plt.close(fig)
    return i


# Main orchestration function in core: renders all sampled frames and writes `trajectories.gif`
def render_gif(
    trajectories_txt,
    illumination_path,
    out_dir,
    step=10,
    tail_s=3.0,
    fps=10,
    disc=130.0,
    pix=PIX,
    dt=DT,
    power=None,
    ctrp=0,
    video_frames=None,
):
    """Render PNG frames and combine them into `trajectories.gif` and metadata dict."""
    # Convert tail duration in seconds into integer frame count
    tail = max(1, int(round(tail_s / dt)))
    init(
        trajectories_txt=trajectories_txt,
        illumination_path=illumination_path,
        tail_frames=tail,
        disc=disc,
        pix=pix,
        dt=dt,
        power=power,
        ctrp=ctrp,
    )
    idx = np.arange(0, len(G["t"]), step)
    out_dir = Path(out_dir)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Iterate through sampled frames sequentially without buffering all video frames in RAM
    vid_iter = iter(video_frames) if video_frames is not None else iter(())
    png_paths = []
    concentration = []
    cells_in_ring = []

    for k, i in enumerate(idx):
        vid_frame = None
        # Consume video stream generator until we reach frame index `i`
        for v_idx, arr in vid_iter:
            if v_idx == i:
                vid_frame = arr
                break
            if v_idx > i:
                break
        png_path = frames_dir / f"{k}.png"
        draw((int(i), str(png_path), vid_frame))
        png_paths.append(png_path)
        concentration.append(round(float(G["ratio"][i]), 6))
        cells_in_ring.append(int(G["n_in"][i]))

    # Encode individual PNG frames into an animated GIF via ImageIO (no external ffmpeg required)
    gif_path = out_dir / "trajectories.gif"
    duration_ms = max(1, int(round(1000 / max(fps, 1))))
    images = [iio.imread(p) for p in png_paths]
    iio.imwrite(gif_path, images, extension=".gif", duration=duration_ms, loop=0)

    meta = {
        "count": len(png_paths),
        "concentration": concentration,
        "cells_in_ring": cells_in_ring,
        "frame_indices": [int(i) for i in idx],
    }
    return gif_path, meta



# CLI entry point preserved from the original laboratory script
def main():
    base = Path(sys.argv[1])
    exp = int(sys.argv[2])
    given = [float(a) for a in sys.argv[3:6]]
    step, tail_s, fps = given + [2, 3, 25][len(given):]            # 2 frames -> 25 fps = 5x real time
    step, fps, tail = int(step), int(fps), int(round(tail_s / DT))
    st = load_settings(base / "talgae_settings.txt")
    row = st.loc[st["exps"] == exp].iloc[0]
    ill = int(row["ill"])
    init(
        base / f"tracking/tAlgae{exp}.txt",
        base / f"illuminations/illumination{ill}.tiff",
        tail,
        pix=float(row["pix_arr"]),
        power=float(row["intensity"]),
        ctrp=int(row["ctr"]),
    )
    idx = np.arange(0, len(G["t"]), step)
    out = base / "gif"
    out.mkdir(exist_ok=True)
    stem = out / f"tAlgae{exp}"
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        jobs = [(int(i), f"{tmp}/f{k:05d}.png") for k, i in enumerate(idx)]
        with Pool(4) as pool:
            for n, _ in enumerate(pool.imap_unordered(draw, jobs, chunksize=8)):
                if n % 100 == 0:
                    print(f"{n}/{len(jobs)}", flush=True)
        src = ["-framerate", str(fps), "-i", f"{tmp}/f%05d.png"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-vf",
                        "split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];"
                        "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                        f"{stem}.gif"], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", f"{stem}.mp4"], check=True)
    print(f"{stem}.gif", f"{len(idx)} frame, {step * DT * fps:g}x tempo reale")


if __name__ == "__main__":
    main()

