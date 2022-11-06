Commands
========

``form <name> <channel> [finishes_in=1] [responses_channel=None] [anonymous=False]``
------------------------------------------------------------------------------------

Create a form!

Parameters
~~~~~~~~~~
name: Required[``Text``]
    The name of the form.

channel: Required[``TextChannel``]
    The channel to send the form in.

finishes_in: Optional[``Number``]
    The hours to finish the form in.

responses_channel: Optional[``TextChannel``]
    The channel to send the form responses in, defaults to DMs.

anonymous: Optional[``Boolean``]
    Whether the form is anonymous.


------------------------------


``finish <message> [send_here=False]``
--------------------------------------

Finish a form early.

Parameters
~~~~~~~~~~
message: Required[``MessageLink`` or ``MessageID``]
    The link or ID to the message that you can start the form from.

send_here: Optional[``Boolean``]
    Whether to send the results in this channel.

------------------------------


``help [command=None]``
-----------------------

The help command for this bot.

Parameters
~~~~~~~~~~
command: Optional[``Text``]
    The command to get help with.

------------------------------


``info``
--------

Get information about the bot.

Parameters
~~~~~~~~~~
This command has no parameters.
