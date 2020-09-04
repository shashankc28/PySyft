from syft.grid.connections.webrtc import WebRTCConnection
from syft.core.node.domain.domain import Domain
from syft.core.node.common.service.repr_service import ReprMessage
from syft.core.io.address import Address
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

from aiortc import RTCSessionDescription
from aiortc.contrib.signaling import object_from_string
from aiortc.contrib.signaling import object_to_string
import pytest
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()


def get_signing_key() -> SigningKey:
    # return a the signing key used to sign the get_signed_message_bytes fixture
    key = "e89ff2e651b42393b6ecb5956419088781309d953d72bd73a0968525a3a6a951"
    return SigningKey(bytes.fromhex(key))


def test_init_without_event_loop() -> None:
    domain = Domain(name="test")
    webrtc = WebRTCConnection(node=domain)


@pytest.mark.asyncio
async def test_signaling_process() -> None:
    domain = Domain(name="test")
    webrtc = WebRTCConnection(node=domain)

    offer_payload = await webrtc._set_offer()
    offer_dict = json.loads(offer_payload)
    aiortc_session = object_from_string(offer_payload)

    assert "sdp" in offer_dict
    assert "type" in offer_dict
    assert offer_dict["type"] == "offer"
    assert isinstance(aiortc_session, RTCSessionDescription)

    answer_webrtc = WebRTCConnection(node=domain)
    answer_payload = await answer_webrtc._set_answer(payload=offer_payload)
    answer_dict = json.loads(answer_payload)
    aiortc_session = object_from_string(answer_payload)

    assert "sdp" in answer_dict
    assert "type" in answer_dict
    assert answer_dict["type"] == "answer"
    assert isinstance(aiortc_session, RTCSessionDescription)

    response = await webrtc._process_answer(payload=answer_payload)
    assert response == None


@pytest.mark.asyncio
async def test_consumer_request() -> None:
    test_domain = Domain(name="test")
    domain_client = test_domain.get_client()

    webrtc_node = WebRTCConnection(node=test_domain)

    msg = ReprMessage(address=test_domain.address)
    signing_key = SigningKey.generate()
    test_domain.root_verify_key = signing_key.verify_key
    signed_msg = msg.sign(signing_key=signing_key)

    msg_bin = signed_msg.to_binary()

    await webrtc_node.consumer(msg=msg_bin)


@pytest.mark.asyncio
async def test_consumer_response() -> None:
    test_domain = Domain(name="test")
    domain_client = test_domain.get_client()

    webrtc_node = WebRTCConnection(node=test_domain)

    msg = ReprMessage(address=domain_client.address)
    signing_key = SigningKey.generate()
    test_domain.root_verify_key = signing_key.verify_key
    signed_msg = msg.sign(signing_key=signing_key)

    msg_bin = signed_msg.to_binary()

    await webrtc_node.consumer(msg=msg_bin)

    recv_msg = await webrtc_node.consumer_pool.get()

    assert recv_msg == msg
