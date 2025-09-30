import os
import re
import cv2
import numpy as np
from ultralytics import YOLO

# model = YOLO("C:\\Users\\pavel\\OneDrive\\Área de Trabalho\\Dataset Anotado Yolo\\Detection\\runs\\detect\\train23\\weights\\best.pt")
model = YOLO("yolov8l.pt") 
root_directory = "H:\\BR 101 - DNIT\\record\\"
log_file = "processados.txt"
direction_file = "directions.txt"
total_classes_file = "contagem_classes.txt"

output_folder = "prints_caminhoes"
os.makedirs(output_folder, exist_ok=True)
line_x = 1200

# CLASS_NAMES = {
#     0: "Caminhao (2C)",
#     1: "Caminhao Duplo Direcional Trucado (4C)",
#     2: "Caminhao Trator + Semi Reboque (2S3)",
#     3: "Caminhao Trator Trucado + Semi Reboque (3J3)",
#     4: "Caminhao Trator Trucado + Semi Reboque (3J4)",
#     5: "Caminhao Trator Trucado + Semi Reboque (3S3)",
#     6: "Caminhao Trucado (3C)",
#     7: "Onibus (2CB)",
#     8: "Onibus Trucado (3CB)",
#     9: "Bitrem Articulado (3D4)",
#     10: "Caminhao Trator Trucado + Semi Reboque (3I3)"
# }

CLASS_NAMES = {
    2: "car",
    5: "bus",
    7: "truck"
    
}

# Função para carregar contagens totais de classes
def load_class_counts():
    class_counts = {"direita": {name: 0 for name in CLASS_NAMES.values()}, 
                    "esquerda": {name: 0 for name in CLASS_NAMES.values()}}

    if os.path.exists(total_classes_file):
        with open(total_classes_file, "r") as f:
            direction = None
            for line in f:
                line = line.strip()
                if line.startswith("Sentido Direita"):
                    direction = "direita"
                elif line.startswith("Sentido Esquerda"):
                    direction = "esquerda"
                elif direction and ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        class_name = parts[0].strip(" -")
                        count = int(parts[1].strip())
                        if class_name in class_counts[direction]:
                            class_counts[direction][class_name] = count
    return class_counts

# Função para salvar contagens totais de classes
def save_class_counts(class_counts):
    with open(total_classes_file, "w") as f:
        f.write("Sentido Direita:\n")
        for name, count in class_counts["direita"].items():
            f.write(f"- {name}:{count}\n")
        f.write("Sentido Esquerda:\n")
        for name, count in class_counts["esquerda"].items():
            f.write(f"- {name}:{count}\n")


def load_direction_counts():
    if os.path.exists(direction_file):
        with open(direction_file, "r") as f:
            line = f.readline().strip()
            if line:
                left, right = map(int, line.split(','))
                return left, right
    return 0, 0

