from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.storage.record import StorageRecord
from aries_cloudagent.core.plugin_registry import PluginRegistry
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.messaging.agent_message import AgentMessage, AgentMessageSchema

from marshmallow import fields
from .util import generate_model_schema
import uuid

PROTOCOL_URL = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/acapy-plugin/1.0/records"

RECORDS_ADD = f"{PROTOCOL_URL}/add"
RECORDS_GET = f"{PROTOCOL_URL}/get"

PROTOCOL_PACKAGE = "acapy_plugin"
RECORDS = f"{PROTOCOL_PACKAGE}.records"

MESSAGE_TYPES = {
    RECORDS_ADD: f"{RECORDS}.RecordsAdd",
    RECORDS_GET: f"{RECORDS}.RecordsGet",
}

RECORDS_ADD_HANDLER = f"{RECORDS}.RecordsAddHandler"
RECORDS_GET_HANDLER = f"{RECORDS}.RecordsGetHandler"


RecordsAdd, RecordsAddSchema = generate_model_schema(
    name="RecordsAdd",
    handler=RECORDS_ADD_HANDLER,
    msg_type=RECORDS_ADD,
    schema={
        "payload": fields.Str(required=True),
        "record_id": fields.Str(required=False),
    },
)


class RecordsAddHandler(BaseHandler):
    async def handle(self, context: RequestContext, responder: BaseResponder):
        storage: BaseStorage = await context.inject(BaseStorage)

        self._logger.debug("RecordsAddHandler called with context %s", context)
        assert isinstance(context.message, RecordsAdd)

        record = StorageRecord(type="OCASchema", value=context.message.payload)
        await storage.add_record(record)

        reply = RecordsAdd(payload=record.value, record_id=record.id)

        reply.assign_thread_from(context.message)
        await responder.send_reply(reply)


RecordsGet, RecordsGetSchema = generate_model_schema(
    name="RecordsGet",
    handler=RECORDS_GET_HANDLER,
    msg_type=RECORDS_GET,
    schema={"record_id": fields.Str(required=True),},
)


class RecordsGetHandler(BaseHandler):
    async def handle(self, context: RequestContext, responder: BaseResponder):
        storage: BaseStorage = await context.inject(BaseStorage)

        self._logger.debug("RecordsGetHandler called with context %s", context)
        assert isinstance(context.message, RecordsGet)

        record = await storage.get_record("OCASchema", context.message.record_id)

        reply = RecordsAdd(record_id=record.id, payload=record.value)

        reply.assign_thread_from(context.message)
        await responder.send_reply(reply)