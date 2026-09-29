"""Config flow and lifecycle options for LockLearn."""

from typing import Any, override

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_CREATE_PERSONAL_PROFILE,
    CONF_PURGE_CONTENT_CACHE,
    CONF_RESTORE_SNAPSHOT,
    CONF_UI_LANGUAGE,
    CONF_UNINSTALL_DATA_POLICY,
    CONFIG_ENTRY_VERSION,
    DEFAULT_UI_LANGUAGE,
    DEFAULT_UNINSTALL_DATA_POLICY,
    DOMAIN,
    SUPPORTED_UI_LANGUAGES,
)
from .storage.database import StoragePaths
from .storage.lifecycle import StorageLifecycleManager, UninstallDataPolicy


def _format_bytes(value: int) -> str:
    """Format a byte count for Home Assistant flow descriptions."""
    amount = float(value)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    unit = units[0]
    for candidate in units:
        unit = candidate
        if amount < 1024 or candidate == units[-1]:
            break
        amount /= 1024
    if unit == "B":
        return f"{int(amount)} {unit}"
    return f"{amount:.1f} {unit}"


class LockLearnOptionsFlow(OptionsFlow):
    """Manage backup visibility, recovery, and uninstall retention policy."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        manager = StorageLifecycleManager(StoragePaths.from_config_dir(self.hass.config.config_dir))
        snapshots = await manager.async_valid_recovery_snapshots()
        snapshot_names = tuple(snapshot.name for snapshot in snapshots)

        errors: dict[str, str] = {}
        if user_input is not None:
            restore_snapshot = str(user_input.pop(CONF_RESTORE_SNAPSHOT, ""))
            purge_content_cache = bool(user_input.pop(CONF_PURGE_CONTENT_CACHE, False))
            policy = UninstallDataPolicy(str(user_input[CONF_UNINSTALL_DATA_POLICY]))
            storage_action_requested = bool(restore_snapshot or purge_content_cache)
            if storage_action_requested:
                was_loaded = self.config_entry.state is ConfigEntryState.LOADED
                if was_loaded and not await self.hass.config_entries.async_unload(
                    self.config_entry.entry_id
                ):
                    errors["base"] = "storage_unload_failed"
                else:
                    try:
                        if restore_snapshot:
                            await manager.async_restore_snapshot(restore_snapshot)
                        if purge_content_cache:
                            await manager.async_delete_content_cache()
                    except (OSError, RuntimeError):
                        errors["base"] = "storage_action_failed"
                    finally:
                        # A loaded runtime must always be recreated after the offline
                        # action. A previously failed runtime is retried after explicit
                        # recovery so a successful restore can clear its Repair.
                        if (
                            was_loaded or restore_snapshot or purge_content_cache
                        ) and not await self.hass.config_entries.async_setup(
                            self.config_entry.entry_id
                        ):
                            errors.setdefault("base", "storage_reload_failed")
            if not errors:
                return self.async_create_entry(
                    title="",
                    data={CONF_UNINSTALL_DATA_POLICY: policy.value},
                )

        usage = await manager.async_usage()
        current_policy = str(
            self.config_entry.options.get(
                CONF_UNINSTALL_DATA_POLICY,
                DEFAULT_UNINSTALL_DATA_POLICY,
            )
        )
        valid_policies = tuple(policy.value for policy in UninstallDataPolicy)
        if current_policy not in valid_policies:
            current_policy = DEFAULT_UNINSTALL_DATA_POLICY
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_UNINSTALL_DATA_POLICY,
                default=current_policy,
            ): vol.In(valid_policies),
            vol.Optional(CONF_PURGE_CONTENT_CACHE, default=False): bool,
        }
        if snapshot_names:
            schema[vol.Optional(CONF_RESTORE_SNAPSHOT, default="")] = vol.In(("", *snapshot_names))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "state_size": _format_bytes(usage.state_bytes),
                "content_cache_size": _format_bytes(usage.content_cache_bytes),
                "asset_size": _format_bytes(usage.asset_bytes),
                "recovery_size": _format_bytes(usage.recovery_snapshot_bytes),
                "backup_policy": usage.backup_policy,
                "snapshot_count": str(len(snapshot_names)),
            },
        )


class LockLearnConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the LockLearn config flow."""

    VERSION = CONFIG_ENTRY_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the storage/recovery options flow."""
        return LockLearnOptionsFlow()

    @override
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create the single LockLearn config entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="LockLearn",
                data=user_input,
                options={
                    CONF_UNINSTALL_DATA_POLICY: DEFAULT_UNINSTALL_DATA_POLICY,
                },
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_CREATE_PERSONAL_PROFILE, default=True): bool,
                vol.Optional(CONF_UI_LANGUAGE, default=DEFAULT_UI_LANGUAGE): vol.In(
                    SUPPORTED_UI_LANGUAGES
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
