# PRD StreakKeeper · Thử nghiệm TikTok trên macOS

Trạng thái dự án hiện tại: có brief và mockup giao diện. Ứng dụng desktop đang ở giai đoạn thiết kế. Phạm vi thử nghiệm trong PRD này cụ thể hóa định hướng dài hạn trong [project brief](StreakKeeper_Project.md).

## Vấn đề

Người dùng dễ quên nhắn cho bạn bè trên TikTok trong ngày và có thể mất streak. Việc gửi một tin nhắn ngắn mỗi ngày cũng tạo thêm thao tác lặp lại. Bản đầu phục vụ một người dùng trên máy Mac cá nhân, với một cuộc trò chuyện do người dùng chọn để thử trong vài ngày.

## Mục tiêu

- Gửi tin cho chat đã bật khi app chưa ghi nhận lần gửi thành công trong ngày.
- Bỏ qua lượt gửi khi app đã ghi nhận gửi thành công trong ngày.
- Cho người dùng kiểm soát người nhận, nội dung và thời điểm dừng tự động gửi.
- Kiểm chứng trên TikTok xem tin mặc định `.` có giúp duy trì streak qua các ngày thử hay không.

## Giải pháp

Người dùng đăng nhập TikTok Web trong hồ sơ Chrome riêng, chọn cuộc trò chuyện, chỉnh nội dung nếu cần và bật lịch gửi tự động. StreakKeeper chạy nền trên macOS và hiển thị kết quả trong lịch sử. Nội dung mặc định là `.` và có thể chỉnh trong app.

## Câu chuyện người dùng

1. Là chủ máy Mac, tôi muốn tự đăng nhập TikTok trong hồ sơ Chrome riêng để dùng phiên của mình với StreakKeeper.
2. Là chủ tài khoản, tôi muốn chọn thủ công cuộc trò chuyện và bật gửi riêng cho từng người để kiểm soát người nhận.
3. Là người gửi, tôi muốn dùng tin mặc định `.` hoặc chỉnh nội dung trong app để kiểm soát tin được gửi.
4. Là người dùng hằng ngày, tôi muốn app tự mở khi đăng nhập macOS và tiếp tục chạy khi đóng cửa sổ để lịch kiểm tra vẫn hoạt động.
5. Là người dùng laptop, tôi muốn app kiểm tra bù khi máy thức để xử lý lượt bị lỡ trong lúc ngủ.
6. Là người gửi, tôi muốn app dùng nhật ký trên máy để biết hôm nay app đã gửi cho chat nào.
7. Là người gửi, tôi muốn xem chat nào app đã gửi và chat nào chưa xác nhận được kết quả.
8. Là người gửi, tôi muốn có thể thử lại ở lượt sau nếu app chưa ghi nhận thành công.
9. Là người gửi, tôi muốn tắt gửi cho từng người hoặc tạm dừng toàn bộ từ thanh menu macOS để chặn các lượt gửi mới khi cần.
10. Là người dùng, tôi muốn app ghi nhớ trạng thái tạm dừng sau khi khởi động lại để việc gửi chỉ tiếp tục khi tôi chủ động bật lại.
11. Là chủ tài khoản, tôi muốn được báo một lần khi phiên hết hạn và để app tự tiếp tục ở lượt kiểm tra kế tiếp sau khi kết nối lại.
12. Là người thử nghiệm, tôi muốn xem kết quả từng lượt để đối chiếu với cuộc trò chuyện và streak hiển thị trên TikTok.
13. Là chủ tài khoản, tôi muốn thoát app để dừng tác vụ và có thể ngắt kết nối, xóa dữ liệu phiên riêng sau khi xác nhận.

## Phạm vi

