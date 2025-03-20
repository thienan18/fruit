from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from db import get_db_connection

taikhoan = Blueprint("taikhoan", __name__)

# 📌 Lấy danh sách tài khoản người dùng có tìm kiếm
@taikhoan.route('/taikhoan', methods=['GET', 'POST'])
def list_accounts():
    timkiem = request.args.get('timkiem', '')  # Lấy giá trị tìm kiếm từ request
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Nếu có tìm kiếm, thêm điều kiện vào câu lệnh SQL
    if timkiem:
        query = """
            SELECT nd.id, nd.ten_nguoi_dung, nd.dia_chi, nd.email, nd.so_dien_thoai, nd.chuc_vu,
                   tk.ten_tai_khoan, q.ten_quyen
            FROM ThongTinNguoiDung nd
            LEFT JOIN TaiKhoan tk ON nd.id = tk.id
            LEFT JOIN Quyen q ON tk.ma_quyen = q.ma_quyen
            WHERE nd.ten_nguoi_dung LIKE %s OR nd.email LIKE %s OR nd.so_dien_thoai LIKE %s 
                  OR tk.ten_tai_khoan LIKE %s OR q.ten_quyen LIKE %s
        """
        cursor.execute(query, tuple(["%" + timkiem + "%"] * 5))  # Tránh lỗi SQL Injection
    else:
        query = """
            SELECT nd.id, nd.ten_nguoi_dung, nd.dia_chi, nd.email, nd.so_dien_thoai, nd.chuc_vu,
                   tk.ten_tai_khoan, q.ten_quyen
            FROM ThongTinNguoiDung nd
            LEFT JOIN TaiKhoan tk ON nd.id = tk.id
            LEFT JOIN Quyen q ON tk.ma_quyen = q.ma_quyen
        """
        cursor.execute(query)

    users = cursor.fetchall()

    cursor.execute("SELECT ma_quyen, ten_quyen FROM Quyen")  # Lấy danh sách quyền để hiển thị
    danh_sach_quyen = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/taikhoan.html", users=users, danh_sach_quyen=danh_sach_quyen, timkiem=timkiem)


@taikhoan.route('/add_account', methods=['POST'])
def add_account():
    ten_nguoi_dung = request.form['ten_nguoi_dung']
    dia_chi = request.form.get('dia_chi', '')
    email = request.form['email']
    so_dien_thoai = request.form['so_dien_thoai']
    chuc_vu = request.form.get('chuc_vu', '')
    ten_tai_khoan = email 
    mat_khau = request.form['password']
    nhap_lai_mat_khau = request.form['confirm_password']
    ma_quyen = request.form['ma_quyen']

    if not all([ten_nguoi_dung, email, so_dien_thoai, ten_tai_khoan, mat_khau, nhap_lai_mat_khau, ma_quyen]):
        flash('Vui lòng nhập đầy đủ thông tin!', 'warning')
        return redirect(url_for('taikhoan.list_accounts'))

    if mat_khau != nhap_lai_mat_khau:
        flash('Mật khẩu không khớp, vui lòng nhập lại!', 'danger')
        return redirect(url_for('taikhoan.list_accounts'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT ma_quyen FROM Quyen WHERE ma_quyen = %s", (ma_quyen,))
    if not cursor.fetchone():
        flash('Quyền không hợp lệ!', 'danger')
        return redirect(url_for('taikhoan.list_accounts'))

    # 📌 Kiểm tra xem email đã tồn tại chưa
    cursor.execute("SELECT * FROM TaiKhoan WHERE ten_tai_khoan = %s", (ten_tai_khoan,))
    if cursor.fetchone():
        flash('Email này đã được sử dụng làm tài khoản!', 'danger')
        return redirect(url_for('taikhoan.list_accounts'))

    try:
        # 📌 Thêm thông tin người dùng
        cursor.execute("""
            INSERT INTO ThongTinNguoiDung (ten_nguoi_dung, dia_chi, email, so_dien_thoai, chuc_vu)
            VALUES (%s, %s, %s, %s, %s)
        """, (ten_nguoi_dung, dia_chi, email, so_dien_thoai, chuc_vu))
        conn.commit()

        cursor.execute("SELECT LAST_INSERT_ID() AS user_id")
        user_id = cursor.fetchone()['user_id']

        hashed_password = generate_password_hash(mat_khau)

        # 📌 Thêm tài khoản với email làm tên đăng nhập
        cursor.execute("""
            INSERT INTO TaiKhoan (ten_tai_khoan, mat_khau, ma_quyen, id)
            VALUES (%s, %s, %s, %s)
        """, (ten_tai_khoan, hashed_password, ma_quyen, user_id))
        conn.commit()

        flash('Đăng ký tài khoản thành công!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi khi đăng ký: {str(e)}', 'danger')

    conn.close()
    return redirect(url_for('taikhoan.list_accounts'))


# 📌 Xóa tài khoản
@taikhoan.route('/delete_account/<int:user_id>', methods=['GET'])
def delete_account(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM TaiKhoan WHERE id=%s", (user_id,))
        cursor.execute("DELETE FROM ThongTinNguoiDung WHERE id=%s", (user_id,))
        conn.commit()
        flash('Xóa tài khoản thành công!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi khi xóa tài khoản: {str(e)}', 'danger')

    conn.close()
    return redirect(url_for('taikhoan.list_accounts'))

# 📌 Cập nhật thông tin tài khoản người dùng
@taikhoan.route('/update_account/<int:user_id>', methods=['POST'])
def update_account(user_id):
    if request.method == 'POST':
        ten_nguoi_dung = request.form['ten_nguoi_dung']
        email = request.form['email']
        so_dien_thoai = request.form['so_dien_thoai']
        dia_chi = request.form.get('dia_chi', '')
        chuc_vu = request.form.get('chuc_vu', '')
        ma_quyen = request.form['ma_quyen']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Cập nhật dữ liệu vào database
        query = """
            UPDATE ThongTinNguoiDung
            SET ten_nguoi_dung = %s, email = %s, so_dien_thoai = %s, dia_chi = %s, chuc_vu = %s
            WHERE id = %s
        """
        cursor.execute(query, (ten_nguoi_dung, email, so_dien_thoai, dia_chi, chuc_vu, user_id))

        query_tk = """
            UPDATE TaiKhoan
            SET ma_quyen = %s
            WHERE id = %s
        """
        cursor.execute(query_tk, (ma_quyen, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Cập nhật tài khoản thành công!", "success")
        return redirect(url_for('taikhoan.list_accounts'))
