from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
from flask import redirect
from flask import Blueprint
import mysql
from db import get_db_connection  # Import kết nối từ db.py

chiTietLoai = Blueprint("chiTietLoai",__name__)

@chiTietLoai.route('/chitiet', methods=['GET', 'POST'])
def chitiet():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    timkiem = request.args.get('timkiem1')
    conn = get_db_connection()
    cur = conn.cursor()
    if timkiem:
        cur.execute(
            """
            SELECT ltc.*, tc.ten_trai_cay, SUM(kh.so_luong_trong_khay) AS tong_so_luong
            FROM loaitraicay ltc 
            LEFT JOIN traicay tc ON ltc.ma_trai_cay = tc.ma_trai_cay
            LEFT JOIN khayhang kh ON ltc.ma_loai = kh.ma_loai 
            WHERE ltc.ma_loai LIKE %s OR ltc.ten_loai LIKE %s OR ltc.xuat_xu LIKE %s OR ltc.so_luong LIKE %s OR tc.ten_trai_cay LIKE %s OR ltc.ghi_chu LIKE %s
            GROUP BY ltc.ma_loai;  
            """,
            ("%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%",
             "%" + timkiem + "%")
        )

    else:
        cur.execute("SELECT ltc.*,tc.ten_trai_cay,SUM(kh.so_luong_trong_khay) AS tong_so_luong FROM loaitraicay ltc LEFT JOIN traicay tc ON ltc.ma_trai_cay = tc.ma_trai_cay LEFT JOIN khayhang kh ON ltc.ma_loai = kh.ma_loai GROUP BY ltc.ma_loai")

    data1 = cur.fetchall()
    cur.execute("SELECT * FROM traicay")
    data2 = cur.fetchall()
    cur.close()

        # Xác định quyền để chọn template phù hợp
    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/chiTietLoai.html", loaitraicay=data1, traicay=data2, timkiem=timkiem)


@chiTietLoai.route('/insert',methods=['POST'])
def insert():
    if request.method == "POST":
        tenloai = request.form['tenloai']
        xuatxu = request.form['xuatxu']
        ghichu = request.form['ghichu']
        tentraicay = request.form['tentraicay']
        hinhanh = request.form['hinhanh']
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT ma_trai_cay FROM traicay WHERE ten_trai_cay = %s", (tentraicay,))
        matraicay = cur.fetchone()
        matraicay = matraicay[0]

        cur.execute("insert into loaitraicay (ten_loai,xuat_xu,ghi_chu,ma_trai_cay,hinh_anh) values (%s,%s,%s,%s,%s)",(tenloai,xuatxu,ghichu,matraicay,hinhanh))
        conn.commit()
        cur.close()
        return redirect(url_for('chiTietLoai.chitiet'))

@chiTietLoai.route('/delete/<string:maloai>', methods=['GET'])
def delete(maloai):
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM loaitraicay WHERE ma_loai=%s", (maloai,))
        conn.commit()  # Đảm bảo MySQL cập nhật dữ liệu
        flash("Xóa thành công!", "success")  # Hiển thị thông báo thành công
    except mysql.connector.IntegrityError:
        conn.rollback()  # Hoàn tác nếu có lỗi
        flash("Không thể xóa! Loại trái cây này đang được sử dụng ở bảng khác.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('chiTietLoai.chitiet'))

@chiTietLoai.route('/update',methods=['POST','GET'])
def update():
    if request.method == 'POST':
        maloai = request.form['maloai']
        tenloai = request.form['tenloai']
        xuatxu = request.form['xuatxu']
        ghichu = request.form['ghichu']
        hinhanh= request.form['hinhanh']
        tentraicay = request.form['tentraicay']
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT ma_trai_cay FROM traicay WHERE ten_trai_cay = %s", (tentraicay,))
        matraicay = cur.fetchone()
        matraicay = matraicay[0]

        cur.execute(
            "update loaitraicay set ten_loai=%s, xuat_xu=%s,ghi_chu=%s, hinh_anh=%s, ma_trai_cay=%s where ma_loai=%s",
            (tenloai, xuatxu, ghichu, hinhanh,matraicay, maloai))
        conn.commit()
        cur.close()
        return redirect(url_for('chiTietLoai.chitiet'))
