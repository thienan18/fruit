from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
from flask import redirect
from flask import Blueprint
from db import get_db_connection  # Import kết nối từ db.py

duLieuHinhAnh = Blueprint("duLieuHinhAnh",__name__)

@duLieuHinhAnh.route('/dulieu', methods=['GET', 'POST'])
def dulieu():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    timkiem = request.args.get('timkiem')
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()

    if timkiem:
        cur.execute(
            "SELECT * FROM dulieuhinhanh dl LEFT JOIN khayhang kh on dl.ma_khay_hang = kh.ma_khay_hang WHERE ma_hinh_anh LIKE %s OR duong_dan_hinh_anh LIKE %s OR ngay_chup LIKE %s OR ma_khay_hang LIKE %s OR so_luong_hu_hong LIKE %s ",
            ("%" + timkiem + "%","%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%", "%" + timkiem + "%")
        )
    else:
        cur.execute("SELECT * FROM dulieuhinhanh dl LEFT JOIN khayhang kh on dl.ma_khay_hang = kh.ma_khay_hang")

    data1 = cur.fetchall()

    cur.execute("SELECT * FROM khayhang")
    data2 = cur.fetchall()

    cur.close()

    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/duLieuHinhAnh.html", dulieuhinhanh=data1, khayhang=data2, timkiem=timkiem)


@duLieuHinhAnh.route('/delete2/<string:mahinhanh>', methods=['GET'])
def delete2(mahinhanh):
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute("DELETE FROM dulieuhinhanh WHERE ma_hinh_anh=%s", (mahinhanh,))
        conn.commit()  # Đảm bảo MySQL cập nhật dữ liệu
        cur.close()
        return redirect(url_for('duLieuHinhAnh.dulieu'))


@duLieuHinhAnh.route('/update2',methods=['POST','GET'])
def update2():
    if request.method == 'POST':
        mahinhanh = request.form['mahinhanh']
        duongdan = request.form['duongdan']
        ngaychup = request.form['ngaychup']
        soluong = request.form['soluong']
        makhay = request.form['makhay']
        conn = get_db_connection()  # Tạo kết nối mới
        cur = conn.cursor()
        cur.execute(
            "update dulieuhinhanh set ma_hinh_anh=%s, duong_dan_hinh_anh=%s, ngay_chup=%s, ma_khay_hang=%s , so_luong_hu_hong=%s where ma_hinh_anh=%s",
            (mahinhanh,duongdan,ngaychup,makhay,soluong,mahinhanh))
        conn.commit()
        cur.close()
        return redirect(url_for('duLieuHinhAnh.dulieu'))
