"""HTTP client for the fixed public Image PPT 5.0 surface.

The image client intentionally lives beside, rather than inside, the existing
HTML client.  It shares only the transport and error types; route policy and
payload construction stay image-specific so a caller cannot accidentally
select an HTML intent, requirement, color, model, or provider.
"""

from __future__ import annotations

from typing import Any

from .client import PlatformError, PptgenClient


IMAGE_5_0_CONFIG_NAME = "Codex Native Image 5.0 Sol Low Director"
IMAGE_GENERATE_MODES = ("auto", "manual")
IMAGE_PRODUCT = "image-pptgen"
IMAGE_SERVICE = "image-pptgen-server"
IMAGE_SURFACE = "public_image_3_0"
IMAGE_DATA_ROOT = "image-pptgen/state/data"
IMAGE_ARTIFACTS_ROOT = "image-pptgen/state/data/artifacts"
IMAGE_RUNTIME_IDENTITY_FIELDS = (
    "artifacts_root",
    "base_url",
    "build_id",
    "data_root",
    "instance_id",
    "product",
    "service",
    "skill_sha256",
    "source_commit",
    "surface",
    "runtime_content_sha256",
    "version",
)


def _require_dict(result: Any, message: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise PlatformError(message)
    return result


def _require_split_draft(result: Any) -> dict[str, Any]:
    payload = _require_dict(result, "PPTGen Platform returned an invalid split draft")
    if not isinstance(payload.get("id"), int) or not isinstance(
        payload.get("slides"), list
    ):
        raise PlatformError("PPTGen Platform returned an invalid split draft")
    return payload


class ImagePptgenClient(PptgenClient):
    """Client for the fixed Image 5.0 public API.

    The inherited ``_request`` method is transport-only and does not choose a
    route.  Every mutating method below constructs its complete, fixed public
    payload explicitly.
    """

    def health(self) -> dict[str, Any]:
        identity = _require_dict(
            self._request("GET", "/api/runtime-identity"),
            "PPTGen Platform returned an invalid Image runtime identity",
        )
        missing = [
            field
            for field in IMAGE_RUNTIME_IDENTITY_FIELDS
            if not isinstance(identity.get(field), str) or not identity[field].strip()
        ]
        if missing:
            raise PlatformError(
                "PPTGen Platform Image runtime identity is missing: " + ", ".join(missing)
            )
        expected = {
            "artifacts_root": IMAGE_ARTIFACTS_ROOT,
            "data_root": IMAGE_DATA_ROOT,
            "product": IMAGE_PRODUCT,
            "service": IMAGE_SERVICE,
            "surface": IMAGE_SURFACE,
        }
        for field, value in expected.items():
            if identity[field] != value:
                raise PlatformError(f"PPTGen Platform Image {field.replace('_', ' ')} mismatch")
        return {**identity, "ok": True}

    def create_split_draft(self, *, deck_id: int) -> dict[str, Any]:
        # The public endpoint owns mode/model/profile/content mode.  An empty
        # object is deliberate: no caller-supplied split override is accepted.
        result = self._request(
            "POST",
            f"/api/decks/{deck_id}/split-drafts",
            {},
            timeout=self.long_timeout,
        )
        return _require_split_draft(result)

    def revise_split_draft(
        self,
        *,
        draft_id: int,
        instruction: str | None = None,
        target_page_count: int | None = None,
        allow_title_changes: bool = False,
    ) -> dict[str, Any]:
        if instruction is not None and target_page_count is not None:
            raise PlatformError(
                "Image split revision accepts instruction or target_page_count, not both"
            )
        if instruction is None and target_page_count is None:
            raise PlatformError(
                "Image split revision requires instruction or target_page_count"
            )
        if type(allow_title_changes) is not bool or (
            allow_title_changes and instruction is None
        ):
            raise PlatformError(
                "Image split revision allow_title_changes requires instruction"
            )
        if instruction is not None:
            if not isinstance(instruction, str) or not instruction.strip():
                raise PlatformError(
                    "Image split revision requires a non-empty instruction"
                )
            payload = {"instruction": instruction}
            if allow_title_changes:
                payload["allow_title_changes"] = True
        else:
            if type(target_page_count) is not int:
                raise PlatformError(
                    "Image split revision target_page_count must be an integer"
                )
            payload = {"target_page_count": target_page_count}
        result = self._request(
            "POST",
            f"/api/deck-split-drafts/{draft_id}/revise",
            payload,
            timeout=self.long_timeout,
        )
        return _require_split_draft(result)

    def confirm_split_draft(self, *, draft_id: int) -> dict[str, Any]:
        result = _require_dict(
            self._request("POST", f"/api/deck-split-drafts/{draft_id}/confirm"),
            "PPTGen Platform returned an invalid confirmation",
        )
        slide_ids = result.get("slide_ids")
        if (
            not isinstance(slide_ids, list)
            or not slide_ids
            or not all(type(slide_id) is int and slide_id > 0 for slide_id in slide_ids)
        ):
            raise PlatformError("PPTGen Platform returned an invalid confirmation")
        deck_id = result.get("deck_id")
        if type(deck_id) is not int or deck_id <= 0:
            slides = result.get("slides")
            if isinstance(slides, list) and slides and isinstance(slides[0], dict):
                deck_id = slides[0].get("deck_id")
        if type(deck_id) is not int or deck_id <= 0:
            raise PlatformError("PPTGen Platform returned an invalid confirmation")
        return {
            "deck_id": deck_id,
            "draft_id": draft_id,
            "slide_count": len(slide_ids),
            "slide_ids": slide_ids,
            "status": "confirmed",
        }

    def start_generation(
        self,
        *,
        deck_id: int,
        mode: str,
        requirement_text: str | None = None,
    ) -> dict[str, Any]:
        """Start exactly one fixed Image 5.0 run for a confirmed deck.

        The caller chooses only the generation intent.  Auto delegates the
        whole Deck to the existing AutoSkill; Manual carries the exact
        confirmed Deck-wide direction text.  The server owns the strategy,
        config, requirements, colors, model and provider.
        """
        if mode not in IMAGE_GENERATE_MODES:
            raise PlatformError("Image generation mode must be auto or manual")
        if mode == "auto":
            if requirement_text is not None:
                raise PlatformError("Image Auto generation accepts no requirement text")
            payload: dict[str, Any] = {"deck_id": deck_id, "mode": "auto"}
        else:
            if not isinstance(requirement_text, str) or not requirement_text.strip():
                raise PlatformError(
                    "Image Manual generation requires confirmed Deck direction text"
                )
            payload = {
                "deck_id": deck_id,
                "mode": "manual",
                "requirement_text": requirement_text,
            }
        result = _require_dict(
            self._request("POST", "/api/generate", payload, timeout=self.long_timeout),
            "PPTGen Platform returned an invalid Image generation",
        )
        batch_id = result.get("batch_id")
        run_ids = result.get("run_ids")
        if (
            type(batch_id) is not int
            or batch_id <= 0
            or not isinstance(run_ids, list)
            or not run_ids
            or len(run_ids) != 1
            or not all(type(run_id) is int and run_id > 0 for run_id in run_ids)
        ):
            raise PlatformError("PPTGen Platform returned an invalid Image generation")
        return {
            "batch_id": batch_id,
            "config_name": IMAGE_5_0_CONFIG_NAME,
            "deck_id": deck_id,
            "run_ids": run_ids,
            "status": "generation_started",
        }
