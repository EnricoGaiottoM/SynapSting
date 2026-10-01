"""PER-bot v1/v2: pontua automaticamente a extensão da probóscide em vídeo.

Ideia: a probóscide que estende muda os pixels numa pequena região (ROI) em volta
da boca. Comparamos a "energia de movimento" na janela logo após o estímulo com a
linha de base antes dele. O instante do estímulo vem do LED de sincronização (v2)
ou de uma lista de tempos (v1, estímulo manual).

Uso:
  python per_score.py video.mp4 --rois rois.json --out scores.csv            # v2 (LED)
  python per_score.py video.mp4 --rois rois.json --onsets 12.5,40.2 --out s.csv  # v1
  python per_score.py video.mp4 --pick-rois rois.json   # desenha as ROIs com o mouse
rois.json: {"led": [x,y,w,h], "flies": {"f1": [x,y,w,h], ...}}
"""
import argparse, json
import cv2, numpy as np, pandas as pd


def pick_rois(video, path, n_flies):
    cap = cv2.VideoCapture(video); ok, fr = cap.read(); cap.release()
    led = cv2.selectROI("Marque o LED e aperte ENTER", fr); flies = {}
    for i in range(n_flies):
        flies[f"f{i+1}"] = cv2.selectROI(f"Marque a probóscide da mosca {i+1}", fr)
    cv2.destroyAllWindows()
    json.dump({"led": list(map(int, led)), "flies": {k: list(map(int, v)) for k, v in flies.items()}}, open(path, "w"), indent=1)


def read_traces(video, rois):
    cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    led_tr, mot = [], {k: [] for k in rois["flies"]}; prev = None
    while True:
        ok, fr = cap.read()
        if not ok: break
        g = cv2.GaussianBlur(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
        x, y, w, h = rois["led"]; led_tr.append(g[y:y+h, x:x+w].mean())
        for k, (x, y, w, h) in rois["flies"].items():
            mot[k].append(0.0 if prev is None else np.abs(g[y:y+h, x:x+w] - prev[y:y+h, x:x+w]).mean())
        prev = g
    cap.release()
    return fps, np.array(led_tr), {k: np.array(v) for k, v in mot.items()}


def led_onsets(led, fps, min_gap_s=1.0):
    thr = led.min() + 0.5 * (led.max() - led.min())
    on = np.flatnonzero((led[1:] > thr) & (led[:-1] <= thr)) + 1
    keep = [o for i, o in enumerate(on) if i == 0 or (o - on[i-1]) > min_gap_s * fps]
    return np.array(keep) / fps


def score(fps, mot, onsets, base_s=1.0, win_s=2.0, z_thr=4.0):
    rows = []
    for t_i, t in enumerate(onsets):
        a, b = int((t - base_s) * fps), int(t * fps); c = int((t + win_s) * fps)
        for k, m in mot.items():
            base, resp = m[max(a, 1):b], m[b:c]
            if len(base) < 3 or len(resp) < 1: continue
            z = (resp.max() - base.mean()) / (base.std() + 1e-6)
            rows.append(dict(trial=t_i + 1, onset_s=round(t, 3), fly=k, z=round(z, 2), per=int(z > z_thr)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--rois"); ap.add_argument("--pick-rois")
    ap.add_argument("--n-flies", type=int, default=8); ap.add_argument("--onsets")
    ap.add_argument("--z", type=float, default=4.0); ap.add_argument("--out", default="scores.csv")
    a = ap.parse_args()
    if a.pick_rois:
        pick_rois(a.video, a.pick_rois, a.n_flies); raise SystemExit
    rois = json.load(open(a.rois)); fps, led, mot = read_traces(a.video, rois)
    ons = np.array([float(x) for x in a.onsets.split(",")]) if a.onsets else led_onsets(led, fps)
    df = score(fps, mot, ons, z_thr=a.z); df.to_csv(a.out, index=False)
    print(f"{len(ons)} estímulos, {len(df)} eventos pontuados -> {a.out}")
