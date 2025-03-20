from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
import cv2
from flask import redirect
from ultralytics import YOLO
import mysql.connector
from flask import Blueprint
from db import get_db_connection  # Import kết nối từ db.py
khayhang = Blueprint("khayhang",__name__)


@khayhang.route('/khayhang', methods=['GET', 'POST'])
def khayhang_view():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    timkiem = request.args.get('timkiem2', '')
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()

    if timkiem:
        cur.execute("SELECT kh.*, lt.ten_loai FROM khayhang kh LEFT JOIN loaitraicay lt ON kh.ma_loai = lt.ma_loai WHERE kh.ma_khay_hang LIKE %s OR kh.ten_khay_hang LIKE %s OR kh.so_luong_trong_khay LIKE %s OR kh.trang_thai LIKE %s OR kh.ghi_chu LIKE %s OR lt.ten_loai LIKE %s",
            ("%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%","%" + timkiem + "%")
        )

    else:
        cur.execute("SELECT kh.*, lt.ten_loai FROM khayhang kh LEFT JOIN loaitraicay lt ON kh.ma_loai = lt.ma_loai")
    data1 = cur.fetchall()

    cur.execute("SELECT * FROM loaitraicay")
    data2 = cur.fetchall()

    cur.close()

    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/khayHang.html", khayhang=data1, loaitraicay=data2, timkiem=timkiem)

@khayhang.route('/insert3',methods=['POST'])
def insert3():
    if request.method == "POST":
        tenkhay = request.form['tenkhay']
        soluong = int(request.form['soluong'])
        trangthai = "Còn hàng" if soluong > 0 else "Hết hàng"
        ghichu = request.form['ghichu']
        tenloai = request.form['tenloai']
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute("SELECT ma_loai FROM loaitraicay WHERE ten_loai = %s", (tenloai,))
        maloai = cur.fetchone()
        maloai = maloai[0]

        cur.execute("INSERT INTO khayhang (ten_khay_hang, so_luong_trong_khay, trang_thai, ghi_chu, ma_loai) VALUES (%s, %s, %s, %s, %s)",
                    (tenkhay, soluong, trangthai, ghichu, maloai))
        conn.commit()
        cur.close()
        return redirect(url_for('khayhang.khayhang_view'))

@khayhang.route('/delete3/<string:makhay>', methods=['GET'])
def delete3(makhay):
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM khayhang WHERE ma_khay_hang=%s", (makhay,))
        conn.commit()  # Đảm bảo MySQL cập nhật dữ liệu
        flash("Xóa thành công!", "success")  # Hiển thị thông báo thành công
    except mysql.connector.IntegrityError:
        conn.rollback()  # Hoàn tác nếu có lỗi
        flash("Không thể xóa! Khay hàng này đang được sử dụng ở bảng khác.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('khayhang.khayhang_view'))

@khayhang.route('/update3',methods=['POST','GET'])
def update3():
    if request.method == 'POST':
        makhay = request.form['makhay']
        tenkhay = request.form['tenkhay']
        soluong = int(request.form['soluong'])
        trangthai = "Còn hàng" if soluong > 0 else "Hết hàng"
        ghichu = request.form['ghichu']
        tenloai= request.form['tenloai']
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()

        cur.execute("SELECT ma_loai FROM loaitraicay WHERE ten_loai = %s", (tenloai,))
        maloai = cur.fetchone()
        maloai = maloai[0]

        cur.execute(
            "UPDATE khayhang SET ten_khay_hang=%s, so_luong_trong_khay=%s, ghi_chu=%s, trang_thai=%s, ma_loai=%s WHERE ma_khay_hang=%s",
            (tenkhay, soluong, ghichu, trangthai, maloai, makhay))
        conn.commit()
        cur.close()
        return redirect(url_for('khayhang.khayhang_view'))