- **Người dùng và nền tảng.** Một người dùng cá nhân, một tài khoản TikTok Web trên Mac. App cho phép bật hoặc tắt theo từng cuộc trò chuyện. Đợt thử ban đầu dùng một cuộc trò chuyện.
- **Lịch chạy.** Lượt đầu chạy khi có chat cần gửi và đã đến giờ bắt đầu nếu người dùng đặt giờ. Các lượt thử lại cách 15 phút. App dừng gửi khi đã gửi đủ và tiếp tục nếu người dùng chọn thêm chat chưa gửi hoặc khi sang ngày mới. Nếu Mac ngủ qua giờ chạy, app thực hiện lượt đến hạn khi máy thức. Ngày bắt đầu lúc 00:00 theo `Asia/Ho_Chi_Minh`, kể cả khi múi giờ hệ thống thay đổi.
- **Điều kiện gửi.** Chỉ gửi vào cuộc trò chuyện đã bật nếu app chưa xác nhận lần gửi nào hôm nay. Tin nhắn thủ công không ảnh hưởng đến quyết định này.
- **Thử lại.** Nếu kết quả gửi chưa rõ, lượt chạy kế tiếp có thể thử lại. Người dùng chấp nhận có thể nhận tin trùng trong trường hợp trước đó TikTok đã nhận tin nhưng app chưa xác nhận được.
- **Điều khiển.** Giữ danh sách đã chọn và trạng thái tạm dừng toàn bộ qua lần khởi động lại. Tạm dừng chặn lượt gửi mới. Khi phiên hết hạn, thông báo một lần và ngừng gửi cho đến khi kết nối lại. Nếu TikTok yêu cầu xác minh bảo mật, dừng tác vụ để người dùng xử lý trực tiếp.
- **Lịch sử.** Hiển thị thời điểm và kết quả lượt kiểm tra, gồm đã gửi, app đã gửi hôm nay, kết quả chưa xác nhận và lỗi cần xử lý.

## Ràng buộc

- Chrome đã cài trên Mac. Người dùng đăng nhập trực tiếp trên TikTok Web trong hồ sơ Chrome dành riêng cho StreakKeeper.
- Phiên đăng nhập và dữ liệu hoạt động của app được giữ trên máy. App không thu mật khẩu, không sao chép cookie từ hồ sơ Chrome cá nhân và không ghi thông tin xác thực hoặc nội dung tin nhắn vào lịch sử.
- Khả năng đọc và gửi phụ thuộc vào những gì TikTok Web cung cấp. Chỉ thử nghiệm gửi thật sau khi xác minh thao tác dự kiến được nền tảng cho phép.

## Ghi chú kỹ thuật

- Mỗi tài khoản chỉ có một lượt xử lý tại một thời điểm để lịch chạy thường kỳ và lượt kiểm tra bù không gửi chồng.
- Quyết định gửi sau khi máy thức dựa trên ngày hiện tại ở Việt Nam. Các ngày đã qua không phát sinh tin nhắn gửi bù.
- Kết quả gửi đã xác nhận được lưu theo tài khoản, cuộc trò chuyện và ngày Việt Nam qua các lần khởi động.

## Ngoài phạm vi

- Duolingo, Windows, Linux và phát hành bộ cài cho người khác.
- Tự tìm hoặc tự bật gửi cho tất cả bạn bè.
- Xác nhận thủ công hằng ngày, hỗ trợ nhiều tài khoản và đồng bộ đám mây.

## Câu hỏi mở cần kiểm chứng

- TikTok Web trên tài khoản thử có cho phép xác định đúng cuộc trò chuyện, người gửi và ngày của các loại tin nhắn cần xét không?
- TikTok Web và điều kiện sử dụng hiện hành có cho phép luồng đọc và gửi dự kiến không?
- Tin `.` có được TikTok tính vào streak không, và cần tương tác gì từ phía người nhận để phân biệt kết quả của app với các điều kiện khác của streak?

## Tiêu chí nghiệm thu thử nghiệm

- Trong vài ngày thử với một cuộc trò chuyện đã bật, app gửi đúng nội dung cho đúng người khi app chưa ghi nhận gửi trong ngày, rồi bỏ qua các lượt sau khi đã xác nhận gửi thành công.
- Tin nhắn thủ công và việc thiếu mốc thời gian trong lịch sử không chặn lượt gửi. Kết quả chưa xác nhận cho phép thử lại ở lượt sau.
- App tự chạy khi đăng nhập macOS, tiếp tục khi đóng cửa sổ và kiểm tra bù sau khi máy thức. Trạng thái tạm dừng được giữ khi mở lại, và Quit dừng tác vụ nền.
- Khi phiên hết hạn, app thông báo một lần và tiếp tục ở lượt kiểm tra đầu tiên sau khi kết nối lại.
- Đối chiếu trực tiếp trên TikTok qua các ngày thử để xác minh tin `.` góp phần duy trì streak. Ghi nhận tương tác của phía bên kia nếu điều đó ảnh hưởng đến kết quả.
