from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import Qt, QIcon

from videotrans.configure.config import ROOT_DIR, tr


class Ui_lawalert(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.main=parent
        self.setupUi(self)
        self.setWindowIcon(QIcon(f"{ROOT_DIR}/videotrans/styles/icon.ico"))

    def setupUi(self, lawalert):

        lawalert.setObjectName("lawalert")
        lawalert.setWindowModality(QtCore.Qt.ApplicationModal)
        lawalert.resize(950, 600)
        flags = QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lawalert.sizePolicy().hasHeightForWidth())
        lawalert.setSizePolicy(sizePolicy)
        self.v1 = QtWidgets.QVBoxLayout(lawalert)
        # 将 v1 设为垂直顶部对齐
        self.v1.setAlignment(Qt.AlignTop)

        self.text1 = QtWidgets.QTextEdit()
        self.text1.setObjectName("text1")
        self.text1.setReadOnly(True)
        self.text1.setMinimumHeight(400)
        self.text1.setHtml("""<!DOCTYPE html>
<html>
<head>
<style>
    body {  line-height: 1.6; font-size: 15px; }
    h1 { font-size: 22px;  border-bottom: 1px solid #eee; padding-bottom: 10px; }
    h2 { font-size: 18px;  margin-top: 30px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 8px; }
    p { margin-bottom: 12px; }
    strong, b { color: #c0392b; }
    code { padding: 2px 5px; border-radius: 3px; }
    .warning {
        border-left: 5px solid #c0392b;
        padding: 10px 15px;
        margin: 15px 0;
    }
</style>
</head>
<body>

<h1>Thỏa thuận Giấy phép và Dịch vụ phần mềm pyVideoTrans</h1>
<p>Ngày cập nhật: Ngày 21 tháng 10 năm 2025</p>

<p>Chào mừng bạn sử dụng pyVideoTrans (sau đây gọi tắt là "phần mềm")! Đây là công cụ mã nguồn mở và miễn phí dùng để dịch video và phiên âm giọng nói cục bộ. Trước khi cài đặt, sao chép hoặc sử dụng phần mềm, vui lòng đọc kỹ và hiểu rõ các điều khoản trong thỏa thuận này.</p>

<p class="warning"><strong>Hành động cài đặt, sao chép, tải xuống hoặc sử dụng phần mềm đồng nghĩa với việc bạn đã đọc, hiểu và vô điều kiện chấp nhận toàn bộ các điều khoản trong thỏa thuận này. Nếu không đồng ý, vui lòng ngừng sử dụng và xóa phần mềm khỏi thiết bị của bạn.</strong></p>

<h2>1. Cấp phép và Tính chất phần mềm</h2>
<ul>
    <li><strong>Mã nguồn mở miễn phí</strong>: Phần mềm được phát hành miễn phí theo giấy phép GPL-v3. Bạn có thể lấy mã nguồn và bản dựng từ GitHub (<code>https://github.com/jianchang512/pyvideotrans</code>) hoặc trang tài liệu (<code>https://pyvideotrans.com</code>).</li>
    <li><strong>Nghiêm cấm bán thương mại</strong>: Nhà phát triển không ủy quyền cho bất kỳ cá nhân hay tổ chức nào bán phần mềm này. Mọi hành vi mua bán qua bên thứ ba đều không liên quan đến tác giả.</li>
    <li><strong>Lưu ý quan trọng:</strong> Đối với các API bên thứ ba, bạn cần tự cung cấp tài khoản và khóa API (chỉ lưu trữ cục bộ). Chi phí phát sinh do nhà cung cấp API thu, không liên quan đến tác giả.</li>
</ul>

<h2>2. Quyền riêng tư dữ liệu</h2>
<ul>
    <li><strong>Chạy cục bộ</strong>: Toàn bộ tính năng cốt lõi chạy hoàn toàn trên máy tính của bạn, không thu thập hoặc tải lên thông tin cá nhân, tệp video hay dữ liệu của bạn lên máy chủ tác giả.</li>
    <li><strong>Dịch vụ bên thứ ba</strong>: Khi bạn chọn sử dụng các dịch vụ API tích hợp (như Microsoft Azure, OpenAI, Edge TTS...), dữ liệu sẽ được gửi trực tiếp từ máy tính của bạn tới nhà cung cấp đó.</li>
</ul>

<h2>3. Tuyên bố từ chối trách nhiệm</h2>
<p class="warning">
    <strong>Phần mềm được cung cấp theo nguyên trạng ("AS IS"), không kèm theo bất kỳ bảo đảm nào, dù rõ ràng hay ngụ ý.</strong>
</p>
<ul>
    <li><strong>Không bảo đảm</strong>: Tác giả không đảm bảo phần mềm đáp ứng mọi nhu cầu của bạn hay hoạt động không có lỗi. Bạn tự chịu mọi rủi ro khi sử dụng.</li>
    <li><strong>Giới hạn trách nhiệm</strong>: Trong mọi trường hợp, tác giả không chịu trách nhiệm đối với bất kỳ thiệt hại trực tiếp, gián tiếp, ngẫu nhiên hoặc do hậu quả nào phát sinh từ việc sử dụng phần mềm.</li>
</ul>

<p>Nếu bạn đã đọc và đồng ý với tất cả các điều khoản trên, vui lòng nhấp vào "<strong>Đồng ý và Tiếp tục</strong>" để bắt đầu sử dụng.</p>

</body>
</html>
"""
                                )
        # text1的边框合为0
        self.text1.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.text1.setStyleSheet("""
        border:none;
        """)
        self.v1.addWidget(self.text1)


        lawbtn = QtWidgets.QPushButton()
        lawbtn.setFixedHeight(35)
        lawbtn.setMaximumWidth(300)

        lawbtn.setCursor(Qt.PointingHandCursor)
        lawbtn.setText(tr("I Agree and Continue"))
        lawbtn.clicked.connect(lambda :self._close(True))

        dont = QtWidgets.QPushButton()
        dont.setFixedHeight(35)
        dont.setMaximumWidth(200)

        dont.setCursor(Qt.PointingHandCursor)
        dont.setText(tr("Disagree"))
        dont.clicked.connect(lambda :self._close(False))

        btn_h=QtWidgets.QHBoxLayout()
        btn_h.addWidget(lawbtn)
        btn_h.addWidget(dont)
        self.v1.addLayout(btn_h)

        lawalert.setWindowTitle('pyVideoTrans '+tr('Software License Agreement'))

    def _close(self,res=True):
        if res:
            Path(ROOT_DIR+"/.agree.txt").write_text("Yes,I Agree and Continue ")
            self.close()
        else:
            self.hide()
            self.main.close()
            Path(ROOT_DIR+"/.agree.txt").unlink(missing_ok=True)
            self.close()



