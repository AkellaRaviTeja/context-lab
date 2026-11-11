"""lantern.pages: the pages on file and the cut-off."""

from lantern import baseline, context, pages


def test_twelve_pages_of_each_kind_and_none_answers_a_signed_question():
    related, unrelated = pages.load("related"), pages.load("unrelated")
    assert len(related) == len(unrelated) == 12
    about = ("Pellmar", "PNL-", "nominee", "MTB-31-02290")
    assert all(any(w in p.text for w in about) for p in related)
    assert not any("Pellmar" in p.text for p in unrelated)
    text = baseline.normal(" ".join(p.text for p in related + unrelated))
    for q in baseline.questions():
        if q["slice"] == "evidence":
            for value in q["expect"].get("all", []):
                assert baseline.normal(value) not in text, (q["id"], value)


def test_pages_join_the_system_message_after_the_summaries():
    parts = context.sections()
    out = pages.with_pages(parts, pages.load("related")[:2])
    names = [s.name for s in out]
    assert names.index(pages.NAME) == names.index("summary week-2026-07-06") + 1
    assert pages.with_pages(parts, []) == parts


def test_select_records_every_page_it_leaves_out():
    pool = pages.load("related")
    kept, left = pages.select(pool, "How much is held at the reserve under MTB-ORD-0001?", 0.5)
    assert [p.path for p in kept] == ["pages/related/p07.md", "pages/related/p08.md"]
    assert len(kept) + len(left) == len(pool)
