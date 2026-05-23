"""Lunar regolith contact and morphology models.

This sub-package consolidates code that previously lived under
``results/GPT/Robotics/`` so there is a single canonical copy of the contact
model. The ``results/GPT/Robotics/`` directory now holds only the generated
artifacts (figures, CSVs, reports) these scripts produce.

Import as ``models.contact`` with the ``weevil-lunar/`` directory on sys.path,
matching the existing convention used for ``models.lunar_integrated_weevil_leg``.
"""

from models.contact.regolith_contact_model import (
    ContactForces,
    FootGeometry,
    RegolithContactModel,
    RegolithProperties,
    RegolithType,
)

__all__ = [
    "ContactForces",
    "FootGeometry",
    "RegolithContactModel",
    "RegolithProperties",
    "RegolithType",
]
