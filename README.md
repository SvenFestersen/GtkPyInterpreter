# GtkPyInterpreter
This widget implements a simple interactive Python command line in a
Gtk.TextView. The implementation is pure Python and makes use of
`code.InteractiveInterpreter` included in the Python standard library. Since
*GtkPyInterpreter* uses *Gtk3*, it heavily depends on GObject introspection
(`PyGObject`).

## Features
* input and output of the Python interpreter in Gtk.TextView widget
* support for multiline code input
* command history
* pass predefined locals to the widget that become available in the interpreter
* various settings to change the appearance
* signals for stdout and stderr write operations

## Known bugs/limitations
* no support for raw_input
* output is displayed _after_ the command returned, i.e. a running something
  like
  
    ```python
    for i in range(0, 10):
      time.sleep(1)
      print i
    ```
    
  will block for 10 seconds and after that display the full output at once.

## Dependencies
The only dependency is `PyGObject`.

## License
GPL 3
