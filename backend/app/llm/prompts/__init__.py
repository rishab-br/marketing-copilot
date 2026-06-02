"""Agent prompts live here — one module per agent prompt.

Keep prompts out of business logic so they can be versioned independently
(sets up v2 prompt versioning). Agent modules import their prompt from here.
"""
