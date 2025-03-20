from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
from flask import redirect
from flask import Blueprint
from flask import flash
import mysql
from db import get_db_connection  # Import kết nối từ db.py
traiCay = Blueprint("traiCay",__name__)

@traiCay.route('/traicay')
def traicay():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    timkiem = request.args.get('timkiem')
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()
    if timkiem:
        cur.execute(
            "SELECT * FROM traicay WHERE ten_trai_cay LIKE %s OR ma_trai_cay LIKE %s OR  ghi_chu LIKE %s",
            ( "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%")
        )
    else:
        cur.execute("SELECT * FROM traicay")

    data = cur.fetchall()
    cur.close()
    
    # Xác định quyền để chọn template phù hợp
    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/traiCay.html", traicay=data)



@traiCay.route('/update1',methods=['POST','GET'])
def update1():
    if request.method == 'POST':
        matraicay = request.form['matraicay']
        tentraicay = request.form['tentraicay']
        ghichu = request.form['ghichu']
        hinhanh = request.form['hinhanh']
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute(
            "update traicay set ma_trai_cay=%s, ten_trai_cay=%s, ghi_chu=%s, hinh_anh=%s where ma_trai_cay=%s",
            (matraicay,tentraicay,ghichu,hinhanh,matraicay))
        conn.commit()
        cur.close()
        return redirect(url_for('traiCay.traicay'))

@traiCay.route('/insert1',methods=['POST'])
def insert1():
    if request.method == "POST":
        tentraicay = request.form['tentraicay']
        ghichu = request.form['ghichu']
        hinhanh = request.form['hinhanh']
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute("insert into traicay (ten_trai_cay,ghi_chu,hinh_anh) values (%s,%s,%s)",(tentraicay,ghichu,hinhanh))
        conn.commit()
        cur.close()
        return redirect(url_for('traiCay.traicay'))


@traiCay.route('/delete1/<string:matraicay>', methods=['GET'])
def delete1(matraicay):
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM traicay WHERE ma_trai_cay=%s", (matraicay,))
        conn.commit()  # Đảm bảo MySQL cập nhật dữ liệu
        flash("Xóa thành công!", "success")  # Hiển thị thông báo thành công
    except mysql.connector.IntegrityError:
        conn.rollback()  # Hoàn tác nếu có lỗi
        flash("Không thể xóa! Trái cây này đang được sử dụng ở bảng khác.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('traiCay.traicay'))