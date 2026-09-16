"""Built-in starter configs offered by the New Config dialog."""

from __future__ import annotations

from typing import List, Optional

from ui.models.preset import Preset


class PresetLibrary:
    """Collection of shipped organize YAML templates."""

    def __init__(self) -> None:
        self._presets: List[Preset] = [
            Preset(
                id="blank",
                title="Blank config",
                description="A single echo rule you can replace.",
                yaml="""\
# organize configuration file
# https://organize.readthedocs.io

rules:
  - name: Hello
    locations: ~
    actions:
      - echo: "Hello from organize"
""",
            ),
            Preset(
                id="sort-downloads",
                title="Sort Downloads by type",
                description="Move common file types from ~/Downloads into dated folders.",
                yaml="""\
rules:
  - name: Images
    locations: ~/Downloads
    filters:
      - extension:
          - jpg
          - jpeg
          - png
          - gif
          - webp
          - heic
      - created
    actions:
      - move: ~/Pictures/Downloads/{created.strftime('%Y-%m')}/

  - name: Documents
    locations: ~/Downloads
    filters:
      - extension:
          - pdf
          - docx
          - odt
          - txt
          - md
      - created
    actions:
      - move: ~/Documents/Downloads/{created.year}/

  - name: Archives
    locations: ~/Downloads
    filters:
      - extension:
          - zip
          - tar
          - gz
          - 7z
          - rar
    actions:
      - move: ~/Downloads/Archives/
""",
            ),
            Preset(
                id="invoices",
                title="Sort invoices and receipts",
                description="Find invoice-like PDFs and file them under Documents/Shopping.",
                yaml="""\
rules:
  - name: Sort invoices and receipts
    locations: ~/Downloads
    subfolders: true
    filters:
      - extension: pdf
      - name:
          contains:
            - Invoice
            - Order
            - Purchase
            - Receipt
          case_sensitive: false
    actions:
      - echo: "Filing {name}"
      - move: ~/Documents/Shopping/
""",
            ),
            Preset(
                id="duplicates",
                title="Find duplicates",
                description="List duplicate files in Desktop and Downloads (dry-run first!).",
                yaml="""\
rules:
  - name: Show duplicates
    locations:
      - ~/Desktop
      - ~/Downloads
    subfolders: true
    filters:
      - not empty
      - duplicate
      - name
    actions:
      - echo: "{name} is a duplicate of {duplicate.original}"
""",
            ),
            Preset(
                id="empty-dirs",
                title="Remove empty folders",
                description="Recursively trash empty directories under Downloads.",
                yaml="""\
rules:
  - name: Trash empty folders
    targets: dirs
    locations: ~/Downloads
    subfolders: true
    filters:
      - empty
    actions:
      - echo: "Empty folder {path}"
      - trash
""",
            ),
            Preset(
                id="desktop-cleanup",
                title="Clean the Desktop",
                description="File old Desktop items into an archive folder by year.",
                yaml="""\
rules:
  - name: Archive old desktop files
    locations: ~/Desktop
    filters:
      - lastmodified:
          days: 30
          mode: older
    actions:
      - move: ~/Documents/Desktop Archive/{now().year}/
""",
            ),
            Preset(
                id="pdf-by-year",
                title="PDFs by year created",
                description="Sort PDFs into folders named after their creation year.",
                yaml="""\
rules:
  - name: Sort PDFs by year
    locations: ~/Documents
    filters:
      - extension: pdf
      - created
    actions:
      - move: ~/Documents/PDF/{created.year}/
""",
            ),
        ]

    def all(self) -> List[Preset]:
        """Return every shipped preset."""
        return list(self._presets)

    def default(self) -> Preset:
        """Return the blank starter preset."""
        return self._presets[0]

    def by_id(self, preset_id: str) -> Optional[Preset]:
        """Look up a preset by its stable id."""
        for preset in self._presets:
            if preset.id == preset_id:
                return preset
        return None
