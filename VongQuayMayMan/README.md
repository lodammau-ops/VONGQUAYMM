# Vòng quay may mắn

Ứng dụng gồm trang HTML/CSS/JavaScript tĩnh và một API Flask chạy trên máy Windows. Khách nhập số và sang màn vòng quay trước; vòng xoay chậm, bóng đèn lấp lánh trong lúc chờ. Chỉ khi khách bấm **Quay ngay**, backend mới kiểm tra trùng, chọn giải và ghi số vào `so_dien_thoai.txt`; sau khi backend xác nhận, vòng chạy hiệu ứng kết quả và dừng đúng giải.

## Lưu ý trước khi tổ chức thật

- File TXT chỉ chứa số điện thoại đã chuẩn hóa; kết quả giải không được lưu. Nếu máy chủ đã ghi số nhưng phản hồi bị mất trên đường truyền, khách sẽ không quay thêm được nhưng trình duyệt có thể không biết giải đã nhận. Nhân viên cần đối chiếu trực tiếp khi gặp trường hợp này. Khôi phục tự động kết quả cũ cần lưu thêm mã giải/lượt.
- Backend dùng khóa tiến trình và file khóa nội bộ `so_dien_thoai.txt.lock` khi kiểm tra/cập nhật TXT, để các tiến trình trên cùng máy cùng kiểm tra danh sách đã lưu. Danh sách số vẫn chỉ nằm trong `so_dien_thoai.txt`. Không mở file TXT để chỉnh sửa khi chương trình đang chạy.
- Số minh họa `0912345678` bị từ chối ở cả giao diện lẫn backend. Điều này chỉ chặn đúng số mẫu; nếu cần xác nhận số khác thuộc về khách nào thì phải tích hợp OTP hoặc phương thức xác minh khác.
- Ô nhập nhận đúng 10 chữ số, bắt đầu bằng `0`; backend cũng từ chối chữ, dấu cách, định dạng quốc tế hoặc số chưa đủ 10 chữ số. Thông báo nhập sai chỉ hiện ở bước nhập số, không đưa quy tắc này lên vòng quay.
- TXT không có giao dịch đa máy chủ hay sao lưu tự động. Hạn chế quyền truy cập Windows, sao chép sao lưu định kỳ ra nơi độc lập và thử khôi phục trước khi chạy chính thức. Mất/hỏng máy hoặc file có thể làm mất dữ liệu; không nên xem TXT là phương án lưu trữ cấp cao.
- Số điện thoại là dữ liệu cá nhân. Hãy thông báo mục đích sử dụng, thời hạn lưu, đầu mối liên hệ và xác nhận yêu cầu pháp lý trước khi thu thập. Không đưa file TXT lên GitHub.
- Dịch vụ HTTPS/tunnel đưa máy tính cá nhân ra Internet, phụ thuộc máy, điện, mạng và tunnel luôn hoạt động. Dùng domain/tunnel ổn định, bảo vệ tài khoản Cloudflare và máy tính. Quick Tunnel có URL thay đổi, chỉ phù hợp thử nghiệm.

## 1. Cài đặt trên Windows

Mở PowerShell tại `D:\VongQuayMayMan`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường ảo, dùng lệnh dưới đây cho cửa sổ hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Chạy backend để kiểm tra

Trong cùng cửa sổ PowerShell đã kích hoạt môi trường:

```powershell
$env:ALLOWED_ORIGINS = "http://127.0.0.1:8080"
python .\server.py
```

Giữ cửa sổ này mở. Waitress lắng nghe trên `127.0.0.1:5000`; không bật Flask debug server.

Mở cửa sổ PowerShell thứ hai, vào thư mục dự án, chạy máy chủ tĩnh:

```powershell
Set-Location D:\VongQuayMayMan
py -3 -m http.server 8080 --bind 127.0.0.1
```

Trong `app.js`, đặt `API_BASE_URL` thành:

```javascript
const API_BASE_URL = "http://127.0.0.1:5000";
```

Mở `http://127.0.0.1:8080` trên máy tính để kiểm tra. Thử số mới, sau đó nhập lại cùng số (kể cả cách viết có dấu cách hoặc `+84`). Số đã quay sẽ nhận thông báo trùng; `so_dien_thoai.txt` được tạo cạnh `server.py`. Đóng hai máy chủ bằng `Ctrl+C`.

Chạy kiểm thử tự động:

```powershell
python -m unittest -v
```

## 3. Đưa frontend lên GitHub Pages

