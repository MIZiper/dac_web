"""Built-in replacement rules.

These serve as examples and defaults.  The ANB mapping stub will be
resolved once the ANB data-source lookup API is available.
"""

from dac_web.import_replace import (
    ActionReplacementRule,
    ReplaceOutcome,
    ReplacementStatus,
)


class LoadActionToAnbRule(ActionReplacementRule):
    """Replace desktop ``LoadAction`` (local TDMS) with ANB data-source loading."""

    source_class = "dac.modules.timedata.actions.LoadAction"
    name = "Local TDMS → ANB data source"
    description = (
        "Replace local TDMS file load with ANB data-source load. "
        "Requires a mapping from file paths to ANB node + channel identifiers."
    )

    async def transform(self, action: dict) -> ReplaceOutcome:
        fpaths: list[str] = action.get("fpaths", [])

        if not fpaths:
            return ReplaceOutcome(
                action=None,
                summary="LoadAction has no file paths — keeping as-is",
                status=ReplacementStatus.UNCHANGED,
            )

        # ----------------------------------------------------------------
        # TODO: call ANB mapping service when available.
        #
        #   mapped = await _anb_mapping_service.resolve(fpaths)
        #   if mapped is None:
        #       return ReplaceOutcome.unresolved(...)
        #   node_id, channel_names = mapped
        #
        #   new_action = {
        #       "_uuid_": action["_uuid_"],
        #       "_class_": "dac_web.actions.AnbLoadAction",
        #       "name": f"Load from ANB: {action.get('name', '')}",
        #       "node_id": node_id,
        #       "channels": channel_names,
        #       "_context_": action.get("_context_"),
        #   }
        #   return ReplaceOutcome.resolved(new_action, ...)
        # ----------------------------------------------------------------

        file_list = ", ".join(fpaths[:3])
        if len(fpaths) > 3:
            file_list += f" ... (+{len(fpaths) - 3})"

        return ReplaceOutcome(
            action=None,
            summary=f"LoadAction({len(fpaths)} files) — ANB mapping not yet available",
            status=ReplacementStatus.UNRESOLVED,
            reason=f"Cannot map local files to ANB data source: {file_list}",
        )
