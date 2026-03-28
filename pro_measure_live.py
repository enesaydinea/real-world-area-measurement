import cv2
import numpy as np

# --- Kart standart ölçüleri (cm) ---
CARD_W = 8.56
CARD_H = 5.398
CARD_AR = CARD_W / CARD_H  # ~1.586

# --- Vergi hesabı ---
BIRIM_FIYAT = 1000  # TL / m² (şimdilik)

# --- Global state ---
sign_pts = None            # tabela 4 köşe (4,2) float32
tracking = False
prev_gray = None

px_per_cm_x = None         # ölçek X
px_per_cm_y = None         # ölçek Y

# Manuel kart seçimi için
card_pts = None            # kart 4 köşe list
selecting_card = False     # C basınca True olur


def order_points(pts):
    pts = np.array(pts, dtype=np.float32)
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    rect[1] = pts[np.argmin(d)]      # top-right
    rect[3] = pts[np.argmax(d)]      # bottom-left
    return rect


def detect_card_scale(frame):
    """
    Kartı otomatik bulup (px/cm)x,y döndürür.
    Bulamazsa (None, None, None).
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 160)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0

    h, w = gray.shape[:2]
    min_area = (h * w) * 0.005  # çok küçükleri ele

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        if not cv2.isContourConvex(approx):
            continue

        pts = approx.reshape(4, 2).astype(np.float32)
        rect = order_points(pts)

        width_px = max(np.linalg.norm(rect[1] - rect[0]), np.linalg.norm(rect[2] - rect[3]))
        height_px = max(np.linalg.norm(rect[3] - rect[0]), np.linalg.norm(rect[2] - rect[1]))
        if width_px < 1 or height_px < 1:
            continue

        ar = width_px / height_px
        if ar < 1:
            ar = 1 / ar

        # Kart oranına yakın olsun (tolerans)
        if abs(ar - CARD_AR) > 0.35:
            continue

        if area > best_area:
            best_area = area
            best = (rect, width_px, height_px)

    if best is None:
        return None, None, None

    rect, width_px, height_px = best

    # uzun kenarı CARD_W'ye eşle
    if width_px < height_px:
        width_px, height_px = height_px, width_px

    pxcm_x = width_px / CARD_W
    pxcm_y = height_px / CARD_H

    return pxcm_x, pxcm_y, rect


def polygon_area_px(pts):
    return abs(cv2.contourArea(pts.astype(np.float32)))


def draw_poly(frame, pts, color=(0, 255, 0), thickness=2):
    pts_i = pts.astype(int)
    cv2.polylines(frame, [pts_i], True, color, thickness)
    for p in pts_i:
        cv2.circle(frame, tuple(p), 5, (0, 0, 255), -1)


def refine_points_subpix(gray, pts):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
    pts2 = pts.reshape(-1, 1, 2).astype(np.float32)
    cv2.cornerSubPix(gray, pts2, (7, 7), (-1, -1), criteria)
    return pts2.reshape(-1, 2)


def track_points(prev_gray, gray, pts):
    p0 = pts.reshape(-1, 1, 2).astype(np.float32)
    p1, st, err = cv2.calcOpticalFlowPyrLK(
        prev_gray, gray, p0, None,
        winSize=(21, 21), maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    )
    st = st.reshape(-1)
    if st.sum() < 4:
        return None
    return p1.reshape(-1, 2)


def on_mouse(event, x, y, flags, param):
    global sign_pts, tracking, card_pts, selecting_card, px_per_cm_x, px_per_cm_y

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # --- Kart seçme modu (C ile) ---
    if selecting_card:
        if card_pts is None:
            card_pts = []
        if len(card_pts) < 4:
            card_pts.append([x, y])
            print(f"Kart nokta {len(card_pts)}: {x}, {y}")

            if len(card_pts) == 4:
                rect = order_points(np.array(card_pts, dtype=np.float32))

                width_px = max(np.linalg.norm(rect[1] - rect[0]), np.linalg.norm(rect[2] - rect[3]))
                height_px = max(np.linalg.norm(rect[3] - rect[0]), np.linalg.norm(rect[2] - rect[1]))

                # uzun kenarı CARD_W'ye eşle
                if width_px < height_px:
                    width_px, height_px = height_px, width_px

                px_per_cm_x = width_px / CARD_W
                px_per_cm_y = height_px / CARD_H

                print(f"KART OLCEK SET: X={px_per_cm_x:.2f} px/cm  Y={px_per_cm_y:.2f} px/cm")
                selecting_card = False
        return

    # --- Tabela seçme modu ---
    if sign_pts is None:
        sign_pts = []
    if isinstance(sign_pts, list) and len(sign_pts) < 4:
        sign_pts.append([x, y])
        print(f"Tabela nokta {len(sign_pts)}: {x}, {y}")
        if len(sign_pts) == 4:
            sign_pts = order_points(np.array(sign_pts, dtype=np.float32))
            tracking = True
            print("Tabela 4 nokta tamam. Takip basladi.")


def main():
    global sign_pts, tracking, prev_gray, px_per_cm_x, px_per_cm_y, card_pts, selecting_card

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera acilamadi.")
        return

    win = "PRO - Kart Otomatik/Manuel (C) + Tabela Takip (X ile kapat)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_mouse)

    print("\nKullanim:")
    print("- Kartı tabelanın yanına koy/tut (aynı düzlem).")
    print("- Kart otomatik bulunmazsa: C bas -> kartın 4 köşesine tıkla (ölçek set).")
    print("- Tabela köşelerine 4 kez tıkla (1 kere).")
    print("- Kart görünür oldukça ölçek güncellenir.")
    print("- R: tabela yeniden sec | ESC: cikis\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1) Kartı otomatik algıla (bulursa ölçeği güncelle)
        auto_x, auto_y, card_rect = detect_card_scale(frame)
        if auto_x is not None:
            px_per_cm_x, px_per_cm_y = auto_x, auto_y
            draw_poly(frame, card_rect, color=(255, 200, 0), thickness=2)

        # Ölçek yazısı
        if px_per_cm_x is not None and px_per_cm_y is not None:
            cv2.putText(frame, f"Scale X:{px_per_cm_x:.2f} px/cm  Y:{px_per_cm_y:.2f} px/cm",
                        (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
        else:
            cv2.putText(frame, "Olcek yok: Kart bulunamadi. (C ile karti sec)",
                        (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Kart seçim modunu ekranda belirt
        if selecting_card:
            cv2.putText(frame, "KART SECIM MODU: 4 koseye tikla",
                        (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # 2) Tabela takip / ölçüm
        if tracking and sign_pts is not None:
            if prev_gray is None:
                sign_pts = refine_points_subpix(gray, sign_pts)
            else:
                new_pts = track_points(prev_gray, gray, sign_pts)
                if new_pts is None:
                    cv2.putText(frame, "Takip kayboldu! R ile yeniden sec.",
                                (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    tracking = False
                else:
                    sign_pts = order_points(new_pts)

            if sign_pts is not None:
                draw_poly(frame, sign_pts, color=(0, 255, 0), thickness=2)

                if px_per_cm_x is not None and px_per_cm_y is not None:
                    area_px2 = polygon_area_px(sign_pts)
                    area_cm2 = area_px2 / (px_per_cm_x * px_per_cm_y)
                    area_m2 = area_cm2 / 10000.0
                    vergi = area_m2 * BIRIM_FIYAT

                    cv2.putText(frame, f"Alan: {area_m2:.3f} m2",
                                (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    cv2.putText(frame, f"Vergi: {vergi:.2f} TL  (Birim: {BIRIM_FIYAT} TL/m2)",
                                (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Olcek yok: once kart (otomatik veya C ile).",
                                (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

        if key in (ord('c'), ord('C')):
            card_pts = None
            selecting_card = True
            print("Kart secimi basladi: 4 koseye tikla (bitince olcek set).")

        if key in (ord('r'), ord('R')):
            sign_pts = None
            tracking = False
            prev_gray = None
            print("Tabela secimi sifirlandi. Tekrar 4 nokta tikla.")

        # X ile kapanma
        if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
            break

        prev_gray = gray

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()