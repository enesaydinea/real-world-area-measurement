import cv2

window_name = "Tabela Okuma Kamera"

# 👇 backend belirtmeden aç (en stabil)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Kamera acilmadi")
    exit()

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 900, 600)

print("Kamera acildi - X ile kapat")

while True:
    ret, frame = cap.read()

    # 👇 Frame gelmiyorsa yazdır
    if not ret:
        print("Frame gelmedi")
        continue

    cv2.imshow(window_name, frame)

    # X ile kapanma
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
