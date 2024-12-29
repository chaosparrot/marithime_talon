# Supported programs

This is a list of programs that are known to be supported. Others might have varying degrees of support depending on how well accessibility is handled. Testing is generally done on the beta release of Talon Voice, for windows on Windows 11 ( 10 if specifically mentioned ).

## Operating system support

Both Windows and MacOS have supported accessibility APIs, which allow us to introspect the currently focused text area in great detail, but Linux does not. For that reason, Linux doesn't have as good of a user experience since we cannot poll the content of a text area directly.

## Browser support

TODO

## Word processor support

TODO

## Code editor / IDE support

| Program         | OS      | Cursor tracking | Content tracking | Notes |
|-----------------|---------|-----------------|------------------|-------|
| VSCode editor   | Windows | Yes*            | Yes*             | This requires turning on accessiblity support |
| VSCode editor   | MacOS   | Yes*            | Yes*             | This requries turning on accessibility support `Shift+Option+F1`|

## Terminal support

| Program         | OS      | Cursor tracking | Content tracking | Selection | Notes |
|-----------------|---------|-----------------|------------------|-----------|-------|
| Terminal        | Windows | Key tracking    | Key tracking     | Virtual   |       |
| Git BASH        | Windows | Key tracking    | Key tracking     | Virtual   |       |
| CMD             | Windows | Key tracking    | Key tracking     | Virtual   |       |
| Cygwin          | Windows | Key tracking    | Key tracking     | Virtual   |       |
| ConEmu          | Windows | Key tracking    | Key tracking     | Virtual   |       |
| Cmder           | Windows | Key tracking    | Key tracking     | Shift     |       |
| PowerShell      | Windows | Key tracking    | Key tracking     | Shift     |       |
| VSCode terminal | Windows | Key tracking    | Key tracking     | Virtual   | This requires [changing the windows title as described in talonhub community](https://github.com/talonhub/community/tree/main/apps/vscode#terminal) |

Terminal programs generally aren't as well supported as other programs with are more rich set of accessibility APIs. Not to mention that text editors such as VIM, emacs and nano each have their own set of hotkeys to navigate the text displayed, so key tracking becomes increasingly hard to do and prone for desyncs.

It seems that the `TextPattern` is supported on Windows 11 for terminals, so it might be worth exploring this more in the future, though each terminal program has a different leading character set ( '$ ' for bash-likes, `λ ` for Cmder, '...>' for PowerShell et cetera ) and we can realistically only support single line programs for now.

While it is possible to tackle this, it is also quite hard to do without major time investments and plugins designed for each text editor available.

Terminals are detected by the `tag: terminal` which is generally retrieved from .talon files like the ones shown in the talon community repository.

### Virtual selection

Virtual selection is used when shift selection isn't supported. What this boils down to is that the text caret will be set after the selected text. Follow up commands, like inserting text, will be have as if the text was actually selected, meaning we would replace the selection in the case of replacing text. This allows you to continue using the same exact commands without worrying about the internals of the specific programs.

While it would be possible to support text selection like the mode supported by holding down Shift in ConEmu, or using mark modes like the ones shown when pressing `Ctrl+Shift+M` in a windows terminal, doing so would further complicate selection, and might not work with Text editors either.