1. Tạo repository GitHub mới và đưa các file frontend `index.html`, `styles.css`, `app.js` lên đó. Không đưa `so_dien_thoai.txt`, `server.py` hoặc thông tin khách hàng lên GitHub.
2. Trong repository, mở **Settings → Pages**, chọn nhánh triển khai và thư mục gốc, rồi lưu.
3. URL trang sẽ có dạng `https://TEN_TAI_KHOAN.github.io/TEN_REPOSITORY/`.
4. Không cấu hình API thành `localhost`: điện thoại của khách hiểu `localhost` là chính điện thoại của họ.

## 4. HTTPS ổn định từ GitHub Pages tới máy tại siêu thị

Để có API URL ổn định, cần một domain đã được cấu hình DNS qua Cloudflare và một Cloudflare Tunnel đã đăng nhập/tạo. Tunnel không yêu cầu mở cổng inbound trên router; chi phí domain có thể phát sinh tùy domain/nhà đăng ký. Không tự mua dịch vụ nếu chưa được duyệt.

1. Cài `cloudflared` bằng Windows Package Manager nếu máy có `winget`:

   ```powershell
   winget install --id Cloudflare.cloudflared -e
   ```

2. Trong PowerShell, đăng nhập Cloudflare, tạo named tunnel và trỏ hostname API:

   ```powershell
   cloudflared tunnel login
   cloudflared tunnel create vong-quay-sieu-thi
   cloudflared tunnel route dns vong-quay-sieu-thi api.tenmiencuaban.vn
   ```

   Thay `api.tenmiencuaban.vn` bằng hostname thuộc domain của bạn. Lưu lại Tunnel UUID được lệnh `create` in ra.

3. Tạo file `%USERPROFILE%\.cloudflared\config.yml` (thay UUID và tên tài khoản Windows):

   ```yaml
   tunnel: UUID-CUA-TUNNEL
   credentials-file: C:\Users\TEN_WINDOWS\.cloudflared\UUID-CUA-TUNNEL.json
   ingress:
     - hostname: api.tenmiencuaban.vn
       service: http://127.0.0.1:5000
     - service: http_status:404
   ```

4. Đặt biến CORS để chỉ cho phép origin GitHub Pages. Với URL project pages, origin chỉ gồm scheme và hostname, không gồm đường dẫn repository:

   ```powershell
   $env:ALLOWED_ORIGINS = "https://TEN_TAI_KHOAN.github.io"
   ```

5. Trong `app.js`, đặt API URL HTTPS thật:

   ```javascript
   const API_BASE_URL = "https://api.tenmiencuaban.vn";
   ```

   Đưa `index.html`, `styles.css`, `app.js` đã cập nhật lên GitHub Pages.

6. Trong hai cửa sổ PowerShell riêng, chạy backend và tunnel:

   ```powershell
   Set-Location D:\VongQuayMayMan
   .\.venv\Scripts\Activate.ps1
   $env:ALLOWED_ORIGINS = "https://TEN_TAI_KHOAN.github.io"
   python .\server.py
   ```

   ```powershell
   cloudflared tunnel run vong-quay-sieu-thi
   ```

   Cả hai cửa sổ, máy tính, Internet và nguồn điện phải hoạt động trong suốt chương trình. Nếu Windows khởi động lại hoặc tunnel dừng, khách không thể quay. Cần người vận hành kiểm tra lại hai tiến trình và trang trước khi tiếp tục.

Trước khi mở cho khách, kiểm tra từ điện thoại dùng mạng di động (không cùng Wi-Fi) rằng GitHub Pages tải được, API báo trạng thái và lượt quay được lưu. Có thể kiểm tra API health trên máy chủ tại `https://api.tenmiencuaban.vn/api/health`; kết quả mong đợi là `{"status":"ok"}`.

## 5. Tạo mã QR và checklist

1. Sao chép URL GitHub Pages đầy đủ của trang chương trình.
2. Mở URL đó trên Chrome hoặc Edge máy tính, chọn chức năng tạo mã QR cho trang hiện tại trong menu Chia sẻ/menu trang, rồi lưu ảnh QR. Kiểm tra QR thực sự trỏ đúng URL GitHub Pages.
3. Bảo đảm QR không trỏ tới trang quản trị hoặc URL `localhost`.
4. Kiểm tra xác suất backend giữ nguyên 10% / 30% / 30% / 30%; frontend chỉ hiển thị giải API trả về.
5. Thử một số mới, thử lại số đó, thử hai yêu cầu đồng thời, khởi động lại backend rồi xác nhận số cũ vẫn bị từ chối.
6. Tạo và thử khôi phục bản sao `so_dien_thoai.txt`; không sao chép file vào repository GitHub.
7. Hướng dẫn nhân viên xử lý tình huống mạng chập chờn: không thử số mới để “lấy lại” lượt; giữ nguyên số và kiểm tra bản ghi trước khi hỗ trợ khách.
