import re,sys
import aiohttp
import requests
from requests.exceptions import TooManyRedirects, MissingSchema, InvalidSchema, InvalidURL, ProxyError, SSLError, \
    Timeout, ConnectionError as ReqConnectionError, RetryError, HTTPError
from tenacity import RetryError as TenRetryError
import httpx
from videotrans.configure.config import defaulelang


# 内部已整理好错误提示消息的异常，将ex=None,message='{错误消息}'
class VideoTransError(Exception):
    def __init__(self, message=''):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return str(self.message)


class TranslateSrtError(VideoTransError):
    pass


class DubbingSrtError(VideoTransError):
    pass


class SpeechToTextError(VideoTransError):
    pass


class LLMSegmentError(VideoTransError):
    pass

class FFmpegError(VideoTransError):
    pass

class DownloadModelsError(VideoTransError):
    pass


class SttTimeoutError(VideoTransError):
    pass




# 出现该类异常时，需要立即停止任务
class StopTask(VideoTransError):
    pass


class StopRetry(VideoTransError):
    pass


# 不可恢复，无需继续重试的异常
NO_RETRY_EXCEPT = (
    ConnectionError,

    TooManyRedirects,  # 重定向次数过多
    InvalidURL,  # URL 格式无效
    # 代理错误
    ProxyError,
    MissingSchema,
    InvalidSchema,
    SSLError,
    ReqConnectionError,

    httpx.ProxyError,
    httpx.ConnectError,
    httpx.InvalidURL,
    httpx.LocalProtocolError,
    httpx.ProtocolError,
    httpx.TooManyRedirects,
    httpx.UnsupportedProtocol,

    StopRetry,
    StopTask
)

"""Kiểm tra xem thông báo lỗi có chứa địa chỉ cục bộ hay không"""
def _is_local_address(url_or_message):
    if not url_or_message:
        return False

    text = str(url_or_message).lower()
    local_indicators = ['127.0.0.1', 'localhost', '0.0.0.0', '::1', '[::1]']

    return any(indicator in text for indicator in local_indicators)


"""Trích xuất địa chỉ API từ thông báo lỗi"""
def _extract_api_url_from_error(error):
    error_str = str(error)

    url_patterns = [
        r'https?://[^\s\'"]+',
        r'www\.[^\s\'"]+\.[a-z]{2,}',
        r'[a-zA-Z0-9.-]+\.[a-z]{2,}',
    ]

    for pattern in url_patterns:
        matches = re.findall(pattern, error_str)
        if matches:
            return matches[0]

    return None


"""Xử lý chi tiết lỗi kết nối mạng"""
def _handle_connection_error_detail(error, lang):
    error_str = str(error).lower()

    is_local = _is_local_address(error_str)
    api_url = _extract_api_url_from_error(error)

    base_message = ""

    if "dns" in error_str or "name or service not known" in error_str:
        base_message = (
            "Phân giải tên miền (DNS) thất bại, không tìm thấy địa chỉ máy chủ" if lang in ('zh', 'vi')
            else "Domain name resolution failed, cannot find server address"
        )
    elif "ProxyError" in error_str:
        base_message = (
            "Cài đặt proxy không đúng hoặc proxy không khả dụng, vui lòng kiểm tra lại proxy hoặc xóa nội dung ô proxy" if lang in ('zh', 'vi')
            else "The proxy address is not available, please check"
        )

    elif "refused" in error_str or "10061" in error_str or "积极拒绝" in error_str:
        if is_local:
            base_message = (
                "Kết nối bị từ chối, vui lòng đảm bảo dịch vụ cục bộ đã được khởi động và đang chạy" if lang in ('zh', 'vi')
                else "Connection refused, please ensure the local service is started and running"
            )
        else:
            base_message = (
                "Kết nối bị từ chối, không thể kết nối tới máy chủ đích" if lang in ('zh', 'vi')
                else "Connection refused"
            )
    elif "reset" in error_str:
        base_message = (
            "Kết nối bị đặt lại (reset), mạng có thể không ổn định" if lang in ('zh', 'vi')
            else "Connection reset, network may be unstable"
        )
    elif "timeout" in error_str or "timed out" in error_str:
        base_message = (
            "Kết nối mạng quá thời gian chờ (timeout), vui lòng kiểm tra đường truyền mạng" if lang in ('zh', 'vi')
            else "Connection timeout, please check network stability"
        )
    elif "max retries exceeded" in error_str:
        if is_local:
            if "0.0.0.0" in error_str:
                base_message = (
                    "Địa chỉ API không thể là 0.0.0.0, vui lòng đổi thành 127.0.0.1" if lang in ('zh', 'vi')
                    else "The API address cannot be 0.0.0.0, please change it to 127.0.0.1"
                )
            else:
                base_message = (
                    "Thử kết nối lại nhiều lần thất bại, vui lòng đảm bảo dịch vụ cục bộ đã khởi động" if lang in ('zh', 'vi')
                    else "Multiple connection retries failed, please ensure local service is properly started"
                )
        else:
            base_message = (
                "Thử kết nối lại nhiều lần thất bại, máy chủ dịch vụ có thể tạm thời không khả dụng" if lang in ('zh', 'vi')
                else "Multiple connection retries failed, service may be temporarily unavailable"
            )

    else:
        base_message = (
            "Kết nối mạng thất bại" if lang in ('zh', 'vi')
            else "Network connection failed"
        )

    if lang in ('zh', 'vi') and api_url and not is_local:
        if "api.msedgeservices.com" in api_url.lower():
            base_message += ". EdgeTTS sử dụng quá thường xuyên có thể bị giới hạn tần suất (rate limit), vui lòng thử lại sau ít phút."
            return base_message
        if "edge.microsoft.com" in api_url.lower():
            base_message += ". Microsoft Dịch thuật sử dụng quá thường xuyên có thể bị giới hạn, vui lòng thử lại sau."
            return base_message
        foreign_apis = ['openai', 'anthropic', 'claude', 'elevenlabs', 'deepgram', 'google', 'aws.amazon']
        if any(api in api_url.lower() for api in foreign_apis):
            base_message += ". Lưu ý: Một số dịch vụ quốc tế có thể cần kiểm tra đường truyền hoặc proxy."

    return base_message



