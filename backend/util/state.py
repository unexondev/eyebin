from fastapi import WebSocket, Request

from .broadcast import BroadcastManager 


def broadcast_manager_from_request(request : Request) -> BroadcastManager:
    return request.app.state.broadcast_manager

def broadcast_manager_from_websocket(socket : WebSocket) -> BroadcastManager:
    return socket.app.state.broadcast_manager