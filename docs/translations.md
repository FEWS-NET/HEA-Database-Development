# Updating translations

The HEA Warehouse holds the gettext catalogs for both the Django backend and the
Livelihoods Explorer (LEX) frontend. Translators work on the `.po` files in this
repository, and `compilemessages` builds them into `.mo` files when containers start
(see `docker/app/run_django.sh`). `.mo` files are not committed.

| Domain     | Source                                            | Catalogs                                         |
|------------|---------------------------------------------------|--------------------------------------------------|
| `django`   | Python and templates in this repository           | `locale/<lang>/LC_MESSAGES/django.po`,           |
|            |                                                   | `apps/<app>/locale/<lang>/LC_MESSAGES/django.po` |
| `djangojs` | `gettext('…')` calls in the Explorer React source | `locale/<lang>/LC_MESSAGES/djangojs.po`          |

The languages are `ar`, `es`, `fr` and `pt` (see `LANGUAGES` in `hea/settings/base.py`).
English is the source language and has no catalog.

LEX loads the compiled `djangojs` catalog from the `/{language}/jsi18n/` endpoint. The Livelihoods Explorer
does not keep any `.po` files of its own.

An update has two stages, and each stage gets its own commit so that the new strings can
be reviewed separately:

1. Refresh the `django` catalogs from this repository's `main`.
2. Refresh the `djangojs` catalogs from LEX's `main`.

The examples below assume that the Livelihoods Explorer is checked out next to this repository, at `../lex`,
and that the frontend is in `../lex/hea-baseline-explorer`.

## Stage 1: Django messages

```bash
# Set aside the current work. Include untracked files: makemessages scans every file under
# the repository root, so untracked work-in-progress code would leak into the catalogs.
git stash push --include-untracked -m "Before translation update"

git checkout main
git pull

# Create the ticket branch for the translation update
git checkout -b HEA-999/update_translations

source .venv/bin/activate
./manage.py makemessages --all

# Stage the refreshed catalogs for review
git add 'locale/*/LC_MESSAGES/django.po' 'apps/*/locale/*/LC_MESSAGES/django.po'
```

Run `makemessages` from the repository root. It writes each string to the nearest
`locale/` directory, which means strings from `apps/baseline` go to
`apps/baseline/locale`, and everything else goes to the root `locale/` directory.

Do **not** run `makemessages -d djangojs` in this repository. The frontend lives
in the Livelihoods Explorer repository, so that command would replace the `djangojs`
catalogs with strings from this repository's own static JavaScript.

After reviewing the staged diff, commit it:

```bash
git commit -m "Add new Django translation strings - see HEA-999"
```

## Stage 2: LEX (JavaScript) messages

Django's `makemessages` cannot reliably extract strings from TypeScript and TSX files,
so LEX strings are extracted with an npm command based on
[`gettext-extractor`](https://www.npmjs.com/package/gettext-extractor). The script
(`scripts/extract-translations.cjs` in LEX) scans `src/**/*.{js,jsx,ts,tsx}` for
`gettext('…')` calls and writes `locale/explorer.pot`. That file is gitignored in LEX.

```bash
cd ../lex
git stash push -m "Before translation update"   # only if the working tree has changes
git checkout main
git pull

cd hea-baseline-explorer
npm ci
npm run extract-translations    # writes locale/explorer.pot
cd ../../hea
```

The `extract-translations` npm script was added in HEA-1439. LEX's own
`docs/i18n.md` documents the extraction from the frontend side.

Merge the template into each language's `djangojs.po`, back in this repository. The
`msgmerge` options are the same ones that `makemessages` uses: they keep existing
translations, add new strings with an empty `msgstr`, and record the previous `msgid` of
any entry that msgmerge fuzzy-matched.

```bash
for lang in ar es fr pt; do
    msgmerge --quiet --backup=none --previous --update \
        "locale/$lang/LC_MESSAGES/djangojs.po" \
        ../lex/hea-baseline-explorer/locale/explorer.pot
done

git add 'locale/*/LC_MESSAGES/djangojs.po'
```

Check the staged diff. The `#:` source references should begin with `src/`. New strings
appear with `msgstr ""`, and strings that LEX no longer uses become obsolete `#~`
entries. Then commit:

```bash
git commit -m "Update djangojs.po files - see HEA-999"
```

## Afterwards

- Fill in the empty `msgstr` entries and resolve the `#, fuzzy` entries. Translators
  can do this in the `.po` files directly or with a tool such as Poedit.
- Run `./manage.py compilemessages` to check that the catalogs compile. To check the LEX
  strings, load `/{language}/jsi18n/` in a browser.
- Return to the previous work: `git checkout <previous-branch> && git stash pop`, and
  the same in LEX if you stashed anything there.
