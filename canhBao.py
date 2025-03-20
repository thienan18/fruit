from flask import Blueprint, request, jsonify, render_template, session
from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
from db import get_db_connection
import smtplib
import time
from email.mime.text import MIMEText
from threading import Thread
from db import get_db_connection

canhBao = Blueprint('canhBao', __name__)


@canhBao.route('/canhbao')
def canhbao():
    if 'loggedin' not in session:
        return redirect(url_for('login'))  # Nếu chưa đăng nhập, chuyển hướng về trang login
    
    conn = get_db_connection()  # Kết nối CSDL
    cur = conn.cursor()

    # Lấy danh sách hình ảnh có quả hỏng
    cur.execute("SELECT ma_hinh_anh, ngay_chup FROM dulieuhinhanh WHERE so_luong_hu_hong > 0")
    data_list = cur.fetchall()

    # Chèn vào bảng cảnh báo nếu chưa tồn tại
    for data in data_list:
        ma_hinh_anh = data[0]
        ngay_chup = data[1]

        # Kiểm tra cảnh báo đã tồn tại chưa
        cur.execute("SELECT 1 FROM canh_bao WHERE ma_hinh_anh = %s", (ma_hinh_anh,))
        existing_warning = cur.fetchone()

        if not existing_warning:
            cur.execute("""
                INSERT INTO canh_bao(ma_hinh_anh, ngay_phat_hien, trang_thai) 
                VALUES (%s, %s, %s)
            """, (ma_hinh_anh, ngay_chup, 'Chưa xử lý'))

    conn.commit()  # Lưu thay đổi

    # Lấy danh sách cảnh báo kèm thông tin hình ảnh
    cur.execute("""
        SELECT cb.ma_canh_bao, cb.ma_hinh_anh, dl.duong_dan_hinh_anh, cb.muc_do_canh_bao, 
               cb.noi_dung, cb.ngay_phat_hien, cb.trang_thai 
        FROM canh_bao cb 
        LEFT JOIN dulieuhinhanh dl ON cb.ma_hinh_anh = dl.ma_hinh_anh
    """)
    data = cur.fetchall()

    conn.close()

    # Xác định quyền để chọn template phù hợp
    ma_quyen = session.get('ma_quyen', '2')  # Mặc định '2' là user nếu không có quyền
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/canhBao.html", canhbao=data)



# API cập nhật trạng thái cảnh báo
@canhBao.route('/update_status', methods=['GET'])
def update_status():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    ma_canh_bao = request.args.get('id')
    if not ma_canh_bao:
        return jsonify({"error": "Thiếu mã cảnh báo"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Cập nhật trạng thái cảnh báo
    cursor.execute("UPDATE canh_bao SET trang_thai='Đã xử lý' WHERE ma_canh_bao=%s", (ma_canh_bao,))
    conn.commit()

    # Lấy thông tin tài khoản liên quan đến cảnh báo
    cursor.execute("""
        SELECT tk.ten_tai_khoan, tk.ma_tai_khoan FROM canh_bao cb
        JOIN taikhoan tk ON cb.ma_tai_khoan = tk.ma_tai_khoan
        WHERE cb.ma_canh_bao = %s
    """, (ma_canh_bao,))
    user_info = cursor.fetchone()

    conn.close()

    return jsonify({
        "message": "Trạng thái đã được cập nhật!",
        "tai_khoan": user_info
    })



def lay_danh_sach_canh_bao():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cb.*
        FROM canh_bao cb
        WHERE cb.trang_thai='Chưa xử lý'
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def gui_email():
    sender_email = "thienan180803@gmail.com"
    sender_password = "uxzombrqnspyzwwq"
    

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Lấy tất cả tài khoản từ CSDL
    cursor.execute("SELECT ten_tai_khoan FROM taikhoan")
    danh_sach_tai_khoan = cursor.fetchall()

    conn.close()

    while True:
        canh_bao_chua_xu_ly = lay_danh_sach_canh_bao()

        if not canh_bao_chua_xu_ly:
            print("Không có cảnh báo nào cần gửi.")
        else:
            # Chuẩn bị nội dung email
            noi_dung_email = ""
            for c in canh_bao_chua_xu_ly:
                noi_dung_email += f"{c['muc_do_canh_bao']}: {c['noi_dung']} (Phát hiện: {c['ngay_phat_hien']})\n"

            msg = MIMEText(f"Danh sách cảnh báo chưa xử lý:\n\n{noi_dung_email}")
            msg['Subject'] = "Cảnh báo trái cây hư hỏng"
            msg['From'] = sender_email

            for tai_khoan in danh_sach_tai_khoan:
                email_list = [tk['ten_tai_khoan'] for tk in danh_sach_tai_khoan]
                msg['To'] = ", ".join(email_list)

                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, email_list, msg.as_string())
                    server.quit()

                    print(f"Email đã gửi thành công đến {email_list}")
                except smtplib.SMTPAuthenticationError:
                    print("Lỗi xác thực SMTP. Kiểm tra lại mật khẩu ứng dụng Gmail.")
                except smtplib.SMTPException as e:
                    print(f"Lỗi gửi email: {e}")

            time.sleep(3600)  # 3 tiếng


# Chạy Flask và gửi email song song
def start_email_thread():
    email_thread = Thread(target=gui_email, daemon=True)
    email_thread.start()