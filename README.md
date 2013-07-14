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
* no `setup.py` yet
* no support for raw_input
* output is displayed _after_ the command returned, i.e. running something
  like
  
    ```python
    for i in range(0, 10):
      time.sleep(1)
      print i
    ```
    
  will block for 10 seconds and after that display the full output at once.
  
## Dependencies
The only dependency is the *PyGObject introspection* module that can be found in
the package repositories of most Linux distributions.
  
## Installation
There's no `setup.py` installation script yet, so to use the package
`gtkpyinterpreter` just copy the complete package directory to a location in
your Python path.

## License
GPL 3
