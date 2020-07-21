# Acapy
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.plugin_registry import PluginRegistry
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager

# Records, messages and schemas
from aries_cloudagent.messaging.agent_message import AgentMessage, AgentMessageSchema
from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.storage.record import StorageRecord

# Exceptions
from aries_cloudagent.storage.error import StorageDuplicateError, StorageNotFoundError
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport

# Internal
from .records import (
    ServiceRecord,
    ServiceRecordSchema,
    ConsentSchema,
    ServiceSchema,
    ServiceDiscoveryRecord,
)
from .message_types import (
    PROTOCOL_PACKAGE_DISCOVERY as PROTOCOL_PACKAGE,
    DISCOVERY,
    DISCOVERY_RESPONSE,
)
from .util import generate_model_schema

# External
from marshmallow import fields
import hashlib
import uuid
import json


Discovery, DiscoverySchema = generate_model_schema(
    name="Discovery",
    handler=f"{PROTOCOL_PACKAGE}.DiscoveryHandler",
    msg_type=DISCOVERY,
    schema={},
)


class DiscoveryResponse(AgentMessage):
    class Meta:
        handler_class = f"{PROTOCOL_PACKAGE}.DiscoveryResponseHandler"
        message_type = DISCOVERY_RESPONSE
        schema_class = "DiscoveryResponseSchema"

    def __init__(self, *, services: list = None, **kwargs):
        super(DiscoveryResponse, self).__init__(**kwargs)
        self.services = services if services else []


class DiscoveryResponseSchema(AgentMessageSchema):
    """DiscoveryResponse message schema used in serialization/deserialization."""

    class Meta:
        model_class = DiscoveryResponse

    services = fields.List(fields.Nested(ServiceRecordSchema()), required=False,)


class DiscoveryHandler(BaseHandler):
    async def handle(self, context: RequestContext, responder: BaseResponder):
        storage: BaseStorage = await context.inject(BaseStorage)

        self._logger.debug("SERVICES DISCOVERY %s, ", context)
        assert isinstance(context.message, Discovery)

        query = await ServiceRecord().query(context)

        response = DiscoveryResponse(services=query)
        response.assign_thread_from(context.message)
        await responder.send_reply(response)


class DiscoveryResponseHandler(BaseHandler):
    async def handle(self, context: RequestContext, responder: BaseResponder):
        self._logger.debug("SERVICES DISCOVERY RESPONSE %s, ", context)
        assert isinstance(context.message, DiscoveryResponse)

        record = ServiceDiscoveryRecord(
            services=context.message.services,
            connection_id=context.connection_record.connection_id,
        )

        await record.save(context)