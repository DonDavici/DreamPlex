#!/bin/bash
# Script to generate po files outside of the normal build process
#  
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# gawk, find, xgettext, gsed, python, msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the po folder.
#
# Author: Pr2
# Version: 1.3
PluginName=DreamPlex
printf "Po files update/creation from script starting.\n"
#
# Retrieve languages from Makefile.am LANGS variable for backward compatibility
#
# languages=($(gawk ' BEGIN { FS=" " } 
#		/^LANGS/ {
#			for (i=3; i<=NF; i++)
#				printf "%s ", $i
#		} ' Makefile.am ))		
#
# To use the existing files as reference for languages
#
languages=($(ls *.po | gsed 's/\.po//'))		

# If you want to define the language locally in this script uncomment and defined languages
#languages=("ar" "bg" "ca" "cs" "da" "de" "el" "en" "es" "et" "fa" "fi" "fr" "fy" "he" "hk" "hr" "hu" "id" "is" "it" "ku" "lt" "lv" "nl" "nb" "nn" "pl" "pt" "pt_BR" "ro" "ru" "sk" "sl" "sr" "sv" "th" "tr" "uk" "zh")

#
# Arguments to generate the pot and po files are not retrieved from the Makefile.
# So if parameters are changed in Makefile please report the same changes in this script.
#

printf "Creating temporary file $PluginName-py.pot\n"
find -s -X .. -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $PluginName -s -o $PluginName-py.pot {} \+
gsed --in-place $PluginName-py.pot --expression=s/CHARSET/UTF-8/
printf "Creating temporary file $PluginName-xml.pot\n"
find -s -X .. -name "*.xml" -exec python xml2po.py {} \+ > $PluginName-xml.pot
printf "Merging pot files to create: $PluginName.pot\n"
cat $PluginName-py.pot $PluginName-xml.pot | msguniq --no-wrap -o $PluginName.pot -
OLDIFS=$IFS
IFS=" "
for lang in "${languages[@]}" ; do
	if [ -f $lang.po ]; then
		printf "Updating existing translation file %s.po\n" $lang
		msgmerge --backup=none --no-wrap -s -U $lang.po $PluginName.pot && touch $lang.po
		msgattrib --no-wrap --no-obsolete $lang.po -o $lang.po
		msgfmt -o $lang.mo $lang.po
	else \
		printf "New file created: %s.po, please add it to github before commit\n" $lang
		msginit -l $lang.po -o $lang.po -i $PluginName.pot --no-translator
		msgfmt -o $lang.mo $lang.po
	fi
done
rm $PluginName-py.pot $PluginName-xml.pot
IFS=$OLDIFS
printf "Po files update/creation from script finished!\n"


