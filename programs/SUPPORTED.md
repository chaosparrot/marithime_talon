# Supported programs

This is a list of programs that are known to be supported. Others might have varying degrees of support depending on how well accessibility is handled.

## Operating system support

Both Windows and MacOS have supported accessibility APIs, which allow us to introspect the currently focused text area in great detail, but Linux does not. For that reason, Linux doesn't have as good of a user experience since we cannot poll the content of a text area directly.

## Browser support

TODO

## Word processor support

TODO

## Code editor / IDE support

| Program         | OS      | Cursor tracking | Content tracking | Selection | Notes |
|-----------------|---------|-----------------|------------------|-----------|-------|
| VSCode editor   | Windows | Yes*            | Yes*             | Shift     | This requires turning on accessiblity support |
| VSCode editor   | MacOS   | Yes*            | Yes*             | Shift     | This requries turning on accessibility support `Shift+Option+F1`|

## Terminal support

| Program         | OS      | Cursor tracking | Content tracking | Selection | Notes |
|-----------------|---------|-----------------|------------------|-----------|-------|
| Terminal        | Windows | Key tracking    | Key tracking     | Virtual   | No accessibility APIs used |
| Git BASH        | Windows | Key tracking    | Key tracking     | Virtual   | No accessibility APIs used |
| CMD             | Windows | Key tracking    | Key tracking     | Virtual   | No accessibility APIs used |
| PowerShell      | Windows | Key tracking    | Key tracking     | Shift     | PowerShell supports shift selection! |

Terminal programs generally aren't as well supported as other programs with are more rich set of accessibility APIs. Not to mention that text editors such as VIM, emacs and nano each have their own set of hotkeys to navigate the text displayed, so key tracking becomes increasingly hard to do and prone for desyncs.

While it is possible to tackle this, it is also quite hard to do without major time investments and plugins designed for each text editor available.