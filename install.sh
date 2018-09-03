BIN=/srv/data/bin

install -m755 backup.sh $BIN/backup.sh

install -m755 update.py $BIN/update.py
install -m755 -d $BIN/databanks/
for module in databanks/*.py ; do
    install -m755 $module $BIN/databanks/$(basename $module)
done

install -m755 -d $BIN/mrs
install -m755 mrs/update $BIN/mrs/update
install -m755 mrs/weekly $BIN/mrs/weekly
install -m755 mrs/daily $BIN/mrs/daily

install -m755 cleanup $BIN/cleanup

pip install -r requirements.txt
