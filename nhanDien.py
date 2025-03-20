from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
import cv2
from ultralytics import YOLO
from flask import Blueprint
from db import get_db_connection  # Import kết nối từ db.py

nhanDien = Blueprint("nhanDien",__name__)

model = YOLO("C:/Users/Del/Desktop/AInhandien-main/best.pt")  # Sử dụng YOLOv8

@nhanDien.route('/nhandien')
def nhandien():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()  
    cur = conn.cursor()
    cur.execute("SELECT ma_khay_hang, ten_khay_hang FROM KhayHang")  # Đảm bảo lấy đúng dữ liệu
    data = cur.fetchall()
    cur.close()

    ma_quyen = session.get('ma_quyen', '2')  
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/nhanDien.html", khayhang=data)


# Hàm nhận diện ảnh
def detect_objects(frame):
    results = model(frame)  # Dự đoán với YOLO
    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])  # Độ tin cậy
            if conf > 0.5:  # Chỉ hiển thị nếu độ tin cậy lớn hơn 0.6
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Tọa độ bbox
                cls = int(box.cls[0])  # Lớp dự đoán

                # Kiểm tra model.names có tồn tại không
                if hasattr(model, "names") and cls in model.names:
                    label = f"{model.names[cls]} {conf:.2f}"
                else:
                    label = f"Object {cls} {conf:.2f}"

                # Vẽ khung chữ nhật
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Hiển thị nhãn
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame


# Camera stream
def generate_frames():
    cap = cv2.VideoCapture(0)  # Mở webcam
    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = detect_objects(frame)  # Nhận diện đối tượng
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame/r/n'
               b'Content-Type: image/jpeg/r/n/r/n' + frame + b'/r/n')

    cap.release()

@nhanDien.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

import os
from werkzeug.utils import secure_filename

# Thư mục lưu ảnh
UPLOAD_FOLDER = "static/img/upload/"
DETECT_FOLDER = "static/img/detect/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DETECT_FOLDER, exist_ok=True)

@nhanDien.route('/upload_files', methods=['POST'])
def upload_files():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    khayhang = request.form.get('khayhang')
    if 'files' not in request.files:
        return "No file uploaded", 400

    files = request.files.getlist('files')  # Lấy danh sách file được chọn
    if not files or files[0].filename == '':
        return "No files selected", 400

    results_list = []  # Danh sách ảnh đã nhận diện

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Xử lý nhận diện bằng YOLO
        img = cv2.imread(file_path)
        results = model(img)
        count_dict = {"rotten_apple": 0, "rotten_banana": 0, "rotten_mango": 0, "rotten_orange": 0, "rotten_peach": 0,
                      "rotten_pear": 0}

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if conf > 0.5:
                    nhan_dang = model.names[cls]
                    if nhan_dang in count_dict:
                        count_dict[nhan_dang] += 1

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = f"{nhan_dang} {conf:.2f}"
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        total_rotten = sum(count_dict.values())

        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dulieuhinhanh (duong_dan_hinh_anh, ngay_chup, so_luong_hu_hong,ma_khay_hang) VALUES (%s, NOW(), %s,%s)",
            (file_path, total_rotten,khayhang))
        conn.commit()
        cur.close()

        # Lưu ảnh kết quả
        output_path = os.path.join(DETECT_FOLDER, filename)
        cv2.imwrite(output_path, img)
        results_list.append(output_path)

    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/nhanDien.html", uploaded=True, detected_images=results_list)