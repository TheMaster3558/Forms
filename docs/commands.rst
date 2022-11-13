Commands
========

``form <name> [finishes_in=1] [responses_channel=None]``
------------------------------------------------------------------------------------

Create a form!

Parameters
~~~~~~~~~~
name: Required[``Text``]
    The name of the form.

finishes_in: Optional[``Number``]
    The hours to finish the form in.

responses_channel: Optional[``TextChannel``]
    The channel to send the form responses in, defaults to DMs.


------------------------------


``finish <form_name> [send_here=False]``
----------------------------------------

Finish a form early.

Parameters
~~~~~~~~~~
form_name: Required[``Text``]
    The name of the form.

send_here: Optional[``Boolean``]
    Whether to send the results in this channel.

------------------------------


``info``
--------

Get information about the bot.

Parameters
~~~~~~~~~~
This command has no parameters.


------------------------------


``report``

Report a bug. This is not a support command.

Parameters
~~~~~~~~~~
This command has no parameters.
