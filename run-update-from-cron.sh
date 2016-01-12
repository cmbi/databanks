#!/bin/sh

cd /data/bin/
rm -f /data/flags/*
/usr/local/bin/mrs-lock-and-run /data/status/UPDATE_LOCK \
   ./update-databanks -rRk 2>&1 | mail -s cmbi4-update cbaakman@cmbi.ru.nl
