import cv2
import numpy as np

CARD_WIDTH = 8.56
CARD_HEIGHT = 5.398
IMG_PATH = "kart.jpeg"

points = []
img = cv2.imread(IMG_PATH)
if img is None:
    print(f"Resim okunamadi: {IMG_PATH}")
    raise SystemExit
orig = img.copy()

def order_points(pts):
    # pts: (4,2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[3] = pts[np.argmax(diff)]   # bottom-left
    return rect

def click(event, x, y, flags, param):
    global points, img
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append([x, y])
        cv2.circle(img, (x, y), 6, (0, 0, 255), -1)
        cv2.imshow("Kart Sec", img)
        print(f"Nokta {len(points)}: {x}, {y}")

cv2.namedWindow("Kart Sec", cv2.WINDOW_NORMAL)
cv2.imshow("Kart Sec", img)
cv2.setMouseCallback("Kart Sec", click)

print("4 koseye tikla (siraya takilma, ben duzeltecegim). ESC=iptal")

while True:
    cv2.imshow("Kart Sec", img)
    key = cv2.waitKey(10) & 0xFF
    if key == 27:
        cv2.destroyAllWindows()
        raise SystemExit

    if len(points) == 4:
        pts = np.array(points, dtype=np.float32)
        rect = order_points(pts)

        # Kartın piksel boyutlarını ölç (gerçek oranla uyumlu olacak)
        wA = np.linalg.norm(rect[2] - rect[3])
        wB = np.linalg.norm(rect[1] - rect[0])
        hA = np.linalg.norm(rect[1] - rect[2])
        hB = np.linalg.norm(rect[0] - rect[3])

        width_px = int(max(wA, wB))
        height_px = int(max(hA, hB))

        # Kartın yönünü düzelt: uzun kenar CARD_WIDTH’a denk gelsin
        if width_px < height_px:
            width_px, height_px = height_px, width_px

        dst = np.array([
            [0, 0],
            [width_px - 1, 0],
            [width_px - 1, height_px - 1],
            [0, height_px - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(orig, M, (width_px, height_px))

        cv2.imshow("Duzeltilmis", warped)

        px_per_cm_w = width_px / CARD_WIDTH
        px_per_cm_h = height_px / CARD_HEIGHT

        print("\nPIXEL / CM (beklenen: birbirine yakin):")
        print("Genislik:", px_per_cm_w)
        print("Yukseklik:", px_per_cm_h)
        print("Ortalama:", (px_per_cm_w + px_per_cm_h) / 2)

        cv2.waitKey(1500)
        break

cv2.destroyAllWindows() 
