from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
import cv2
import smtplib
from flask import redirect
from ultralytics import YOLO
import mysql.connector
from khayHang import khayhang
from traiCay import traiCay
from chiTietLoai import chiTietLoai
from nhanDien import nhanDien
from duLieuHinhAnh import duLieuHinhAnh
from thongKe import thongKe
from taikhoan import taikhoan
from canhBao import canhBao
from canhBao import gui_email  # Import hàm gửi email
from db import get_db_connection  # Import kết nối từ db.py

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import random
from threading import Thread

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



app = Flask(__name__)
app.register_blueprint(khayhang)
app.register_blueprint(traiCay)
app.register_blueprint(chiTietLoai)
app.register_blueprint(nhanDien)
app.register_blueprint(duLieuHinhAnh)
app.register_blueprint(thongKe)
app.register_blueprint(taikhoan)
app.register_blueprint(canhBao)


app.secret_key = 'your_secret_key'
def get_fruits():
    conn = get_db_connection()  # Tạo kết nối mới
    cur = conn.cursor()
    cur.execute("select * from traicay")
    data = cur.fetchall()
    cur.close()
    return data

@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/')
def index():
    # Nếu chưa đăng nhập, về trang index
    if 'loggedin' not in session or 'ma_quyen' not in session:
        return redirect(url_for('home'))

    ma_quyen = session.get('ma_quyen')

    # Đảm bảo ma_quyen là chuỗi
    if ma_quyen == '0':  # Admin
        return redirect(url_for('admin_home'))
    elif ma_quyen == '1':  # Manager
        return redirect(url_for('manager_home'))
    else:  # Nhân viên (User)
        return redirect(url_for('user_home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ten_tai_khoan = request.form.get('username')
        mat_khau = request.form.get('password')

        if not ten_tai_khoan or not mat_khau:
            flash('Vui lòng nhập đầy đủ thông tin!', 'warning')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)

            # Truy vấn tài khoản từ bảng TaiKhoan
            cur.execute("""
                SELECT ma_tai_khoan, ten_tai_khoan, mat_khau, ma_quyen, id
                FROM TaiKhoan
                WHERE ten_tai_khoan = %s
            """, (ten_tai_khoan,))
            user = cur.fetchone()

            if user and check_password_hash(user['mat_khau'], mat_khau):
                # Lấy thông tin tên người dùng từ bảng ThongTinNguoiDung
                cur.execute("SELECT ten_nguoi_dung FROM ThongTinNguoiDung WHERE id = %s", (user['id'],))
                user_info = cur.fetchone()

                session['loggedin'] = True
                session['ma_tai_khoan'] = user['ma_tai_khoan']
                session['ten_tai_khoan'] = user['ten_tai_khoan']
                session['ma_quyen'] = user['ma_quyen']
                session['ten_nguoi_dung'] = user_info['ten_nguoi_dung'] if user_info else user['ten_tai_khoan']

                flash(f'Chào mừng {session["ten_nguoi_dung"]}!', 'success')

                cur.close()
                conn.close()

                return redirect(
                    url_for('admin_home') if user['ma_quyen'] == '0' else 
                    url_for('manager_home') if user['ma_quyen'] == '1' else 
                    url_for('user_home')
                )


            flash('Tên tài khoản hoặc mật khẩu không đúng!', 'danger')

        except Exception as e:
            flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        finally:
            cur.close()
            conn.close()

    return render_template('login.html')

@app.route('/nguoidung')
def nguoidung():
    if 'loggedin' not in session:
        return redirect(url_for('login'))  # Nếu chưa đăng nhập, chuyển hướng về trang login

    # Nếu đã đăng nhập, tiếp tục xử lý dữ liệu
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM thongtinnguoidung WHERE id = %s", (session['ma_tai_khoan'],))
    user = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('nguoidung.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/dangky', methods=['GET', 'POST'])
def dangky():
    if request.method == 'POST':
        # Lấy thông tin từ form
        ten_nguoi_dung = request.form.get('ten_nguoi_dung')
        dia_chi = request.form.get('dia_chi')
        email = request.form.get('email')
        so_dien_thoai = request.form.get('so_dien_thoai')
        chuc_vu = request.form.get('chuc_vu')
        mat_khau = request.form.get('password')
        nhap_lai_mat_khau = request.form.get('confirm_password')  # Lấy giá trị nhập lại mật khẩu

        # Kiểm tra dữ liệu nhập vào
        if not ten_nguoi_dung or not email or not so_dien_thoai or not mat_khau or not nhap_lai_mat_khau:
            flash('Vui lòng nhập đầy đủ thông tin!', 'warning')
            return redirect(url_for('dangky'))

            # Kiểm tra mật khẩu và mật khẩu nhập lại có khớp nhau không
        if mat_khau != nhap_lai_mat_khau:
            flash('Mật khẩu không khớp, vui lòng nhập lại!', 'danger')
            return redirect(url_for('dangky'))

        conn = get_db_connection()
        cur = conn.cursor()

        # Kiểm tra email đã tồn tại chưa
        cur.execute("SELECT * FROM TaiKhoan WHERE ten_tai_khoan = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash('Tài khoản đã tồn tại!', 'danger')
        else:
            try:
                # Thêm thông tin vào bảng ThongTinNguoiDung
                cur.execute("""
                    INSERT INTO ThongTinNguoiDung (ten_nguoi_dung, dia_chi, email, so_dien_thoai, chuc_vu)
                    VALUES (%s, %s, %s, %s, %s)
                """, (ten_nguoi_dung, dia_chi, email, so_dien_thoai, chuc_vu))
                conn.commit()

                # Lấy ID vừa tạo
                cur.execute("SELECT LAST_INSERT_ID()")
                user_id = cur.fetchone()[0]

                # Mã hóa mật khẩu trước khi lưu
                hashed_password = generate_password_hash(nhap_lai_mat_khau)  # Sử dụng mật khẩu đã xác nhận

                # Thêm tài khoản vào bảng TaiKhoan
                cur.execute("""
                    INSERT INTO TaiKhoan (ten_tai_khoan, mat_khau, ma_quyen, id)
                    VALUES (%s, %s, %s, %s)
                """, (email, hashed_password, '2', user_id))
                conn.commit()

                flash('Đăng ký thành công! Bạn có thể đăng nhập.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Lỗi đăng ký: {str(e)}', 'danger')

        cur.close()
        conn.close()

    return render_template('dangky.html')


@app.route('/admin')
def admin_home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    traicay = get_fruits()
    return render_template('admin/index.html', traicay=traicay) 

@app.route('/manager')
def manager_home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    traicay = get_fruits()
    return render_template('manager/index.html', traicay=traicay)


@app.route('/user')
def user_home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    traicay = get_fruits()
    return render_template('user/index.html', traicay=traicay) 



# -------------------------Quen mat khau----------------------------------
otp_store = {}


# Gửi OTP đến email từ Database
@app.route('/quenmk', methods=['GET', 'POST'])
def quenmk():
    email = ""
    phone = ""
    otp_sent = False

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        otp = request.form.get('otp')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Kiểm tra email và số điện thoại trong database
        cur.execute("SELECT * FROM ThongTinNguoiDung WHERE email = %s AND so_dien_thoai = %s", (email, phone))
        user = cur.fetchone()

        if not user:
            flash('Email hoặc số điện thoại không đúng!', 'danger')
            return render_template('quenmk.html', email=email, phone=phone, otp_sent=False)

        # Nếu OTP đã nhập, kiểm tra tính hợp lệ
        if otp:
            if otp_store.get(email) == otp:
                flash('OTP hợp lệ! Hãy đặt lại mật khẩu mới.', 'success')
                return render_template('reset_password.html', email=email)
            else:
                flash('Mã OTP không đúng!', 'danger')

        # Nếu chưa có OTP, tạo và gửi OTP mới
        else:
            otp_code = str(random.randint(100000, 999999))
            otp_store[email] = otp_code
            otp_sent = True

            sender_email = "thienan180803@gmail.com"
            sender_password = "uxzombrqnspyzwwq"

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = "Mã OTP để đặt lại mật khẩu"

            body = f"Mã OTP của bạn là: {otp_code}. Vui lòng nhập mã này để đặt lại mật khẩu."
            msg.attach(MIMEText(body, 'plain'))

            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, msg.as_string())
                server.quit()

                flash('Mã OTP đã được gửi đến email của bạn!', 'success')

            except Exception as e:
                flash(f'Lỗi khi gửi email: {str(e)}', 'danger')

    return render_template('quenmk.html', email=email, phone=phone, otp_sent=otp_sent)


@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    new_password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Kiểm tra nếu email chưa xác minh OTP thì không cho đặt lại mật khẩu
    if email not in otp_store:
        flash('Bạn chưa xác minh OTP!', 'danger')
        return redirect(url_for('quenmk'))

    # Kiểm tra nếu hai mật khẩu không trùng nhau
    if new_password != confirm_password:
        flash('Mật khẩu nhập lại không khớp!', 'danger')
        return render_template('reset_password.html', email=email)

    try:
        # Kết nối đến database
        conn = get_db_connection()
        cur = conn.cursor()

        # Băm mật khẩu mới
        hashed_password = generate_password_hash(new_password)

        # Cập nhật mật khẩu trong database
        cur.execute("UPDATE TaiKhoan SET mat_khau = %s WHERE ten_tai_khoan = %s", (hashed_password, email))
        conn.commit()

        flash('Mật khẩu đặt lại thành công! Bạn có thể đăng nhập.', 'success')

        # Xóa OTP sau khi đặt lại mật khẩu
        del otp_store[email]

        return redirect(url_for('login'))

    except Exception as e:
        flash(f'Lỗi hệ thống: {str(e)}', 'danger')
        return render_template('reset_password.html', email=email)

    finally:
        cur.close()
        conn.close()


@app.route('/doimk', methods=['POST'])
def doimk():
    if 'ten_tai_khoan' not in session:
        flash("Bạn cần đăng nhập trước!", "danger")
        return redirect(url_for('login'))

    ten_tai_khoan = session['ten_tai_khoan']
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Lấy thông tin tài khoản
    cur.execute("SELECT * FROM TaiKhoan WHERE ten_tai_khoan = %s", (ten_tai_khoan,))
    user = cur.fetchone()

    if not user:
        flash("Không tìm thấy tài khoản!", "danger")
        return render_template('nguoidung.html', show_modal=True)

    # Kiểm tra mật khẩu cũ
    if not check_password_hash(user["mat_khau"], old_password):
        flash("Mật khẩu cũ không đúng!", "danger")
        return render_template('nguoidung.html', show_modal=True)

    # Kiểm tra mật khẩu mới có khớp không
    if new_password != confirm_password:
        flash("Mật khẩu mới không khớp!", "danger")
        return render_template('nguoidung.html', show_modal=True)

    # Cập nhật mật khẩu mới
    hashed_password = generate_password_hash(new_password)
    cur.execute("UPDATE TaiKhoan SET mat_khau = %s WHERE ten_tai_khoan = %s", (hashed_password, ten_tai_khoan))
    conn.commit()
    conn.close()

    flash("Đổi mật khẩu thành công!", "success")
    return redirect(url_for('nguoidung'))

if __name__ == "__main__":
    email_thread = Thread(target=gui_email, daemon=True)
    email_thread.start()  # 🚀 Bắt đầu gửi email mỗi 1 tiếng
    app.run(debug=True, port=5001)
