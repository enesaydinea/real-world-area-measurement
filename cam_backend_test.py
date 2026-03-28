import cv2
import time

tests = [
    ("ANY",  cv2.CAP_ANY),
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW",cv2.CAP_DSHOW),
]

def try_cam(index, backend):
    cap = cv2.VideoCapture(index, backend)
    time.sleep(0.3)
    if not cap.isOpened():
        cap.release()
        return None

    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        return "OPENED_BUT_NO_FRAME"
    return cap

for name, backend in tests:
    for idx in range(0, 6):
        res = try_cam(idx, backend)
        if res == "OPENED_BUT_NO_FRAME":
            print(f"{name} index={idx} -> ACILDI AMA FRAME YOK")
            continue
        if res is not None:
            print(f"{name} index={idx} -> TAMAM (GORUNTU VAR)")
            cap = res
            cv2.imshow("camera", cap.read()[1])
            cv2.waitKey(800)
            cap.release()
            cv2.destroyAllWindows()
            raise SystemExit

print("HICBIR BACKEND/INDEX frame veremedi.")
print("Bu durumda sorun %90: izin / kamera kilidi / driver.")
