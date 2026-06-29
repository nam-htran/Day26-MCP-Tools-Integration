# Examples — Function Calling vs MCP

Cùng một tool `get_weather`, hai cách triển khai chạy được để so sánh.

## Cách chạy nhanh (ví dụ MCP, không cần API key)

```bash
cd examples
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd mcp && python weather_client.py
```

Kết quả mong đợi:

```
Tools server cung cấp:
  - get_weather: Lấy thời tiết hiện tại của một thành phố.

call_tool get_weather(city='Hà Nội'):
  -> Hà Nội: 29°C, trời mưa

call_tool get_weather(city='Đà Nẵng'):
  -> Đà Nẵng: 30°C, nhiều mây

call_tool get_weather(city='Hải Phòng'):
  -> Hải Phòng: 33°C, mưa rào
```

## Cài đặt

```bash
cd examples
python -m venv venv && source venv/bin/activate 
pip install -r requirements.txt
```

## 1. Function Calling thuần

Tool được định nghĩa schema thủ công và thực thi ngay trong app. Cần API key.

```bash
export GEMINI_API_KEY=...
cd function_calling
python weather_function_calling.py
```

## 2. MCP

Tool nằm ở một server độc lập, client khám phá và gọi qua giao thức MCP.
Không cần API key (minh hoạ riêng lớp giao thức).

```bash
cd mcp
python weather_client.py   # client tự khởi động weather_server.py
```

Đăng ký server với Claude Code để dùng trong chat (làm 1 lần):

```bash
claude mcp add weather -- /đường/dẫn/tới/venv/bin/python /đường/dẫn/tới/weather_server.py
```

Đăng ký server với Antigravity CLI (làm 1 lần):

```bash
vim ~/.gemini/config/mcp_config.json

"weather": {
    "command": "/đường/dẫn/tới/venv/bin/python",
    "args": [
      "/đường/dẫn/tới/weather_server.py"
    ]
}
```

## Khác biệt chính

| | Function Calling | MCP |
|---|---|---|
| Khai báo schema | Viết tay trong app | `@mcp.tool()` tự sinh từ type hints |
| Nơi thực thi tool | Trong app gọi model | Trong MCP server riêng |
| Khám phá tool | Hard-code danh sách | `session.list_tools()` tại runtime |
| Dùng lại ở app khác | Copy code | Cắm thêm client, không sửa server |

Xem giải thích đầy đủ ở [../README.md](../README.md).
