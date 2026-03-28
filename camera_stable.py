import cv2
import time

window_name = "Tabela Okuma Kamera (X ile kapat)"

tests = [
    (cv2.CAP_ANY,  "ANY"),
    (cv2.CAP_MSMF, "MSMF"),
    (cv2.CAP_DSHOW,"DSHOW"),
]

def open_best_camera():
    for backend, name in tests:
        for idx in range(0, 6):
            cap = cv2.VideoCapture(idx, backend)
            time.sleep(0.2)
            if not cap.isOpened():
                cap.release()
                continue
            ok, frame = cap.read()
            if ok and frame is not None:
                print(f"KULLANILAN: backend={name}, index={idx}")
                return cap
            cap.release()
    return None

cap = open_best_camera()
if cap is None:
    print("Kamera acilamadi / frame gelmedi.")
    raise SystemExit

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 900, 600)
cv2.moveWindow(window_name, 80, 80)

print("Kamera acildi. Pencereyi X ile kapatabilirsin.")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    cv2.imshow(window_name, frame)

    # OpenCV olay döngüsünü çalıştır (X'i yakalar)
    cv2.waitKey(1)

    # X ile kapanma
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
