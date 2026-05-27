from pathlib import Path


def register_skills(mcp) -> None:
    """Scan *.md files in this directory and register each as a FastMCP prompt.

    Each .md file should be structured as:

        # Skill Title (heading — used as the prompt name, not the description)

        One-sentence description used for prompt discovery. This is what the LLM
        sees when deciding whether to invoke the skill, so it should name the key
        outputs and the trigger condition (e.g. "Use when the user asks to...").

        ## Steps
        ...full instructions...

    The discovery description is the first non-heading, non-blank line in the file.
    """
    skills_dir = Path(__file__).parent

    for md_file in sorted(skills_dir.glob("*.md")):
        name = md_file.stem
        content = md_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        # First non-blank, non-heading line becomes the prompt description shown during discovery.
        description = next((l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")), name)

        def _make(c):
            def fn() -> str:
                return c
            return fn

        fn = _make(content)
        fn.__name__ = name
        fn.__doc__ = description
        mcp.prompt(name=name)(fn)
