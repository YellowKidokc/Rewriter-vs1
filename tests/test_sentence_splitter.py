import unittest

from app.core.sentence_splitter import split_document, split_sentence_text


class SentenceSplitterTests(unittest.TestCase):
    def test_preserves_common_abbreviations(self) -> None:
        text = "Dr. Smith cited Fig. 1. The result held."
        self.assertEqual(
            split_sentence_text(text),
            ["Dr. Smith cited Fig. 1.", "The result held."],
        )

    def test_keeps_decimal_inside_sentence(self) -> None:
        text = "The reported correlation reached 6.35 sigma. That is not proof by itself."
        self.assertEqual(
            split_sentence_text(text),
            ["The reported correlation reached 6.35 sigma.", "That is not proof by itself."],
        )

    def test_splits_markdown_sections(self) -> None:
        sections = split_document("# Opening\n\nFirst sentence. Second sentence.\n\n## Proof\n\nNoether applies.")
        self.assertEqual([section.title for section in sections], ["Opening", "Proof"])
        self.assertEqual([sentence.id for sentence in sections[0].sentences], ["s0001", "s0002"])
        self.assertEqual(sections[1].sentences[0].section, "Proof")


if __name__ == "__main__":
    unittest.main()
