from talon import Context, Module, actions
from dataclasses import dataclass
from ...apps.vscode.vscode import is_untitled


@dataclass
class Language:
    id: str
    extension: str
    spoken_form: str


languages = [
    Language("batch", "bat", "batch"),
    Language("c", "c", "see"),
    Language("cplusplus", "cpp", "see plus plus"),
    Language("csharp", "cs", "see sharp"),
    Language("csv", "csv", "csv"),
    Language("css", "css", "css"),
    Language("go", "go", "go"),
    Language("html", "html", "html"),
    Language("java", "java", "java"),
    Language("javascript", "mjs", "java script"),
    Language("javascript", "js", "java script"),
    Language("javascriptreact", "jsx", "react"),
    Language("json", "json", "json"),
    Language("jsonl", "jsonl", "json lines"),
    Language("lua", "lua", "lua"),
    Language("markdown", "md", "mark down"),
    Language("perl", "pl", "perl"),
    Language("plaintext", "txt", "text"),
    Language("powershell", "ps1", "power shell"),
    Language("python", "py", "python"),
    Language("php", "php", "php"),    
    Language("r", "r", "are"),
    Language("ruby", "rb", "ruby"),
    Language("shellscript", "sh", "shell script"),
    Language("scm", "scm", "tree sitter"),
    Language("talon", "talon", "talon"),
    Language("talon-list", "talon-list", "talon list"),
    Language("typescript", "ts", "type script"),
    Language("typescriptreact", "tsx", "type script react"),
    Language("xml", "xml", "xml"),
]

extension_lang_map = {
    **{f".{l.extension}": l.id for l in languages},
    ".bashbook": "bash",
    ".ipynb": "python",
    ".h": "c",
}

language_ids = set(extension_lang_map.values())
forced_language = None

mod = Module()

mod.list("code_extension", "List of file programming languages file extensions")
mod.list("code_language", "List of file programming language identifiers")

# Add a tag for each forced language mode
for lang in language_ids:
    mod.tag(f"code_{lang}_forced")


ctx = Context()
ctx.matches = r"""
mode: command
"""

ctx_vscode = Context()
ctx_vscode.matches = r"""
mode: command
app: vscode
"""

ctx_other = Context()


ctx.lists["self.code_extension"] = {
    **{l.spoken_form: l.extension for l in languages},
    "pie": "py",
}

ctx.lists["self.code_language"] = {l.spoken_form: l.id for l in languages}


# Disable `code.language` when not in command mode
@ctx_other.action_class("code")
class OtherCodeActions:
    def language() -> str:
        return ""


# Vscode specific `code.language`
@ctx_vscode.action_class("code")
class VscodeCodeActions:
    def language() -> str:
        # New untitled files are markdown in vscode
        if not forced_language and is_untitled(actions.win.filename()):
            return "markdown"
        return actions.next()


@ctx.action_class("code")
class CodeActions:
    def language() -> str:
        if forced_language:
            return forced_language
        file_extension = actions.win.file_ext()
        return extension_lang_map.get(file_extension, "")


@mod.action_class
class Actions:
    def code_set_language(language: str):
        """Forces the active programming language to <language> and disables extension matching"""
        global forced_language
        forced_language = language
        # Update tags to force a context refresh. Otherwise `code.language` will not update.
        ctx.tags = [f"user.code_{language}_forced"]

    def code_automatic_language():
        """Clears the forced language and re-enables code.language: extension matching"""
        global forced_language
        forced_language = None
        ctx.tags = []