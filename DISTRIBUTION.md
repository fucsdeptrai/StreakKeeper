# Kế hoạch phát hành StreakKeeper trên macOS

## Định dạng phát hành

Phát hành **StreakKeeper.app trong một tệp DMG** cho macOS Apple Silicon trước. App dùng giao diện Qt, biểu tượng thanh menu macOS và Chrome trên cùng máy. Docker phù hợp cho các bài test phần xử lý độc lập nếu sau này cần môi trường CI dùng chung.

## Bản cài thử 0.1.0

Tệp `dist/StreakKeeper-0.1.0-macos-arm64.dmg` chứa `StreakKeeper.app` và lối tắt đến Applications. Bản này đã được thử trên macOS 26.5 Apple Silicon. App dùng Google Chrome cài trên máy và tự mang theo Python cùng các thư viện của nó.

Chọn **Thoát** trong bản dev trước khi mở bản cài để giải phóng thư mục dữ liệu. Khi mở bằng cùng tài khoản macOS, bản cài dùng lại cài đặt và hồ sơ TikTok tại `~/Library/Application Support/StreakKeeper`.

Gói thử có chữ ký ad hoc. Phân phối qua Gatekeeper cần Developer ID Application, Hardened Runtime và notarization.

## Các mốc

1. **Chạy bản mô phỏng local.** Kiểm tra khởi động, thêm người nhận, lịch sử, tạm dừng và thoát. Tạo bản `.app` bằng PyInstaller trên máy Mac đích để kiểm tra mở bằng Finder và hoạt động ngoài thư mục repo.
2. **Hoàn thiện tích hợp TikTok cho bản thử kín.** Dùng hồ sơ Chrome riêng ở chế độ headless, lưu người nhận theo ID và cho người dùng bật gửi riêng từng người. Xác minh tài khoản gửi và ngày gửi trước mọi quyết định. Khi dữ liệu thiếu hoặc TikTok yêu cầu đăng nhập/xác minh lại, dừng gửi. Xác minh thao tác tự động dự kiến được TikTok cho phép trước khi bật gửi định kỳ trên tài khoản thật.
3. **Chạy thử trên một máy sạch.** Kiểm tra cài đặt không cần Python, quyền thông báo, đăng nhập Chrome, ngủ/thức, tự mở khi đăng nhập, đóng cửa sổ, Quit và gỡ cài đặt. Dùng người nhận thử đã đồng ý. Đối chiếu việc bỏ qua tin đã gửi và khả năng duy trì streak qua nhiều ngày.
4. **Ký và phát hành thử kín.** Dùng Developer ID Application, Hardened Runtime và Apple Notary Service. Đính vé xác nhận lên gói phát hành và xác minh bằng Gatekeeper. Phát hành DMG kèm phiên bản và checksum, rồi nhận phản hồi từ nhóm thử nhỏ. [Hướng dẫn của Apple](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution/)
5. **Mở rộng khi có nhu cầu.** Chốt phiên bản macOS tối thiểu theo máy đã kiểm thử. Nếu có người dùng Intel, kiểm tra build và dependency trên Intel trước khi công bố hỗ trợ.

## Điều kiện để đưa cho người dùng

- Bản dev đã thử đọc và tự động gửi TikTok. Kiểm thử trên một máy sạch cần xác nhận lại việc thiết lập phiên, đọc hộp thư, gửi định kỳ và hành vi sau khi máy thức.
- Tài khoản Apple Developer và chứng chỉ Developer ID cần có trước bước ký công khai. Thông tin xác thực ký được giữ ngoài repo.
- Phiên Chrome và lịch sử lưu local. Bản phân phối chỉ chứa mã và tài nguyên cài đặt.
