import asyncio
import websockets

# Shared state: our boolean flag
class AppState:
    is_panel_visible = True

state = AppState()

async def handler(websocket):
    print("Client connected!")
    async for message in websocket:
        # Check the message to change the flag
        if message.lower() == "toggle":
            state.is_panel_visible = not state.is_panel_visible
        elif message.lower() == "true":
            state.is_panel_visible = True
        elif message.lower() == "false":
            state.is_panel_visible = False
            
        print(f"Flag changed to: {state.is_panel_visible}")
        await websocket.send(f"Server updated visibility to: {state.is_panel_visible}")

async def main():
    # Start the server on localhost port 8765
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket Server running on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running forever

if __name__ == "__main__":
    asyncio.run(main())