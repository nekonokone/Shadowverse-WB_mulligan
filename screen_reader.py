"""Capture card images and compare them to user-registered OpenCV templates."""
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


def _capture_screen(parent):
    try:
        import mss
        from PIL import Image
    except ImportError as exc:
        raise ImportError("mss と Pillow が必要") from exc
    parent.withdraw()
    parent.update_idletasks()
    time.sleep(0.7)
    try:
        with mss.mss() as capture:
            monitor = capture.monitors[1]
            shot = capture.grab(monitor)
            image = Image.frombytes("RGB", shot.size, shot.rgb)
        return image, monitor
    finally:
        parent.deiconify()
        parent.lift()


def _select_region(parent, image, monitor, count, instruction):
    result = {"box": None}
    picker = tk.Toplevel(parent)
    picker.title(instruction)
    picker.attributes("-topmost", True)
    picker.overrideredirect(True)
    width, height = image.size
    picker.geometry(f"{width}x{height}+{monitor['left']}+{monitor['top']}")
    canvas = tk.Canvas(picker, width=width, height=height, highlightthickness=0, cursor="crosshair")
    canvas.pack(fill="both", expand=True)
    from PIL import ImageTk
    photo = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, image=photo, anchor="nw")
    rect = None
    start = [0, 0]

    def down(event):
        nonlocal rect
        start[:] = [event.x, event.y]
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#ffe45e", width=4)

    def move(event):
        if rect is not None:
            canvas.coords(rect, start[0], start[1], event.x, event.y)

    def up(event):
        x1, x2 = sorted((start[0], event.x))
        y1, y2 = sorted((start[1], event.y))
        if x2 - x1 < max(40, count * 30) or y2 - y1 < 45:
            messagebox.showinfo("範囲を選び直してね", instruction, parent=picker)
            if rect is not None:
                canvas.delete(rect)
            return
        result["box"] = (x1, y1, x2, y2)
        picker.destroy()

    canvas.bind("<Button-1>", down)
    canvas.bind("<B1-Motion>", move)
    canvas.bind("<ButtonRelease-1>", up)
    picker.bind("<Escape>", lambda _event: picker.destroy())
    parent.wait_window(picker)
    if result["box"] is None:
        return None
    return image.crop(result["box"])


def capture_card_template(parent, path):
    image, monitor = _capture_screen(parent)
    crop = _select_region(parent, image, monitor, 1, "画面上のカード1枚全体をドラッグで囲んでね。Escで中止。")
    if crop is None:
        return False
    crop.save(path, format="PNG")
    return True


def _image_score(query, reference, cv2, np):
    def standardize(image):
        rgb = cv2.resize(image, (180, 250), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        return rgb, gray

    query_rgb, query_gray = standardize(query)
    ref_rgb, ref_gray = standardize(reference)
    correlation = float(cv2.matchTemplate(query_gray, ref_gray, cv2.TM_CCOEFF_NORMED)[0][0])
    if not np.isfinite(correlation):
        correlation = 0.0

    orb = cv2.ORB_create(nfeatures=700)
    _qk, qdesc = orb.detectAndCompute(query_gray, None)
    _rk, rdesc = orb.detectAndCompute(ref_gray, None)
    feature_score = 0.0
    if qdesc is not None and rdesc is not None:
        pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(qdesc, rdesc, k=2)
        good = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < 0.76 * pair[1].distance]
        feature_score = min(1.0, len(good) / 24.0)

    hist_scores = []
    for channel in range(3):
        qhist = cv2.calcHist([query_rgb], [channel], None, [24], [0, 256])
        rhist = cv2.calcHist([ref_rgb], [channel], None, [24], [0, 256])
        cv2.normalize(qhist, qhist)
        cv2.normalize(rhist, rhist)
        hist_scores.append(max(0.0, float(cv2.compareHist(qhist, rhist, cv2.HISTCMP_CORREL))))
    color_score = sum(hist_scores) / len(hist_scores)
    return 0.62 * feature_score + 0.25 * max(0.0, correlation) + 0.13 * color_score


def _template_path(value, template_dir):
    if isinstance(value, list):
        return [Path(template_dir) / item for item in value]
    return [Path(template_dir) / value] if value else []


def read_card_row(parent, count, templates, template_dir):
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise ImportError("opencv-python-headless、numpy、Pillow が必要") from exc

    image, monitor = _capture_screen(parent)
    strip = _select_region(parent, image, monitor, count, f"カード{count}枚全体が横一列に入る範囲を選んでね。Escで中止。")
    if strip is None:
        return None

    references = []
    for name, filenames in templates.items():
        for path in _template_path(filenames, template_dir):
            try:
                with Image.open(path) as reference_image:
                    references.append((name, np.asarray(reference_image.convert("RGB"))))
            except (OSError, ValueError):
                continue
    if not references:
        messagebox.showinfo("見本画像が見つからないよ", "カード登録タブで見本画像を登録してね。")
        return None

    found = []
    for i in range(count):
        left = round(i * strip.width / count)
        right = round((i + 1) * strip.width / count)
        crop = strip.crop((left, 0, right, strip.height))
        query = np.asarray(crop.convert("RGB"))
        scores = {}
        for name, reference in references:
            score = _image_score(query, reference, cv2, np)
            scores[name] = max(scores.get(name, 0.0), score)
        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        if not ranked or ranked[0][1] < 0.28 or (len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.035):
            found.append("")
        else:
            found.append(ranked[0][0])
    if not any(found):
        messagebox.showwarning("見本と一致しなかったよ", "カード全体が入るように選び直すか、カード登録から見本画像を追加してね。")
        return None
    return found
