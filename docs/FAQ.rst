FAQ
==========================

.. contents::
   :local:

How to make the input form not disappear after submission, and can continue to receive input?
----------------------------------------------------------------------------------------------

The design of PyWebIO is that the input form is destroyed after successful submission. The input function of PyWebIO is blocking. Once the form is submitted, the input function returns. So it is meaningless to leave the form on the page after submission of form. If you want to make continuous input, you can put input and subsequent operations into a ``while`` loop.


How to output an input widget such as a search bar?
----------------------------------------------------------

Unfortunately, PyWebIO does not support outputting input widget to the page as general output widget.
Because this will make the input asynchronous, which is exactly what PyWebIO strives to avoid. Callbacks will increase the complexity of application development. PyWebIO does not recommend relying too much on the callback mechanism, so it only provides a little support.
However, there is a compromise way to achieve similar behavior: just put a button (`put_buttons() <pywebio.output.put_buttons>`) where the input widget needs to be displayed, and in the button's callback function, you can call the input function to get input and perform subsequent operations.


Why the callback of ``put_buttons()`` does not work?
----------------------------------------------------------

In general, in Server mode, once the task function returns (or in Script mode, the script exits), the session closes. After this, the event callback will not work. You can call the `pywebio.session.hold()` function at the end of the task function (or script) to hold the session, so that the event callback will always be available before the browser page is closed by user.


Why I cannot download the file using ``put_file()``?
----------------------------------------------------------

The reason is the same as above. The page needs to request server for data when the download button is clicked, so the download link will be unavailable after the session is closed. You can use the `pywebio.session.hold()` function at the end of the task function to hold the session.