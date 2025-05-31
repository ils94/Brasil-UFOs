# Brasil-UFOs

Here I post scripts to help download PDFs related to anything from the Brazilian National Archive (SIAN).

The **Tampermonkey script** injects JavaScript into the page and allows you to extract all the PDF paths from the buttons with just one click.

The **Python script** processes all the `.txt` files you saved and downloads each PDF. It's important to save the `.txt` files with numeric names (1, 2, 3, ...) because the script uses `range()` to easily loop through all the files containing the links.
