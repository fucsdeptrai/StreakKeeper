import argparse
from datetime import datetime
import fcntl
from pathlib import Path
import subprocess
import sys
from threading import Event
import time

from PySide6.QtCore import QThread, Qt, QTime, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QProgressBar, QPushButton, QStackedWidget, QStyle, QSystemTrayIcon, QTableWidget, QTableWidgetItem, QTimeEdit,
    QVBoxLayout, QWidget,
)

from .core import DemoMessages, Status, Store, VIETNAM, check
from .streak_browser import (
    HeadlessMessages, PlaywrightError, active_login_pid, chrome_session, close_login_chrome, open_inbox,
    login_required, open_login_chrome, read_inbox_snapshot, wait_for_owner,
)
from .streak_schedule import next_streak_run, pending_streak_chats
from .theme import STYLESHEET


class StreakRun(QThread):
    progress = Signal(str, str)

    def __init__(self, store, profile, owner, parent, *, pending=None):
        super().__init__(parent)
        self.store = store
        self.profile = profile
        self.owner = owner
        self.pending = pending
        self.cancelled = Event()
        self.error = ""
        self.auth_blocked = False

    def run(self):
        try:
            if active_login_pid(self.profile) is not None:
                self.error = "Chrome thiết lập vẫn đang mở. Chọn Kiểm tra đăng nhập trong Settings để tiếp tục."
                return
            with chrome_session(self.profile) as page:
                open_inbox(page)
                owner = wait_for_owner(page, self.cancelled, 8)
                if self.cancelled.is_set():
                    return
                if not owner and login_required(page):
                    self.auth_blocked = True
                    self.error = "TikTok chuyển Chrome headless sang trang đăng nhập. Phiên này chưa dùng được để giữ chuỗi."
                elif not owner:
                    self.error = "Chưa đọc được hộp thư ở nền. Kiểm tra phiên TikTok trong Settings."
                elif owner != self.owner:
                    self.auth_blocked = True
                    self.error = "Tài khoản TikTok trong hồ sơ nền không khớp. Kết nối lại trong Settings."
                else:
                    result = check(self.store, HeadlessMessages(page, owner, self.cancelled), owner=owner,
                                   on_result=self.progress.emit, cancelled=self.cancelled.is_set, only=self.pending)
                    self.auth_blocked = result in (Status.LOGIN_REQUIRED, Status.VERIFICATION_REQUIRED)
                    self.store.set(f"auto_streak_auth/{owner}", "1" if self.auth_blocked else "0")
        except (OSError, ValueError, PlaywrightError, subprocess.SubprocessError) as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "Không đọc được TikTok trong Chrome headless."


class StreakLogin(QThread):
    def __init__(self, profile, parent):
        super().__init__(parent)
        self.profile = profile
        self.cancelled = Event()
        self.owner = ""
        self.error = ""

    def run(self):
        try:
            close_login_chrome(self.profile)
            with chrome_session(self.profile) as page:
                open_inbox(page)
                owner = wait_for_owner(page, self.cancelled, 10)
                if owner and not self.cancelled.is_set():
                    self.owner = owner
                elif not self.cancelled.is_set():
                    self.error = (
                        "TikTok chuyển Chrome headless sang trang đăng nhập dù hồ sơ riêng đã mở."
                        if login_required(page) else "Đã mở Chrome headless nhưng chưa đọc được tài khoản trong hộp thư."
                    )
        except (OSError, ValueError, PlaywrightError, subprocess.SubprocessError) as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "Không mở được TikTok để thiết lập hồ sơ riêng."


class InboxRead(QThread):
    def __init__(self, profile, expected_owner, target, parent):
        super().__init__(parent)
        self.profile = profile
        self.expected_owner = expected_owner
        self.target = target
        self.cancelled = Event()
        self.snapshot = None
        self.error = ""

    def run(self):
        try:
            if active_login_pid(self.profile) is not None:
                self.error = "Chrome thiết lập vẫn đang mở. Chọn Kiểm tra đăng nhập trong Settings."
                return
            with chrome_session(self.profile) as page:
                open_inbox(page)
                result = read_inbox_snapshot(page, self.cancelled, self.target)
                if self.expected_owner and self.expected_owner != result["owner"]:
                    self.error = "Tài khoản trong hồ sơ nền đã thay đổi. Bấm Kiểm tra đăng nhập trong Settings để kết nối."
                elif not self.cancelled.is_set():
                    self.snapshot = result
        except (OSError, ValueError, PlaywrightError, subprocess.SubprocessError) as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else "Không đọc được hộp thư ở nền."


