"""Minh hoạ FUNCTION CALLING với 9Router thông qua thư viện OpenAI.

Cách chạy:
    pip install openai python-dotenv
    python weather_function_calling.py
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load .env từ thư mục gốc của project
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Khởi tạo client OpenAI kết nối tới 9Router từ .env
client = OpenAI(
    api_key=os.getenv("MODEL_API_KEY"),
    base_url=os.getenv("MODEL_BASE_URL")
)

MODEL = os.getenv("MODEL_USING")

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

# 1. Định nghĩa schema của tool theo chuẩn OpenAI
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. App tự thực thi tool (giữ nguyên logic gốc)
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


def run(prompt: str) -> str:
    """Gửi *prompt* tới 9Router, xử lý function calling và trả về câu trả lời."""
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt}
    ]

    # 3. Gọi model 
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    
    # 4. Vòng lặp: nếu model yêu cầu gọi tool
    while response_message.tool_calls:
        # Lưu lại tin nhắn yêu cầu gọi tool của Assistant vào lịch sử
        messages.append(response_message)
        
        # Duyệt qua các tool mà model muốn gọi
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "get_weather":
                print(f"  [model yêu cầu] {function_name}({function_args})")
                
                # Thực thi hàm local
                result = get_weather(**function_args)
                print(f"  [app thực thi]  -> {result}")
                
                # Trả kết quả của tool về lại cho model
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result
                })
        
        # Gửi lại lịch sử (kèm kết quả tool) cho model tiếp tục phản hồi
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        response_message = response.choices[0].message

    # 5. Model tổng hợp và trả về text cuối cùng
    return response_message.content

if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
