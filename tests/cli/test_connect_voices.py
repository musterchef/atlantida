import socket

import pytest
from pythonosc.osc_packet import OscPacket

from desnivel.cli.connect_voices import CONNECT_ALL_ADDRESS, main


def test_connect_all_sends_one_local_osc_request(capsys):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1', 0))
        receiver.settimeout(1)
        assert main(['--port', str(receiver.getsockname()[1])]) == 0
        packet = OscPacket(receiver.recv(65535)).messages[0].message
    assert packet.address == CONNECT_ALL_ADDRESS
    assert packet.params == []
    assert 'Richiesta Collega tutte inviata' in capsys.readouterr().out


@pytest.mark.parametrize('port', ['0', '1023', '65536'])
def test_connect_all_rejects_invalid_port(port):
    with pytest.raises(SystemExit) as error:
        main(['--port', port])
    assert error.value.code == 2
