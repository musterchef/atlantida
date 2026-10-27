import json
import socket

from pythonosc.osc_packet import OscPacket
from pythonosc.udp_client import SimpleUDPClient

from desnivel.adapters.voice_device import CONTROL_ADDRESS, DeviceVoice
from desnivel.cli.voice_device import VoiceDeviceServer
from desnivel.music.phrases import Note, Phrase


def test_device_handshake_and_phrase_over_local_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1', 0))
        receiver.settimeout(1)
        port = receiver.getsockname()[1]
        server = VoiceDeviceServer({'part': DeviceVoice(role='melody')}, port=0)
        try:
            client = SimpleUDPClient('127.0.0.1', server.server.server_address[1])
            client.send_message(CONTROL_ADDRESS, list(json.dumps(dict(
                version=1, voice='part', instance='device', serial=1,
                reply_port=port, action='hello')).encode('utf-8')))
            server.server.handle_request()
            packet = OscPacket(receiver.recv(65535)).messages[0].message
            state = json.loads(bytes(packet.params).decode('utf-8'))
            assert state['role'] == 'melody'
            phrase = Phrase(4, (Note(0, 64, 1, 80),))
            server.bridge.destination('part')(8, phrase)
            packet = OscPacket(receiver.recv(65535)).messages[0].message
            plan = json.loads(bytes(packet.params).decode('utf-8'))
            assert plan['voice'] == 'part' and plan['instance'] == 'device'
            assert plan['plan']['start'] == 8
            assert plan['plan']['phrase']['notes'][0]['pitch'] == 64
        finally:
            server.close()
