"""
Agent tuỳ chỉnh dùng 9router LLM + kết nối tới MCP Server qua HTTP.
"""
import os
import json
import asyncio
import httpx
from openai import OpenAI
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

# Load config từ .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(env_path)

MCP_SERVER_URL = "http://localhost:8085/mcp"
MODEL = os.getenv("MODEL_USING", "oc/mimo-v2.5-free")

client = OpenAI(
    api_key=os.getenv("MODEL_API_KEY"),
    base_url=os.getenv("MODEL_BASE_URL")
)

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thông minh. Hãy tận dụng các tool cung cấp để tra cứu thông tin "
    "khi người dùng hỏi. Dữ liệu này là lấy thật từ WeatherAPI. Hãy trả lời bằng tiếng Việt, dùng emoji sinh động và format markdown đẹp mắt."
)

def mcp_tool_to_openai_schema(mcp_tool) -> dict:
    """Chuyển đổi từ MCP Tool Schema sang OpenAI Tool Schema."""
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }

async def run_agent(prompt: str):
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        # 1. Kết nối tới MCP Server
        async with streamable_http_client(MCP_SERVER_URL, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 2. Khám phá tools từ server tự động
                mcp_tools = await session.list_tools()
                openai_tools = [mcp_tool_to_openai_schema(t) for t in mcp_tools.tools]
                
                print(f"📡 Đã lấy {len(openai_tools)} tools từ server:")
                for t in openai_tools:
                    print(f"  - {t['function']['name']}")
                
                messages = [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt}
                ]
                
                print(f"\n🗣️ User: {prompt}")
                print("🤔 Đang suy nghĩ...")
                
                # 3. Chuyển cho 9router LLM phân tích
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )
                
                response_message = response.choices[0].message
                
                # 4. Vòng lặp Function Calling
                while response_message.tool_calls:
                    messages.append(response_message.model_dump(exclude_unset=True))
                    
                    for tool_call in response_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        print(f"  [Model Yêu Cầu] 🛠️ {func_name}({func_args})")
                        
                        # Chạy tool trên Remote MCP Server!
                        result = await session.call_tool(func_name, func_args)
                        result_text = result.content[0].text
                        print(f"  [Server Trả Về] 📩 Dữ liệu đã nhận thành công")
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": result_text
                        })
                    
                    # Gửi lại kết quả cho LLM
                    print("🤔 Đang tổng hợp kết quả...")
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        tools=openai_tools,
                    )
                    response_message = response.choices[0].message
                
                print(f"\n🤖 Agent:\n{response_message.content}")


if __name__ == "__main__":
    import sys
    question = "Thời tiết Đà Nẵng hôm nay thế nào? Và dự báo 2 ngày tới ra sao?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    asyncio.run(run_agent(question))
