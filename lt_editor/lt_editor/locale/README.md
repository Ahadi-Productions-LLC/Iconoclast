# Install PyBabel

You will need this python library to create new translation files.

`pip install Babel`

# Important Commands

To regenerate all symbols to be translated:

`pybabel extract app/editor/ -o locale/base.pot`

`pybabel update -i locale/base.pot -d locale`

To initialize new language locale (replace `en_US` with language code of choice)

`pybabel init -l en_US -i locale/base.pot -d locale`

To finalize and compile language pack:

`pybabel compile -d locale`


# Creating a new translation

Run the first two commands above; this extracts every symbol that needs to be translated, and updates `base.pot`, which is a masterlist, as well as the subordinate `locale.po` files,
which contain the translations.

Then, enter the directory locale of choice - e.g. `locale/zh_CN/LC_MESSAGES`. Open the `.po` file: `locale/zh_CN/LC_MESSAGES/messages.po`. This will contain a copied masterlist
of all strings extant in the editor that need to be translated. Edit the `msgstr` field to provide the translation to the `msgid` field directly above.

Finally, run the compilation step (4th command above), and start the editor. Notice that the translation has taken.

# Converting editor strings to translation symbols

This part is very simple. If you see a string you wish to translate, surround it with `_()`. This will automatically turn it into a translation symbol.