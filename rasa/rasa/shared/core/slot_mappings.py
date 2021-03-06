from enum import Enum
from typing import Text, Dict, Any, List, Optional, TYPE_CHECKING

from rasa.shared.constants import DOCS_URL_SLOTS, IGNORED_INTENTS
import rasa.shared.utils.io
from rasa.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_TYPE,
    ENTITY_ATTRIBUTE_ROLE,
    ENTITY_ATTRIBUTE_GROUP,
)

if TYPE_CHECKING:
    from rasa.shared.core.trackers import DialogueStateTracker
    from rasa.shared.core.domain import Domain


class SlotMapping(Enum):
    """Defines the available slot mappings."""

    FROM_ENTITY = 0
    FROM_INTENT = 1
    FROM_TRIGGER_INTENT = 2
    FROM_TEXT = 3
    CUSTOM = 4

    def __str__(self) -> Text:
        """Returns a string representation of the object."""
        return self.name.lower()

    @staticmethod
    def validate(mapping: Dict[Text, Any], slot_name: Text) -> None:
        """Validates a slot mapping.

        Args:
            mapping: The mapping which is validated.
            slot_name: The name of the slot which is mapped by this mapping.

        Raises:
            InvalidDomain: In case the slot mapping is not valid.
        """
        from rasa.shared.core.domain import InvalidDomain

        if not isinstance(mapping, dict):
            raise InvalidDomain(
                f"Please make sure that the slot mappings for slot '{slot_name}' in "
                f"your domain are valid dictionaries. Please see "
                f"{DOCS_URL_SLOTS} for more information."
            )

        validations = {
            str(SlotMapping.FROM_ENTITY): ["entity"],
            str(SlotMapping.FROM_INTENT): ["value"],
            str(SlotMapping.FROM_TRIGGER_INTENT): ["value"],
            str(SlotMapping.FROM_TEXT): [],
            str(SlotMapping.CUSTOM): [],
        }

        mapping_type = mapping.get("type")
        required_keys = validations.get(mapping_type)

        if required_keys is None:
            raise InvalidDomain(
                f"Your domain uses an invalid slot mapping of type "
                f"'{mapping_type}' for slot '{slot_name}'. Please see "
                f"{DOCS_URL_SLOTS} for more information."
            )

        for required_key in required_keys:
            if mapping.get(required_key) is None:
                raise InvalidDomain(
                    f"You need to specify a value for the key "
                    f"'{required_key}' in the slot mapping of type '{mapping_type}' "
                    f"for slot '{slot_name}'. Please see "
                    f"{DOCS_URL_SLOTS} for more information."
                )

    @staticmethod
    def _get_active_loop_ignored_intents(
        mapping: Dict[Text, Any], domain: "Domain", active_loop_name: Text,
    ) -> List[Text]:
        from rasa.shared.core.constants import ACTIVE_LOOP

        mapping_conditions = mapping.get("conditions")
        active_loop_match = True
        ignored_intents = []

        if mapping_conditions:
            match_list = [
                condition.get(ACTIVE_LOOP) == active_loop_name
                for condition in mapping_conditions
            ]
            active_loop_match = any(match_list)

        if active_loop_match:
            form_ignored_intents = domain.forms[active_loop_name].get(
                IGNORED_INTENTS, []
            )
            ignored_intents = SlotMapping.to_list(form_ignored_intents)

        return ignored_intents

    @staticmethod
    def intent_is_desired(
        mapping: Dict[Text, Any], tracker: "DialogueStateTracker", domain: "Domain",
    ) -> bool:
        """Checks whether user intent matches slot mapping intent specifications."""
        mapping_intents = SlotMapping.to_list(mapping.get("intent", []))
        mapping_not_intents = SlotMapping.to_list(mapping.get("not_intent", []))

        active_loop_name = tracker.active_loop_name
        if active_loop_name:
            mapping_not_intents = set(
                mapping_not_intents
                + SlotMapping._get_active_loop_ignored_intents(
                    mapping, domain, active_loop_name
                )
            )

        intent = tracker.latest_message.intent.get("name")

        intent_not_blocked = not mapping_intents and intent not in mapping_not_intents

        return intent_not_blocked or intent in mapping_intents

    # helpers
    @staticmethod
    def to_list(x: Optional[Any]) -> List[Any]:
        """Convert object to a list if it isn't."""
        if x is None:
            x = []
        elif not isinstance(x, list):
            x = [x]

        return x

    @staticmethod
    def entity_is_desired(
        mapping: Dict[Text, Any], tracker: "DialogueStateTracker",
    ) -> bool:
        """Checks whether slot should be filled by an entity in the input or not.

        Args:
            mapping: Slot mapping.
            tracker: The tracker.

        Returns:
            True, if slot should be filled, false otherwise.
        """
        slot_fulfils_entity_mapping = False
        extracted_entities = tracker.latest_message.entities

        for entity in extracted_entities:
            if (
                mapping.get(ENTITY_ATTRIBUTE_TYPE) == entity[ENTITY_ATTRIBUTE_TYPE]
                and mapping.get(ENTITY_ATTRIBUTE_ROLE)
                == entity.get(ENTITY_ATTRIBUTE_ROLE)
                and mapping.get(ENTITY_ATTRIBUTE_GROUP)
                == entity.get(ENTITY_ATTRIBUTE_GROUP)
            ):
                matching_values = tracker.get_latest_entity_values(
                    mapping.get(ENTITY_ATTRIBUTE_TYPE),
                    mapping.get(ENTITY_ATTRIBUTE_ROLE),
                    mapping.get(ENTITY_ATTRIBUTE_GROUP),
                )
                slot_fulfils_entity_mapping = matching_values is not None
                break

        return slot_fulfils_entity_mapping


def validate_slot_mappings(domain_slots: Dict[Text, Any]) -> None:
    """Raises InvalidDomain exception if slot mappings are invalid."""
    rasa.shared.utils.io.raise_warning(
        f"Slot auto-fill has been removed in 3.0 and replaced with a "
        f"new explicit mechanism to set slots. "
        f"Please refer to {DOCS_URL_SLOTS} to learn more.",
        UserWarning,
    )

    for slot_name, properties in domain_slots.items():
        mappings = properties.get("mappings")

        for slot_mapping in mappings:
            SlotMapping.validate(slot_mapping, slot_name)