def save_direction_counts():
    with open(direction_file, "w") as f:
        f.write(f"{total_left},{total_right}\n")

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    return cv2.warpAffine(image, M, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

def get_unique_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(new_filename):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1
    return new_filename

total_left, total_right = load_direction_counts()
class_counts = load_class_counts()

region_start = line_x - 30
region_end = line_x + 30

cooldown_active = False
cooldown_start_frame = 0
COOLDOWN_DURATION_FRAMES = 3

for root, _, files in os.walk(root_directory):
    for file in files:
        if file.endswith(".mp4"):
            video_path = os.path.join(root, file)

            with open(log_file, "r") as f:
                if video_path in f.read().splitlines():
                    print(f"🔹 Já processado: {video_path}")
                    continue

            print(f"🚀 Processando: {video_path}")
            match = re.search(r"_(\d{8})", file)
            formatted_date = f"{match.group(1)[6:8]}-{match.group(1)[4:6]}-{match.group(1)[:4]}" if match else "data_desconhecida"
            vehicle_tracks = {}
            counted_vehicles = {}
            cap = cv2.VideoCapture(video_path)

            fps = cap.get(cv2.CAP_PROP_FPS)
            repeat_frame_threshold = int(fps * 18)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            processed_frames = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # processed_frames += 1
                # if processed_frames <= repeat_frame_threshold or processed_frames >= total_frames - repeat_frame_threshold:
                #     continue

                if cooldown_active and abs(current_frame_number - cooldown_start_frame) > COOLDOWN_DURATION_FRAMES:
                    cooldown_active = False

                current_frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                original_frame = frame.copy()
                results = model.track(frame, persist=True, tracker="botsort.yaml")

                for obj in results[0].boxes:
                    if obj.id is None or obj.cls is None or obj.conf < 0.5:
                        continue

                    classe = int(obj.cls)
                    if classe not in CLASS_NAMES:
                        continue

                    id = int(obj.id)
                    bbox = obj.xyxy.cpu().numpy().flatten() if hasattr(obj.xyxy, "cpu") else obj.xyxy.flatten()
                    if len(bbox) < 4:
                        continue

                    x1, y1, x2, y2 = map(int, bbox)
                    x_center = (x1 + x2) / 2

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Classse: {classe} Conf: {obj.conf}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    MAX_DISAPPEAR_FRAMES = 100
                    REGION_WIDTH = 80
                    DELAY_FRAMES = 50
                    region_start = line_x - REGION_WIDTH // 2
                    region_end = line_x + REGION_WIDTH // 2

                    if id in vehicle_tracks:
                        prev_x = vehicle_tracks[id]["x"]

                        if region_start <= x_center <= region_end:
                            if prev_x < x_center:
                                direction = "direita"
                            elif prev_x > x_center:
                                direction = "esquerda"
                            else:
                                direction = None

                            if direction:
                                if id in counted_vehicles:
                                    last_dir = counted_vehicles[id]["direction"]
                                    last_frame = counted_vehicles[id]["frame"]
                                    if direction == last_dir and abs(current_frame_number - last_frame) < DELAY_FRAMES:
                                        continue
                                    if direction != last_dir and abs(current_frame_number - last_frame) < DELAY_FRAMES:
                                        continue

                                if not cooldown_active:
                                    if direction == "direita":
                                        total_right += 1
                                        class_counts["direita"][CLASS_NAMES[classe]] += 1
                                    else:
                                        total_left += 1
                                        class_counts["esquerda"][CLASS_NAMES[classe]] += 1

                                    counted_vehicles[id] = {"direction": direction, "frame": current_frame_number}

                                    # Ativa o cooldown
                                    cooldown_active = True
                                    cooldown_start_frame = current_frame_number

                                    # Salva print, etc.
                                    # rotated_frame = rotate_image(original_frame, angle=0)
                                    # filename = f"{output_folder}/caminhao_{id}_{direction}.png"
                                    # unique_filename = get_unique_filename(filename)
                                    # cv2.imwrite(unique_filename, rotated_frame)
                                    # print(f"📸 Print salvo: {unique_filename}")

                    vehicle_tracks[id] = {"x": x_center, "frame": current_frame_number}

                    to_remove = [
                        vid for vid, info in counted_vehicles.items()
                        if current_frame_number - info["frame"] > MAX_DISAPPEAR_FRAMES
                    ]
                    for vid in to_remove:
                        del counted_vehicles[vid]
                        if vid in vehicle_tracks:
                            del vehicle_tracks[vid]
                        print(f"🗑️ Veículo {vid} removido da memória (desapareceu).")

                cv2.putText(frame, f"Total Esquerda: {total_left}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Total Direita: {total_right}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.line(frame, (region_start, 0), (region_start, frame.shape[0]), (0, 0, 255), 2)
                cv2.line(frame, (region_end, 0), (region_end, frame.shape[0]), (0, 0, 255), 2)

                cv2.imshow("Tracking", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()

            with open(log_file, "a") as f:
                f.write(video_path + "\n")

            save_direction_counts()
            save_class_counts(class_counts)
            print(f"✅ Processamento concluído: {video_path}\n")

print("🚀 Todos os vídeos foram processados!")