class Window(QMainWindow):
    def __init__(self, store: Store, data_dir: Path, *, demo: bool = False):
        super().__init__()
        self.store = store
        self.data_dir = data_dir
        self.demo = demo
        self.messages = DemoMessages(store) if demo else None
        self.reader = None
        self.streak_run = None
        self.streak_login = None
        self.streak_profile = data_dir / "headless-chrome"
        self.streak_results = []
        self.last_tick = time.time()
        self.next_check = self.last_tick + 3600
        self.setWindowTitle("StreakKeeper")
        self.resize(1100, 720)
        self.setMinimumSize(850, 590)
        self.setStyleSheet(STYLESHEET)
        self.build_ui()
        self.setup_tray()
        if self.demo:
            self.refresh_history()
        else:
            self.refresh_streak_history()
            QApplication.instance().aboutToQuit.connect(self.stop_streak_run)
        self.update_summary()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(15_000)
        QTimer.singleShot(0, self.start_background_tasks)

    def build_ui(self):
        root = QWidget()
        root.setObjectName("workspace")
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        rail = QFrame()
        rail.setObjectName("rail")
        rail_layout = QHBoxLayout(rail)
        rail_layout.setContentsMargins(18, 9, 18, 9)
        rail_layout.addWidget(self.label("ϟ  StreakKeeper", "brand"))
        rail_layout.addStretch()
        self.summary = self.label("", "muted")
        rail_layout.addWidget(self.summary)
        rail_layout.addSpacing(12)
        rail_layout.addWidget(self.label("MÔ PHỎNG" if self.demo else "TIKTOK · CHẠY NỀN", "badge"))
        shell.addWidget(rail)

        body = QHBoxLayout()
        body.setSpacing(0)
        shell.addLayout(body, 1)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(13, 14, 13, 14)
        navigation.addWidget(self.label("LOCAL DAEMON", "section"))
        navigation.addSpacing(6)
        self.pages = QStackedWidget()
        group = QButtonGroup(self)
        self.navigation = group
        for index, (icon, title, builder) in enumerate((
            ("▦", "Dashboard", self.dashboard_page),
            ("ϟ", "TikTok", self.tiktok_page),
            ("♧", "Duolingo", self.duolingo_page),
            ("▤", "Activity Log", self.activity_page),
            ("⚙", "Settings", self.settings_page),
        )):
            self.pages.addWidget(builder())
            button = QPushButton(f"{icon}   {title}     ⌘{index + 1}")
            button.setAccessibleName(title)
            button.setProperty("nav", True)
            button.setCheckable(True)
            group.addButton(button, index)
            navigation.addWidget(button)
            button.clicked.connect(lambda _checked=False, i=index: self.pages.setCurrentIndex(i))
            QShortcut(QKeySequence(f"Ctrl+{index + 1}"), self, activated=button.click)
        group.button(0).setChecked(True)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.check_button.click)
        navigation.addStretch()
        status_box, status_layout = self.panel()
        self.daemon_status = self.label("", "status")
        status_layout.addWidget(self.daemon_status)
        row = QHBoxLayout()
        self.pause_button = QPushButton()
        self.pause_button.clicked.connect(self.toggle_pause)
        row.addWidget(self.pause_button)
        tray_button = QPushButton("Tray")
        tray_button.clicked.connect(self.close)
        row.addWidget(tray_button)
        status_layout.addLayout(row)
        navigation.addWidget(status_box)
        body.addWidget(sidebar)
        body.addWidget(self.pages, 1)

    @staticmethod
    def label(text, role):
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setObjectName(role)
        return label

    @staticmethod
    def panel(role="panel"):
        panel = QFrame()
        panel.setObjectName(role)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        return panel, layout

    def notice(self, title, *lines):
        panel, layout = self.panel("notice")
        layout.setSpacing(4)
        layout.addWidget(self.label(title, "noteTitle"))
        for line in lines:
            text = self.label(line, "noteText")
            text.setWordWrap(True)
            layout.addWidget(text)
        return panel

    def page(self, section, title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QVBoxLayout()
        header.setSpacing(3)
        header.addWidget(self.label(section, "section"))
        header.addWidget(self.label(title, "title"))
        header.addWidget(self.label(description, "muted"))
        layout.addLayout(header)
        return page, layout

    def dashboard_page(self):
        description = (
            "Theo dõi lượt kiểm tra và trạng thái TikTok hôm nay." if self.demo
            else "Theo dõi tiến độ gửi trong ngày, tính theo giờ Việt Nam."
        )
        page, layout = self.page("TỔNG QUAN", "Dashboard", description)
        if not self.demo:
            return self.live_dashboard(page, layout)
        hero, hero_layout = self.panel("hero")
        row = QHBoxLayout()
        intro = QVBoxLayout()
        intro.addWidget(self.label("LỊCH CHẠY", "section"))
        self.next_run = self.label("", "heading")
        intro.addWidget(self.next_run)
        intro.addWidget(self.label("Mỗi giờ · Asia/Ho_Chi_Minh", "muted"))
        row.addLayout(intro, 1)
        self.check_button = QPushButton("↻  Kiểm tra ngay  ⌘R")
        self.check_button.setProperty("primary", True)
        self.check_button.clicked.connect(self.run_check)
        row.addWidget(self.check_button)
        hero_layout.addLayout(row)
        layout.addWidget(hero)
        stats = QHBoxLayout()
        self.metrics = []
        for title in ("CUỘC TRÒ CHUYỆN", "ĐANG BẬT GỬI", "HOÀN TẤT HÔM NAY"):
            card, card_layout = self.panel()
            card_layout.addWidget(self.label(title, "section"))
            value = self.label("0", "metric")
            card_layout.addWidget(value)
            self.metrics.append(value)
            stats.addWidget(card, 1)
        layout.addLayout(stats)
        overview, details = self.panel()
        details.addWidget(self.label("ϟ  TikTok · Tiến độ hôm nay", "heading"))
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        details.addWidget(self.progress)
        self.progress_text = self.label("", "muted")
        details.addWidget(self.progress_text)
        layout.addWidget(overview)
        recent, recent_layout = self.panel()
        recent_layout.addWidget(self.label("Hoạt động gần đây", "heading"))
        self.recent = self.table(["Thời điểm", "Cuộc trò chuyện", "Kết quả"])
        self.recent.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        recent_layout.addWidget(self.recent)
        layout.addWidget(recent, 1)
        return page

    def live_dashboard(self, page, layout):
        card, overview = self.panel("hero")
        row = QHBoxLayout()
        self.dashboard_account = self.label("", "heading")
        row.addWidget(self.dashboard_account, 1)
        self.check_button = QPushButton("Mở hộp thư")
        self.check_button.clicked.connect(self.check_now)
        row.addWidget(self.check_button)
        self.dashboard_streak_button = QPushButton("Chạy giữ chuỗi")
        self.dashboard_streak_button.setProperty("primary", True)
        self.dashboard_streak_button.clicked.connect(self.start_streak_run)
        row.addWidget(self.dashboard_streak_button)
        overview.addLayout(row)
        self.live_state = self.label("", "noteText")
        self.live_state.setWordWrap(True)
        overview.addWidget(self.live_state)
        self.dashboard_run_status = self.label("", "noteText")
        self.dashboard_run_status.setWordWrap(True)
        self.dashboard_run_status.hide()
        overview.addWidget(self.dashboard_run_status)
        self.dashboard_auto_status = self.label("", "noteText")
        self.dashboard_auto_status.setWordWrap(True)
        overview.addWidget(self.dashboard_auto_status)
        layout.addWidget(card)

        stats = QHBoxLayout()
        self.live_metrics = []
        for title in ("CHAT ĐÃ CHỌN", "ĐÃ GỬI HÔM NAY", "CÒN CẦN GỬI"):
            metric, metric_layout = self.panel()
            metric_layout.addWidget(self.label(title, "section"))
            value = self.label("0", "metric")
            metric_layout.addWidget(value)
            self.live_metrics.append(value)
            stats.addWidget(metric, 1)
        layout.addLayout(stats)

        recent, recent_layout = self.panel()
        recent_header = QHBoxLayout()
        recent_header.addWidget(self.label("Hoạt động gần đây", "heading"), 1)
        view_log = QPushButton("Xem nhật ký")
        view_log.clicked.connect(lambda: self.navigation.button(3).click())
        recent_header.addWidget(view_log)
        recent_layout.addLayout(recent_header)
        self.live_recent = self.table(["Thời điểm", "Cuộc trò chuyện", "Kết quả"])
        self.live_recent.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        recent_layout.addWidget(self.live_recent)
        self.live_recent_empty = self.label("Chưa có lượt giữ chuỗi nào.", "noteText")
        recent_layout.addWidget(self.live_recent_empty, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(recent, 1)
        return page

    @staticmethod
    def table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(37)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def tiktok_page(self):
        if not self.demo:
            return self.live_tiktok_page()
        page, layout = self.page("THEO DÕI", "TikTok", "Quản lý cuộc trò chuyện và bật gửi mô phỏng cho từng người.")
        account, account_layout = self.panel()
        row = QHBoxLayout()
        info = QVBoxLayout()
        info.addWidget(self.label("ϟ  TikTok Web", "heading"))
        info.addWidget(self.label("Chế độ mô phỏng · Không gửi tin thật", "muted"))
        row.addLayout(info, 1)
        account_layout.addLayout(row)
        layout.addWidget(account)
        controls = QHBoxLayout()
        self.target_search = QLineEdit()
        self.target_search.setPlaceholderText("Tìm cuộc trò chuyện")
        self.target_search.textChanged.connect(self.filter_targets)
        controls.addWidget(self.target_search, 1)
        self.target_name = QLineEdit()
        self.target_name.setPlaceholderText("Tên người nhận mô phỏng")
        self.target_name.returnPressed.connect(self.add_target)
        controls.addWidget(self.target_name, 1)
        add = QPushButton("+  Thêm người nhận")
        add.setProperty("primary", True)
        add.clicked.connect(self.add_target)
        controls.addWidget(add)
        layout.addLayout(controls)
        self.targets = self.table(["Cuộc trò chuyện", "Bật gửi", "Lần kiểm tra gần nhất"])
        self.targets.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.targets.itemChanged.connect(self.update_target)
        layout.addWidget(self.targets, 1)
        self.target_empty = self.label("", "muted")
        layout.addWidget(self.target_empty)
        return page

    def live_tiktok_page(self):
        page, layout = self.page("THEO DÕI", "TikTok", "Các cuộc trò chuyện được đọc bằng hồ sơ nền của StreakKeeper.")
        account, controls = self.panel()
        row = QHBoxLayout()
        self.inbox_status = self.label("Chưa đọc hộp thư", "heading")
        self.inbox_status.setWordWrap(True)
        row.addWidget(self.inbox_status, 1)
        self.read_button = QPushButton("Mở hộp thư")
        self.read_button.clicked.connect(self.check_now)
        row.addWidget(self.read_button)
        self.streak_button = QPushButton("Chạy giữ chuỗi")
        self.streak_button.setProperty("primary", True)
        self.streak_button.clicked.connect(self.start_streak_run)
        row.addWidget(self.streak_button)
        controls.addLayout(row)
        message_row = QHBoxLayout()
        message_row.addWidget(self.label("Tin nhắn chung", "heading"))
        self.streak_content = QLineEdit(self.store.get("streak_content", "."))
        self.streak_content.setPlaceholderText("Mặc định: .")
        self.streak_content.editingFinished.connect(self.save_streak_content)
        message_row.addWidget(self.streak_content, 1)
        controls.addLayout(message_row)
        controls.addWidget(self.notice(
            "Giữ chuỗi và nội dung gửi",
            "Chọn Giữ chuỗi để thêm chat vào lượt gửi.",
            "Nhấp đúp ô Tin nhắn riêng để sửa. Để trống để dùng tin nhắn chung.",
        ))
        self.streak_summary = self.label("", "noteText")
        self.streak_summary.hide()
        self.streak_summary.setWordWrap(True)
        controls.addWidget(self.streak_summary)
        layout.addWidget(account)
        self.live_table = self.table(["Cuộc trò chuyện", "Giữ chuỗi", "Tin nhắn riêng"])
        self.live_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.live_table.itemChanged.connect(self.update_streak_chat)
        self.live_table.cellDoubleClicked.connect(self.read_conversation)
        layout.addWidget(self.live_table, 1)
        self.chat_summary = self.label("", "noteText")
        self.chat_summary.setWordWrap(True)
        layout.addWidget(self.chat_summary)
        return page

    def save_streak_content(self):
        content = self.streak_content.text().strip() or "."
        self.streak_content.setText(content)
        self.store.set("streak_content", content)
        self.live_table.blockSignals(True)
        for row in range(self.live_table.rowCount()):
            self.update_streak_tooltip(row)
        self.live_table.blockSignals(False)

    def update_streak_chat(self, item):
        owner = self.store.get("tiktok_headless_owner")
        if not owner or item.column() not in (1, 2):
            return
        row = item.row()
        conversation_id = self.live_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        enabled = self.live_table.item(row, 1).checkState() == Qt.CheckState.Checked
        message = self.live_table.item(row, 2).text()
        new_selection = item.column() == 1 and enabled
        now = datetime.now(VIETNAM)
        was_empty = new_selection and not pending_streak_chats(self.store, owner, now)
        self.store.save_streak_chat(owner, conversation_id, enabled, message)
        if was_empty and pending_streak_chats(self.store, owner, now):
            self.store.set(f"auto_streak_last_start/{owner}", "")
        if item.column() == 1:
            QTimer.singleShot(0, self.maybe_run_auto)
        self.live_table.blockSignals(True)
        self.update_streak_tooltip(row)
        self.live_table.blockSignals(False)
        self.refresh_streak_history()

    def update_streak_tooltip(self, row):
        owner = self.store.get("tiktok_headless_owner")
        conversation_id = self.live_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        message = self.store.streak_message(owner, conversation_id)
        self.live_table.item(row, 2).setToolTip(
            f"Tin nhắn sẽ dùng: {message}" if message is not None else "Chat chưa được chọn giữ chuỗi."
        )

    def show_conversations(self, conversations):
        choices = self.store.streak_chats(self.store.get("tiktok_headless_owner"))
        self.live_table.blockSignals(True)
        self.live_table.setRowCount(len(conversations))
        for row, entry in enumerate(conversations):
            conversation_id = entry["id"]
            enabled, message = choices.get(conversation_id, (False, ""))
            item = self.table_item(entry["name"])
            item.setData(Qt.ItemDataRole.UserRole, conversation_id)
            self.live_table.setItem(row, 0, item)
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            self.live_table.setItem(row, 1, checkbox)
            self.live_table.setItem(row, 2, QTableWidgetItem(message))
            self.update_streak_tooltip(row)
        self.live_table.blockSignals(False)

    def start_streak_run(self, *, pending=None):
        if self.reader is not None or self.streak_run is not None or self.streak_login is not None or self.store.get("paused") == "1":
            return
        owner = self.store.get("tiktok_headless_owner")
        if not owner or not (self.streak_profile / "Local State").is_file():
            self.set_streak_summary("Vào Settings để kết nối TikTok trước.")
            return
        self.save_streak_content()
        if not any(enabled for enabled, _ in self.store.streak_chats(owner).values()):
            self.set_streak_summary("Vào TikTok và đánh dấu Giữ chuỗi cho ít nhất một chat.")
            return
        self.streak_results = []
        self.set_streak_summary("Đang gửi tự động…" if pending is not None else "Đang xử lý các chat đã chọn…")
        worker = StreakRun(self.store, self.streak_profile, owner, self, pending=pending)
        self.store.set(f"auto_streak_last_start/{owner}", datetime.now(VIETNAM).isoformat())
        self.streak_run = worker
        worker.progress.connect(self.on_streak_result)
        worker.finished.connect(self.finish_streak_run)
        self.update_summary()
        worker.start()

    def on_streak_result(self, conversation_id, status):
        self.streak_results.append(status)
        names = self.conversation_labels()
        name = names.get(conversation_id, f"Chat …{conversation_id[-6:]}")
        self.set_streak_summary(f"{len(self.streak_results)} chat đã kiểm tra · {name} · {status}")
        self.refresh_streak_history()

    def set_streak_summary(self, message):
        for label in (self.streak_summary, self.dashboard_run_status):
            label.setText(message)
            label.setVisible(bool(message))

    def finish_streak_run(self):
        worker, self.streak_run = self.streak_run, None
        error = worker.error
        if worker.auth_blocked:
            self.store.set(f"auto_streak_auth/{worker.owner}", "1")
        worker.deleteLater()
        if error:
            self.set_streak_summary(error)
            self.update_summary()
            return
        checked = len(self.streak_results)
        sent = self.streak_results.count(Status.SENT)
        existing = self.streak_results.count(Status.APP_SENT_TODAY)
        self.set_streak_summary(
            f"{checked} chat đã kiểm tra · {sent} gửi mới · {existing} đã gửi trước đó · "
            f"{checked - sent - existing} cần xem nhật ký."
        )
        self.update_summary()
        QTimer.singleShot(0, self.maybe_run_auto)

    def stop_streak_run(self):
        for worker in (self.reader, self.streak_run, self.streak_login):
            if worker is not None:
                worker.cancelled.set()
                worker.wait()

    def start_streak_login(self):
        if self.reader is not None or self.streak_run is not None or self.streak_login is not None:
            return
        try:
            if active_login_pid(self.streak_profile) is not None:
                self.streak_login_status.setText(
                    "Chrome thiết lập đã mở. Nếu bạn đang ở hộp thư TikTok, bấm Kiểm tra đăng nhập."
                )
                return
            open_login_chrome(self.streak_profile)
        except ValueError as exc:
            self.streak_login_status.setText(str(exc))
            return
        except (OSError, subprocess.SubprocessError):
            self.streak_login_status.setText("Không mở được Google Chrome để đăng nhập.")
            return
        self.streak_login_status.setText("Đăng nhập tài khoản TikTok bạn muốn dùng. Khi hộp thư mở được, bấm Kiểm tra đăng nhập.")

    def verify_streak_login(self):
        if self.reader is not None or self.streak_run is not None or self.streak_login is not None:
            return
        if not (self.streak_profile / "Local State").is_file():
            self.streak_login_status.setText("Đăng nhập TikTok cho hồ sơ nền trước khi kiểm tra.")
            return
        worker = StreakLogin(self.streak_profile, self)
        self.streak_login = worker
        self.streak_login_status.setText("Đang kiểm tra phiên TikTok đã lưu…")
        worker.finished.connect(self.finish_streak_login)
        self.update_summary()
        worker.start()

    def finish_streak_login(self):
        worker, self.streak_login = self.streak_login, None
        if worker.owner:
            changed = worker.owner != self.store.get("tiktok_headless_owner")
            self.store.confirm_tiktok_account(worker.owner)
            self.store.set(f"auto_streak_auth/{worker.owner}", "")
            self.streak_login_status.setText(f"Đã kết nối @{worker.owner}. Mở hộp thư để chọn chat giữ chuỗi.")
            if changed:
                self.complete_read("Bấm Mở hộp thư để chọn cuộc trò chuyện.")
                self.refresh_streak_history()
        else:
            self.streak_login_status.setText(worker.error or "Chưa hoàn tất đăng nhập.")
        worker.deleteLater()
        self.update_summary()
        if worker.owner:
            QTimer.singleShot(0, self.maybe_run_auto)

    def conversation_labels(self):
        return {
            item.data(Qt.ItemDataRole.UserRole): item.text()
            for row in range(self.live_table.rowCount())
            if (item := self.live_table.item(row, 0)) is not None
        }

    def refresh_streak_history(self):
        names = self.conversation_labels()
        owner = self.store.get("tiktok_headless_owner")
        rows = [
            (time, names.get(target, f"Chat …{target[-6:]}"), status)
            for time, target, status in (self.store.activity(owner) if owner else [])
        ]
        self.fill_history(self.history, rows)
        self.fill_history(self.live_recent, rows[:5])
        self.live_recent.setVisible(bool(rows))
        self.live_recent_empty.setVisible(not rows)

        self.dashboard_day = datetime.now(VIETNAM).date()
        choices = self.store.streak_chats(owner) if owner else {}
        selected = {target for target, (enabled, _) in choices.items() if enabled}
        sent = self.store.confirmed_streak_chats(owner, self.dashboard_day.isoformat()) if selected else set()
        sent = selected & sent
        for label, count in zip(self.live_metrics, (len(selected), len(sent), len(selected) - len(sent))):
            label.setText(str(count))
        self.dashboard_account.setText(f"TikTok · @{owner}" if owner else "Chưa kết nối TikTok")

    def duolingo_page(self):
        page, layout = self.page("NỀN TẢNG", "Duolingo", "Theo dõi chuỗi học và tiến độ.")
        card, content = self.panel()
        content.addWidget(self.label("Chưa tích hợp Duolingo", "heading"))
        content.addWidget(self.label("Bản hiện tại hỗ trợ TikTok.", "muted"))
        layout.addWidget(card)
        layout.addStretch()
        return page

    def activity_page(self):
        page, layout = self.page("NHẬT KÝ", "Activity Log", "Kết quả kiểm tra được lưu trên máy · Giờ Việt Nam.")
        card, content = self.panel()
        if not self.demo:
            content.addWidget(self.label("Kết quả các lượt giữ chuỗi", "heading"))
            self.history = self.table(["Thời điểm", "Cuộc trò chuyện", "Kết quả"])
            content.addWidget(self.history)
            layout.addWidget(card, 1)
            return page
        filters = QHBoxLayout()
        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Tìm người nhận hoặc kết quả")
        self.log_search.textChanged.connect(self.filter_history)
        filters.addWidget(self.log_search, 1)
        self.log_status = QComboBox()
        self.log_status.addItems(["Tất cả kết quả", *(state.value for state in Status)])
        self.log_status.currentIndexChanged.connect(self.filter_history)
        filters.addWidget(self.log_status)
        content.addLayout(filters)
        self.history = self.table(["Thời điểm", "Cuộc trò chuyện", "Kết quả"])
        content.addWidget(self.history)
        self.log_count = self.label("", "muted")
        content.addWidget(self.log_count)
        layout.addWidget(card, 1)
        return page

    def settings_page(self):
        description = "Tùy chỉnh nội dung mô phỏng và lịch chạy." if self.demo else "Kết nối TikTok và đặt lịch gửi."
        page, layout = self.page("CẤU HÌNH", "Settings", description)
        config, config_layout = self.panel()
        if not self.demo:
            config_layout.addWidget(self.label("TikTok Web", "heading"))
            config_layout.addWidget(self.notice(
                "Kết nối lần đầu",
                "1. Đăng nhập TikTok trong cửa sổ thiết lập.",
                "2. Khi hộp thư mở được, quay lại và bấm Kiểm tra đăng nhập.",
                "Đọc hộp thư và giữ chuỗi chạy ở nền sau khi kết nối.",
            ))
            self.streak_login_button = QPushButton("Đăng nhập TikTok cho chế độ nền")
            self.streak_login_button.clicked.connect(self.start_streak_login)
            self.streak_verify_button = QPushButton("Kiểm tra đăng nhập")
            self.streak_verify_button.clicked.connect(self.verify_streak_login)
            login_actions = QHBoxLayout()
            login_actions.addWidget(self.streak_login_button)
            login_actions.addWidget(self.streak_verify_button)
            login_actions.addStretch()
            config_layout.addLayout(login_actions)
            self.streak_login_status = self.label("", "noteText")
            self.streak_login_status.setWordWrap(True)
            if self.store.get("tiktok_headless_owner"):
                self.streak_login_status.setText("Hồ sơ nền đã được thiết lập.")
            elif (self.streak_profile / "Local State").is_file():
                self.streak_login_status.setText("Đã có hồ sơ riêng. Bấm Kiểm tra đăng nhập để kiểm tra phiên đã lưu.")
            config_layout.addWidget(self.streak_login_status)
            layout.addWidget(config)
            layout.addWidget(self.auto_schedule_panel())
            layout.addStretch()
            return page
        config_layout.addWidget(self.label("TikTok · Mô phỏng", "heading"))
        form = QFormLayout()
        form.setVerticalSpacing(8)
        self.content = QLineEdit(self.store.get("content", "."))
        self.content.editingFinished.connect(self.save_content)
        form.addRow("Nội dung tin nhắn", self.content)
        self.scenario = QComboBox()
        for status in (
            Status.NO_OUTGOING, Status.HAS_OUTGOING, Status.UNKNOWN,
            Status.LOGIN_REQUIRED, Status.VERIFICATION_REQUIRED,
        ):
            self.scenario.addItem(status.value)
        self.scenario.setCurrentText(self.store.get("demo_status", Status.NO_OUTGOING))
        self.scenario.currentTextChanged.connect(self.set_scenario)
        form.addRow("Trạng thái mô phỏng", self.scenario)
        uncertain = QCheckBox("Mô phỏng kết quả gửi chưa rõ")
        uncertain.setChecked(self.store.get("demo_uncertain") == "1")
        uncertain.toggled.connect(lambda enabled: self.store.set("demo_uncertain", str(int(enabled))))
        form.addRow(uncertain)
        config_layout.addLayout(form)
        layout.addWidget(config)
        schedule, schedule_layout = self.panel()
        schedule_layout.addWidget(self.label("Lịch chạy và múi giờ", "heading"))
        schedule_layout.addWidget(self.label("Kiểm tra mỗi giờ · Asia/Ho_Chi_Minh (UTC+07:00)", "muted"))
        schedule_layout.addWidget(self.label("App chạy nền khi đóng cửa sổ nếu có biểu tượng thanh menu.", "muted"))
        layout.addWidget(schedule)
        layout.addStretch()
        return page

    def auto_schedule_panel(self):
        panel, layout = self.panel()
        layout.addWidget(self.label("Lịch gửi tự động", "heading"))
        self.auto_enabled = QCheckBox("Bật tự động giữ chuỗi")
        self.auto_enabled.setChecked(self.auto_streak_enabled())
        layout.addWidget(self.auto_enabled)
        row = QHBoxLayout()
        self.auto_use_start_time = QCheckBox("Đặt giờ bắt đầu mỗi ngày")
        start_time = self.store.get("auto_streak_start_time")
        self.auto_use_start_time.setChecked(bool(start_time))
        row.addWidget(self.auto_use_start_time)
        self.auto_start_time = QTimeEdit(QTime.fromString(start_time or "09:00", "HH:mm"))
        self.auto_start_time.setDisplayFormat("HH:mm")
        self.auto_start_time.setKeyboardTracking(False)
        self.auto_start_time.setEnabled(bool(start_time))
        row.addWidget(self.auto_start_time)
        row.addStretch()
        layout.addLayout(row)
        for widget in (self.auto_enabled, self.auto_use_start_time):
            widget.toggled.connect(self.save_auto_schedule)
        self.auto_start_time.timeChanged.connect(self.save_auto_schedule)
        layout.addWidget(self.notice(
            "Cách chạy",
            "Mặc định gửi ngay khi có chat cần gửi. Có thể đặt giờ bắt đầu theo giờ Việt Nam.",
            "App thử lại sau mỗi 15 phút cho các chat còn thiếu rồi dừng khi gửi đủ.",
        ))
        self.settings_auto_status = self.label("", "noteText")
        self.settings_auto_status.setWordWrap(True)
        layout.addWidget(self.settings_auto_status)
        return panel

    def auto_streak_enabled(self):
        return self.store.get("auto_streak_enabled") == "1"

    def save_auto_schedule(self):
        enabled = self.auto_enabled.isChecked()
        self.store.set("auto_streak_enabled", "1" if enabled else "0")
        use_start = self.auto_use_start_time.isChecked()
        self.auto_start_time.setEnabled(use_start)
        self.store.set("auto_streak_start_time", self.auto_start_time.time().toString("HH:mm") if use_start else "")
        if not enabled and self.streak_run is not None and self.streak_run.pending is not None:
            self.streak_run.cancelled.set()
        self.update_summary()
        QTimer.singleShot(0, self.maybe_run_auto)

    def auto_schedule(self, now):
        if not self.auto_streak_enabled():
            return "Gửi tự động đang tắt", None, set()
        if self.store.get("paused") == "1":
            return "Gửi tự động đang tạm dừng", None, set()
        owner = self.store.get("tiktok_headless_owner")
        if not owner or not (self.streak_profile / "Local State").is_file():
            return "Kết nối TikTok để gửi tự động", None, set()
        if self.store.get(f"auto_streak_auth/{owner}") == "1":
            return "Kiểm tra đăng nhập để tiếp tục gửi tự động", None, set()
        if self.streak_run is not None:
            return "Đang chạy giữ chuỗi", None, set()
        pending = pending_streak_chats(self.store, owner, now)
        if not pending:
            selected = any(enabled for enabled, _ in self.store.streak_chats(owner).values())
            status = "Đã gửi đủ hôm nay · Chờ ngày mới hoặc chat mới" if selected else "Chờ chọn chat giữ chuỗi"
            return status, None, set()
        due = next_streak_run(
            now, self.store.get(f"auto_streak_last_start/{owner}"),
            self.store.get("auto_streak_start_time"),
        )
        status = f"Lượt gửi kế tiếp · {due:%H:%M} (VN) · {len(pending)} chat còn chờ"
        return status, due, pending

    def maybe_run_auto(self):
        if self.demo:
            return False
        now = datetime.now(VIETNAM)
        status, due, pending = self.auto_schedule(now)
        self.dashboard_auto_status.setText(status)
        self.settings_auto_status.setText(status)
        if due is None or due > now or self.reader is not None or self.streak_login is not None:
            return False
        self.start_streak_run(pending=pending)
        return self.streak_run is not None

    def start_background_tasks(self):
        if not self.demo and self.auto_streak_enabled():
            self.maybe_run_auto()
        else:
            self.run_check()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), self)
        menu = QMenu(self)
        menu.addAction("Mở StreakKeeper", self.show_window)
        menu.addAction("Kiểm tra ngay", self.check_now)
        self.pause_action = menu.addAction("Tạm dừng", self.toggle_pause)
        self.pause_action.setCheckable(True)
        menu.addAction("Thoát", QApplication.instance().quit)
        self.menuBar().addMenu(menu)
        menu.setTitle("StreakKeeper")
        tray_menu = QMenu(self)
        for action in menu.actions():
            tray_menu.addAction(action)
        self.tray.setContextMenu(tray_menu)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)

    def save_content(self):
        content = self.content.text().strip() or "."
        self.content.setText(content)
        self.store.set("content", content)

    def set_scenario(self, value: str):
        self.store.set("demo_status", value)
        if value != Status.LOGIN_REQUIRED:
            self.store.set("login_notice", "0")

    def add_target(self):
        name = self.target_name.text().strip()
        if not name:
            return
        if name not in dict(self.store.targets()):
            self.store.save_target(name, False)
        self.target_name.clear()
        self.refresh_targets()

    def refresh_targets(self, activity=None):
        if activity is None:
            activity = self.store.activity()
        latest = {}
        for _, target, result in activity:
            latest.setdefault(target, result)

        self.targets.blockSignals(True)
        rows = self.store.targets()
        self.targets.setRowCount(len(rows))
        for index, (name, enabled) in enumerate(rows):
            self.targets.setItem(index, 0, self.table_item(name))
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            self.targets.setItem(index, 1, item)
            self.targets.setItem(index, 2, self.table_item(latest.get(name, "Chưa kiểm tra"), status=True))
        self.targets.blockSignals(False)
        self.filter_targets()
        self.refresh_dashboard(rows)

    def filter_targets(self):
        query = self.target_search.text().strip().casefold()
        matches = 0
        for row in range(self.targets.rowCount()):
            show = query in self.targets.item(row, 0).text().casefold()
            self.targets.setRowHidden(row, not show)
            matches += int(show)
        self.target_empty.setText(f"{matches} cuộc trò chuyện" if matches else "Không có cuộc trò chuyện phù hợp.")

    def update_target(self, item):
        if item.column() == 1:
            name = self.targets.item(item.row(), 0).text()
            self.store.save_target(name, item.checkState() == Qt.CheckState.Checked)
            self.refresh_dashboard(self.store.targets())

    @staticmethod
    def table_item(value, status=False):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if status:
            if value in (Status.SENT, Status.HAS_OUTGOING, Status.APP_SENT_TODAY):
                item.setForeground(QColor("#67df70"))
            elif value in (Status.LOGIN_REQUIRED, Status.VERIFICATION_REQUIRED):
                item.setForeground(QColor("#ffb4ab"))
            elif value != "Chưa kiểm tra":
                item.setForeground(QColor("#ffb689"))
        return item

    def refresh_dashboard(self, targets):
        enabled = {name for name, active in targets if active}
        completed = enabled & self.store.completed_today(datetime.now(VIETNAM))
        for label, count in zip(self.metrics, (len(targets), len(enabled), len(completed))):
            label.setText(str(count))
        self.progress.setRange(0, max(1, len(enabled)))
        self.progress.setValue(len(completed))
        self.progress_text.setText(
            f"{len(completed)} / {len(enabled)} người nhận đã có tin đi trong mô phỏng."
            if enabled else "Chưa bật gửi cho người nhận nào."
        )

    def fill_history(self, table, rows):
        table.setRowCount(len(rows))
        for index, (timestamp, target, status) in enumerate(rows):
            local = datetime.fromisoformat(timestamp).astimezone(VIETNAM)
            for column, value in enumerate((local.strftime("%d/%m %H:%M:%S"), target, status)):
                table.setItem(index, column, self.table_item(value, status=column == 2))

    def refresh_history(self):
        rows = self.store.activity()
        self.fill_history(self.history, rows)
        self.fill_history(self.recent, rows[:5])
        self.filter_history()
        self.refresh_targets(rows)

    def filter_history(self):
        query = self.log_search.text().strip().casefold()
        status = self.log_status.currentText() if self.log_status.currentIndex() else ""
        matches = 0
        for row in range(self.history.rowCount()):
            name = self.history.item(row, 1).text()
            result = self.history.item(row, 2).text()
            show = (query in name.casefold() or query in result.casefold()) and (not status or status == result)
            self.history.setRowHidden(row, not show)
            matches += int(show)
        self.log_count.setText(f"{matches} / {self.history.rowCount()} lượt kiểm tra")

    def toggle_pause(self):
        paused = self.store.get("paused") == "1"
        self.store.set("paused", "0" if paused else "1")
        if not paused and self.streak_run is not None:
            self.streak_run.cancelled.set()
        self.update_summary()
        if paused and not self.demo:
            QTimer.singleShot(0, self.maybe_run_auto)

    def update_summary(self):
        paused = self.store.get("paused") == "1"
        next_time = datetime.fromtimestamp(self.next_check, VIETNAM)
        next_label = "Lượt kế tiếp" if self.demo else "Đọc hộp thư kế tiếp"
        self.summary.setText("Đang tạm dừng" if paused else f"{next_label} · {next_time:%d/%m %H:%M} (VN)")
        if self.demo:
            self.next_run.setText("Đang tạm dừng" if paused else f"Lượt kế tiếp · {next_time:%d/%m %H:%M}")
        else:
            can_run = not paused and self.reader is None and self.streak_run is None and self.streak_login is None
            self.read_button.setEnabled(can_run)
            self.streak_button.setEnabled(can_run)
            self.dashboard_streak_button.setEnabled(can_run)
            self.streak_login_button.setEnabled(self.reader is None and self.streak_login is None and self.streak_run is None)
            self.streak_verify_button.setEnabled(self.reader is None and self.streak_login is None and self.streak_run is None)
            status, _, _ = self.auto_schedule(datetime.now(VIETNAM))
            self.dashboard_auto_status.setText(status)
            self.settings_auto_status.setText(status)
            if not paused and self.auto_streak_enabled():
                self.summary.setText("")
        self.daemon_status.setText("●  Đang tạm dừng" if paused else "●  Đang chạy")
        self.daemon_status.setProperty("paused", paused)
        self.daemon_status.style().unpolish(self.daemon_status)
        self.daemon_status.style().polish(self.daemon_status)
        self.pause_button.setText("Tiếp tục" if paused else "Tạm dừng")
        self.pause_action.setChecked(paused)
        self.check_button.setEnabled(
            not paused and self.reader is None and self.streak_run is None and self.streak_login is None
        )

    def tick(self):
        now = time.time()
        timer_gap = now - self.last_tick
        self.last_tick = now
        if not self.demo and datetime.fromtimestamp(now, VIETNAM).date() != self.dashboard_day:
            self.refresh_streak_history()
        if not self.demo and self.auto_streak_enabled():
            self.maybe_run_auto()
            return
        if now >= self.next_check or timer_gap > 45 or timer_gap < 0:
            self.run_check()

    def check_now(self):
        self.run_check()

    def run_check(self):
        if self.store.get("paused") == "1" or self.reader is not None or self.streak_run is not None:
            return
        self.next_check = time.time() + 3600
        if not self.demo:
            self.read_inbox()
            return
        self.save_content()
        result = check(self.store, self.messages)
        if result == Status.LOGIN_REQUIRED and self.store.get("login_notice") != "1":
            self.store.set("login_notice", "1")
            if self.tray.isVisible():
                self.tray.showMessage("StreakKeeper · Mô phỏng", result.value)
        self.update_summary()
        self.refresh_history()

    def read_conversation(self, row, column):
        if column == 0:
            item = self.live_table.item(row, column)
            self.read_inbox(item.data(Qt.ItemDataRole.UserRole))

    def read_inbox(self, target=""):
        if self.reader is not None or self.streak_run is not None or self.streak_login is not None:
            return
        if not (self.streak_profile / "Local State").is_file():
            self.complete_read("Vào Settings để đăng nhập TikTok cho hồ sơ nền.")
            return
        worker = InboxRead(self.streak_profile, self.store.get("tiktok_headless_owner"), target, self)
        self.reader = worker
        self.update_summary()
        self.live_state.setText("Đang đọc TikTok ở nền…")
        self.inbox_status.setText("Đang đọc hộp thư ở nền…")
        worker.finished.connect(self.finish_read)
        worker.start()

    def finish_read(self):
        worker, self.reader = self.reader, None
        snapshot = worker.snapshot
        error = worker.error
        worker.deleteLater()
        if snapshot is None:
            self.complete_read(error or "Đã dừng đọc hộp thư.")
            return
        conversations = snapshot["conversations"]
        self.store.confirm_tiktok_account(snapshot["owner"])
        self.store.set(f"auto_streak_auth/{snapshot['owner']}", "")
        self.show_conversations(conversations)
        self.refresh_streak_history()
        current = snapshot["current"]
        if current:
            latest = current.get("latestTime")
            timing = ("Mốc nhóm tin gần nhất" if current.get("latestTimeGrouped") else "Giờ tin gần nhất")
            time_summary = f"\n{timing}: {latest}" if latest else "\nChưa thấy mốc giờ cho tin gần nhất."
            composer = "Có ô soạn" if current["composer"] else "Chưa thấy ô soạn"
            self.chat_summary.setText(
                f'{current["name"]} · {current["count"]} tin đã tải '
                f'({current["text"]} văn bản, {current["videos"]} video) · {composer}\n'
                f'{current["incoming"]} tin khớp hồ sơ người kia · '
                f'{current["otherProfile"]} tin từ hồ sơ khác'
                f'{time_summary}'
            )
        else:
            self.chat_summary.setText("Nhấp đúp tên chat để xem số tin và giờ gần nhất.")
        self.complete_read(f"{len(conversations)} cuộc trò chuyện đang tải", clear=False)
        QTimer.singleShot(0, self.maybe_run_auto)

    def complete_read(self, message, *, clear=True):
        if clear:
            self.live_table.setRowCount(0)
            self.chat_summary.clear()
        for label in (self.live_state, self.inbox_status):
            label.setText(message)
            label.setWordWrap(True)
        self.update_summary()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path.home() / "Library/Application Support/StreakKeeper")
    parser.add_argument("--demo", action="store_true", help="Chạy với dữ liệu mô phỏng.")
    args = parser.parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_name = "demo.lock" if args.demo else "app.lock"
    with (data_dir / lock_name).open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("StreakKeeper đang chạy với thư mục dữ liệu này.", file=sys.stderr)
            return 1
        app = QApplication(sys.argv[:1])
        app.setApplicationName("StreakKeeper")
        database = "demo.sqlite3" if args.demo else "app.sqlite3"
        window = Window(Store(data_dir / database), data_dir, demo=args.demo)
        window.show()
        return app.exec()


if __name__ == "__main__":
    sys.exit(main())
