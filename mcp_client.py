from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import asyncio
import os
load_dotenv()


os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")

from langchain_openai import ChatOpenAI
model = ChatOpenAI()




async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["math_mcp_server.py"],
                "transport": "stdio",
            },
            "search":{
                "url": "http://localhost:8000/mcp/",
                "transport": "streamable_http",
            }

        }
    )
    tools = await client.get_tools()

    # Create ToolNode
    tool_node = ToolNode(tools)

    # Bind tools to model
    model_with_tools = model.bind_tools(tools)



    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        print(last_message.tool_calls)
        if last_message.tool_calls:
            return "tools"
        return END

    # Define call_model function
    async def call_model(state: MessagesState):
        messages = state["messages"]
        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # Build the graph
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        should_continue,
    )
    builder.add_edge("tools", "call_model")

    # Compile the graph
    graph = builder.compile()

    # Test the graph
    math_response = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )

    search_response = await graph.ainvoke(
    {"messages": [{"role": "user", "content": "who won the IPL 2025?"}]})

    print(math_response["messages"][-1].content)
    print(search_response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())