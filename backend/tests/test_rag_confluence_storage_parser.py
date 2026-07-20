from rag.parsers.confluence_storage import parse_confluence_storage


def test_headings_and_paragraphs_are_converted():
    html = "<h1>Title</h1><p>Some <strong>bold</strong> text.</p>"
    markdown = parse_confluence_storage(html)
    assert "# Title" in markdown
    assert "**bold**" in markdown


def test_lists_are_converted():
    html = "<ul><li>First</li><li>Second</li></ul>"
    markdown = parse_confluence_storage(html)
    assert "- First" in markdown
    assert "- Second" in markdown


def test_table_is_converted_to_markdown_table():
    html = "<table><tr><th>Service</th><th>Owner</th></tr><tr><td>api</td><td>team-a</td></tr></table>"
    markdown = parse_confluence_storage(html)
    assert "| Service | Owner |" in markdown
    assert "| api | team-a |" in markdown


def test_code_macro_is_converted_to_fenced_code_block():
    html = (
        '<ac:structured-macro ac:name="code">'
        "<ac:plain-text-body>systemctl restart nginx</ac:plain-text-body>"
        "</ac:structured-macro>"
    )
    markdown = parse_confluence_storage(html)
    assert "```" in markdown
    assert "systemctl restart nginx" in markdown


def test_code_macro_cdata_content_is_preserved():
    # Confluence's real API response always wraps a code macro's body in a
    # CDATA section (unlike the plain-text fixture above) — CDATA is an
    # XML-only construct that an HTML-mode parser silently drops entirely,
    # which is exactly what happened here before this was parsed as XML.
    html = (
        '<ac:structured-macro ac:name="code">'
        "<ac:plain-text-body><![CDATA[# Recovery steps\n\n1. Restart the pool\n2. Verify connections]]>"
        "</ac:plain-text-body>"
        "</ac:structured-macro>"
    )
    markdown = parse_confluence_storage(html)
    assert "# Recovery steps" in markdown
    assert "1. Restart the pool" in markdown
    assert "2. Verify connections" in markdown


def test_multiple_top_level_elements_are_all_preserved():
    # A real page body is a fragment with many sibling top-level elements,
    # not a single wrapping element — XML requires exactly one root, so
    # without wrapping the fragment first, everything after the first
    # top-level element (here, the second <p>) was silently dropped.
    html = "<h1>Title</h1><p>First paragraph.</p><p>Second paragraph.</p>"
    markdown = parse_confluence_storage(html)
    assert "# Title" in markdown
    assert "First paragraph." in markdown
    assert "Second paragraph." in markdown


def test_admonition_macro_is_converted():
    html = (
        '<ac:structured-macro ac:name="warning">'
        "<ac:rich-text-body><p>Do not restart during business hours.</p></ac:rich-text-body>"
        "</ac:structured-macro>"
    )
    markdown = parse_confluence_storage(html)
    assert "Warning" in markdown
    assert "Do not restart during business hours." in markdown


def test_navigational_macros_are_stripped():
    html = '<ac:structured-macro ac:name="toc"></ac:structured-macro><p>Real content.</p>'
    markdown = parse_confluence_storage(html)
    assert "Real content." in markdown


def test_scripts_are_stripped_and_never_treated_as_instructions():
    html = "<script>alert('xss')</script><p>Safe content.</p>"
    markdown = parse_confluence_storage(html)
    assert "script" not in markdown.lower()
    assert "Safe content." in markdown


def test_links_are_converted():
    html = '<a href="https://example.atlassian.net/wiki/page">Runbook</a>'
    markdown = parse_confluence_storage(html)
    assert "[Runbook](https://example.atlassian.net/wiki/page)" in markdown
