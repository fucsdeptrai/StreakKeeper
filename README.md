# StreakKeeper

StreakKeeper là ứng dụng macOS chạy local để theo dõi streak. App đọc hộp thư TikTok Web và có thể gửi theo yêu cầu hoặc tự động theo lịch. Tự khởi động khi đăng nhập macOS chưa được tích hợp.

## Đọc hộp thư TikTok Web

```sh
uv run streakkeeper
```

Lần đầu, vào **Settings → Đăng nhập TikTok cho chế độ nền** và đăng nhập tài khoản TikTok bạn muốn dùng. Khi hộp thư mở được, bấm **Kiểm tra đăng nhập** trong StreakKeeper. App đóng cửa sổ thiết lập rồi xác nhận phiên bằng Chrome headless. Sau đó mới mở hộp thư và chọn chat giữ chuỗi. Phiên được Chrome giữ trong `headless-chrome` thuộc thư mục dữ liệu của StreakKeeper. Các lựa chọn giữ chuỗi được lưu theo tài khoản đã xác nhận.

Bấm **Mở hộp thư** để đọc danh sách ở nền. Nhấp đúp vào tên chat để xem số tin và mốc giờ trên Dashboard. Bạn có thể chọn **Giữ chuỗi**, đặt **Tin nhắn chung** hoặc sửa **Tin nhắn riêng**. Chỉ chat đã chọn đủ điều kiện gửi.

Bấm **Chạy giữ chuỗi** để gửi cho các chat đã chọn nếu app chưa ghi nhận gửi thành công hôm nay, tính theo giờ Việt Nam. Tin bạn gửi thủ công không chặn lượt gửi. Nếu kết quả chưa rõ, lần bấm tiếp theo có thể thử lại. Cả đọc hộp thư và chạy giữ chuỗi dùng cùng hồ sơ riêng ở chế độ headless. Xem kết quả trong **Activity Log**.

Trong **Settings → Lịch gửi tự động**, bật tự động giữ chuỗi nếu bạn muốn app gửi khi đang chạy. Mặc định, lượt đầu bắt đầu khi có chat cần gửi. Có thể đặt giờ bắt đầu mỗi ngày theo giờ Việt Nam. Các lượt sau cách 15 phút và chỉ xử lý chat còn thiếu. Khi gửi đủ, app chờ ngày mới hoặc một chat mới được chọn. Đóng xuống thanh menu vẫn giữ lịch chạy. Nút **Tạm dừng** dừng lượt tự động.

## Chạy bản mô phỏng trên macOS

```sh
uv run streakkeeper --demo
```

Thêm một cuộc trò chuyện mô phỏng, đánh dấu **Bật gửi**, rồi chọn **Kiểm tra ngay**. Với trạng thái **Chưa có tin đi**, lần kiểm tra đầu ghi **Đã gửi** với nội dung mặc định `.`. Lần kiểm tra tiếp theo trong cùng ngày ghi **Đã có tin đi**. Bạn có thể đổi trạng thái mô phỏng hoặc bật **Mô phỏng kết quả gửi chưa rõ** để thử các nhánh khác.

Dữ liệu mô phỏng mặc định nằm trong `~/Library/Application Support/StreakKeeper`. Có thể dùng `--data-dir` để chạy với thư mục dữ liệu riêng.

Kiểm thử quy tắc gửi bằng Python 3.11 trở lên, không cần PySide6 hoặc tài khoản TikTok.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Bắt đầu đọc

1. [PRD thử nghiệm TikTok trên macOS](PRD.md) mô tả phạm vi bản đầu và tiêu chí nghiệm thu.
2. [Kế hoạch phát hành macOS](DISTRIBUTION.md) mô tả cách đóng gói và các điều kiện trước khi đưa app cho người dùng.
3. [Project brief](StreakKeeper_Project.md) mô tả phạm vi MVP, kiến trúc, mô hình dữ liệu dự kiến và tiêu chí nghiệm thu. Cấu trúc thư mục ở mục 8 là đề xuất triển khai.
4. [Hướng dẫn thiết kế](stitch_streakkeeper_desktop_app/kinetic_utilitarianism/DESIGN.md) mô tả màu sắc, kiểu chữ, bố cục và thành phần giao diện.
5. Dùng bảng dưới đây để tìm màn hình cần xem. Mở HTML trong trình duyệt để xem mockup hoặc dùng ảnh chụp để đối chiếu bố cục.

## Mockup giao diện

| Màn hình | HTML | Ảnh chụp |
| --- | --- | --- |
| Dashboard | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_dashboard/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_dashboard/screen.png) |
| TikTok Friends | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_tiktok_friends/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_tiktok_friends/screen.png) |
| Duolingo | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_duolingo/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_duolingo/screen.png) |
| Activity Log | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_activity_log/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_activity_log/screen.png) |
| Settings | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_settings/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_settings/screen.png) |
| System Tray Companion | [code.html](stitch_streakkeeper_desktop_app/streakkeeper_system_tray_companion/code.html) | [screen.png](stitch_streakkeeper_desktop_app/streakkeeper_system_tray_companion/screen.png) |