def _nofoundfile(e,lang):
    filename=getattr(e, 'filename', '')
    if sys.platform=='win32' and filename and "/tmp/" not in filename and len(filename)>250:
        return f'Vui lòng kiểm tra tệp có tồn tại không. Nếu có, tên tệp có thể quá dài, hãy đổi tên ngắn hơn và chuyển vào thư mục nông hơn:\n{filename}' if lang in ('zh', 'vi') else f'The filename may be too long. Please rename it to a shorter name and move it to a shallow directory.:\n{filename}'
    return f"Không tìm thấy tệp: {filename}" if lang in ('zh', 'vi') else f"File not found: {filename}"

# Trả về thông báo lỗi có thể đọc được dựa trên loại ngoại lệ
def get_msg_from_except(ex:Exception)->str:
    if isinstance(ex, VideoTransError):
        return str(ex)

    lang = defaulelang
    if isinstance(ex, TenRetryError):
        try:
            ex = ex.last_attempt.exception()
        except AttributeError:
            pass
    from elevenlabs.core import ApiError as ApiError_11
    import httpcore
    from deepgram.clients.common.v1.errors import DeepgramApiError
    from openai import AuthenticationError, PermissionDeniedError, NotFoundError, BadRequestError, RateLimitError, \
    APIConnectionError, APIError, ContentFilterFinishReasonError, InternalServerError, LengthFinishReasonError

    exception_handlers = {
        # === Xác thực và quyền hạn ===
        AuthenticationError: lambda e: (
            f"Khóa API không chính xác, vui lòng kiểm tra lại: {e.message}" if lang in ('zh', 'vi')
            else (e.body.get('message') if e.body else e.message)
        ),

        PermissionDeniedError: lambda e: (
            f"Khóa hiện tại không có quyền truy cập, vui lòng kiểm tra lại quyền hạn: {e.message}" if lang in ('zh', 'vi')
            else (e.body.get('message') if e.body else e.message)
        ),

        (RateLimitError,InternalServerError, NotFoundError, BadRequestError, APIConnectionError, APIError): lambda e: e.body.get('message') if hasattr(e, 'body') and e.body else e.message,

        LengthFinishReasonError: lambda e: f'Nội dung quá dài vượt quá Token tối đa cho phép, hãy giảm bớt nội dung hoặc tăng max_tokens\n{e}' if lang in ('zh', 'vi') else f'{e}',
        ContentFilterFinishReasonError: lambda
            e: f"Nội dung vi phạm chính sách kiểm duyệt an toàn AI và đã bị lọc\n{e}" if lang in ('zh', 'vi') else f'Content triggers AI risk control and is filtered\n{e}',

        # === Cấu hình và địa chỉ URL ===
        (TooManyRedirects, MissingSchema, InvalidSchema, InvalidURL): lambda e: (
            f"Định dạng địa chỉ yêu cầu không hợp lệ, vui lòng kiểm tra cấu hình: {e.message}" if lang in ('zh', 'vi')
            else f"Request URL format is incorrect, check configuration {e.message}"
        ),

        (ProxyError, aiohttp.client_exceptions.ClientProxyConnectionError): lambda e: (
            "Cấu hình proxy không đúng hoặc proxy không khả dụng, vui lòng kiểm tra lại hoặc tắt proxy" if lang in ('zh', 'vi')
            else "Proxy configuration issue, check settings or disable proxy"
        ),
        SSLError: lambda e: (
            "Kết nối bảo mật SSL thất bại, vui lòng kiểm tra giờ hệ thống hoặc mạng (tắt proxy nếu có)" if lang in ('zh', 'vi')
            else "Secure connection failed, check system time or network settings"
        ),

        (HTTPError, RetryError): lambda e: f'{e}',

        DeepgramApiError: lambda e: e.message if hasattr(e, 'message') else str(e),
        ApiError_11: lambda e: e.body.get('detail', {}).get('message', e.body) if hasattr(e, 'body') else str(e),
        # === Kết nối mạng ===
        (ReqConnectionError, ConnectionError, ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError,
         httpcore.ConnectTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadError, Timeout): lambda e: (
            _handle_connection_error_detail(e, lang)
        ),

        (RuntimeError, ValueError, requests.exceptions.RequestException): lambda e: f"{e}",

        FileNotFoundError: lambda e: (
            _nofoundfile(e,lang)
        ),

        PermissionError: lambda e: (
            f"{e}：{getattr(e, 'filename', '')}"
        ),

        FileExistsError: lambda e: (
            f"Tệp đã tồn tại: {getattr(e, 'filename', '')}" if lang in ('zh', 'vi')
            else f"File already exists: {getattr(e, 'filename', '')}"
        ),

        # === Lỗi hệ điều hành ===
        OSError: lambda e: (
            f"Lỗi hệ thống ({e.errno})：{e.strerror}" if lang in ('zh', 'vi')
            else f"System Error ({e.errno}): {e.strerror}"
        ),

        # === Lỗi xử lý dữ liệu ===
        KeyError: lambda e: (
            f"Thiếu khóa dữ liệu cần thiết: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        IndexError: lambda e: (
            f"Chỉ số vượt ngoài giới hạn danh sách: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        LookupError: lambda e: (
            f"Lỗi tra cứu, không tìm thấy khóa hoặc chỉ số: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        UnicodeDecodeError: lambda e: (
            f"Giải mã tệp hoặc dữ liệu thất bại, lỗi định dạng mã hóa: {e.reason}" if lang in ('zh', 'vi')
            else f" {e.reason}"
        ),

        # === Lỗi nội bộ chương trình ===
        AttributeError: lambda e: (
            f"Lỗi chương trình: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        NameError: lambda e: (
            f"Lỗi chương trình, biến chưa được định nghĩa '{e.name}'" if lang in ('zh', 'vi') else f"{e}"
        ),

        TypeError: lambda e: (
            f"Lỗi chương trình: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        RecursionError: lambda e: (
            f"Lỗi chương trình, đệ quy vô hạn: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        ZeroDivisionError: lambda e: (
            f"Lỗi số học, chia cho 0: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        OverflowError: lambda e: (
            f"Lỗi số học, giá trị vượt quá giới hạn tối đa: {e}" if lang in ('zh', 'vi')
            else f"{e}"
        ),

        BrokenPipeError: lambda e: (
            "Đường ống kết nối bị đứt, vui lòng kiểm tra lại kết nối mạng" if lang in ('zh', 'vi')
            else "Broken pipe error, check network connection"
        ),
    }

    for exc_types, handler in exception_handlers.items():
        if isinstance(ex, exc_types):
            return handler(ex)

    error_str = str(ex)
    if any(keyword in error_str.lower() for keyword in [
        'connection', 'connect', 'refused', 'reset', 'timeout', 'retries',
        'kết nối', 'từ chối', 'đặt lại', 'quá giờ', 'thử lại', 'host', 'port', 'http', 'tcp', 'ProxyError'
    ]):
        return _handle_connection_error_detail(ex, lang)

    _msg = None
    if hasattr(ex, 'detail') and ex.detail:
        _msg = ex.detail
    elif hasattr(ex, 'body') and ex.body:
        _msg = ex.body
    elif hasattr(ex, 'error'):
        _msg = ex.error

    if _msg and isinstance(_msg, dict):
        if message := _msg.get('message'):
            return str(message)
        if error_info := _msg.get('error'):
            if isinstance(error_info, dict):
                return str(error_info.get('message', error_info))
            return str(error_info)
        return str(_msg)
    return ''
