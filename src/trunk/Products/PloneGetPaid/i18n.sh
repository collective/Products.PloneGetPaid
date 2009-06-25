#!/bin/sh

#This script must be executed from the product folder.
#i18ndude should be available in current $PATH

i18ndude rebuild-pot --pot i18n/plonegetpaid.pot --create plonegetpaid --merge i18n/manual.pot ./

for file in i18n/plonegetpaid-??.po
do
    echo Syncing $file ...
    i18ndude sync --pot i18n/plonegetpaid.pot $file
done

for file in i18n/plonegetpaid-plone-??.po
do
    echo Syncing $file ...
    i18ndude sync --pot i18n/plonegetpaid-plone.pot $file
done

#Caveman style extraction of message ids from settings.zcml
#grep title="" browser/settings.zcml | sed -e "s/.*title=/msgid /g"

#Optional command sequence which prints all the supposedly untranslated strings in page templates

#pagetemplates=`find . -iregex ".*pt"`
#i18ndude find-untranslated $pagetemplates
